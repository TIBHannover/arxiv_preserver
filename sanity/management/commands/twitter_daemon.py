from django.core.management.base import BaseCommand, CommandError
import sanity.models as models
import re
import urllib.request
import urllib.parse
import time
import datetime
import dateutil.parser
import os

import multiprocessing
import functools
from django.conf import settings

from django.db.models import Max

from django.db import transaction

#TODO catch url param
paper_url_re = re.compile(r'^.*?arxiv.org/abs/(.+?)(v\d+)?$')


def find_paper_ids(tweet):
    ids = []
    for link in tweet.urls:
        match = re.match(paper_url_re, link.expanded_url)
        if match:
            ids.append(match.group(1))
    return ids


# tweet_id = models.CharField(max_length=128)
#
# papers = models.ManyToManyField(User)
#
# text = models.DateField()
# lang = models.CharField(max_length=64)
# date = models.CharField(max_length=64)
# user_image = models.CharField(max_length=256)
# user_name = models.CharField(max_length=256)
# user_follower = models.IntegerField()
# user_following = models.IntegerField()


class Command(BaseCommand):
    help = 'Closes the specified poll for voting'
    api = None

    def add_arguments(self, parser):
        parser.add_argument('-d', '--daemon', action='store_true', help='Path to the pdf file')

    def handle(self, *args, **options):

        if not settings.USE_TWITTER:
            self.stdout.write(self.style.ERROR('Twitter is disabled in settings'))
            return
        self._login()
        if self.api is None:
            return
        if options['daemon']:
            while True:
                self._search()
                time.sleep(60 * 10)

        else:
            self._search()

    def _login(self):
        try:
            import twitter

        except ModuleNotFoundError:
            self.stdout.write(self.style.ERROR('Couldn\'t find package twitter-python'))
            return
        self.api = twitter.Api(
            consumer_key=settings.TWITTER_AUTH['consumer_key'],
            consumer_secret=settings.TWITTER_AUTH['consumer_secret'],
            access_token_key=settings.TWITTER_AUTH['access_token_key'],
            access_token_secret=settings.TWITTER_AUTH['access_token_secret'])

    def _search(self):
        not_found = True
        while not_found:
            try:
                result = self.api.GetSearch(raw_query="q=arxiv.org&result_type=recent&count=100")
                not_found = False
            except Exception as e:
                self.stdout.write(self.style.NOTICE('Twitter api timeout. We wait a minute and try again.'))
                time.sleep(60 * 10)

        with transaction.atomic():
            for x in result:
                ids = find_paper_ids(x)
                if len(ids) == 0:
                    continue
                try:
                    tweet = models.Tweet.objects.get(tweet_id=x.id)

                except models.Tweet.DoesNotExist as e:
                    tweet = models.Tweet(tweet_id=x.id)

                tweet.text = x.text
                tweet.lang = x.lang
                tweet.date = dateutil.parser.parse(x.created_at)

                tweet.user_name = x.user.screen_name
                tweet.user_image = x.user.profile_image_url
                tweet.user_follower = x.user.followers_count
                tweet.user_following = x.user.friends_count

                for x in tweet.tweetarxiv_set.all():
                    x.delete()

                # store all informations
                tweet.save()

                for paper_id in ids:
                    try:
                        paper = models.Paper.objects.get(paper_id=paper_id)
                        tweet.papers.add(paper)
                    except models.Paper.DoesNotExist as e:
                        tweet_arxiv = models.TweetArxiv(tweet=tweet, paper_id=paper_id[:30])
                        tweet_arxiv.save()

                tweet.save()
                self.stdout.write(self.style.NOTICE('Store tweet for paper {}'.format(paper_id)))

    def _write_entry(self, tweet, ids):
        pass

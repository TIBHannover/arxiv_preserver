from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

from arxiv_makeover.settings import ES_INDEX

from django.db import transaction

from django.db.models import Q, F, Max, Min, Count, Exists, Case, When, Value, Sum, BooleanField, IntegerField

import os

import datetime
import dateutil.relativedelta
import sanity.search as search

from django.db.models.signals import post_save

from django.db import connection

import logging


class Author(models.Model):
    name = models.CharField(max_length=256, null=True)
    surname = models.CharField(max_length=128, null=True)
    forename = models.CharField(max_length=128, null=True)

    def __str__(self):
        if self.name is not None:
            return self.name
        else:
            return "{} {}".format(self.forename, self.surname)


class Category(models.Model):
    name = models.CharField(max_length=128)

    def __str__(self):
        return self.name


class Paper(models.Model):
    # Idetifier from arxiv
    paper_id = models.CharField(max_length=30, unique=True, db_index=True)
    # Info from oai
    title = models.TextField()
    summary = models.TextField()
    authors = models.ManyToManyField(Author)
    categories = models.ManyToManyField(Category)
    # Library of a user
    users = models.ManyToManyField(User, through="PaperUserRelation")

    page_count = models.IntegerField(null=True)
    pdf_exists = models.BooleanField(default=False)
    png_exists = models.BooleanField(default=False)
    txt_exists = models.BooleanField(default=False)

    first_version = models.ForeignKey("Version", null=True, related_name="+", on_delete=models.SET_NULL)

    last_version = models.ForeignKey("Version", null=True, related_name="+", on_delete=models.SET_NULL)

    url = models.CharField(max_length=128)

    hash = models.CharField(max_length=64, unique=True, db_index=True)
    namespace = models.CharField(max_length=64, default="arxiv")

    def save(self, *args, **kwargs):
        self.first_version = self.version_set.order_by("date").first()
        self.last_version = self.version_set.order_by("-date").first()

        super(Paper, self).save(*args, **kwargs)

    def __str__(self):
        return "{}".format(self.paper_id)

    def to_path(self):
        return os.path.join(self.hash[0:2], self.hash[2:4], self.hash)

    def to_pdf_url(self):
        if self.namespace == "arxiv":
            return "https://arxiv.org/pdf/" + self.paper_id

    @property
    def pdf_url(self):
        return self.to_pdf_url()

    def to_html_url(self):
        if self.namespace == "arxiv":
            return "https://arxiv.org/abs/" + self.paper_id

    @property
    def html_url(self):
        return self.to_html_url()

    @property
    def preview_url(self):
        return os.path.join(settings.MEDIA_URL, "png", self.to_path())

    def indexing(self):
        obj = search.PaperIndex(meta={"id": self.id}, index=ES_INDEX)

        for author in self.authors.all():
            obj.authors.append(search.AuthorIndex(name=author.name, forename=author.forename, surname=author.surname))

        for version in self.version_set.all():
            obj.versions.append(search.VersionIndex(name=version.name, date=version.date))

        for category in self.categories.all():
            obj.categories.append(search.CategoryIndex(name=category.name))

        obj.paper_id = self.paper_id
        obj.title = self.title
        obj.summary = self.summary
        # TODO indexing text to
        obj.text = ""
        obj.url = self.url
        obj.save(index=ES_INDEX)
        return obj.to_dict(include_meta=True)


def create_index(sender, instance, **kwargs):
    print("############# Create Index ##############")
    print(instance)
    if not hasattr(instance, "paperindex"):
        index = PaperIndex.objects.create(paper=instance)
        index.save()


post_save.connect(create_index, sender=Paper)


class PaperIndex(models.Model):

    paper = models.OneToOneField(Paper, on_delete=models.CASCADE, primary_key=True)

    date_last = models.IntegerField(null=True, unique=True, db_index=True)
    date_first = models.IntegerField(null=True, unique=True, db_index=True)

    library = models.IntegerField(null=True, db_index=True)
    library_last_y = models.IntegerField(null=True, db_index=True)
    library_last_m = models.IntegerField(null=True, db_index=True)
    library_last_w = models.IntegerField(null=True, db_index=True)
    library_last_d = models.IntegerField(null=True, db_index=True)

    tweet = models.IntegerField(null=True, db_index=True)
    tweet_last_y = models.IntegerField(null=True, db_index=True)
    tweet_last_m = models.IntegerField(null=True, db_index=True)
    tweet_last_w = models.IntegerField(null=True, db_index=True)
    tweet_last_d = models.IntegerField(null=True, db_index=True)

    @staticmethod
    def generate():
        with connection.cursor() as cursor:
            print(PaperIndex.objects.order_by("paper__last_version__date").query)
            index_name = PaperIndex._meta.db_table
            paper_name = Paper._meta.db_table

            # update date

            cursor.execute(
                "CREATE OR REPLACE TEMPORARY TABLE index_date_last (PRIMARY KEY ( id )) (SELECT sanity_paper.id as id, DATEDIFF(CURDATE(),`sanity_version`.`date`) as date_last from sanity_paper LEFT OUTER JOIN `sanity_version` ON (`sanity_paper`.`last_version_id` = `sanity_version`.`id`));"
            )
            cursor.execute(
                "CREATE OR REPLACE TEMPORARY TABLE index_date_first (PRIMARY KEY ( id )) (SELECT sanity_paper.id as id, DATEDIFF(CURDATE(),`sanity_version`.`date`) as date_first from sanity_paper LEFT OUTER JOIN `sanity_version` ON (`sanity_paper`.`first_version_id` = `sanity_version`.`id`));"
            )

            today = datetime.datetime.utcnow()

            # update tweet

            cursor.execute(
                "CREATE OR REPLACE TEMPORARY TABLE index_tweet (PRIMARY KEY ( id )) (SELECT sanity_paper.id as id, COUNT(`sanity_tweet_papers`.`tweet_id`) as tweet from sanity_paper INNER JOIN `sanity_tweet_papers` ON (`sanity_paper`.`id` = `sanity_tweet_papers`.`paper_id`) INNER JOIN `sanity_tweet` ON (`sanity_tweet_papers`.`tweet_id` = `sanity_tweet`.`id`) GROUP BY `sanity_paper`.`paper_id`)"
            )

            cursor.execute(
                'CREATE OR REPLACE TEMPORARY TABLE index_tweet_last_y (PRIMARY KEY ( id )) (SELECT sanity_paper.id as id, COUNT(`sanity_tweet_papers`.`tweet_id`) as tweet_last_y from sanity_paper INNER JOIN `sanity_tweet_papers` ON (`sanity_paper`.`id` = `sanity_tweet_papers`.`paper_id`) INNER JOIN `sanity_tweet` ON (`sanity_tweet_papers`.`tweet_id` = `sanity_tweet`.`id`) WHERE `sanity_tweet`.`date` >= "{}" GROUP BY `sanity_paper`.`paper_id`)'.format(
                    str(today - dateutil.relativedelta.relativedelta(years=1))
                )
            )

            cursor.execute(
                'CREATE OR REPLACE TEMPORARY TABLE index_tweet_last_m (PRIMARY KEY ( id )) (SELECT sanity_paper.id as id, COUNT(`sanity_tweet_papers`.`tweet_id`) as tweet_last_m from sanity_paper INNER JOIN `sanity_tweet_papers` ON (`sanity_paper`.`id` = `sanity_tweet_papers`.`paper_id`) INNER JOIN `sanity_tweet` ON (`sanity_tweet_papers`.`tweet_id` = `sanity_tweet`.`id`) WHERE `sanity_tweet`.`date` >= "{}" GROUP BY `sanity_paper`.`paper_id`)'.format(
                    str(today - dateutil.relativedelta.relativedelta(months=1))
                )
            )

            cursor.execute(
                'CREATE OR REPLACE TEMPORARY TABLE index_tweet_last_w (PRIMARY KEY ( id )) (SELECT sanity_paper.id as id, COUNT(`sanity_tweet_papers`.`tweet_id`) as tweet_last_w from sanity_paper INNER JOIN `sanity_tweet_papers` ON (`sanity_paper`.`id` = `sanity_tweet_papers`.`paper_id`) INNER JOIN `sanity_tweet` ON (`sanity_tweet_papers`.`tweet_id` = `sanity_tweet`.`id`) WHERE `sanity_tweet`.`date` >= "{}" GROUP BY `sanity_paper`.`paper_id`)'.format(
                    str(today - dateutil.relativedelta.relativedelta(weeks=1))
                )
            )

            cursor.execute(
                'CREATE OR REPLACE TEMPORARY TABLE index_tweet_last_d (PRIMARY KEY ( id )) (SELECT sanity_paper.id as id, COUNT(`sanity_tweet_papers`.`tweet_id`) as tweet_last_d from sanity_paper INNER JOIN `sanity_tweet_papers` ON (`sanity_paper`.`id` = `sanity_tweet_papers`.`paper_id`) INNER JOIN `sanity_tweet` ON (`sanity_tweet_papers`.`tweet_id` = `sanity_tweet`.`id`) WHERE `sanity_tweet`.`date` >= "{}" GROUP BY `sanity_paper`.`paper_id`)'.format(
                    str(today - dateutil.relativedelta.relativedelta(days=1))
                )
            )

            # update library

            cursor.execute(
                "CREATE OR REPLACE TEMPORARY TABLE index_library (PRIMARY KEY ( id )) (SELECT sanity_paper.id as id, SUM(CASE WHEN `sanity_paperuserrelation`.`library` = True THEN 1 ELSE 0 END) as library from sanity_paper LEFT OUTER JOIN `sanity_paperuserrelation` ON (`sanity_paper`.`id` = `sanity_paperuserrelation`.`paper_id`) GROUP BY `sanity_paper`.`paper_id`)"
            )

            cursor.execute(
                'CREATE OR REPLACE TEMPORARY TABLE index_library_last_y (PRIMARY KEY ( id )) (SELECT sanity_paper.id as id, SUM(CASE WHEN `sanity_paperuserrelation`.`library` = True THEN 1 ELSE 0 END) as library_last_y from sanity_paper LEFT OUTER JOIN `sanity_paperuserrelation` ON (`sanity_paper`.`id` = `sanity_paperuserrelation`.`paper_id`) WHERE `sanity_paperuserrelation`.`date` >= "{}" GROUP BY `sanity_paper`.`paper_id`)'.format(
                    str(today - dateutil.relativedelta.relativedelta(years=1))
                )
            )

            cursor.execute(
                'CREATE OR REPLACE TEMPORARY TABLE index_library_last_m (PRIMARY KEY ( id )) (SELECT sanity_paper.id as id, SUM(CASE WHEN `sanity_paperuserrelation`.`library` = True THEN 1 ELSE 0 END) as library_last_m from sanity_paper LEFT OUTER JOIN `sanity_paperuserrelation` ON (`sanity_paper`.`id` = `sanity_paperuserrelation`.`paper_id`) WHERE `sanity_paperuserrelation`.`date` >= "{}" GROUP BY `sanity_paper`.`paper_id`)'.format(
                    str(today - dateutil.relativedelta.relativedelta(months=1))
                )
            )

            cursor.execute(
                'CREATE OR REPLACE TEMPORARY TABLE index_library_last_w (PRIMARY KEY ( id )) (SELECT sanity_paper.id as id, SUM(CASE WHEN `sanity_paperuserrelation`.`library` = True THEN 1 ELSE 0 END) as library_last_w from sanity_paper LEFT OUTER JOIN `sanity_paperuserrelation` ON (`sanity_paper`.`id` = `sanity_paperuserrelation`.`paper_id`) WHERE `sanity_paperuserrelation`.`date` >= "{}" GROUP BY `sanity_paper`.`paper_id`)'.format(
                    str(today - dateutil.relativedelta.relativedelta(weeks=1))
                )
            )

            cursor.execute(
                'CREATE OR REPLACE TEMPORARY TABLE index_library_last_d (PRIMARY KEY ( id )) (SELECT sanity_paper.id as id, SUM(CASE WHEN `sanity_paperuserrelation`.`library` = True THEN 1 ELSE 0 END) as library_last_d from sanity_paper LEFT OUTER JOIN `sanity_paperuserrelation` ON (`sanity_paper`.`id` = `sanity_paperuserrelation`.`paper_id`) WHERE `sanity_paperuserrelation`.`date` >= "{}" GROUP BY `sanity_paper`.`paper_id`)'.format(
                    str(today - dateutil.relativedelta.relativedelta(days=1))
                )
            )

            # join all results
            table_list = [
                "index_date_last",
                "index_date_first",
                "index_tweet",
                "index_tweet_last_y",
                "index_tweet_last_m",
                "index_tweet_last_w",
                "index_tweet_last_d",
                "index_library",
                "index_library_last_y",
                "index_library_last_m",
                "index_library_last_w",
                "index_library_last_d",
            ]
            fields = ", ".join([x.replace("index_", "") for x in table_list])
            fields_with_tbl = ", ".join(
                ["{}.{} as {}".format(x, x.replace("index_", ""), x.replace("index_", "")) for x in table_list]
            )
            print(fields)
            join_str = "CREATE OR REPLACE TABLE {} (PRIMARY KEY ( id ), UNIQUE INDEX ({})) (SELECT sanity_paper.id as id, sanity_paper.id as paper_id, {} FROM sanity_paper".format(
                index_name, fields, fields_with_tbl
            )
            for tbl in table_list:
                join_str += " LEFT OUTER JOIN {} ON (sanity_paper.id = {}.id)".format(tbl, tbl)
            join_str += ")"

            cursor.execute(join_str)

            cursor.execute("SELECT COUNT(*) FROM {} ".format(index_name))

            logging.info("New index contains {} elements.".format(cursor.fetchone()))


def hash_to_path(hash):
    os.path.join(hash[0:2], hash[2:4], hash)


class Version(models.Model):
    name = models.CharField(max_length=128)
    date = models.DateField()

    paper = models.ForeignKey(Paper, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return "{}".format(self.name)


class PaperUserRelation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    paper = models.ForeignKey(Paper, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    # TODO on delete
    library = models.BooleanField(default=False)

    def __str__(self):
        return "{} {}, {}".format(self.user, self.paper.paper_id, self.library)


class PaperUserTag(models.Model):
    name = models.CharField(max_length=128)

    PaperUserRelation = models.ForeignKey(PaperUserRelation, on_delete=models.CASCADE)


class Tweet(models.Model):
    tweet_id = models.CharField(max_length=128, unique=True, db_index=True)

    papers = models.ManyToManyField(Paper)

    text = models.TextField()
    lang = models.CharField(max_length=64)
    date = models.DateTimeField()
    user_image = models.CharField(max_length=256)
    user_name = models.CharField(max_length=256)
    user_follower = models.IntegerField()
    user_following = models.IntegerField()

    class Meta:
        ordering = ["-user_follower"]


class TweetArxiv(models.Model):
    paper_id = models.CharField(max_length=30)
    tweet = models.ForeignKey(Tweet, on_delete=models.CASCADE)

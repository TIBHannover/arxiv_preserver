from django.core.management.base import BaseCommand, CommandError
from django.db.models import Max
import sanity.models as models
import sanity.utils as utils
import xml.etree.ElementTree as ET
import re
import urllib.request
import urllib.parse
import time
import datetime
import os
import sys
import argparse

from django.db import transaction


def create_path(path):
    if not os.path.exists(path):
        os.makedirs(path)


def download(url):
    try:
        with urllib.request.urlopen(url) as response:
            read_data = response.read()

    except urllib.error.HTTPError as e:
        if e.code in (403, 500):
            print(e.code)
            return None

    return read_data


def valid_date(s):
    try:
        return datetime.datetime.strptime(s, "%Y-%m-%d")
    except ValueError:
        msg = "Not a valid date: '{0}'.".format(s)
        raise argparse.ArgumentTypeError(msg)


class Command(BaseCommand):
    help = 'Closes the specified poll for voting'

    def add_arguments(self, parser):
        parser.add_argument('-d', '--dryrun', action='store_true', help='Make no commits on the database')

        subparser = parser.add_subparsers(help='', dest='mode')
        dump_parser_ = subparser.add_parser(cmd='register', name='register', help='')
        dump_parser_.add_argument('-i', '--path', type=str, required=True)

        web_parser_ = subparser.add_parser(cmd='download', name='download', help='')
        web_parser_.add_argument('-o', '--output', type=str)
        web_parser_.add_argument('-c', '--continue', action='store_true')
        web_parser_.add_argument('-f', '--from', type=valid_date)

    def handle(self, *args, **options):

        if options['mode'] == 'register':
            self._register_files(options['path'], not options['dryrun'])

        if options['mode'] == 'download':

            date_from = None
            if options['continue']:
                date_from = models.Paper.objects.filter(pdf_exists=True).aggregate(Max('date'))['date__max']

            if options['from']:
                date_from = options['from']
            self._download_pdf(options['output'], not options['dryrun'], date_from=date_from)

        self.stdout.write(self.style.SUCCESS('Successfully closed poll '))

    def _register_files(self, path, update_db=True, date_from=None):
        self.stdout.write(self.style.NOTICE('Indexing path {}'.format(path)))
        for root, dirs, files in os.walk(path):
            for f in files:
                file_path = os.path.join(root, f)

        for x in models.Paper.objects.filter(pdf_exists=False):
            pdf_path = os.path.join(path, x.to_path())
            if os.path.exists(pdf_path):
                self.stdout.write(self.style.SUCCESS('{}:{} change to pdf_exists=True'.format(x.namespace, x.paper_id)))
                if update_db:
                    x.pdf_exists = True
                    x.save()

    def _download_pdf(self, path, update_db=True, date_from=None):
        if date_from is not None:
            query_set = models.Paper.objects.filter(pdf_exists=False, date__gte=date_from)

        else:
            query_set = models.Paper.objects.filter(pdf_exists=False)
        self.stdout.write(self.style.NOTICE('Start downloading of {} documents.'.format(len(query_set))))
        for x in query_set:

            print(x.date)

            url = x.to_pdf_url()
            data = download(url)
            if data is None:
                self.stdout.write(self.style.ERROR('{}:{} file not found'.format(x.namespace, x.paper_id)))
                continue

            pdf_path = os.path.join(path, x.to_path())
            create_path(pdf_path)
            with open(os.path.join(pdf_path, str(1) + '.pdf'), 'wb') as f:
                f.write(data)

            if update_db:
                x.pdf_exists = True
                x.save()

            self.stdout.write(self.style.SUCCESS('{}:{} downloaded'.format(x.namespace, x.paper_id)))

            time.sleep(0.5)

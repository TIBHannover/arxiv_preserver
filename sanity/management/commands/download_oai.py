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

import sanity.arxiv.download as arxiv_dl


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
        dump_parser_ = subparser.add_parser(cmd='file', name='file', help='')
        dump_parser_.add_argument('-f', '--dump', type=str, required=True)

        web_parser_ = subparser.add_parser(cmd='web', name='web', help='')
        web_parser_.add_argument('-o', '--output', type=str)
        web_parser_.add_argument('-c', '--continue', action='store_true')
        web_parser_.add_argument('-f', '--from', type=valid_date)

    def handle(self, *args, **options):

        if options['mode'] == 'file':
            self._parse_files(options['dump'], not options['dryrun'])

        if options['mode'] == 'web':

            # create dump writer if necessary
            dump_writer = None
            if 'output' in options and options['output']:
                dump_writer = arxiv_dl.DumpWriter(options['output'])

            date_from = None
            if options['continue']:
                date_from = models.Paper.objects.all().aggregate(Max('date'))['date__max']

            if options['from']:
                date_from = options['from']
            self._parse_api(not options['dryrun'], dump_writer, date_from=date_from)

        self.stdout.write(self.style.SUCCESS('Successfully closed poll '))

    def _parse_files(self, path, update_db=True):

        iteration = 0
        if os.path.isfile(path):
            read_data = arxiv_dl.read_file(path)
            resume_token, entries = arxiv_dl.extract_info(read_data)
            if update_db:
                arxiv_dl.write_entries(entries)

            self.stdout.write('Found {} entries in dump'.format(len(entries)))

        elif os.path.isdir(path):
            for root, dirs, files in os.walk(path):
                for f in files:
                    file_path = os.path.join(root, f)
                    try:
                        read_data = arxiv_dl.read_file(file_path)

                        resume_token, entries = arxiv_dl.extract_info(read_data)
                        if update_db:
                            arxiv_dl.write_entries(entries)

                        iteration += 1

                        self.stdout.write('Found {} entries in dump {}'.format(len(entries), iteration))
                    except ET.ParseError:

                        self.stdout.write('Could not parse {}'.format(file_path))

    def _parse_api(self, update_db=True, dump_writer=None, date_from=None):

        if date_from is not None:
            date_from = date_from.strftime('%Y-%m-%d')

        read_data = arxiv_dl.read_oai(date_from=date_from)
        resume_token, entries = arxiv_dl.extract_info(read_data)
        if update_db:
            arxiv_dl.write_entries(entries)

        iteration = 0

        if dump_writer:
            dump_writer.write_dump(read_data, iteration)

        self.stdout.write('Found {} entries in block {}'.format(len(entries), iteration))

        while (resume_token is not None):

            time.sleep(10)

            read_data = arxiv_dl.read_oai(resumption=resume_token, prefix=None)
            resume_token, entries = arxiv_dl.extract_info(read_data)
            if update_db:
                arxiv_dl.write_entries(entries)

            iteration += 1

            if dump_writer:
                dump_writer.write_dump(read_data, iteration)

            self.stdout.write('Found {} entries in block {}'.format(len(entries), iteration))

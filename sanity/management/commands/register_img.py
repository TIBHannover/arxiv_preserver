from django.core.management.base import BaseCommand, CommandError
from django.db.utils import IntegrityError
import sanity.models as models
import sanity.utils as utils
import re
import time
import datetime
import os

from django.db.models import Max

from django.db import transaction

import sanity.arxiv.download as arxiv_dl


def valid_date(s):
    try:
        return datetime.datetime.strptime(s, "%Y-%m-%d")
    except ValueError:
        msg = "Not a valid date: '{0}'.".format(s)
        raise argparse.ArgumentTypeError(msg)


preview_re = re.compile(r'\d+\.png')


class Command(BaseCommand):
    help = 'Closes the specified poll for voting'

    def add_arguments(self, parser):
        parser.add_argument('-i', '--input', help='Path to the pdf file')
        parser.add_argument('-f', '--from', type=valid_date)
        parser.add_argument('-c', '--count_page', action='store_true')

    def handle(self, *args, **options):

        self.output_path = options['input']
        png_path = os.path.join(self.output_path, 'png')
        date_from = None
        if options['from']:
            date_from = options['from']

        if date_from is not None:
            query_set = models.Paper.objects.annotate(date=Max('version__date')).filter(
                pdf_exists=True, png_exists=False, date__gte=date_from)

        else:
            query_set = models.Paper.objects.filter(png_exists=False)
        #
        # self.stdout.write(
        #     self.style.NOTICE('Look for {} documents to see if they have previews'.format(len(query_set))))
        for x in query_set:
            try:
                preview_path = os.path.join(png_path, x.to_path())

                if os.path.exists(preview_path):
                    if options['count_page']:
                        count = 0
                        for preview in os.listdir(preview_path):
                            if re.match(preview_re, preview):
                                count += 1
                        x.page_count = count

                    # if x.page_count is None and pdf_meta is not None:
                    #     x.page_count = pdf_meta['pages']
                    x.png_exists = True
                    x.save()

                    self.stdout.write(self.style.SUCCESS('Document {} have a preview'.format(x.paper_id)))
                else:
                    self.stdout.write(
                        self.style.NOTICE('Document {} have no previews in {}'.format(x.paper_id, preview_path)))
            except IntegrityError:
                self.stdout.write(self.style.ERROR('Document {} produce a IntegrityError'.format(x.paper_id)))

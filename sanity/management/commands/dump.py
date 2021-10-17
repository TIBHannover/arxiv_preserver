from django.core.management.base import BaseCommand, CommandError
import sanity.models as models
import sanity.pdf_renderer.build.libpdf_python as pdf_python
import sanity.utils as utils
import xml.etree.ElementTree as ET
import re
import urllib.request
import urllib.parse
import time
import datetime
import os
import tarfile
import skimage.io
import skimage.transform

import multiprocessing
import functools

import json

from django.db import transaction


class Command(BaseCommand):
    help = 'Closes the specified poll for voting'

    def add_arguments(self, parser):
        parser.add_argument('-o', '--output', help='Path to the dump file')
        parser.add_argument('-n', '--numbers', default=1000, type=int, help='Numbers of entries per file')

    def handle(self, *args, **options):

        split = options['numbers']
        out_path = options['output']

        if not os.path.exists(out_path):
            os.makedirs(out_path)

        out_file = None

        for i, x in enumerate(models.Paper.objects.all()):
            if i % split == 0:
                print(i)
                if out_file is not None:
                    out_file.close()
                index = i / split
                out_file = open(os.path.join(out_path, '{}.jsonl'.format(index)), 'w')

            output_obj = {}
            output_obj['id'] = x.paper_id
            output_obj['title'] = x.title
            output_obj['summary'] = x.summary
            output_obj['hash'] = x.hash
            output_obj['url'] = x.url
            output_obj['versions'] = []
            output_obj['authors'] = []
            output_obj['categories'] = []
            for v in x.version_set.all():
                output_obj['versions'].append({'id': v.name, 'date': str(v.date)})
                # authors
            # categories
            for v in x.authors.all():
                output_obj['authors'].append({'name': v.name})

            for v in x.categories.all():
                output_obj['categories'].append({'name': v.name})

            out_file.write(json.dumps(output_obj) + '\n')

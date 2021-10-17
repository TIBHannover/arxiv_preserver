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

from django.db import transaction

import sanity.arxiv.download as arxiv_dl


class Command(BaseCommand):
    help = 'Closes the specified poll for voting'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):

        self.stdout.write(self.style.SUCCESS('Database stats'))
        self.stdout.write('Number of papers: {}'.format(len(models.Paper.objects.all())))
        self.stdout.write('Number of papers with pdf: {}'.format(len(models.Paper.objects.filter(pdf_exists=True))))
        self.stdout.write('Number of papers with png: {}'.format(len(models.Paper.objects.filter(png_exists=True))))
        self.stdout.write('Number of papers with txt: {}'.format(len(models.Paper.objects.filter(txt_exists=True))))
        self.stdout.write('Number of tweets: {}'.format(len(models.Tweet.objects.all())))

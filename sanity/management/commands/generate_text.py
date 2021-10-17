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


def extract_fn(args):
    path, output_path, max_pages = args
    if tarfile.is_tarfile(path):
        Command.extract_tar(path, output_path, max_pages)
    elif os.path.isfile(path):
        Command.extract_file(path, output_path, max_pages)


def rescale_with_as(size, target_size_max):
    assert len(target_size_max) == len(size)
    ratio = float(size[0]) / size[1]
    target_ratio = float(target_size_max[0]) / target_size_max[1]
    # scale to max_height
    if ratio > target_ratio:
        return [int(target_size_max[0]), int(size[1] * target_size_max[0] / size[0])]

    # scale to max_width
    else:
        return [int(target_size_max[0] * target_size_max[1] / size[1]), int(target_size_max[1])]


class Command(BaseCommand):
    help = 'Closes the specified poll for voting'

    def add_arguments(self, parser):
        parser.add_argument('-i', '--input', help='Path to the pdf file')
        parser.add_argument('-o', '--output', help='Path to the pdf file')
        parser.add_argument('-p', '--pages', default=-1, type=int, help='Path to the pdf file')

    def handle(self, *args, **options):

        self.output_path = options['output']
        self.max_pages = options['pages']
        # create dump writer if necessary
        if os.path.isdir(options['input']):
            self.extract_dir(options['input'], self.output_path, self.max_pages)
        elif tarfile.is_tarfile(options['input']):
            self.extract_tar(options['input'], self.output_path, self.max_pages)
        elif os.path.isfile(options['input']):
            self.extract_file(options['input'], self.output_path, self.max_pages)

        self.stdout.write(self.style.SUCCESS('Successfully closed poll '))

    @staticmethod
    def extract_dir(path, output_path, max_pages):
        file_list = []
        for root, dirs, files in os.walk(path):
            for f in files:
                file_path = os.path.join(root, f)
                if os.path.isfile(file_path):
                    file_list.append(file_path)

        with multiprocessing.Pool(12) as p:

            p.map(extract_fn, [(f, output_path, max_pages) for f in file_list])

    @staticmethod
    def extract_tar(path, output_path, max_pages):
        tar = tarfile.TarFile(path)
        for f in tar:
            print(f)

            if f.isfile():
                arxiv_id = utils.arxiv_pdf(f.name)
                print(arxiv_id)
                if arxiv_id is not None:

                    data = tar.extractfile(f).read()
                    Command.store_txt(utils.paper_hash(arxiv_id), data, output_path, max_pages)

    @staticmethod
    def extract_file(path, output_path, max_pages):

        arxiv_id = utils.arxiv_pdf(path)
        if arxiv_id is not None:
            with open(path, 'r') as f:
                data = f.read()
                Command.store_txt(utils.paper_hash(arxiv_id), data, output_path, max_pages)

    @staticmethod
    def store_txt(hash, data, output_path, max_pages):
        output_dir = os.path.join(output_path, hash[0:2], hash[2:4], hash)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        document = pdf_python.Document(data)
        page_number = 0
        if max_pages < 0:
            max_pages = document.size()
        while page_number < max_pages and page_number < document.size():
            page = document.page(page_number)
            with open(os.path.join(output_dir, str(page_number) + '.txt'), 'w') as f:
                f.write(page.text())
            page_number += 1

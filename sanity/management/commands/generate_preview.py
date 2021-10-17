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
    path, output_path, max_pages, target_max_size = args
    if tarfile.is_tarfile(path):
        Command.extract_tar(path, output_path, max_pages, target_max_size)
    elif os.path.isfile(path):
        Command.extract_file(path, output_path, max_pages, target_max_size)


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
        parser.add_argument('-p', '--pages', default=6, type=int, help='Path to the pdf file')
        parser.add_argument('-s', '--size', default=500, type=int, help='Path to the pdf file')

    def handle(self, *args, **options):

        self.output_path = options['output']
        self.max_pages = options['pages']
        self.target_max_size = options['size']
        # create dump writer if necessary
        if os.path.isdir(options['input']):
            self.extract_dir(options['input'], self.output_path, self.max_pages, self.target_max_size)
        elif tarfile.is_tarfile(options['input']):
            self.extract_tar(options['input'], self.output_path, self.max_pages, self.target_max_size)
        elif os.path.isfile(options['input']):
            self.extract_file(options['input'], self.output_path, self.max_pages, self.target_max_size)

        self.stdout.write(self.style.SUCCESS('Successfully closed poll '))

    @staticmethod
    def extract_dir(path, output_path, max_pages, target_max_size):
        file_list = []
        for root, dirs, files in os.walk(path):
            for f in files:
                file_path = os.path.join(root, f)
                if os.path.isfile(file_path):
                    file_list.append(file_path)

        with multiprocessing.Pool(8) as p:

            p.map(extract_fn, [(f, output_path, max_pages, target_max_size) for f in file_list])

    @staticmethod
    def extract_tar(path, output_path, max_pages, target_max_size):
        tar = tarfile.TarFile(path)
        for f in tar:
            print(f)

            if f.isfile():
                arxiv_id = utils.arxiv_pdf(f.name)
                print(arxiv_id)
                if arxiv_id is not None:

                    data = tar.extractfile(f).read()
                    Command.store_preview(utils.paper_hash(arxiv_id), data, output_path, max_pages, target_max_size)

    @staticmethod
    def extract_file(path, output_path, max_pages, target_max_size):

        arxiv_id = utils.arxiv_pdf(path)
        if arxiv_id is not None:
            with open(path, 'r') as f:
                data = f.read()
                Command.store_preview(utils.paper_hash(arxiv_id), data, output_path, max_pages, target_max_size)

    @staticmethod
    def store_preview(hash, data, output_path, max_pages, target_max_size):
        output_dir = os.path.join(output_path, hash[0:2], hash[2:4], hash)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        document = pdf_python.Document(data)
        page_number = 0
        while page_number < max_pages and page_number < document.size():
            page = document.page(page_number)

            size = page.size()
            target_size = rescale_with_as(size, [target_max_size, target_max_size])
            img = page.renderToArray()
            img = skimage.transform.resize(img, target_size)
            skimage.io.imsave(os.path.join(output_dir, str(page_number) + '.png'), img)
            page_number += 1

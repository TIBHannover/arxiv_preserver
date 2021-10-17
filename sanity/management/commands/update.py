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

from django.db.models import Max

from django.db import transaction

import sanity.arxiv.download as arxiv_dl


def download(url):
    try:
        with urllib.request.urlopen(url) as response:
            read_data = response.read()

    except urllib.error.HTTPError as e:
        if e.code in (403, 500):
            print(e.code)
            time.sleep(600)
            return None

    return read_data


def create_path(path):
    if not os.path.exists(path):
        os.makedirs(path)


def valid_date(s):
    try:
        return datetime.datetime.strptime(s, "%Y-%m-%d")
    except ValueError:
        msg = "Not a valid date: '{0}'.".format(s)
        raise argparse.ArgumentTypeError(msg)


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
    help = "Closes the specified poll for voting"

    def add_arguments(self, parser):
        parser.add_argument("-i", "--input", help="Path to the pdf file")
        parser.add_argument("-o", "--output", help="Path to the pdf file")
        parser.add_argument("-t", "--txt_pages", default=-1, type=int, help="Path to the pdf file")
        parser.add_argument("-p", "--png_pages", default=6, type=int, help="Path to the pdf file")
        parser.add_argument("-s", "--size", default=500, type=int, help="Path to the pdf file")
        parser.add_argument("-c", "--continue", action="store_true")
        parser.add_argument("-f", "--from", type=valid_date)
        parser.add_argument("-r", "--register", action="store_true")

    def handle(self, *args, **options):

        self.output_path = options["output"]
        self.max_png_pages = options["png_pages"]
        self.max_txt_pages = options["txt_pages"]
        self.target_max_size = options["size"]
        self.register = options["register"]

        # create path
        png_path = os.path.join(self.output_path, "png")
        create_path(png_path)
        txt_path = os.path.join(self.output_path, "txt")
        create_path(txt_path)
        pdf_path = os.path.join(self.output_path, "pdf")
        create_path(pdf_path)
        dump_path = os.path.join(self.output_path, "dump")
        create_path(dump_path)

        # download meta
        dump_writer = arxiv_dl.DumpWriter(dump_path)

        date_from = None
        if options["continue"]:
            date_from = models.Paper.objects.all().aggregate(Max("date"))["date__max"]

        if options["from"]:
            date_from = options["from"]
            if isinstance(date_from, str):
                date_from = datetime.datetime.strptime(date_from, "%Y-%m-%d")

        self.stdout.write("Start from {}".format(date_from))

        entries = self._parse_api(dump_writer=dump_writer, date_from=date_from)
        self.stdout.write("Found {} entries".format(len(entries)))

        self.stdout.write(self.style.SUCCESS("Database updated"))

        self._download_pdf(pdf_path, date_from=date_from)
        self._generate_preview(pdf_path, png_path, date_from=date_from)
        self._generate_txt(pdf_path, txt_path, date_from=date_from)

        self.stdout.write(self.style.SUCCESS("Update done"))

    def _parse_api(self, update_db=True, dump_writer=None, date_from=None):

        if date_from is not None:
            date_from = date_from.strftime("%Y-%m-%d")

        read_data = arxiv_dl.read_oai(date_from=date_from)
        resume_token, entries = arxiv_dl.extract_info(read_data)
        if update_db:
            arxiv_dl.write_entries(entries)

        iteration = 0

        if dump_writer:
            dump_writer.write_dump(read_data, iteration)

        self.stdout.write("Found {} entries in block {}".format(len(entries), iteration))

        all_entries = []
        while resume_token is not None:

            time.sleep(10)

            read_data = arxiv_dl.read_oai(resumption=resume_token, prefix=None)
            resume_token, entries = arxiv_dl.extract_info(read_data)
            if update_db:
                arxiv_dl.write_entries(entries)

            iteration += 1

            if dump_writer:
                dump_writer.write_dump(read_data, iteration)

            all_entries.extend(entries)

        return all_entries

    def _download_pdf(self, path, update_db=True, date_from=None):
        if date_from is not None:
            query_set = models.Paper.objects.annotate(date=Max("version__date")).filter(
                pdf_exists=False, date__gte=date_from
            )

        else:
            query_set = models.Paper.objects.filter(pdf_exists=False)
        self.stdout.write(self.style.NOTICE("Start downloading of {} documents.".format(len(query_set))))
        for x in query_set:
            pdf_path = os.path.join(path, x.to_path())
            output_path = os.path.join(pdf_path, str(1) + ".pdf")
            if not self.register or not os.path.exists(output_path):

                url = x.to_pdf_url()
                data = download(url)
                if data is None:
                    self.stdout.write(self.style.ERROR("{}:{} file not found".format(x.namespace, x.paper_id)))
                    continue

                create_path(pdf_path)
                with open(output_path, "wb") as f:
                    f.write(data)

            if update_db:
                x.pdf_exists = True
                x.save()

            if not self.register or not os.path.exists(output_path):
                self.stdout.write(self.style.SUCCESS("{}:{} downloaded".format(x.namespace, x.paper_id)))
                time.sleep(0.5)

            else:
                self.stdout.write(self.style.SUCCESS("{}:{} already exists".format(x.namespace, x.paper_id)))

    def _generate_preview(self, pdf_path, png_path, update_db=True, date_from=None):
        if date_from is not None:
            query_set = models.Paper.objects.annotate(date=Max("version__date")).filter(
                pdf_exists=True, png_exists=False, date__gte=date_from
            )

        else:
            query_set = models.Paper.objects.filter(pdf_exists=True, png_exists=False)
        self.stdout.write(self.style.NOTICE("Start preview generation of {} documents".format(len(query_set))))
        for x in query_set:
            try:
                origin_path = os.path.join(pdf_path, x.to_path())
                preview_path = os.path.join(png_path, x.to_path())

                if not self.register or not os.path.exists(preview_path):
                    if not os.path.exists(origin_path):
                        self.stdout.write(self.style.ERROR("PDF path to paper {} not exists".format(x.paper_id)))
                        continue

                    pdf_files = os.listdir(origin_path)
                    if len(pdf_files) == 0:
                        self.stdout.write(self.style.ERROR("No pdf for paper {}".format(x.paper_id)))
                        continue

                    create_path(preview_path)

                    with open(os.path.join(origin_path, pdf_files[0]), "rb") as f:
                        data = f.read()
                        pdf_meta = Command.store_preview(preview_path, data, self.max_png_pages, self.target_max_size)

                if update_db:
                    # if x.page_count is None and pdf_meta is not None:
                    #     x.page_count = pdf_meta['pages']
                    x.png_exists = True
                    x.save()
            except RuntimeError:
                self.stdout.write(self.style.ERROR("PDF {} is corrupted".format(x.paper_id)))
                continue

    def _generate_txt(self, pdf_path, txt_path, update_db=True, date_from=None):
        if date_from is not None:
            query_set = models.Paper.objects.annotate(date=Max("version__date")).filter(
                pdf_exists=True, txt_exists=False, date__gte=date_from
            )

        else:
            query_set = models.Paper.objects.filter(pdf_exists=True, txt_exists=False)
        self.stdout.write(self.style.NOTICE("Start text extraction of {} documents".format(len(query_set))))
        for x in query_set:
            try:
                origin_path = os.path.join(pdf_path, x.to_path())
                text_path = os.path.join(txt_path, x.to_path())

                if not self.register or not os.path.exists(text_path):
                    if not os.path.exists(origin_path):
                        self.stdout.write(self.style.ERROR("PDF path to paper {} not exists".format(x.paper_id)))
                        continue

                    pdf_files = os.listdir(origin_path)
                    if len(pdf_files) == 0:
                        self.stdout.write(self.style.ERROR("No pdf for paper {}".format(x.paper_id)))
                        continue

                    create_path(text_path)

                    with open(os.path.join(origin_path, pdf_files[0]), "rb") as f:
                        data = f.read()
                        pdf_meta = Command.store_txt(text_path, data, self.max_txt_pages)

                if update_db:
                    # if x.page_count is None and pdf_meta is not None:
                    #     x.page_count = pdf_meta['pages']
                    x.txt_exists = True
                    x.save()
            except RuntimeError:
                self.stdout.write(self.style.ERROR("PDF {} is corrupted".format(x.paper_id)))
                continue

    @staticmethod
    def store_preview(path, data, max_pages, target_max_size):
        document = pdf_python.Document(data)
        page_number = 0
        while page_number < max_pages and page_number < document.size():
            page = document.page(page_number)

            size = page.size()
            target_size = rescale_with_as(size, [target_max_size, target_max_size])
            img = page.renderToArray()
            img = skimage.transform.resize(img, target_size)
            skimage.io.imsave(os.path.join(path, str(page_number) + ".png"), img)
            page_number += 1

        return {"pages": document.size()}

    @staticmethod
    def store_txt(path, data, max_pages):
        document = pdf_python.Document(data)
        page_number = 0
        if max_pages < 0:
            max_pages = document.size()
        while page_number < max_pages and page_number < document.size():
            page = document.page(page_number)
            with open(os.path.join(path, str(page_number) + ".txt"), "w") as f:
                f.write(page.text())
            page_number += 1

        return {"pages": document.size()}

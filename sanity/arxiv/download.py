import sanity.models as models
import sanity.utils as utils
import xml.etree.ElementTree as ET

import os
import sys
import re
import urllib
import datetime

from sanity.latex2utf.pylatexenc.latex2text import LatexNodes2Text

from django.db import transaction

from django.db.utils import IntegrityError

BASE_URL = 'http://export.arxiv.org/oai2?'


def normalize(name):
    if name[0] == "{":
        uri, tag = name[1:].split("}")
        return tag
    else:
        return name


def parse_arXiv(arxiv):

    result = {}

    for field in arxiv:
        if normalize(field.tag) == 'id':
            result['id'] = field.text

        if normalize(field.tag) == 'created':
            result['created'] = field.text

        if normalize(field.tag) == 'updated':
            result['updated'] = field.text

        if normalize(field.tag) == 'title':
            result['title'] = field.text

        if normalize(field.tag) == 'abstract':
            result['abstract'] = field.text

        if normalize(field.tag) == 'doi':
            result['doi'] = field.text

        if normalize(field.tag) == 'authors':
            result['authors'] = []
            for author in field:
                author_result = {}
                if normalize(author.tag) == 'author':

                    for author_field in author:
                        if normalize(author_field.tag) == 'keyname':
                            author_result['keyname'] = author_field.text
                        if normalize(author_field.tag) == 'forenames':
                            author_result['forenames'] = author_field.text

                result['authors'].append(author_result)

        if normalize(field.tag) == 'categories':
            result['categories'] = re.split("\s+", field.text)

    return result


def parse_arXivRaw(arxiv):

    result = {}
    versions = []

    for field in arxiv:
        if normalize(field.tag) == 'id':
            result['id'] = field.text

        if normalize(field.tag) == 'title':
            result['title'] = field.text

        if normalize(field.tag) == 'abstract':
            result['abstract'] = field.text

        if normalize(field.tag) == 'doi':
            result['doi'] = field.text

        if normalize(field.tag) == 'version':
            version = field.get('version')
            for version_field in field:
                if normalize(version_field.tag) == 'date':
                    date = datetime.datetime.strptime(version_field.text, '%a, %d %b %Y %H:%M:%S %Z')
                if normalize(version_field.tag) == 'size':
                    pass

            versions.append({'version': version, 'date': date})

        if normalize(field.tag) == 'authors':
            result['authors'] = []
            #TODO 1712.08994 1710.05497
            text = re.sub(r'\(.*\)', r'', field.text)
            text = re.sub(r'\sand\s', r', ', text)
            text = re.sub(',+', ',', text)
            text = re.sub('\s+', ' ', text)
            try:
                text = LatexNodes2Text().latex_to_text(text)
            except:
                pass
            for x in re.split(",\s+", text):
                result['authors'].append(x.strip())

        if normalize(field.tag) == 'categories':
            result['categories'] = re.split("\s+", field.text)

    result['versions'] = versions
    return result


def parse_record(record):
    oai_id = ''

    result = None

    for child in record:
        if normalize(child.tag) == 'header':
            for sub_child in child:
                if normalize(child.tag) == 'identifier':
                    pass

        if normalize(child.tag) == 'metadata':
            for sub_child in child:
                if normalize(sub_child.tag) == 'arXiv':
                    result = parse_arXiv(sub_child)
                if normalize(sub_child.tag) == 'arXivRaw':
                    result = parse_arXivRaw(sub_child)

    return result


def parse_resume(record):
    token = record.text
    size = 0
    cursor = 0
    for key, value in record.attrib.items():
        if key == 'cursor':
            cursor = value
        if key == 'completeListSize':
            size = value

    return token, size, cursor


def extract_info(xml_data):
    # default results
    token = None
    entries = []

    root = ET.fromstring(xml_data)
    for child in root:
        if normalize(child.tag) == 'ListRecords':
            for record in child:
                if normalize(record.tag) == 'record':
                    parse_result = parse_record(record)
                    if parse_result is not None:
                        entries.append(parse_result)
                if normalize(record.tag) == 'resumptionToken':
                    token, size, cursor = parse_resume(record)

    return token, entries


def read_oai(categorie=None, verb='ListRecords', prefix='arXivRaw', resumption=None, date_from=None):

    query = {'verb': verb}

    if prefix is not None:
        query['metadataPrefix'] = prefix

    if categorie is not None:
        query['set'] = categorie

    if date_from is not None:
        query['from'] = date_from

    if resumption is not None:
        query['resumptionToken'] = resumption

    url = BASE_URL + urllib.parse.urlencode(query)

    with urllib.request.urlopen(url) as response:
        read_data = response.read()

    return read_data


def read_file(path):
    with open(path, 'r') as f:
        read_data = f.read()

    return read_data


class DumpWriter():

    def __init__(self, folder, name=None):
        self._folder = folder
        self._name = name
        if self._name is None:
            self._name = str(datetime.datetime.today()) + '_{}.xml'

        if not os.path.exists(self._folder):
            os.makedirs(self._folder)

    def write_dump(self, dump, index):
        with open(os.path.join(self._folder, self._name.format(index)), 'wb') as f:
            f.write(dump)


def write_entries(entries):

    with transaction.atomic():
        for entry in entries:

            try:
                paper = models.Paper.objects.get(paper_id=entry['id'])

            except models.Paper.DoesNotExist as e:
                paper = models.Paper(paper_id=entry['id'])

            # update title
            paper.summary = entry['abstract']
            paper.title = entry['title']

            # update versions

            try:
                paper.save()
            except IntegrityError:
                self.stdout.write(self.style.ERROR('Document {} produce a IntegrityError'.format(paper.paper_id)))
                continue

            if 'versions' in entry:
                for x in paper.version_set.all():
                    x.delete()

                for x in entry['versions']:
                    version = models.Version(paper=paper, name=x['version'], date=x['date'])
                    version.save()

                paper.paper_url = 'https://arxiv.org/pdf/{}'.format(entry['id'])
                paper.hash = utils.paper_hash(entry['id'])

            # remove categories
            if 'categories' in entry:
                paper.categories.clear()

            # categories update

            for x in entry['categories']:
                try:
                    category = models.Category.objects.get(name=x)

                except models.Category.DoesNotExist as e:
                    category = models.Category(name=x)
                    category.save()

                paper.categories.add(category)

            # remove authors
            if 'authors' in entry:
                query_set = paper.authors.all()
                for x in query_set:
                    x.delete()
            # add authors

            if 'authors' in entry:
                for x in entry['authors']:
                    if isinstance(x, dict):
                        author = models.Author(forename=x['forename'], surname=x['surename'])
                        author.save()
                    else:
                        # Fix long name
                        author = models.Author(name=x[:255])
                        author.save()
                    paper.authors.add(author)

            try:
                paper.save()
            except IntegrityError:
                self.stdout.write(self.style.ERROR('Document {} produce a IntegrityError'.format(paper.paper_id)))

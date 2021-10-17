from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
import sanity.models as models
import sanity.utils as utils
import re
import time
import datetime
import os

import sanity.search as search

from elasticsearch.helpers import bulk
from elasticsearch import Elasticsearch

from arxiv_makeover.settings import ES_INDEX


class Command(BaseCommand):
    help = "Closes the specified poll for voting"

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):

        search.PaperIndex.init(index=ES_INDEX)
        es = Elasticsearch()
        bulk(client=es, actions=(b.indexing() for b in models.Paper.objects.all().iterator()))

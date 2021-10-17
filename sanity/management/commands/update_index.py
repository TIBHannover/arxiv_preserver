from django.core.management.base import BaseCommand, CommandError
import sanity.models as models
import re
import time
import datetime
import os

from django.db.models import Max


class Command(BaseCommand):
    help = "Closes the specified poll for voting"

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):

        start = time.time()
        models.PaperIndex.generate()
        end = time.time()

        self.stdout.write(self.style.SUCCESS("Index created in {}s".format(end - start)))

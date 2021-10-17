from django.http import JsonResponse

import hashlib
import random
import time
import string
import re

from . import models

# function for paper

re_arxiv_id = re.compile('.*?(\d{2})(\d{2})\.(\d+).*?')
re_arxiv_id_old = re.compile('.*?([a-zA-Z-]+\.)(\d{2})(\d{2})(\d+).*?')

re_pdf_name = re.compile('.*?/?([^/]+)(v\d+)?\.pdf')


def unique_id():
    seed = str(time.time()) + ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(100))
    l = list(seed)
    random.shuffle(l)
    seed = ''.join(l)
    return hashlib.sha256(seed.encode()).hexdigest()


def paper_hash(paper_id):
    return hashlib.sha256('{}'.format(paper_id).encode()).hexdigest()


def arxiv_id(url):
    match = re.match(re_arxiv_id, url)
    if match:
        return (match.group(1), match.group(2), match.group(3))
    return None


def arxiv_id(url):
    match = re.match(re_arxiv_id, url)
    if match:
        return (match.group(1), match.group(2), match.group(3))
    return None


def arxiv_id_old(url):
    match = re.match(re_arxiv_id_old, url)
    if match:
        return (match.group(1), match.group(2), match.group(3))
    return None


def arxiv_pdf(url):
    match = re.match(re_pdf_name, url)
    if match:
        return match.group(1)
    return None


# function for views


def _user_info(user):
    if user.is_authenticated:
        return {'library_count': len(models.PaperUserRelation.objects.filter(user=user, library=True))}

    return {}

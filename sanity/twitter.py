#django imports

from django.shortcuts import render
from django.template.loader import render_to_string
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, Http404
from django.template import loader, RequestContext
from django.contrib import auth
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, F, Max, Min, Count, Exists, Case, When, Value, Sum, BooleanField, IntegerField
from django.views.decorators.http import require_http_methods

from enum import Enum
import datetime
import dateutil.parser
import json

from . import models
from sanity import utils


@require_http_methods(['POST'])
def twitter(request):
    context = {}
    if 'paper_pk' not in request.POST:
        return JsonResponse({'status': 'error'})

    try:
        paper = models.Paper.objects.get(pk=request.POST['paper_pk'])

    except models.Paper.DoesNotExist as e:
        return JsonResponse({'status': 'error'})

    try:
        page = int(request.POST.get('page', 0))
        count = int(request.POST.get('count', -1))

        retweets = bool(request.POST.get('retweets', True))

        if count < 0:
            count = paper.tweet_set.count()

        tweet_query = paper.tweet_set.all()
        if not retweets:
            tweet_query = tweet_query.exclude(text__startswith="RT")
        paginator = Paginator(tweet_query, count)
        page = paginator.page(page)
        context.update({'tweets': page})

    except ValueError:
        return JsonResponse({'status': 'error'})

    content = render_to_string('sanity/tweet_list_content.html', context, request=request)
    return JsonResponse({
        'status': 'ok',
        'content': content,
        'has_next': page.has_next(),
        'number': page.number
        # 'next_page_number': result_query.next_page_number()
    })

    return JsonResponse({'status': 'error'})

#django imports

from django.shortcuts import render
from django.template.loader import render_to_string
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, Http404
from django.template import loader, RequestContext
from django.contrib import auth
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, F, Max, Min, Count, Exists, Case, When, Value, Sum, BooleanField, IntegerField
from django.views.decorators.http import require_http_methods

import datetime
import dateutil.parser
import json

from . import models

from sanity import utils


@require_http_methods(['POST'])
def in_library(request):
    current_user = request.user
    if current_user.is_authenticated:
        if 'paper_hash' not in request.POST:
            return JsonResponse({'status': 'error'})

        try:
            paper = models.Paper.objects.get(hash=request.POST['paper_hash'])

        except models.Paper.DoesNotExist as e:
            return JsonResponse({'status': 'error'})

        try:
            paper_user_relation = models.PaperUserRelation.objects.get(user=current_user, paper=paper)

        except models.PaperUserRelation.DoesNotExist as e:
            return JsonResponse({'status': 'ok', 'state': 'out'})

        state = None
        if not paper_user_relation.library:
            state = 'out'
        else:
            state = 'in'

        return JsonResponse({'status': 'ok', 'state': state})

    return JsonResponse({'status': 'ok', 'state': 'out'})


@require_http_methods(['POST'])
def toggle_library(request):
    current_user = request.user
    if current_user.is_authenticated:
        if 'paper_hash' not in request.POST:
            return JsonResponse({'status': 'error'})

        try:
            paper = models.Paper.objects.get(hash=request.POST['paper_hash'])

        except models.Paper.DoesNotExist as e:
            return JsonResponse({'status': 'error'})

        try:
            paper_user_relation = models.PaperUserRelation.objects.get(user=current_user, paper=paper)

        except models.PaperUserRelation.DoesNotExist as e:
            paper_user_relation = models.PaperUserRelation(user=current_user, paper=paper, library=False)

        state = None
        if not paper_user_relation.library:
            paper_user_relation.library = True
            paper_user_relation.save()
            state = 'in'
        else:
            paper_user_relation.library = False
            paper_user_relation.save()
            state = 'out'

        return JsonResponse({'status': 'ok', 'state': state, 'user_info': utils._user_info(current_user)})

    return JsonResponse({'status': 'error'})

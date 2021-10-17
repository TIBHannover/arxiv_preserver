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

import re

from . import models
from sanity import utils
import sanity.search as search

query_re = re.compile(r'(([^\s]+)\:)?(("(.*?)")|(([^\s]+)))')


def _parse_date(date):
    try:
        date_rel = int(date)
    except ValueError as e:
        date_rel = None

    if date_rel is not None and date_rel > 0:
        date_from = datetime.date.today() - datetime.timedelta(days=date_rel)

    else:
        try:
            date_from = dateutil.parser.parse(date)
        except ValueError as e:
            return None

    return date_from


class Query():

    def __init__(self):
        self.category = None
        self.author = None
        self.library = None
        self.date_from = None
        self.group = None
        self.sort = 'date'
        self.q = None

    def __getattr__(self, name):
        return 'foo'

    def to_dict(self):
        result_dict = {'sort': self.sort}
        if self.category is not None:
            result_dict.update({'category': self.category})
        if self.author is not None:
            result_dict.update({'author': self.author})
        if self.library is not None:
            result_dict.update({'library': self.library})
        if self.date_from is not None:
            result_dict.update({'date_from': self.date_from})
        if self.group is not None:
            result_dict.update({'group': self.group})
        if self.q is not None:
            result_dict.update({'q': self.q})
        return result_dict

    @property
    def to_string(self):
        print(self.q)
        if self.q is None:
            return ''
        return ' '.join(self.q)

    @property
    def to_json(self):

        return json.dumps(self.to_dict())

    def from_json(self, string):
        #TODO error handler
        result_dict = json.loads(string)

        if 'sort' in result_dict:
            self.sort = result_dict['sort']
        if 'category' in result_dict:
            self.category = result_dict['category']
        if 'author' in result_dict:
            self.author = result_dict['author']
        if 'library' in result_dict:
            self.library = result_dict['library']
        if 'date_from' in result_dict:
            self.date_from = result_dict['date_from']
        if 'group' in result_dict:
            self.group = result_dict['group']
        if 'q' in result_dict:
            self.q = result_dict['q']
        print(self.q)

    @property
    def is_sort_date(self):
        return self.sort == 'date'

    @property
    def is_sort_tweet(self):
        return self.sort == 'twitter'

    @property
    def is_sort_library(self):
        return self.sort == 'library'

    @property
    def is_sort_relevance(self):
        return self.sort == 'relevance'

    @property
    def is_show_library(self):
        return self.library

    @staticmethod
    def parse(request):
        result = Query()

        print(request.POST)

        if 'query' in request.POST:
            result.from_json(request.POST['query'])

        # parse request POST parameter

        # parse request GET parameter
        if 'category' in request.GET:
            result.category = request.GET['category']

        if 'author' in request.GET:
            result.author = request.GET['author']

        if 'library' in request.GET:
            result.library = bool(request.GET['library'])

        if 'date_from' in request.GET:
            result.date_from = _parse_date(request.GET['date_from'])

        if 'q' in request.GET:
            q = []
            for x in re.findall(query_re, request.GET['q'].lower().strip()):
                if x[1]:
                    q.append('{}:{}'.format(x[1], x[4] + x[6]))

                else:
                    q.append('{}'.format(x[4] + x[6]))
            if len(q) > 0:
                result.q = q

        if 'sort' in request.GET:
            get_sort = request.GET['sort'].lower()
            if get_sort == 'date':
                result.sort = 'date'
            if get_sort == 'tweet':
                result.sort = 'tweet'
            if get_sort == 'library':
                result.sort = 'library'
            if get_sort == 'relevance':
                result.sort = 'relevance'
        else:
            if result.q is not None:
                result.sort = 'relevance'

        return result


# Create your views here.
def index(request):
    context = {}

    query = Query.parse(request)

    context.update({'query': query})

    # filter options
    paper_query = models.PaperIndex.objects.all()
    if query.category is not None:
        # dirty hack for debian
        category = models.Category.objects.get(name=query.category)
        paper_query = paper_query.filter(paper__categories=category)

    if query.author is not None:
        paper_query = paper_query.filter(paper__authors__name=query.author)

    if query.library and request.user.is_authenticated:
        paper_query = paper_query.filter(paper__users=request.user, paper__paperuserrelation__library=True)

    elif query.library and not request.user.is_authenticated:
        raise Http404("LOGIN ERROR")

    # query options
    result_list = None
    if query.q is not None:
        result_list = search.search(query.q)
        paper_query = paper_query.filter(pk__in=[x[0] for x in result_list])

    # find library entries
    if request.user.is_authenticated:
        #TODO maybe we could use the template system
        context['user_info'] = utils._user_info(request.user)

    # sort result
    if not query.is_sort_tweet:
        paper_query = paper_query.annotate(tweet_count=F('tweet'))

    if query.is_sort_relevance:
        if result_list is not None:
            ranking = {i: v for i, v in result_list}
            print(ranking)
            paper_query = list(paper_query)
            paper_query.sort(key=lambda obj: ranking[str(obj.paper.id)])

    elif query.is_sort_tweet:
        group_string = 'tweet'
        if query.group == 'y':
            group_string = 'tweet_last_y'
            paper_query = paper_query.annotate(tweet_count=F('tweet_last_y'))
        if query.group == 'm':
            group_string = 'tweet_last_m'
            paper_query = paper_query.annotate(tweet_count=F('tweet_last_m'))
        if query.group == 'w':
            group_string = 'tweet_last_w'
            paper_query = paper_query.annotate(tweet_count=F('tweet_last_w'))
        if query.group == 'd':
            group_string = 'tweet_last_d'
            paper_query = paper_query.annotate(tweet_count=F('tweet_last_d'))
        if group_string == 'tweet':
            paper_query = paper_query.annotate(tweet_count=F('tweet'))
        paper_query = paper_query.order_by(F(group_string).desc())

    elif query.is_sort_library:

        group_string = 'library'
        if query.group == 'y':
            group_string = 'library_last_y'
        if query.group == 'm':
            group_string = 'library_last_m'
        if query.group == 'w':
            group_string = 'library_last_w'
        if query.group == 'd':
            group_string = 'library_last_d'
        paper_query = paper_query.order_by(F(group_string).desc())
    else:
        # if query.date_from is not None:
        #     paper_query = paper_query.filter(last_version__date__gte=query.date_from)
        paper_query = paper_query.order_by(F('date_last').asc())

    total_paper = models.Paper.objects.count()

    #uery_paper = paper_query.count()
    context.update({'total_paper': total_paper, 'preview_range': range(0, 6)})

    # print(paper_query.query)
    # paginator
    paginator = Paginator(paper_query, 25)

    # ajax -> render content
    if request.is_ajax():
        try:
            response = {'status': 'ok', 'query': query.to_dict()}
            page = request.POST.get('page', 1)
            result_query = paginator.page(page)

            print(page)
            print(query.to_json)
            for x in result_query:
                print('{} {}'.format(x.paper.paper_id, x.tweet_count))
            context.update({'paper_list': result_query})
            content = render_to_string('sanity/paper_list_content.html', context, request=request)
            print(context)
            if result_query.has_next():
                response.update({'content': content, 'next_page_number': result_query.next_page_number()})
                return JsonResponse(response)
            else:
                response.update({'content': content, 'next_page_number': None})
                return JsonResponse(response)
        except PageNotAnInteger:
            return JsonResponse({'status': 'error'})
        except EmptyPage:
            #TODO maybe render a button
            return JsonResponse({'status': 'error'})

    # render whole list
    else:

        try:
            page = request.GET.get('page', 1)
            result_query = paginator.page(page)

        except PageNotAnInteger:
            result_query = paginator.page(1)
        except EmptyPage:
            #TODO maybe render a button
            return render(request, 'sanity/paper_list.html', context)

        context.update({'paper_list': result_query})
        return render(request, 'sanity/paper_list.html', context)


@require_http_methods(['POST'])
def login(request):
    print(request.POST)

    if 'username' not in request.POST:
        return JsonResponse({'status': 'error'})

    if 'password' not in request.POST:
        return JsonResponse({'status': 'error'})

    username = request.POST['username']
    password = request.POST['password']

    if username == "" or password == "":
        return JsonResponse({'status': 'error'})

    user = auth.authenticate(username=username, password=password)
    if user is not None:
        auth.login(request, user)

        return JsonResponse({'status': 'ok'})
        # Redirect to a success page.
    else:
        # Return an 'invalid login' error message.

        if auth.models.User.objects.filter(username=username).count() > 0:
            return JsonResponse({'status': 'error'})

        user = auth.models.User.objects.create_user(username, 'n@n.n', password)
        user.save()
        user = auth.authenticate(username=username, password=password)

        if user is not None:
            auth.login(request, user)
            return JsonResponse({'status': 'ok'})

    return JsonResponse({'status': 'error'})


@require_http_methods(['POST'])
def logout(request):
    auth.logout(request)
    return JsonResponse({'status': 'ok'})

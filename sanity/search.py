from elasticsearch_dsl.connections import connections
from elasticsearch_dsl import Document, Text, Date, Nested, InnerDoc, Q

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search

from arxiv_makeover.settings import ES_INDEX
import re

connections.create_connection()


class AuthorIndex(InnerDoc):
    name = Text()
    surname = Text()
    forename = Text()


class CategoryIndex(InnerDoc):
    name = Text()


class VersionIndex(InnerDoc):
    name = Text()
    date = Date()


class PaperIndex(Document):
    # Idetifier from arxiv
    paper_id = Text()
    # Info from oai
    title = Text()
    summary = Text()
    text = Text()
    authors = Nested(AuthorIndex)
    categories = Nested(CategoryIndex)
    versions = Nested(VersionIndex)

    url = Text()

    class Meta:
        index = ES_INDEX

    @staticmethod
    def build_field_lut():
        return {
            "id": "paper_id",
            "paper_id": "paper_id",
            "title": "title",
            "text": "text",
            "cat": "categories.name",
            "category": "categories.name",
            "categories": "categories.name",
            "a": "authors.name",
            "aut": "authors.name",
            "author": "authors.name",
            "authors": "authors.name",
            "s": "summary",
            "sum": "summary",
            "summary": "summary",
        }


field_search_re = re.compile(r"(.*?):(.+)")
tag_search_re = re.compile(r"#(.*?)")


def search(query_text):

    lut = PaperIndex.build_field_lut()

    filtered_q = []

    queries = []

    print(query_text)
    for q in query_text:
        print(q)
        match = re.match(field_search_re, q)
        if match:
            field = match.group(1)
            value = match.group(2)
            print(field)
            print(value)
            if field in lut:
                field = lut[field]
                if "." in field:
                    queries.append(
                        Q("nested", path=field.split(".")[0], query=Q("multi_match", query=value, fields=[field]))
                    )
                else:
                    queries.append(Q("multi_match", query=value, fields=[field]))
                continue

        match = re.match(tag_search_re, q)
        if match:
            pass

        filtered_q.append(q)

    if len(filtered_q) > 0:
        queries.append(
            Q(
                "multi_match",
                query=" ".join(filtered_q),
                fields=[
                    "paper_id",
                    "body",
                    "title",
                    "summary",
                    "text",
                    "authors.name",
                    "categories",
                    "versions",
                    "url",
                ],
            )
        )

    client = Elasticsearch()

    s = Search(using=client)

    print(queries)

    for q in queries:
        s = s.query(q)

    response = s.execute()

    result_list = []

    for i, x in enumerate(response):
        result_list.append((x.meta.id, i))

    return result_list

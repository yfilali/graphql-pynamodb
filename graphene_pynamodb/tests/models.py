from __future__ import absolute_import

import os
from datetime import datetime

from pynamodb.attributes import (NumberAttribute, NumberSetAttribute, UnicodeAttribute, UTCDateTimeAttribute)
from pynamodb.models import Model

from graphene_pynamodb.relationships import OneToOne, OneToMany

DB_HOST = None if os.getenv('TRAVIS', False) else "http://localhost:8000"
DB_REGION = "us-west-2"


class Editor(Model):
    class Meta:
        table_name = 'test_graphene_pynamodb_editors'
        host = DB_HOST
        region = DB_REGION

    id = NumberAttribute(hash_key=True)
    name = UnicodeAttribute()


class Pet(Model):
    class Meta:
        table_name = 'test_graphene_pynamodb_pets'
        host = DB_HOST
        region = DB_REGION

    id = NumberAttribute(hash_key=True)
    name = UnicodeAttribute()
    reporter_id = NumberAttribute()


class Article(Model):
    class Meta:
        table_name = 'test_graphene_pynamodb_articles'
        host = DB_HOST
        region = DB_REGION

    id = NumberAttribute(hash_key=True)
    headline = UnicodeAttribute()
    pub_date = UTCDateTimeAttribute(default=datetime.now)
    reporter = OneToOne('Reporter')


class Reporter(Model):
    class Meta:
        table_name = 'test_graphene_pynamodb_reporters'
        host = DB_HOST
        region = DB_REGION

    id = NumberAttribute(hash_key=True)
    first_name = UnicodeAttribute()
    last_name = UnicodeAttribute()
    email = UnicodeAttribute(null=True)
    pets = NumberSetAttribute(null=True)
    articles = OneToMany(Article, null=True)
    favorite_article = OneToOne(Article, null=True)

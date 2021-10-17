# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-01-04 10:01
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Author',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=256, null=True)),
                ('surname', models.CharField(max_length=128, null=True)),
                ('forename', models.CharField(max_length=128, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128)),
            ],
        ),
        migrations.CreateModel(
            name='Paper',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('paper_id', models.CharField(db_index=True, max_length=30, unique=True)),
                ('title', models.CharField(max_length=256)),
                ('summary', models.TextField()),
                ('page_count', models.IntegerField(null=True)),
                ('pdf_exists', models.BooleanField(default=False)),
                ('png_exists', models.BooleanField(default=False)),
                ('txt_exists', models.BooleanField(default=False)),
                ('url', models.CharField(max_length=128)),
                ('hash', models.CharField(db_index=True, max_length=64, unique=True)),
                ('namespace', models.CharField(default='arxiv', max_length=64)),
                ('authors', models.ManyToManyField(to='sanity.Author')),
                ('categories', models.ManyToManyField(to='sanity.Category')),
                ('user_id', models.ManyToManyField(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Tweet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tweet_id', models.CharField(db_index=True, max_length=128, unique=True)),
                ('text', models.TextField()),
                ('lang', models.CharField(max_length=64)),
                ('date', models.DateTimeField()),
                ('user_image', models.CharField(max_length=256)),
                ('user_name', models.CharField(max_length=256)),
                ('user_follower', models.IntegerField()),
                ('user_following', models.IntegerField()),
                ('papers', models.ManyToManyField(to='sanity.Paper')),
            ],
        ),
        migrations.CreateModel(
            name='TweetArxiv',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('paper_id', models.CharField(max_length=30)),
                ('tweet', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sanity.Tweet')),
            ],
        ),
        migrations.CreateModel(
            name='Version',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128)),
                ('date', models.DateField()),
                ('paper', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='sanity.Paper')),
            ],
        ),
    ]
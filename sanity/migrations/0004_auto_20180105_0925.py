# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-01-05 09:25
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('sanity', '0003_auto_20180105_0924'),
    ]

    operations = [
        migrations.CreateModel(
            name='PaperUserTag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128)),
            ],
        ),
        migrations.RemoveField(
            model_name='paperuserrelation',
            name='tag',
        ),
        migrations.DeleteModel(
            name='PaperTag',
        ),
        migrations.AddField(
            model_name='paperusertag',
            name='PaperUserRelation',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sanity.PaperUserRelation'),
        ),
    ]

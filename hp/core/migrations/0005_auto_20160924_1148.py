# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-09-24 11:48
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_auto_20160903_1321'),
    ]

    operations = [
        migrations.AddField(
            model_name='blogpost',
            name='html_summary_de',
            field=models.TextField(blank=True, help_text='Any length, but must be valid HTML.', null=True),
        ),
        migrations.AddField(
            model_name='blogpost',
            name='html_summary_en',
            field=models.TextField(blank=True, help_text='Any length, but must be valid HTML.', null=True),
        ),
        migrations.AddField(
            model_name='blogpost',
            name='meta_summary_de',
            field=models.CharField(blank=True, help_text='The meta summary should is a maximum of 160 characters and shows up in search engines. <a href="https://support.google.com/webmasters/answer/35624">More info</a>.', max_length=160, null=True),
        ),
        migrations.AddField(
            model_name='blogpost',
            name='meta_summary_en',
            field=models.CharField(blank=True, help_text='The meta summary should is a maximum of 160 characters and shows up in search engines. <a href="https://support.google.com/webmasters/answer/35624">More info</a>.', max_length=160, null=True),
        ),
        migrations.AddField(
            model_name='blogpost',
            name='opengraph_summary_de',
            field=models.CharField(blank=True, help_text='Between two and four sentences, defaults to first three sentences.', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='blogpost',
            name='opengraph_summary_en',
            field=models.CharField(blank=True, help_text='Between two and four sentences, defaults to first three sentences.', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='blogpost',
            name='twitter_summary_de',
            field=models.CharField(blank=True, help_text='At most 200 characters.', max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='blogpost',
            name='twitter_summary_en',
            field=models.CharField(blank=True, help_text='At most 200 characters.', max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='page',
            name='html_summary_de',
            field=models.TextField(blank=True, help_text='Any length, but must be valid HTML.', null=True),
        ),
        migrations.AddField(
            model_name='page',
            name='html_summary_en',
            field=models.TextField(blank=True, help_text='Any length, but must be valid HTML.', null=True),
        ),
        migrations.AddField(
            model_name='page',
            name='meta_summary_de',
            field=models.CharField(blank=True, help_text='The meta summary should is a maximum of 160 characters and shows up in search engines. <a href="https://support.google.com/webmasters/answer/35624">More info</a>.', max_length=160, null=True),
        ),
        migrations.AddField(
            model_name='page',
            name='meta_summary_en',
            field=models.CharField(blank=True, help_text='The meta summary should is a maximum of 160 characters and shows up in search engines. <a href="https://support.google.com/webmasters/answer/35624">More info</a>.', max_length=160, null=True),
        ),
        migrations.AddField(
            model_name='page',
            name='opengraph_summary_de',
            field=models.CharField(blank=True, help_text='Between two and four sentences, defaults to first three sentences.', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='page',
            name='opengraph_summary_en',
            field=models.CharField(blank=True, help_text='Between two and four sentences, defaults to first three sentences.', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='page',
            name='twitter_summary_de',
            field=models.CharField(blank=True, help_text='At most 200 characters.', max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='page',
            name='twitter_summary_en',
            field=models.CharField(blank=True, help_text='At most 200 characters.', max_length=200, null=True),
        ),
    ]

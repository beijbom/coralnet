# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-09-05 07:35
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('annotations', '0006_update_label_thumbnail_filepaths'),
    ]

    operations = [
        migrations.AlterField(
            model_name='annotationtoolsettings',
            name='human_annotated_point_color',
            field=models.CharField(default=b'8888FF', max_length=6, verbose_name=b'Confirmed point color'),
        ),
    ]

# -*- coding: utf-8 -*-
# Generated by Django 1.11.25 on 2019-11-06 21:15
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('images', '0022_modified_some_defaults'),
        ('vision_backend', '0007_features_populate_image_field'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='image',
            name='features',
        ),
    ]

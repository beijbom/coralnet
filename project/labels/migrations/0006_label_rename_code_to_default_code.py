# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-09-08 06:06
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('labels', '0005_create_locallabels_for_existing_labelsets'),
    ]

    operations = [
        migrations.RenameField(
            model_name='Label', old_name='code', new_name='default_code')
    ]

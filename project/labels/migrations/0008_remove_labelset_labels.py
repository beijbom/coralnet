# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-09-13 23:56
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('labels', '0007_alter_label_default_code_verbose_name'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='labelset',
            name='labels',
        ),
    ]

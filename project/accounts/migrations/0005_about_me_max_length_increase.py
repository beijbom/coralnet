# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-10-31 04:55
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_remove_language_and_other_alterations'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='about_me',
            field=models.CharField(blank=True, max_length=1000, verbose_name=b'About me'),
        ),
    ]

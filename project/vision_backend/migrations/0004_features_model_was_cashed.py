# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-09-13 17:03
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vision_backend', '0003_alter_score_label_foreignkey'),
    ]

    operations = [
        migrations.AddField(
            model_name='features',
            name='model_was_cashed',
            field=models.NullBooleanField(),
        ),
    ]

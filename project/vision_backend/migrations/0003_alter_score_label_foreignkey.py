# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-09-13 21:19
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('labels', '0002_label'),
        ('vision_backend', '0002_remove_legacy_robot_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='score',
            name='label',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='labels.Label'),
        ),
    ]

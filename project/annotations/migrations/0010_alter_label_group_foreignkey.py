# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-09-06 04:52
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('annotations', '0009_rename_labelgroup_table'),
        ('labels', '0001_initial'),
    ]

    # This migration was auto-generated when I changed the model FK references.
    # We need to remove the DeleteModel operation because that model exists in
    # state only.
    operations = [
        migrations.AlterField(
            model_name='label',
            name='group',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='labels.LabelGroup', verbose_name=b'Functional Group'),
        ),
        # Cut the DeleteModel operation. Will use in next migration.
    ]

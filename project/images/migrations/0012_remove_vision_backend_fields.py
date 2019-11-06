# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-09-12 04:54
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('images', '0011_rename_dupe_image_names'),
    ]
    
    operations = [
        migrations.RemoveField(
            model_name='robot',
            name='source',
        ),
        migrations.RemoveField(
            model_name='image',
            name='latest_robot_annotator',
        ),
        migrations.RemoveField(
            model_name='image',
            name='process_date',
        ),
        migrations.RemoveField(
            model_name='imagestatus',
            name='annotatedByRobot',
        ),
        migrations.RemoveField(
            model_name='imagestatus',
            name='featureFileHasHumanLabels',
        ),
        migrations.RemoveField(
            model_name='imagestatus',
            name='featuresExtracted',
        ),
        migrations.RemoveField(
            model_name='imagestatus',
            name='hasRandomPoints',
        ),
        migrations.RemoveField(
            model_name='imagestatus',
            name='preprocessed',
        ),
        migrations.RemoveField(
            model_name='imagestatus',
            name='usedInCurrentModel',
        ),        
        migrations.DeleteModel(
            name='Robot',
        ),
    ]
    

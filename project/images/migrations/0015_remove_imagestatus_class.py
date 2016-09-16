# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-09-15 18:30
from __future__ import unicode_literals

from django.db import migrations, models


def copy_confirmed_status(apps, schema_editor):
    Image = apps.get_model("images", "Image")
    for image in Image.objects.filter():
        image.confirmed = image.status.annotatedByHuman
        image.save()

def copy_confirmed_status_backwards(apps, schema_editor):
    Image = apps.get_model("images", "Image")
    Status = apps.get_model("images", "ImageStatus")
    for image in Image.objects.filter():
        status = Status()
        status.annotatedByHuman = image.confirmed
        status.save()
        image.status = status
        image.save()

class Migration(migrations.Migration):

    dependencies = [
        ('images', '0014_alter_source_labelset_foreignkey'),
    ]

    operations = [

        # Add new confirmed bool field to the image model.
        migrations.AddField(
            model_name='image',
            name='confirmed',
            field=models.BooleanField(default=False),
        ),

        # Copy image.status.annotatedByHuman to new confirmed field
        migrations.RunPython(copy_confirmed_status, copy_confirmed_status_backwards),
        
        # Remove the whole Image Status model
        migrations.RemoveField(
            model_name='image',
            name='status',
        ),
        
        migrations.DeleteModel(
            name='ImageStatus',
        ),
    ]
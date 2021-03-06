# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-09-06 07:45
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import easy_thumbnails.fields
import labels.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('annotations', '0012_rename_label_table'),
        ('labels', '0001_initial'),
    ]

    # Convert "operations" to only be "state_operations"
    state_operations = [
        # These migrations were auto-generated by Django makemigrations.
        migrations.CreateModel(
            name='Label',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=45)),
                ('code', models.CharField(max_length=10, verbose_name=b'Short Code')),
                ('description', models.TextField(null=True)),
                ('thumbnail', easy_thumbnails.fields.ThumbnailerImageField(help_text=b"For best results, please use an image that's close to 150 x 150 pixels. Otherwise, we'll resize and crop your image to make sure it's that size.", null=True, upload_to=labels.models.get_label_thumbnail_upload_path, verbose_name=b'Example image (thumbnail)')),
                ('create_date', models.DateTimeField(auto_now_add=True, null=True, verbose_name=b'Date created')),
                ('created_by', models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name=b'Created by')),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='labels.LabelGroup', verbose_name=b'Functional Group')),
            ],
        ),
    ]

    operations = [
        # By running only state operations, we are making Django think it has
        # applied this migration to the database. In reality, we renamed a
        # "annotations_label" table to "labels_label" earlier.
        migrations.SeparateDatabaseAndState(state_operations=state_operations)
    ]

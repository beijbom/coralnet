# -*- coding: utf-8 -*-
# Generated by Django 1.11.25 on 2020-05-03 06:29
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations
from django.db.models import F
from tqdm import tqdm

from annotations.model_utils import AnnotationAreaUtils


def indexing_change(apps, change_value):

    # Migrate Points' row and column values.

    Point = apps.get_model('images', 'Point')

    # Update all Points with a single query instead of <Point count> queries.
    # Based off of the example here:
    # https://docs.djangoproject.com/en/dev/ref/models/expressions/#f-expressions
    # Much faster than saving each object individually, but doesn't call the
    # model's save() method and doesn't emit pre/post save signals.
    Point.objects.all().update(
        row=F('row') + change_value, column=F('column') + change_value)

    if change_value == -1:
        # Check bounds of the updated points. We'll only bother doing this for
        # the forwards migration, since hopefully we won't need the backwards
        # one for production.

        points_with_column_below_min = Point.objects.filter(column__lt=0)
        assert not points_with_column_below_min.exists()

        points_with_column_above_max = Point.objects.filter(
            column__gte=F('image__original_width'))
        assert not points_with_column_above_max.exists()

        points_with_row_below_min = Point.objects.filter(row__lt=0)
        assert not points_with_row_below_min.exists()

        points_with_row_above_max = Point.objects.filter(
            row__gte=F('image__original_height'))
        assert not points_with_row_above_max.exists()

    # Migrate Metadatas' annotation area values. Only pixel based ones,
    # not percentage based ones (percentages already started from 0 prior
    # to this migration).

    Metadata = apps.get_model('images', 'Metadata')
    metadatas_with_pixel_annotation_area = Metadata.objects.filter(
        annotation_area__contains=',')

    # Updating annotation area is more involved, so we can't do the
    # same F expression trick here.
    for metadata in tqdm(
            metadatas_with_pixel_annotation_area,
            disable=settings.TQDM_DISABLE):

        area_dict = AnnotationAreaUtils.db_format_to_numbers(
            metadata.annotation_area)
        area_dict['min_x'] += change_value
        area_dict['max_x'] += change_value
        area_dict['min_y'] += change_value
        area_dict['max_y'] += change_value

        metadata.annotation_area = AnnotationAreaUtils.pixels_to_db_format(
            area_dict['min_x'], area_dict['max_x'],
            area_dict['min_y'], area_dict['max_y'])
        metadata.save()


def indexing_one_to_zero(apps, schema_editor):
    """
    Migrate point rows/columns from start-1 indexes (1 to width/height)
    to start-0 indexes (0 to width-1/height-1).
    This can take a long time.
    """
    indexing_change(apps, -1)


def indexing_zero_to_one(apps, schema_editor):
    """
    Migrate from start-0 indexes to start-1 indexes.
    This can take a long time.
    """
    indexing_change(apps, 1)


class Migration(migrations.Migration):

    dependencies = [
        ('images', '0022_modified_some_defaults'),
    ]

    operations = [
        migrations.RunPython(
            indexing_one_to_zero, indexing_zero_to_one),
    ]

# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-05-31 19:28
from __future__ import unicode_literals
import posixpath
from django.db import migrations


def update_image_filepaths_in_db(apps, schema_editor):
    old_dir = 'data/original/'
    new_dir = 'images/'

    # Note: This migration will NOT move the image files themselves,
    # because using storage classes (which abstract away local vs. S3
    # storage), there is not a simple way to just move a file. There's
    # only copying, which can be a lot slower, and we may have a LOT
    # of images.
    # If you're not setting up a new development machine, make sure
    # that you've moved your image files from the old directory
    # to the new directory.
    # (If you haven't moved them yet, do it later.)

    Image = apps.get_model('images', 'Image')
    images = Image.objects.all()
    image_count = images.count()

    for num, image in enumerate(images, 1):
        old_filepath = image.original_file.name
        filename = posixpath.split(old_filepath)[1]
        new_filepath = posixpath.join(new_dir, filename)

        # Update the filepath in the DB.
        # Since we have to craft a different filepath for each image,
        # there seems to be no way to do a bulk save/update.
        # http://stackoverflow.com/a/12661327
        image.original_file.name = new_filepath
        image.save()

        # Give progress updates every so often.
        if num % 1000 == 0:
            print("Updated {num} of {count} DB entries...".format(
                num=num, count=image_count))


def dont_rollback_filepaths(apps, schema_editor):
    print("\nNo action taken in this migration rollback."
          " If any filepaths in your Image objects were already updated,"
          " those filepaths will just be re-written with the same values"
          " when you re-run this migration.")


class Migration(migrations.Migration):

    dependencies = [
        ('images', '0003_alter_source_labelset_null'),
    ]

    operations = [
        migrations.RunPython(
            update_image_filepaths_in_db, dont_rollback_filepaths,
            elidable=True),
    ]

## This migration should be viewed together with 0016. 
# 0015 adds a field and does the data-migrations.
# 0016 removes the old redundant fields
# The reason for this is postgresql does one migration in a single
# 'transaction'
# http://stackoverflow.com/questions/12838111/south-cannot-alter-table-because-it-has-pending-trigger-events
#
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
        migrations.RunPython(
            copy_confirmed_status, copy_confirmed_status_backwards,
            elidable=True),
        
        
    ]

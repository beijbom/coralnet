# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def add_empty_labelset(apps, schema_editor):
    # We can't import the LabelSet model directly as it may be a newer
    # version than this migration expects. We use the historical version.
    LabelSet = apps.get_model('annotations', 'LabelSet')
    labelset = LabelSet(
        # Must match the former LabelSet.EMPTY_LABELSET_ID.
        # (Even if we hadn't removed that attribute, we couldn't have
        # accessed it directly from here anyway.)
        pk=-1,
        description="Empty labelset. A dummy labelset for new sources.",
    )
    labelset.save()

class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('annotations', '0002_auto_20160415_1727'),
    ]

    operations = [
        migrations.RunPython(add_empty_labelset, elidable=True),
    ]

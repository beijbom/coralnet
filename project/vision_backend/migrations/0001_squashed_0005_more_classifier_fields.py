# -*- coding: utf-8 -*-
# Generated by Django 1.11.25 on 2019-11-06 07:05
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    replaces = [(b'vision_backend', '0001_initial'), (b'vision_backend', '0002_remove_legacy_robot_fields'), (b'vision_backend', '0003_alter_score_label_foreignkey'), (b'vision_backend', '0004_features_model_was_cashed'), (b'vision_backend', '0005_more_classifier_fields')]

    initial = True

    dependencies = [
        ('images', '0011_rename_dupe_image_names'),
        ('labels', '0002_label'),
    ]

    operations = [
        migrations.CreateModel(
            name='Classifier',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('valid', models.BooleanField(default=False)),
                ('runtime_train', models.BigIntegerField(default=0)),
                ('nbr_train_images', models.IntegerField(null=True)),
                ('create_date', models.DateTimeField(auto_now_add=True, verbose_name='Date created')),
                ('source', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='images.Source')),
                ('accuracy', models.FloatField(null=True)),
                ('epoch_ref_accuracy', models.CharField(max_length=512, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Features',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('extracted', models.BooleanField(default=False)),
                ('classified', models.BooleanField(default=False)),
                ('runtime_total', models.IntegerField(null=True)),
                ('runtime_core', models.IntegerField(null=True)),
                ('extracted_date', models.DateTimeField(null=True)),
                ('model_was_cashed', models.NullBooleanField()),
            ],
        ),
        migrations.CreateModel(
            name='Score',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('score', models.IntegerField(default=0)),
                ('image', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='images.Image')),
                ('label', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='labels.Label')),
                ('point', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='images.Point')),
                ('source', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='images.Source')),
            ],
        ),
    ]

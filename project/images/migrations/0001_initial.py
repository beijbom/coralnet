# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import easy_thumbnails.fields
import images.models
from django.conf import settings
import django.core.validators


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Image',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('original_file', easy_thumbnails.fields.ThumbnailerImageField(height_field=b'original_height', width_field=b'original_width', upload_to=images.models.get_original_image_upload_path)),
                ('original_width', models.IntegerField()),
                ('original_height', models.IntegerField()),
                ('upload_date', models.DateTimeField(auto_now_add=True, verbose_name=b'Upload date')),
                ('point_generation_method', models.CharField(max_length=50, verbose_name=b'How points were generated', blank=True)),
                ('process_date', models.DateTimeField(verbose_name=b'Date processed', null=True, editable=False)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ImageStatus',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('preprocessed', models.BooleanField(default=False)),
                ('hasRandomPoints', models.BooleanField(default=False)),
                ('featuresExtracted', models.BooleanField(default=False)),
                ('annotatedByRobot', models.BooleanField(default=False)),
                ('annotatedByHuman', models.BooleanField(default=False)),
                ('featureFileHasHumanLabels', models.BooleanField(default=False)),
                ('usedInCurrentModel', models.BooleanField(default=False)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Metadata',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200, blank=True)),
                ('photo_date', models.DateField(help_text=b'Format: YYYY-MM-DD', null=True, verbose_name=b'Date', blank=True)),
                ('latitude', models.CharField(max_length=20, verbose_name=b'Latitude', blank=True)),
                ('longitude', models.CharField(max_length=20, verbose_name=b'Longitude', blank=True)),
                ('depth', models.CharField(max_length=45, verbose_name=b'Depth', blank=True)),
                ('height_in_cm', models.IntegerField(blank=True, help_text=b'What is the actual span between the top and bottom of this image?\n(This information is used by the automatic annotator.)', null=True, verbose_name=b'Height (cm)', validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(100000)])),
                ('annotation_area', models.CharField(help_text=b'This defines a rectangle of the image where annotation points are allowed to be generated. If you change this, then new points will be generated for this image, and the old points will be deleted.', max_length=50, null=True, verbose_name=b'Annotation area', blank=True)),
                ('camera', models.CharField(max_length=200, verbose_name=b'Camera', blank=True)),
                ('photographer', models.CharField(max_length=45, verbose_name=b'Photographer', blank=True)),
                ('water_quality', models.CharField(max_length=45, verbose_name=b'Water quality', blank=True)),
                ('strobes', models.CharField(max_length=200, verbose_name=b'Strobes', blank=True)),
                ('framing', models.CharField(max_length=200, verbose_name=b'Framing gear used', blank=True)),
                ('balance', models.CharField(max_length=200, verbose_name=b'White balance card', blank=True)),
                ('comments', models.TextField(max_length=1000, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Point',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('row', models.IntegerField()),
                ('column', models.IntegerField()),
                ('point_number', models.IntegerField()),
                ('annotation_status', models.CharField(max_length=1, blank=True)),
                ('image', models.ForeignKey(to='images.Image')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Robot',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('version', models.IntegerField(unique=True)),
                ('path_to_model', models.CharField(max_length=500)),
                ('time_to_train', models.BigIntegerField()),
                ('create_date', models.DateTimeField(auto_now_add=True, verbose_name=b'Date created')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Source',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=200)),
                ('visibility', models.CharField(default=b'v', max_length=1, choices=[(b'b', b'Public'), (b'v', b'Private')])),
                ('create_date', models.DateTimeField(auto_now_add=True, verbose_name=b'Date created')),
                ('description', models.TextField()),
                ('affiliation', models.CharField(max_length=200)),
                ('key1', models.CharField(max_length=50, verbose_name=b'Key 1')),
                ('key2', models.CharField(max_length=50, verbose_name=b'Key 2', blank=True)),
                ('key3', models.CharField(max_length=50, verbose_name=b'Key 3', blank=True)),
                ('key4', models.CharField(max_length=50, verbose_name=b'Key 4', blank=True)),
                ('key5', models.CharField(max_length=50, verbose_name=b'Key 5', blank=True)),
                ('default_point_generation_method', models.CharField(default=b'm_200', help_text=b"When we create annotation points for uploaded images, this is how we'll generate the point locations. Note that if you change this setting later on, it will NOT apply to images that are already uploaded.", max_length=50, verbose_name=b'Point generation method')),
                ('image_height_in_cm', models.IntegerField(help_text=b"This is the number of centimeters of substrate the image cover from the top of the image to the bottom. For example, if you use a framer that is 50cm wide and 35cm tall, this value should be set to 35 (or slightly larger if you image covers areas outside the framer). If use you an AUV, you will need to calculate this based on the field of view and distance from the bottom. This information is needed for the automatic annotation system to normalize the pixel to centimeter ratio.\nYou can also set this on a per-image basis; for images that don't have a specific value set, this default value will be used. Note that all images gets assigned this global default ON UPLOAD. If you change this default, and want this to apply to images that you have already upladed, you must first delete them (under the Browse tab) and then re-upload them.", null=True, verbose_name=b'Default image height coverage (centimeters)', validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(100000)])),
                ('image_annotation_area', models.CharField(help_text=b"This defines a rectangle of the image where annotation points are allowed to be generated.\nFor example, X boundaries of 10% and 95% mean that the leftmost 10% and the rightmost 5% of the image will not have any points.\nYou can also set these boundaries as pixel counts on a per-image basis; for images that don't have a specific value set, these percentages will be used.", max_length=50, null=True, verbose_name=b'Default image annotation area')),
                ('alleviate_threshold', models.IntegerField(default=0, verbose_name=b'Level of alleviation (%)', validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)])),
                ('enable_robot_classifier', models.BooleanField(default=True, help_text=b"With this option on, the automatic classification system will go through your images and add unofficial annotations to them. Then when you enter the annotation tool, you will be able to start from the system's suggestions instead of from a blank slate.", verbose_name=b'Enable robot classifier')),
                ('longitude', models.CharField(max_length=20, blank=True)),
                ('latitude', models.CharField(max_length=20, blank=True)),
                ('labelset', models.ForeignKey(to='annotations.LabelSet')),
            ],
            options={
                'permissions': (('source_view', 'View'), ('source_edit', 'Edit'), ('source_admin', 'Admin')),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SourceInvite',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('source_perm', models.CharField(max_length=50, choices=[(b'source_view', b'View'), (b'source_edit', b'Edit'), (b'source_admin', b'Admin')])),
                ('recipient', models.ForeignKey(related_name=b'invites_received', to=settings.AUTH_USER_MODEL)),
                ('sender', models.ForeignKey(related_name=b'invites_sent', editable=False, to=settings.AUTH_USER_MODEL)),
                ('source', models.ForeignKey(editable=False, to='images.Source')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Value1',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50)),
                ('source', models.ForeignKey(to='images.Source')),
            ],
            options={
                'ordering': ['name'],
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Value2',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50)),
                ('source', models.ForeignKey(to='images.Source')),
            ],
            options={
                'ordering': ['name'],
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Value3',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50)),
                ('source', models.ForeignKey(to='images.Source')),
            ],
            options={
                'ordering': ['name'],
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Value4',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50)),
                ('source', models.ForeignKey(to='images.Source')),
            ],
            options={
                'ordering': ['name'],
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Value5',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50)),
                ('source', models.ForeignKey(to='images.Source')),
            ],
            options={
                'ordering': ['name'],
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='sourceinvite',
            unique_together=set([('recipient', 'source')]),
        ),
        migrations.AddField(
            model_name='robot',
            name='source',
            field=models.ForeignKey(to='images.Source'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='metadata',
            name='value1',
            field=models.ForeignKey(blank=True, to='images.Value1', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='metadata',
            name='value2',
            field=models.ForeignKey(blank=True, to='images.Value2', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='metadata',
            name='value3',
            field=models.ForeignKey(blank=True, to='images.Value3', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='metadata',
            name='value4',
            field=models.ForeignKey(blank=True, to='images.Value4', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='metadata',
            name='value5',
            field=models.ForeignKey(blank=True, to='images.Value5', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='image',
            name='latest_robot_annotator',
            field=models.ForeignKey(editable=False, to='images.Robot', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='image',
            name='metadata',
            field=models.ForeignKey(to='images.Metadata'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='image',
            name='source',
            field=models.ForeignKey(to='images.Source'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='image',
            name='status',
            field=models.ForeignKey(editable=False, to='images.ImageStatus'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='image',
            name='uploaded_by',
            field=models.ForeignKey(editable=False, to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
    ]

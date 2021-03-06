# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'annotation_attempt'
        db.create_table('annotations_annotation_attempt', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('source', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['images.Source'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['accounts.Profile'])),
        ))
        db.send_create_signal('annotations', ['annotation_attempt'])

        # Adding model 'LabelGroup'
        db.create_table('annotations_labelgroup', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=45, blank=True)),
            ('code', self.gf('django.db.models.fields.CharField')(max_length=5, blank=True)),
        ))
        db.send_create_signal('annotations', ['LabelGroup'])

        # Adding model 'Label'
        db.create_table('annotations_label', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=45, blank=True)),
            ('code', self.gf('django.db.models.fields.CharField')(max_length=5, blank=True)),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['annotations.LabelGroup'])),
        ))
        db.send_create_signal('annotations', ['Label'])

        # Adding model 'LabelSet'
        db.create_table('annotations_labelset', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('location', self.gf('django.db.models.fields.CharField')(max_length=45, blank=True)),
            ('attempt', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['annotations.annotation_attempt'])),
        ))
        db.send_create_signal('annotations', ['LabelSet'])

        # Adding model 'Annotation'
        db.create_table('annotations_annotation', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('annotation_date', self.gf('django.db.models.fields.DateField')()),
            ('point', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['images.Point'])),
            ('image', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['images.Image'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['accounts.Profile'])),
            ('label', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['annotations.Label'])),
            ('attempt', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['annotations.annotation_attempt'])),
        ))
        db.send_create_signal('annotations', ['Annotation'])


    def backwards(self, orm):
        
        # Deleting model 'annotation_attempt'
        db.delete_table('annotations_annotation_attempt')

        # Deleting model 'LabelGroup'
        db.delete_table('annotations_labelgroup')

        # Deleting model 'Label'
        db.delete_table('annotations_label')

        # Deleting model 'LabelSet'
        db.delete_table('annotations_labelset')

        # Deleting model 'Annotation'
        db.delete_table('annotations_annotation')


    models = {
        'accounts.profile': {
            'Meta': {'object_name': 'Profile'},
            'about_me': ('django.db.models.fields.CharField', [], {'max_length': '45', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'default': "'en'", 'max_length': '5'}),
            'location': ('django.db.models.fields.CharField', [], {'max_length': '45', 'blank': 'True'}),
            'mugshot': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'blank': 'True'}),
            'privacy': ('django.db.models.fields.CharField', [], {'default': "'registered'", 'max_length': '15'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'my_profile'", 'unique': 'True', 'to': "orm['auth.User']"}),
            'website': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'})
        },
        'annotations.annotation': {
            'Meta': {'object_name': 'Annotation'},
            'annotation_date': ('django.db.models.fields.DateField', [], {}),
            'attempt': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['annotations.annotation_attempt']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['images.Image']"}),
            'label': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['annotations.Label']"}),
            'point': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['images.Point']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['accounts.Profile']"})
        },
        'annotations.annotation_attempt': {
            'Meta': {'object_name': 'annotation_attempt'},
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['images.Source']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['accounts.Profile']"})
        },
        'annotations.label': {
            'Meta': {'object_name': 'Label'},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '5', 'blank': 'True'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['annotations.LabelGroup']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '45', 'blank': 'True'})
        },
        'annotations.labelgroup': {
            'Meta': {'object_name': 'LabelGroup'},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '5', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '45', 'blank': 'True'})
        },
        'annotations.labelset': {
            'Meta': {'object_name': 'LabelSet'},
            'attempt': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['annotations.annotation_attempt']"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.db.models.fields.CharField', [], {'max_length': '45', 'blank': 'True'})
        },
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'images.camerainfo': {
            'Meta': {'object_name': 'CameraInfo'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '45', 'blank': 'True'}),
            'height': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '45', 'blank': 'True'}),
            'photographer': ('django.db.models.fields.CharField', [], {'max_length': '45', 'blank': 'True'}),
            'pixel_cm_ratio': ('django.db.models.fields.IntegerField', [], {}),
            'water_quality': ('django.db.models.fields.CharField', [], {'max_length': '45', 'blank': 'True'}),
            'width': ('django.db.models.fields.IntegerField', [], {})
        },
        'images.image': {
            'Meta': {'object_name': 'Image'},
            'camera': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['images.CameraInfo']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['images.Source']"}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'total_points': ('django.db.models.fields.IntegerField', [], {})
        },
        'images.point': {
            'Meta': {'object_name': 'Point'},
            'annotation_status': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'column': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['images.Image']"}),
            'point_number': ('django.db.models.fields.IntegerField', [], {}),
            'row': ('django.db.models.fields.IntegerField', [], {})
        },
        'images.source': {
            'Meta': {'object_name': 'Source'},
            'create_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key1': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'key2': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'key3': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'key4': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'key5': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'latitude': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'longitude': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'visibility': ('django.db.models.fields.CharField', [], {'max_length': '1'})
        }
    }

    complete_apps = ['annotations']

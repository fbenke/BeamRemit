# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'BeamProfile.proof_of_residence_verified'
        db.delete_column(u'account_beamprofile', 'proof_of_residence_verified')

        # Deleting field 'BeamProfile.passport_verified'
        db.delete_column(u'account_beamprofile', 'passport_verified')

        # Adding field 'BeamProfile.passport_state'
        db.add_column(u'account_beamprofile', 'passport_state',
                      self.gf('django.db.models.fields.CharField')(default='EMP', max_length=3),
                      keep_default=False)

        # Adding field 'BeamProfile.proof_of_residence_state'
        db.add_column(u'account_beamprofile', 'proof_of_residence_state',
                      self.gf('django.db.models.fields.CharField')(default='EMP', max_length=3),
                      keep_default=False)


    def backwards(self, orm):
        # Adding field 'BeamProfile.proof_of_residence_verified'
        db.add_column(u'account_beamprofile', 'proof_of_residence_verified',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)

        # Adding field 'BeamProfile.passport_verified'
        db.add_column(u'account_beamprofile', 'passport_verified',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)

        # Deleting field 'BeamProfile.passport_state'
        db.delete_column(u'account_beamprofile', 'passport_state')

        # Deleting field 'BeamProfile.proof_of_residence_state'
        db.delete_column(u'account_beamprofile', 'proof_of_residence_state')


    models = {
        u'account.beamprofile': {
            'Meta': {'object_name': 'BeamProfile'},
            'aws_passport_content_type': ('django.db.models.fields.CharField', [], {'max_length': '15', 'blank': 'True'}),
            'aws_proof_of_residence_content_type': ('django.db.models.fields.CharField', [], {'max_length': '15', 'blank': 'True'}),
            'city': ('django.db.models.fields.CharField', [], {'max_length': '40', 'blank': 'True'}),
            'country': ('django_countries.fields.CountryField', [], {'max_length': '2', 'blank': 'True'}),
            'date_of_birth': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mugshot': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'blank': 'True'}),
            'passport_state': ('django.db.models.fields.CharField', [], {'default': "'EMP'", 'max_length': '3'}),
            'post_code': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
            'privacy': ('django.db.models.fields.CharField', [], {'default': "'registered'", 'max_length': '15'}),
            'proof_of_residence_state': ('django.db.models.fields.CharField', [], {'default': "'EMP'", 'max_length': '3'}),
            'street': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'profile'", 'unique': 'True', 'to': u"orm['auth.User']"})
        },
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['account']
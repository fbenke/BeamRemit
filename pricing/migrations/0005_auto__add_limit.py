# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Limit'
        db.create_table(u'pricing_limit', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('max_gbp', self.gf('django.db.models.fields.FloatField')()),
            ('start', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('end', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'pricing', ['Limit'])


    def backwards(self, orm):
        # Deleting model 'Limit'
        db.delete_table(u'pricing_limit')


    models = {
        u'pricing.comparison': {
            'Meta': {'object_name': 'Comparison'},
            'end': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'price_comparison': ('jsonfield.fields.JSONField', [], {}),
            'start': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        u'pricing.limit': {
            'Meta': {'object_name': 'Limit'},
            'end': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'max_gbp': ('django.db.models.fields.FloatField', [], {}),
            'start': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        u'pricing.pricing': {
            'Meta': {'object_name': 'Pricing'},
            'end': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'fee': ('django.db.models.fields.FloatField', [], {}),
            'gbp_ghs': ('django.db.models.fields.FloatField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'markup': ('django.db.models.fields.FloatField', [], {}),
            'start': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['pricing']
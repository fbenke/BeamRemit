# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'Comparison.comparison'
        db.delete_column(u'pricing_comparison', 'comparison')

        # Adding field 'Comparison.price_comparison'
        db.add_column(u'pricing_comparison', 'price_comparison',
                      self.gf('jsonfield.fields.JSONField')(default=''),
                      keep_default=False)


    def backwards(self, orm):
        # Adding field 'Comparison.comparison'
        db.add_column(u'pricing_comparison', 'comparison',
                      self.gf('jsonfield.fields.JSONField')(default=''),
                      keep_default=False)

        # Deleting field 'Comparison.price_comparison'
        db.delete_column(u'pricing_comparison', 'price_comparison')


    models = {
        u'pricing.comparison': {
            'Meta': {'object_name': 'Comparison'},
            'end': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'price_comparison': ('jsonfield.fields.JSONField', [], {}),
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
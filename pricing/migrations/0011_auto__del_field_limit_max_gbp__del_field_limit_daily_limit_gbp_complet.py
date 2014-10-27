# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'Limit.max_gbp'
        db.delete_column(u'pricing_limit', 'max_gbp')

        # Deleting field 'Limit.daily_limit_gbp_complete'
        db.delete_column(u'pricing_limit', 'daily_limit_gbp_complete')

        # Deleting field 'Limit.daily_limit_gbp_basic'
        db.delete_column(u'pricing_limit', 'daily_limit_gbp_basic')

        # Deleting field 'Limit.min_gbp'
        db.delete_column(u'pricing_limit', 'min_gbp')


    def backwards(self, orm):
        # Adding field 'Limit.max_gbp'
        db.add_column(u'pricing_limit', 'max_gbp',
                      self.gf('django.db.models.fields.FloatField')(default=0),
                      keep_default=False)

        # Adding field 'Limit.daily_limit_gbp_complete'
        db.add_column(u'pricing_limit', 'daily_limit_gbp_complete',
                      self.gf('django.db.models.fields.FloatField')(default=0),
                      keep_default=False)

        # Adding field 'Limit.daily_limit_gbp_basic'
        db.add_column(u'pricing_limit', 'daily_limit_gbp_basic',
                      self.gf('django.db.models.fields.FloatField')(default=0),
                      keep_default=False)

        # Adding field 'Limit.min_gbp'
        db.add_column(u'pricing_limit', 'min_gbp',
                      self.gf('django.db.models.fields.FloatField')(default=0),
                      keep_default=False)


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
            'start': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'transaction_max_gbp': ('django.db.models.fields.FloatField', [], {}),
            'transaction_min_gbp': ('django.db.models.fields.FloatField', [], {}),
            'user_limit_basic_gbp': ('django.db.models.fields.FloatField', [], {}),
            'user_limit_complete_gbp': ('django.db.models.fields.FloatField', [], {})
        },
        u'pricing.pricing': {
            'Meta': {'object_name': 'Pricing'},
            'end': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'fee': ('django.db.models.fields.FloatField', [], {}),
            'gbp_ghs': ('django.db.models.fields.FloatField', [], {}),
            'gbp_sll': ('django.db.models.fields.FloatField', [], {}),
            'gbp_usd': ('django.db.models.fields.FloatField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'markup': ('django.db.models.fields.FloatField', [], {}),
            'start': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['pricing']
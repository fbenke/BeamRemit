# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Limit.transaction_min_gbp'
        db.add_column(u'pricing_limit', 'transaction_min_gbp',
                      self.gf('django.db.models.fields.FloatField')(default=0),
                      keep_default=False)

        # Adding field 'Limit.transaction_max_gbp'
        db.add_column(u'pricing_limit', 'transaction_max_gbp',
                      self.gf('django.db.models.fields.FloatField')(default=0),
                      keep_default=False)

        # Adding field 'Limit.user_limit_basic_gbp'
        db.add_column(u'pricing_limit', 'user_limit_basic_gbp',
                      self.gf('django.db.models.fields.FloatField')(default=0),
                      keep_default=False)

        # Adding field 'Limit.user_limit_complete_gbp'
        db.add_column(u'pricing_limit', 'user_limit_complete_gbp',
                      self.gf('django.db.models.fields.FloatField')(default=0),
                      keep_default=False)

        # Adding field 'Pricing.gbp_usd'
        db.add_column(u'pricing_pricing', 'gbp_usd',
                      self.gf('django.db.models.fields.FloatField')(default=0),
                      keep_default=False)

        # Adding field 'Pricing.gbp_ssl'
        db.add_column(u'pricing_pricing', 'gbp_ssl',
                      self.gf('django.db.models.fields.FloatField')(default=0),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Limit.transaction_min_gbp'
        db.delete_column(u'pricing_limit', 'transaction_min_gbp')

        # Deleting field 'Limit.transaction_max_gbp'
        db.delete_column(u'pricing_limit', 'transaction_max_gbp')

        # Deleting field 'Limit.user_limit_basic_gbp'
        db.delete_column(u'pricing_limit', 'user_limit_basic_gbp')

        # Deleting field 'Limit.user_limit_complete_gbp'
        db.delete_column(u'pricing_limit', 'user_limit_complete_gbp')

        # Deleting field 'Pricing.gbp_usd'
        db.delete_column(u'pricing_pricing', 'gbp_usd')

        # Deleting field 'Pricing.gbp_ssl'
        db.delete_column(u'pricing_pricing', 'gbp_ssl')


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
            'daily_limit_gbp_basic': ('django.db.models.fields.FloatField', [], {}),
            'daily_limit_gbp_complete': ('django.db.models.fields.FloatField', [], {}),
            'end': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'max_gbp': ('django.db.models.fields.FloatField', [], {}),
            'min_gbp': ('django.db.models.fields.FloatField', [], {}),
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
            'gbp_ssl': ('django.db.models.fields.FloatField', [], {}),
            'gbp_usd': ('django.db.models.fields.FloatField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'markup': ('django.db.models.fields.FloatField', [], {}),
            'start': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['pricing']
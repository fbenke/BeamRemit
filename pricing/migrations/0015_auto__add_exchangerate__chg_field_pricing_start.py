# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'ExchangeRate'
        db.create_table(u'pricing_exchangerate', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('start', self.gf('django.db.models.fields.DateTimeField')()),
            ('end', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('markup', self.gf('django.db.models.fields.FloatField')()),
            ('fee_usd', self.gf('django.db.models.fields.FloatField')()),
            ('fee_gbp', self.gf('django.db.models.fields.FloatField')()),
            ('gbp_ghs', self.gf('django.db.models.fields.FloatField')()),
            ('gbp_usd', self.gf('django.db.models.fields.FloatField')()),
            ('gbp_sll', self.gf('django.db.models.fields.FloatField')()),
        ))
        db.send_create_signal(u'pricing', ['ExchangeRate'])

        # Changing field 'Pricing.start'
        db.alter_column(u'pricing_pricing', 'start', self.gf('django.db.models.fields.DateTimeField')())

    def backwards(self, orm):
        # Deleting model 'ExchangeRate'
        db.delete_table(u'pricing_exchangerate')


        # Changing field 'Pricing.start'
        db.alter_column(u'pricing_pricing', 'start', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True))

    models = {
        u'pricing.comparison': {
            'Meta': {'object_name': 'Comparison'},
            'end': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'price_comparison': ('jsonfield.fields.JSONField', [], {}),
            'start': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        u'pricing.exchangerate': {
            'Meta': {'object_name': 'ExchangeRate'},
            'end': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'fee_gbp': ('django.db.models.fields.FloatField', [], {}),
            'fee_usd': ('django.db.models.fields.FloatField', [], {}),
            'gbp_ghs': ('django.db.models.fields.FloatField', [], {}),
            'gbp_sll': ('django.db.models.fields.FloatField', [], {}),
            'gbp_usd': ('django.db.models.fields.FloatField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'markup': ('django.db.models.fields.FloatField', [], {}),
            'start': ('django.db.models.fields.DateTimeField', [], {})
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
            'fee_gbp': ('django.db.models.fields.FloatField', [], {}),
            'fee_usd': ('django.db.models.fields.FloatField', [], {}),
            'gbp_ghs': ('django.db.models.fields.FloatField', [], {}),
            'gbp_sll': ('django.db.models.fields.FloatField', [], {}),
            'gbp_usd': ('django.db.models.fields.FloatField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'markup': ('django.db.models.fields.FloatField', [], {}),
            'start': ('django.db.models.fields.DateTimeField', [], {})
        }
    }

    complete_apps = ['pricing']
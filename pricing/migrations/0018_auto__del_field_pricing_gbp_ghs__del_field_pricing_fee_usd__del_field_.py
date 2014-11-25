# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'Pricing.gbp_ghs'
        db.delete_column(u'pricing_pricing', 'gbp_ghs')

        # Deleting field 'Pricing.fee_usd'
        db.delete_column(u'pricing_pricing', 'fee_usd')

        # Deleting field 'Pricing.gbp_usd'
        db.delete_column(u'pricing_pricing', 'gbp_usd')

        # Deleting field 'Pricing.gbp_sll'
        db.delete_column(u'pricing_pricing', 'gbp_sll')

        # Deleting field 'Pricing.fee_gbp'
        db.delete_column(u'pricing_pricing', 'fee_gbp')

        # Adding field 'Pricing.fee'
        db.add_column(u'pricing_pricing', 'fee',
                      self.gf('django.db.models.fields.FloatField')(default=0),
                      keep_default=False)

        # Adding field 'Pricing.fee_currency'
        db.add_column(u'pricing_pricing', 'fee_currency',
                      self.gf('django.db.models.fields.CharField')(default='GBP', max_length=4),
                      keep_default=False)

        # Adding field 'Pricing.site'
        db.add_column(u'pricing_pricing', 'site',
                      self.gf('django.db.models.fields.related.ForeignKey')(default=0, related_name='pricing', to=orm['sites.Site']),
                      keep_default=False)


    def backwards(self, orm):
        # Adding field 'Pricing.gbp_ghs'
        db.add_column(u'pricing_pricing', 'gbp_ghs',
                      self.gf('django.db.models.fields.FloatField')(default=0),
                      keep_default=False)

        # Adding field 'Pricing.fee_usd'
        db.add_column(u'pricing_pricing', 'fee_usd',
                      self.gf('django.db.models.fields.FloatField')(default=0),
                      keep_default=False)

        # Adding field 'Pricing.gbp_usd'
        db.add_column(u'pricing_pricing', 'gbp_usd',
                      self.gf('django.db.models.fields.FloatField')(default=0),
                      keep_default=False)

        # Adding field 'Pricing.gbp_sll'
        db.add_column(u'pricing_pricing', 'gbp_sll',
                      self.gf('django.db.models.fields.FloatField')(default=0),
                      keep_default=False)

        # Adding field 'Pricing.fee_gbp'
        db.add_column(u'pricing_pricing', 'fee_gbp',
                      self.gf('django.db.models.fields.FloatField')(default=0),
                      keep_default=False)

        # Deleting field 'Pricing.fee'
        db.delete_column(u'pricing_pricing', 'fee')

        # Deleting field 'Pricing.fee_currency'
        db.delete_column(u'pricing_pricing', 'fee_currency')

        # Deleting field 'Pricing.site'
        db.delete_column(u'pricing_pricing', 'site_id')


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
            'fee': ('django.db.models.fields.FloatField', [], {}),
            'fee_currency': ('django.db.models.fields.CharField', [], {'max_length': '4'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'markup': ('django.db.models.fields.FloatField', [], {}),
            'site': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'pricing'", 'to': u"orm['sites.Site']"}),
            'start': ('django.db.models.fields.DateTimeField', [], {})
        },
        u'sites.site': {
            'Meta': {'ordering': "(u'domain',)", 'object_name': 'Site', 'db_table': "u'django_site'"},
            'domain': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        }
    }

    complete_apps = ['pricing']
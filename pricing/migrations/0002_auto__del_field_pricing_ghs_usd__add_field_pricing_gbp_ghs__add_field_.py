# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'Pricing.ghs_usd'
        db.delete_column(u'pricing_pricing', 'ghs_usd')

        # Adding field 'Pricing.gbp_ghs'
        db.add_column(u'pricing_pricing', 'gbp_ghs',
                      self.gf('django.db.models.fields.FloatField')(default=0),
                      keep_default=False)

        # Adding field 'Pricing.fee'
        db.add_column(u'pricing_pricing', 'fee',
                      self.gf('django.db.models.fields.FloatField')(default=0),
                      keep_default=False)


    def backwards(self, orm):
        # Adding field 'Pricing.ghs_usd'
        db.add_column(u'pricing_pricing', 'ghs_usd',
                      self.gf('django.db.models.fields.FloatField')(default=0),
                      keep_default=False)

        # Deleting field 'Pricing.gbp_ghs'
        db.delete_column(u'pricing_pricing', 'gbp_ghs')

        # Deleting field 'Pricing.fee'
        db.delete_column(u'pricing_pricing', 'fee')


    models = {
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
# -*- coding: utf-8 -*-
from south.v2 import DataMigration
from south.db import db


class Migration(DataMigration):

    def forwards(self, orm):
        for pricing in orm.Pricing.objects.all():
            exchange_rate = orm.ExchangeRate(
                id=pricing.id,
                start=pricing.start,
                end=pricing.end,
                gbp_ghs=pricing.gbp_ghs,
                gbp_sll=pricing.gbp_sll,
                gbp_usd=pricing.gbp_usd,
                markup=pricing.markup,
                fee_gbp=pricing.fee_gbp,
                fee_usd=pricing.fee_usd
            )
            exchange_rate.save()

        db.execute('SELECT setval(pg_get_serial_sequence(\'"pricing_exchangerate"\',\'id\'), coalesce(max("id"), 1), max("id") IS NOT null) FROM "pricing_exchangerate";')

    def backwards(self, orm):
        pass

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
    symmetrical = True

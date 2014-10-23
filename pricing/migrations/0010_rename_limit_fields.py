from south.v2 import DataMigration


class Migration(DataMigration):

    def forwards(self, orm):
        for limit in orm.Limit.objects.all():
            limit.transaction_min_gbp = limit.max_gbp
            limit.transaction_max_gbp = limit.min_gbp
            limit.user_limit_basic_gbp = limit.daily_limit_gbp_basic
            limit.user_limit_complete_gbp = limit.daily_limit_gbp_complete
            limit.save()

    def backwards(self, orm):
        for limit in orm.Limit.objects.all():
            limit.max_gbp = limit.transaction_min_gbp
            limit.min_gbp = limit.transaction_max_gbp
            limit.daily_limit_gbp_basic = limit.user_limit_basic_gbp
            limit.daily_limit_gbp_complete = limit.user_limit_complete_gbp
            limit.save()

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
            'gbp_sll': ('django.db.models.fields.FloatField', [], {}),
            'gbp_usd': ('django.db.models.fields.FloatField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'markup': ('django.db.models.fields.FloatField', [], {}),
            'start': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['pricing']
    symmetrical = True

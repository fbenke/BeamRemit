# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'BlockchainPayment.state'
        db.add_column(u'btc_payment_blockchainpayment', 'state',
                      self.gf('django.db.models.fields.CharField')(default='PEND', max_length=4),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'BlockchainPayment.state'
        db.delete_column(u'btc_payment_blockchainpayment', 'state')


    models = {
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
        u'btc_payment.blockchaininvoice': {
            'Meta': {'object_name': 'BlockchainInvoice'},
            'balance_due': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'btc_address': ('django.db.models.fields.CharField', [], {'max_length': '34'}),
            'btc_usd': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invoice_id': ('django.db.models.fields.CharField', [], {'max_length': '36'}),
            'sender_usd': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'state': ('django.db.models.fields.CharField', [], {'default': "'UNPD'", 'max_length': '4'}),
            'transaction': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'blockchain_invoice'", 'unique': 'True', 'to': u"orm['transaction.Transaction']"})
        },
        u'btc_payment.blockchainpayment': {
            'Meta': {'object_name': 'BlockchainPayment'},
            'amount': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'forward_transaction_hash': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'input_transaction_hash': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'invoice': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'payments'", 'to': u"orm['btc_payment.BlockchainInvoice']"}),
            'received_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'state': ('django.db.models.fields.CharField', [], {'default': "'PEND'", 'max_length': '4'})
        },
        u'btc_payment.gocoininvoice': {
            'Meta': {'object_name': 'GoCoinInvoice'},
            'balance_due': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'btc_address': ('django.db.models.fields.CharField', [], {'max_length': '34'}),
            'btc_usd': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invoice_id': ('django.db.models.fields.CharField', [], {'max_length': '36'}),
            'sender_usd': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'state': ('django.db.models.fields.CharField', [], {'default': "'UNPD'", 'max_length': '4'}),
            'transaction': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'gocoin_invoice'", 'unique': 'True', 'to': u"orm['transaction.Transaction']"})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'pricing.exchangerate': {
            'Meta': {'object_name': 'ExchangeRate'},
            'end': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'gbp_ghs': ('django.db.models.fields.FloatField', [], {}),
            'gbp_sll': ('django.db.models.fields.FloatField', [], {}),
            'gbp_usd': ('django.db.models.fields.FloatField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'start': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        u'pricing.pricing': {
            'Meta': {'object_name': 'Pricing'},
            'end': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'fee': ('django.db.models.fields.FloatField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'markup': ('django.db.models.fields.FloatField', [], {}),
            'site': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'pricing'", 'to': u"orm['sites.Site']"}),
            'start': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        u'sites.site': {
            'Meta': {'ordering': "(u'domain',)", 'object_name': 'Site', 'db_table': "u'django_site'"},
            'domain': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'transaction.recipient': {
            'Meta': {'object_name': 'Recipient'},
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'phone_number': ('django.db.models.fields.CharField', [], {'max_length': '15'})
        },
        u'transaction.transaction': {
            'Meta': {'ordering': "['-initialized_at']", 'object_name': 'Transaction'},
            'amount_btc': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'cancelled_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'comments': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'exchange_rate': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'transaction'", 'to': u"orm['pricing.ExchangeRate']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'initialized_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'invalidated_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'paid_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'payment_processor': ('django.db.models.fields.CharField', [], {'max_length': '4'}),
            'pricing': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'transaction'", 'to': u"orm['pricing.Pricing']"}),
            'processed_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'received_amount': ('django.db.models.fields.FloatField', [], {}),
            'receiving_country': ('django_countries.fields.CountryField', [], {'max_length': '2'}),
            'recipient': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'transactions'", 'to': u"orm['transaction.Recipient']"}),
            'reference_number': ('django.db.models.fields.CharField', [], {'max_length': '6'}),
            'sender': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'transactions'", 'to': u"orm['auth.User']"}),
            'sent_amount': ('django.db.models.fields.FloatField', [], {}),
            'sent_currency': ('django.db.models.fields.CharField', [], {'max_length': '4'}),
            'state': ('django.db.models.fields.CharField', [], {'default': "'INIT'", 'max_length': '4'})
        }
    }

    complete_apps = ['btc_payment']
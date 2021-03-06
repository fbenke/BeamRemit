# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    depends_on = (
        ('pricing', '0001_initial'),
    )

    def forwards(self, orm):
        # Adding model 'Recipient'
        db.create_table(u'transaction_recipient', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('phone_number', self.gf('django.db.models.fields.CharField')(max_length=15)),
            ('notification_email', self.gf('django.db.models.fields.EmailField')(max_length=75, blank=True)),
        ))
        db.send_create_signal(u'transaction', ['Recipient'])

        # Adding model 'Transaction'
        db.create_table(u'transaction_transaction', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('recipient', self.gf('django.db.models.fields.related.ForeignKey')(related_name='transactions', to=orm['transaction.Recipient'])),
            ('sender', self.gf('django.db.models.fields.related.ForeignKey')(related_name='transactions', to=orm['auth.User'])),
            ('pricing', self.gf('django.db.models.fields.related.ForeignKey')(related_name='transactions', to=orm['pricing.Pricing'])),
            ('amount_gbp', self.gf('django.db.models.fields.FloatField')()),
            ('amount_btc', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('amount_ghs', self.gf('django.db.models.fields.FloatField')(null=True)),
            ('coinbase_button_code', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('reference_number', self.gf('django.db.models.fields.CharField')(max_length=6)),
            ('coinbase_order_reference', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('state', self.gf('django.db.models.fields.CharField')(default='INIT', max_length=4)),
            ('initialized_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('paid_at', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('processed_at', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('declined_at', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('cancelled_at', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('invalidated_at', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'transaction', ['Transaction'])


    def backwards(self, orm):
        # Deleting model 'Recipient'
        db.delete_table(u'transaction_recipient')

        # Deleting model 'Transaction'
        db.delete_table(u'transaction_transaction')


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
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'pricing.pricing': {
            'Meta': {'object_name': 'Pricing'},
            'end': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'ghs_usd': ('django.db.models.fields.FloatField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'markup': ('django.db.models.fields.FloatField', [], {}),
            'start': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        u'transaction.recipient': {
            'Meta': {'object_name': 'Recipient'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'notification_email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'phone_number': ('django.db.models.fields.CharField', [], {'max_length': '15'})
        },
        u'transaction.transaction': {
            'Meta': {'ordering': "['-initialized_at']", 'object_name': 'Transaction'},
            'amount_btc': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'amount_gbp': ('django.db.models.fields.FloatField', [], {}),
            'amount_ghs': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'cancelled_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'coinbase_button_code': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'coinbase_order_reference': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'declined_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'initialized_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'invalidated_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'paid_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'pricing': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'transactions'", 'to': u"orm['pricing.Pricing']"}),
            'processed_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'recipient': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'transactions'", 'to': u"orm['transaction.Recipient']"}),
            'reference_number': ('django.db.models.fields.CharField', [], {'max_length': '6'}),
            'sender': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'transactions'", 'to': u"orm['auth.User']"}),
            'state': ('django.db.models.fields.CharField', [], {'default': "'INIT'", 'max_length': '4'})
        }
    }

    complete_apps = ['transaction']
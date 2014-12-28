# -*- coding: utf-8 -*-
from south.v2 import DataMigration
from pricing.models import end_previous_object
from django.core.exceptions import ObjectDoesNotExist


class Migration(DataMigration):

    def forwards(self, orm):
        "Write your forwards methods here."
        # Note: Don't use "from appname.models import ModelName".
        # Use orm.ModelName to refer to models in this application,
        # and orm['appname.ModelName'] for models in other applications.
        try:
            site = orm['sites.Site'].objects.get(id=0)
            end_previous_object(orm.State, site=site)

            state_beam = orm.State(
                state='UP',
                site=orm['sites.Site'].objects.get(id=0)
            )
            state_beam.save()

            state_bae = orm.State(
                state='UP',
                site=orm['sites.Site'].objects.get(id=1)
            )
            state_bae.save()
        except ObjectDoesNotExist:
            pass

    def backwards(self, orm):
        pass

    models = {
        u'sites.site': {
            'Meta': {'ordering': "(u'domain',)", 'object_name': 'Site', 'db_table': "u'django_site'"},
            'domain': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'state.state': {
            'Meta': {'object_name': 'State'},
            'end': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'site': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'app_state'", 'to': u"orm['sites.Site']"}),
            'start': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'state': ('django.db.models.fields.CharField', [], {'default': "'UP'", 'max_length': '4'})
        }
    }

    complete_apps = ['sites', 'state']
    symmetrical = True

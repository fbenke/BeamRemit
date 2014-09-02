from south.v2 import DataMigration

from django.conf import settings


class Migration(DataMigration):

    def forwards(self, orm):
        "Write your forwards methods here."

        orm['sites.site'].objects.all().delete()
        site = orm['sites.site'].objects.create(
            id=0,
            domain=settings.ENV_SITE_MAPPING[settings.ENV][settings.SITE_USER],
            name='Beam'
        )
        site.save()

    def backwards(self, orm):
        orm['sites.site'].objects.all().delete()
        site = orm['sites.site'].objects.create(
            id=0,
            domain='example.com',
            name='example.com'
        )
        site.save()

    models = {
        u'sites.site': {
            'Meta': {'ordering': "(u'domain',)", 'object_name': 'Site', 'db_table': "u'django_site'"},
            'domain': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        }
    }

    complete_apps = ['sites']
    symmetrical = True

from django.contrib import admin
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone

from beam.utils.log import log_error

from state.models import State


class StateAdmin(admin.ModelAdmin):

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ('id', 'start', 'end', 'state')
        else:
            return ('id', 'start', 'end')

    list_display = ('id', 'start', 'end', 'state')

    def save_model(self, request, obj, form, change):

        if obj.id:
            return

        try:
            previous_object = State.objects.get(end__isnull=True)
            if previous_object.state != obj.state:
                previous_object.end = timezone.now()
                previous_object.save()
        except ObjectDoesNotExist:
            if State.objects.all().exists():
                log_error('ERROR State - Failed to end previous state.')
        
        obj.save()

admin.site.register(State, StateAdmin)

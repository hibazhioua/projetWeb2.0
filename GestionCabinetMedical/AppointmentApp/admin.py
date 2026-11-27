from django.contrib import admin
from AppointmentApp.models import Appointment


# Register your models here.
@admin.register(Appointment)
class AppointmentAdminPersonaliser(admin.ModelAdmin):
    list_display = ( 'reason', 'status', 'appointment_date')
    list_filter = ('status','reason', 'appointment_date')

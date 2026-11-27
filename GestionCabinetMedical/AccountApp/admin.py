from django.contrib import admin
from AppointmentApp.models import Appointment

from AccountApp.models import Doctor, Patient, User, specialty
admin.site.register(User)
admin.site.register(Doctor)
admin.site.register(Patient)
admin.site.register(specialty)

# Register your models here.

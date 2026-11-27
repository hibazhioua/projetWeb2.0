from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinLengthValidator,MaxLengthValidator,RegexValidator
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db import models


# Create your models here.
class specialty (models.Model):
    name=models.CharField(max_length=50)
    class Meta():
        verbose_name = "specialty"
        verbose_name_plural = "specialties"
    def __str__(self):
         return f'{self.name}'
class User(AbstractUser): 
    pass


number_validators=[RegexValidator(regex=r'^\d{8}$', message='Phone number must be 8 digits')]
def birth_date_validator(date):
    if date >= timezone.localdate():
        raise ValidationError("Birth date cannot be in the future.")
class Doctor (User):
    license_number=models.CharField(max_length=6,unique=True, validators=[MinLengthValidator(6)])
    phone=models.CharField(max_length=8,unique=True, validators=number_validators)
    specialty=models.ManyToManyField(specialty,related_name='doctors')
    class Meta():
        verbose_name = "Doctor"
        verbose_name_plural = "Doctors"
    def __str__(self):
        return f'{self.first_name} {self.last_name} - {self.license_number}'


class Patient (User):
    national_id=models.CharField(max_length=8,unique=True)
    phone=models.CharField(max_length=8,unique=True, validators=number_validators)
    birth_date=models.DateField(blank=True, validators=[birth_date_validator])
    class Meta():
        verbose_name = "Patient"
        verbose_name_plural = "Patients"

    
    
    
import tempfile
from datetime import date, timedelta

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from django.test import TestCase, override_settings
from django.utils import timezone

# pyrefly: ignore[missing-import]
from AccountApp.models import Doctor, Patient
# pyrefly: ignore[missing-import]
from AppointmentApp.models import Appointment


class AppointmentModelTests(TestCase):
    def setUp(self):
        self.doctor = Doctor.objects.create_user(
            username='doc1',
            password='password123',
            first_name='Ali',
            last_name='Ben Salah',
            license_number='DOC123',
            phone='12345678',
        )
        self.other_doctor = Doctor.objects.create_user(
            username='doc2',
            password='password123',
            first_name='Sami',
            last_name='Trabelsi',
            license_number='DOC456',
            phone='87654321',
        )
        self.patient = Patient.objects.create_user(
            username='pat1',
            password='password123',
            first_name='Hiba',
            last_name='Mansour',
            national_id='11223344',
            phone='55667788',
            birth_date=date(2000, 1, 15),
        )

    def test_valid_future_appointment_and_defaults(self):
        future_date = timezone.now() + timedelta(days=1)
        appt = Appointment(
            doctor=self.doctor,
            patient=self.patient,
            reason='Consultation générale',
            appointment_date=future_date,
        )
        appt.full_clean()
        appt.save()

        self.assertEqual(appt.status, Appointment.Status.PENDING)
        self.assertEqual(appt.duration_minutes, 30)
        self.assertIsNotNone(appt.created_at)
        self.assertIsNotNone(appt.updated_at)

    def test_past_appointment_date_rejected_on_creation(self):
        past_date = timezone.now() - timedelta(hours=2)
        appt = Appointment(
            doctor=self.doctor,
            patient=self.patient,
            reason='Consultation passée',
            appointment_date=past_date,
        )
        with self.assertRaises(ValidationError) as ctx:
            appt.full_clean()
        self.assertIn('appointment_date', ctx.exception.message_dict)

    def test_past_appointment_remains_editable_when_date_unchanged(self):
        past_date = timezone.now() - timedelta(days=1)
        # Saved directly (simulating an appointment that was created earlier and is now in the past)
        appt = Appointment.objects.create(
            doctor=self.doctor,
            patient=self.patient,
            reason='Suivi',
            appointment_date=past_date,
        )
        with tempfile.TemporaryDirectory() as tmp_media:
            with override_settings(MEDIA_ROOT=tmp_media):
                appt.status = Appointment.Status.CONFIRMED
                appt.prescription = SimpleUploadedFile('ordonnance.pdf', b'%PDF-1.4 test')
                appt.full_clean()  # Should not raise ValidationError
                appt.save()
        self.assertEqual(appt.status, Appointment.Status.CONFIRMED)

    def test_changing_appointment_date_to_past_is_rejected(self):
        future_date = timezone.now() + timedelta(days=2)
        appt = Appointment.objects.create(
            doctor=self.doctor,
            patient=self.patient,
            reason='Contrôle',
            appointment_date=future_date,
        )
        appt.appointment_date = timezone.now() - timedelta(hours=1)
        with self.assertRaises(ValidationError) as ctx:
            appt.full_clean()
        self.assertIn('appointment_date', ctx.exception.message_dict)

    def test_prescription_only_accepts_pdf(self):
        future_date = timezone.now() + timedelta(days=1)
        appt = Appointment(
            doctor=self.doctor,
            patient=self.patient,
            reason='Test fichier',
            appointment_date=future_date,
            prescription=SimpleUploadedFile('notes.txt', b'hello'),
        )
        with self.assertRaises(ValidationError) as ctx:
            appt.full_clean()
        self.assertIn('prescription', ctx.exception.message_dict)

    def test_unique_doctor_appointment_date_constraint(self):
        slot = timezone.now() + timedelta(days=3)
        Appointment.objects.create(
            doctor=self.doctor,
            patient=self.patient,
            reason='Premier RDV',
            appointment_date=slot,
        )
        # Same doctor & same slot -> IntegrityError
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Appointment.objects.create(
                    doctor=self.doctor,
                    patient=self.patient,
                    reason='Doublon',
                    appointment_date=slot,
                )
        # Different doctor & same slot -> allowed
        other = Appointment.objects.create(
            doctor=self.other_doctor,
            patient=self.patient,
            reason='Autre médecin',
            appointment_date=slot,
        )
        self.assertIsNotNone(other.pk)

    def test_ordering_by_appointment_date(self):
        d2 = timezone.now() + timedelta(days=5)
        d1 = timezone.now() + timedelta(days=2)
        a2 = Appointment.objects.create(
            doctor=self.doctor,
            patient=self.patient,
            reason='Plus tard',
            appointment_date=d2,
        )
        a1 = Appointment.objects.create(
            doctor=self.doctor,
            patient=self.patient,
            reason='Plus tôt',
            appointment_date=d1,
        )
        self.assertEqual(list(Appointment.objects.all()), [a1, a2])

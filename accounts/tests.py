# accounts/tests.py
from django.test import TestCase
from django.core.exceptions import ValidationError
from accounts.models import User, EmployerProfile


class EmployerProfileValidationTests(TestCase):
    def test_rejects_non_employer_user(self):
        candidate = User.objects.create_user(
            username='cand1', password='x', role=User.Role.CANDIDATE
        )
        profile = EmployerProfile(user=candidate, company_name='Test Co')
        with self.assertRaises(ValidationError):
            profile.clean()

    def test_accepts_employer_user(self):
        employer = User.objects.create_user(
            username='emp1', password='x', role=User.Role.EMPLOYER
        )
        profile = EmployerProfile(user=employer, company_name='Test Co')
        profile.clean()  # should not raise

    def test_rejects_non_admin_reviewer(self):
        employer = User.objects.create_user(
            username='emp2', password='x', role=User.Role.EMPLOYER
        )
        candidate = User.objects.create_user(
            username='cand2', password='x', role=User.Role.CANDIDATE
        )
        profile = EmployerProfile(
            user=employer, company_name='Test Co', reviewed_by=candidate
        )
        with self.assertRaises(ValidationError):
            profile.clean()
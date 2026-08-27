from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from accounts.models import User
from jobs.models import Job


class JobValidationTests(TestCase):
    def setUp(self):
        self.employer = User.objects.create_user(
            username='emp1', password='x', role=User.Role.EMPLOYER
        )
        self.admin = User.objects.create_user(
            username='admin1', password='x', role=User.Role.ADMIN
        )
        self.candidate = User.objects.create_user(
            username='cand1', password='x', role=User.Role.CANDIDATE
        )

    def _make_job(self, **overrides):
        defaults = dict(
            employer=self.employer,
            title='Chef',
            description='Kitchen role',
            country='Taiwan',
            city='Taipei',
            salary_min=Decimal('20000'),
            salary_max=Decimal('25000'),
            currency='TWD',
            quota=5,
        )
        defaults.update(overrides)
        return Job(**defaults)

    def test_accepts_valid_job(self):
        job = self._make_job()
        job.clean()  # should not raise

    def test_rejects_non_employer_user(self):
        job = self._make_job(employer=self.candidate)
        with self.assertRaises(ValidationError):
            job.clean()

    def test_rejects_salary_min_greater_than_max(self):
        job = self._make_job(salary_min=Decimal('30000'), salary_max=Decimal('25000'))
        with self.assertRaises(ValidationError):
            job.clean()

    def test_rejects_non_admin_reviewer(self):
        job = self._make_job(reviewed_by=self.candidate)
        with self.assertRaises(ValidationError):
            job.clean()

    def test_accepts_admin_reviewer(self):
        job = self._make_job(reviewed_by=self.admin)
        job.clean()  # should not raise
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from accounts.models import User
from jobs.models import Job, JobQualification


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

class JobQualificationValidationTests(TestCase):
    def setUp(self):
        self.employer = User.objects.create_user(
            username='emp2', password='x', role=User.Role.EMPLOYER
        )
        self.job = Job(
            employer=self.employer,
            title='Line Cook',
            description='Kitchen role',
            country='Taiwan',
            city='Taipei',
            salary_min=Decimal('20000'),
            salary_max=Decimal('25000'),
            currency='TWD',
            quota=3,
        )
        self.job.full_clean()
        self.job.save()

    def test_accepts_valid_qualification(self):
        qual = JobQualification(
            job=self.job,
            category=JobQualification.Category.LANGUAGE,
            label='Bahasa Mandarin',
            min_value=3,
            min_value_label='HSK 3',
        )
        qual.clean()  # should not raise

    def test_rejects_negative_min_value(self):
        qual = JobQualification(
            job=self.job,
            category=JobQualification.Category.LANGUAGE,
            label='Bahasa Mandarin',
            min_value=-1,
        )
        with self.assertRaises(ValidationError):
            qual.clean()

    def test_str_uses_min_value_label_when_present(self):
        qual = JobQualification(
            job=self.job,
            category=JobQualification.Category.LANGUAGE,
            label='Bahasa Mandarin',
            min_value=3,
            min_value_label='HSK 3',
        )
        self.assertIn('HSK 3', str(qual))

    def test_str_falls_back_to_min_value_when_label_blank(self):
        qual = JobQualification(
            job=self.job,
            category=JobQualification.Category.AGE,
            label='Minimum Age',
            min_value=18,
            min_value_label='',
        )
        self.assertIn('18', str(qual))
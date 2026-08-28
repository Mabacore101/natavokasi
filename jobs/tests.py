from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from accounts.models import User
from jobs.models import Job, JobQualification

from django.contrib.admin.sites import AdminSite
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory
from jobs.admin import JobAdmin

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


class JobAdminActionTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(
            username='admin3', password='x', role=User.Role.ADMIN, is_staff=True
        )
        self.employer = User.objects.create_user(
            username='emp20', password='x', role=User.Role.EMPLOYER
        )
        self.job = Job.objects.create(
            employer=self.employer,
            title='Housekeeper',
            description='Hotel role',
            country='Taiwan',
            city='Taichung',
            salary_min=Decimal('17000'),
            salary_max=Decimal('20000'),
            currency='TWD',
            quota=1,
            status=Job.Status.PENDING_REVIEW,
        )
        self.site = AdminSite()
        self.model_admin = JobAdmin(Job, self.site)
        self.factory = RequestFactory()

    def _request(self):
        request = self.factory.get('/admin/jobs/job/')
        request.user = self.admin_user
        setattr(request, 'session', {})
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        return request

    def test_approve_jobs_sets_status_and_audit_fields(self):
        queryset = Job.objects.filter(pk=self.job.pk)
        self.model_admin.approve_jobs(self._request(), queryset)

        self.job.refresh_from_db()
        self.assertEqual(self.job.status, Job.Status.LIVE)
        self.assertEqual(self.job.reviewed_by, self.admin_user)
        self.assertIsNotNone(self.job.reviewed_at)

    def test_request_revision_sets_status_and_audit_fields(self):
        queryset = Job.objects.filter(pk=self.job.pk)
        self.model_admin.request_revision(self._request(), queryset)

        self.job.refresh_from_db()
        self.assertEqual(self.job.status, Job.Status.REVISION_REQUESTED)
        self.assertEqual(self.job.reviewed_by, self.admin_user)
        self.assertIsNotNone(self.job.reviewed_at)
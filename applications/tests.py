from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from accounts.models import User
from applications.models import Application
from jobs.models import Job


class ApplicationValidationTests(TestCase):
    def setUp(self):
        self.candidate = User.objects.create_user(
            username='cand1', password='x', role=User.Role.CANDIDATE
        )
        self.employer = User.objects.create_user(
            username='emp1', password='x', role=User.Role.EMPLOYER
        )

        self.live_job = Job(
            employer=self.employer,
            title='Line Cook',
            description='Kitchen role',
            country='Taiwan',
            city='Taipei',
            salary_min=Decimal('20000'),
            salary_max=Decimal('25000'),
            currency='TWD',
            quota=3,
            status=Job.Status.LIVE,
        )
        self.live_job.full_clean()
        self.live_job.save()

        self.draft_job = Job(
            employer=self.employer,
            title='Waiter',
            description='Service role',
            country='Taiwan',
            city='Taipei',
            salary_min=Decimal('18000'),
            salary_max=Decimal('22000'),
            currency='TWD',
            quota=2,
            status=Job.Status.DRAFT,
        )
        self.draft_job.full_clean()
        self.draft_job.save()

    def test_accepts_valid_application(self):
        app = Application(candidate=self.candidate, job=self.live_job)
        app.clean()  # should not raise

    def test_rejects_non_candidate_user(self):
        app = Application(candidate=self.employer, job=self.live_job)
        with self.assertRaises(ValidationError):
            app.clean()

    def test_rejects_application_to_non_live_job(self):
        app = Application(candidate=self.candidate, job=self.draft_job)
        with self.assertRaises(ValidationError):
            app.clean()

    def test_duplicate_application_raises_integrity_error(self):
        Application.objects.create(candidate=self.candidate, job=self.live_job)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Application.objects.create(candidate=self.candidate, job=self.live_job)
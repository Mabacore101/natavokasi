from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from accounts.models import User
from applications.models import Application, ApplicationAnswer
from jobs.models import Job, JobQualification


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

class ApplicationAnswerValidationTests(TestCase):
    def setUp(self):
        self.candidate = User.objects.create_user(
            username='cand2', password='x', role=User.Role.CANDIDATE
        )
        self.employer = User.objects.create_user(
            username='emp3', password='x', role=User.Role.EMPLOYER
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
            status=Job.Status.LIVE,
        )
        self.job.full_clean()
        self.job.save()

        self.qualification = JobQualification(
            job=self.job,
            category=JobQualification.Category.LANGUAGE,
            label='Bahasa Mandarin',
            min_value=3,
            min_value_label='HSK 3',
        )
        self.qualification.full_clean()
        self.qualification.save()

        self.other_job = Job(
            employer=self.employer,
            title='Waiter',
            description='Service role',
            country='Taiwan',
            city='Taipei',
            salary_min=Decimal('18000'),
            salary_max=Decimal('22000'),
            currency='TWD',
            quota=2,
            status=Job.Status.LIVE,
        )
        self.other_job.full_clean()
        self.other_job.save()

        self.other_qualification = JobQualification(
            job=self.other_job,
            category=JobQualification.Category.LANGUAGE,
            label='English',
            min_value=1,
        )
        self.other_qualification.full_clean()
        self.other_qualification.save()

        self.application = Application.objects.create(
            candidate=self.candidate, job=self.job
        )

    def test_computes_meets_requirement_true_when_value_sufficient(self):
        answer = ApplicationAnswer(
            application=self.application,
            qualification=self.qualification,
            candidate_value=4,
        )
        answer.save()
        self.assertTrue(answer.meets_requirement)

    def test_computes_meets_requirement_false_when_value_insufficient(self):
        answer = ApplicationAnswer(
            application=self.application,
            qualification=self.qualification,
            candidate_value=2,
        )
        answer.save()
        self.assertFalse(answer.meets_requirement)

    def test_rejects_qualification_from_different_job(self):
        answer = ApplicationAnswer(
            application=self.application,
            qualification=self.other_qualification,
            candidate_value=1,
        )
        with self.assertRaises(ValidationError):
            answer.save()

    def test_duplicate_answer_raises_validation_error(self):
        ApplicationAnswer.objects.create(
            application=self.application,
            qualification=self.qualification,
            candidate_value=4,
        )
        with self.assertRaises(ValidationError):
            ApplicationAnswer.objects.create(
                application=self.application,
                qualification=self.qualification,
                candidate_value=5,
            )

    def test_meets_requirement_not_recomputed_on_update(self):
        answer = ApplicationAnswer.objects.create(
            application=self.application,
            qualification=self.qualification,
            candidate_value=4,
        )
        self.assertTrue(answer.meets_requirement)

        answer.candidate_value = 1
        answer.save()

        answer.refresh_from_db()
        self.assertTrue(answer.meets_requirement)
        self.assertEqual(answer.candidate_value, 1)
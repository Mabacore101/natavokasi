# accounts/tests.py
from django.test import TestCase
from django.core.exceptions import ValidationError
from accounts.models import User, EmployerProfile

from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory
from accounts.admin import EmployerProfileAdmin
from django.contrib.messages.storage.fallback import FallbackStorage

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

class EmployerProfileAdminActionTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(
            username='admin2', password='x', role=User.Role.ADMIN, is_staff=True
        )
        self.employer_user = User.objects.create_user(
            username='emp10', password='x', role=User.Role.EMPLOYER
        )
        self.profile = EmployerProfile.objects.create(
            user=self.employer_user, company_name='Test Co 2'
        )
        self.site = AdminSite()
        self.model_admin = EmployerProfileAdmin(EmployerProfile, self.site)
        self.factory = RequestFactory()

    def _request(self):
        request = self.factory.get('/admin/accounts/employerprofile/')
        request.user = self.admin_user
        setattr(request, 'session', {})
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        return request

    def test_approve_employers_sets_status_and_audit_fields(self):
        queryset = EmployerProfile.objects.filter(pk=self.profile.pk)
        self.model_admin.approve_employers(self._request(), queryset)

        self.profile.refresh_from_db()
        self.assertEqual(self.profile.verification_status, EmployerProfile.VerificationStatus.VERIFIED)
        self.assertEqual(self.profile.reviewed_by, self.admin_user)
        self.assertIsNotNone(self.profile.reviewed_at)

    def test_reject_employers_sets_status_and_audit_fields(self):
        queryset = EmployerProfile.objects.filter(pk=self.profile.pk)
        self.model_admin.reject_employers(self._request(), queryset)

        self.profile.refresh_from_db()
        self.assertEqual(self.profile.verification_status, EmployerProfile.VerificationStatus.REJECTED_SUSPENDED)
        self.assertEqual(self.profile.reviewed_by, self.admin_user)
        self.assertIsNotNone(self.profile.reviewed_at)
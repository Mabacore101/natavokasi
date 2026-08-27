from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import ValidationError

class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'admin', 'Admin'
        EMPLOYER = 'employer', 'Employer'
        CANDIDATE = 'candidate', 'Candidate'

    role = models.CharField(max_length=20, choices=Role.choices)

    def __str__(self):
        return f"{self.username} ({self.role})"

class EmployerProfile(models.Model):
    class VerificationStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        VERIFIED = 'verified', 'Verified'
        REJECTED_SUSPENDED = 'rejected_suspended', 'Rejected / Suspended'

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='employer_profile',
        limit_choices_to={'role': 'employer'},
    )
    company_name = models.CharField(max_length=255)
    business_doc_note = models.TextField(blank=True)
    verification_status = models.CharField(
        max_length=30,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING,
    )
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employer_profiles_reviewed',
        limit_choices_to={'role': 'admin'},
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    def clean(self):
        if self.user.role != User.Role.EMPLOYER:
            raise ValidationError({'user': 'Linked user must have role=employer.'})
        if self.reviewed_by and self.reviewed_by.role != User.Role.ADMIN:
            raise ValidationError({'reviewed_by': 'Reviewer must have role=admin.'})
    
    def __str__(self):
        return self.company_name
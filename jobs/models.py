from django.core.exceptions import ValidationError
from django.db import models

from accounts.models import User


class Job(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        PENDING_REVIEW = 'pending_review', 'Pending Review'
        REVISION_REQUESTED = 'revision_requested', 'Revision Requested'
        LIVE = 'live', 'Live'
        CLOSED_FILLED = 'closed_filled', 'Closed / Filled'

    employer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='jobs',
        limit_choices_to={'role': 'employer'},
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    country = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    salary_min = models.DecimalField(max_digits=12, decimal_places=2)
    salary_max = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=10)
    quota = models.PositiveIntegerField()
    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='jobs_reviewed',
        limit_choices_to={'role': 'admin'},
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    def clean(self):
        if self.employer.role != User.Role.EMPLOYER:
            raise ValidationError({'employer': 'Linked user must have role=employer.'})
        if self.salary_min is not None and self.salary_max is not None:
            if self.salary_min > self.salary_max:
                raise ValidationError({'salary_max': 'salary_max must be greater than or equal to salary_min.'})
        if self.reviewed_by and self.reviewed_by.role != User.Role.ADMIN:
            raise ValidationError({'reviewed_by': 'Reviewer must have role=admin.'})

    def __str__(self):
        return f"{self.title} @ {self.employer}"

class JobQualification(models.Model):
    class Category(models.TextChoices):
        LANGUAGE = 'language', 'Language'
        EDUCATION = 'education', 'Education'
        EXPERIENCE = 'experience', 'Experience'
        AGE = 'age', 'Age'
        CERTIFICATION = 'certification', 'Certification'

    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name='qualifications',
    )
    category = models.CharField(max_length=20, choices=Category.choices)
    label = models.CharField(max_length=255)
    min_value = models.IntegerField()
    min_value_label = models.CharField(max_length=100, blank=True)

    def clean(self):
        if self.min_value is not None and self.min_value < 0:
            raise ValidationError({'min_value': 'min_value cannot be negative.'})

    def __str__(self):
        display = self.min_value_label or self.min_value
        return f"{self.job.title} — {self.label} (min {display})"
from django.core.exceptions import ValidationError
from django.db import models

from accounts.models import User
from jobs.models import Job


class Application(models.Model):
    class Status(models.TextChoices):
        SUBMITTED = 'submitted', 'Submitted'
        REVIEWED = 'reviewed', 'Reviewed'
        ACCEPTED = 'accepted', 'Accepted'
        REJECTED = 'rejected', 'Rejected'

    candidate = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='applications',
        limit_choices_to={'role': 'candidate'},
    )
    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name='applications',
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SUBMITTED,
    )
    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('candidate', 'job')

    def clean(self):
        if self.candidate.role != User.Role.CANDIDATE:
            raise ValidationError({'candidate': 'Linked user must have role=candidate.'})
        if self.job.status != Job.Status.LIVE:
            raise ValidationError({'job': 'Applications can only be submitted for jobs with status=live.'})

    def __str__(self):
        return f"{self.candidate} → {self.job.title} ({self.status})"
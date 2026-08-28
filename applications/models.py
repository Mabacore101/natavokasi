from django.core.exceptions import ValidationError
from django.db import models

from accounts.models import User
from jobs.models import Job, JobQualification

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

class ApplicationAnswer(models.Model):
    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name='answers',
    )
    qualification = models.ForeignKey(
        JobQualification,
        on_delete=models.CASCADE,
    )
    candidate_value = models.IntegerField()
    meets_requirement = models.BooleanField(editable=False)

    class Meta:
        unique_together = ('application', 'qualification')

    def clean(self):
        if self.qualification.job_id != self.application.job_id:
            raise ValidationError({
                'qualification': 'This qualification does not belong to the job being applied for.'
            })

    def save(self, *args, **kwargs):
        if self._state.adding:
            self.meets_requirement = self.candidate_value >= self.qualification.min_value
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.application} — {self.qualification.label}: {self.candidate_value}"
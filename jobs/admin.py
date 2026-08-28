from django.contrib import admin
from django.utils import timezone

from .models import Job, JobQualification


class JobQualificationInline(admin.TabularInline):
    model = JobQualification
    extra = 1


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('title', 'employer', 'country', 'city', 'status', 'quota')
    list_filter = ('status', 'country')
    search_fields = ('title', 'employer__employer_profile__company_name')
    inlines = (JobQualificationInline,)
    actions = ('approve_jobs', 'request_revision')

    @admin.action(description='Approve selected jobs (set live)')
    def approve_jobs(self, request, queryset):
        updated = queryset.update(
            status=Job.Status.LIVE,
            reviewed_by=request.user,
            reviewed_at=timezone.now(),
        )
        self.message_user(request, f"{updated} job(s) approved and set live.")

    @admin.action(description='Request revision on selected jobs')
    def request_revision(self, request, queryset):
        updated = queryset.update(
            status=Job.Status.REVISION_REQUESTED,
            reviewed_by=request.user,
            reviewed_at=timezone.now(),
        )
        self.message_user(request, f"{updated} job(s) marked as revision requested.")
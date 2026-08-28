from django.contrib import admin
from django.utils import timezone

from .models import User, EmployerProfile


@admin.register(EmployerProfile)
class EmployerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'company_name', 'verification_status', 'reviewed_by', 'reviewed_at')
    list_filter = ('verification_status',)
    search_fields = ('company_name', 'user__email', 'user__username')
    actions = ('approve_employers', 'reject_employers')

    @admin.action(description='Approve selected employer accounts')
    def approve_employers(self, request, queryset):
        updated = queryset.update(
            verification_status=EmployerProfile.VerificationStatus.VERIFIED,
            reviewed_by=request.user,
            reviewed_at=timezone.now(),
        )
        self.message_user(request, f"{updated} employer account(s) approved.")

    @admin.action(description='Reject/suspend selected employer accounts')
    def reject_employers(self, request, queryset):
        updated = queryset.update(
            verification_status=EmployerProfile.VerificationStatus.REJECTED_SUSPENDED,
            reviewed_by=request.user,
            reviewed_at=timezone.now(),
        )
        self.message_user(request, f"{updated} employer account(s) rejected/suspended.")
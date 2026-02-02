from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from tenants.models import AbstractTenantModel
from courses.models import Course, SubModule


class Enrollment(AbstractTenantModel):

    class Status(models.TextChoices):
        NOT_STARTED = 'NOT_STARTED', _('Not Started')
        IN_PROGRESS = 'IN_PROGRESS', _('In Progress')
        COMPLETED = 'COMPLETED', _('Completed')

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='enrollments'
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='enrollments'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NOT_STARTED
    )
    enrolled_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_enrollments',
        help_text="Admin who assigned this course (null for self-enrollment)"
    )

    class Meta:
        unique_together = ['user', 'course']
        ordering = ['-enrolled_at']

    def __str__(self):
        return f"{self.user.email} - {self.course.name} ({self.status})"

    @property
    def progress_percentage(self):
        total_submodules = SubModule.objects.filter(
            module__course=self.course
        ).count()
        if total_submodules == 0:
            return 0
        completed = self.submodule_progress.filter(is_completed=True).count()
        return round((completed / total_submodules) * 100, 2)


class SubModuleProgress(AbstractTenantModel):

    enrollment = models.ForeignKey(
        Enrollment,
        on_delete=models.CASCADE,
        related_name='submodule_progress'
    )
    submodule = models.ForeignKey(
        SubModule,
        on_delete=models.CASCADE,
        related_name='user_progress'
    )
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Score for assignment-type submodules (0-100)"
    )
    time_spent = models.DurationField(
        null=True,
        blank=True,
        help_text="Time spent on this submodule"
    )

    class Meta:
        unique_together = ['enrollment', 'submodule']
        ordering = ['submodule__order']

    def __str__(self):
        status = "✓" if self.is_completed else "❌"
        return f"{status} {self.enrollment.user.email} - {self.submodule.title}"

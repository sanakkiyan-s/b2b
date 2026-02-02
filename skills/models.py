from django.db import models
from django.utils.text import slugify
from django.conf import settings
from tenants.models import AbstractTenantModel
from courses.models import Course


class Skill(AbstractTenantModel):
    """
    Tenant-specific skill/competency definition.
    Skills are associated with courses and user proficiency is tracked.
    """
    name = models.CharField(max_length=255)
    slug = models.SlugField(blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        unique_together = ['tenant', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs): 
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class CourseSkill(AbstractTenantModel):
    """
    Many-to-many relationship between courses and skills.
    Weight determines how much completing this course contributes to skill proficiency.
    """
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='course_skills'
    )
    skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        related_name='skill_courses'
    )
    weight = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=1.00,
        help_text="Weight of this course's contribution to skill proficiency (0.00-1.00)"
    )

    class Meta:
        unique_together = ['course', 'skill']
        ordering = ['skill__name']

    def __str__(self):
        return f"{self.course.name} -> {self.skill.name} (weight: {self.weight})"


class UserSkill(AbstractTenantModel):
    """
    Tracks user proficiency for each skill.
    Proficiency is automatically calculated based on completed courses.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='user_skills'
    )
    skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        related_name='user_proficiencies'
    )
    proficiency = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        help_text="Proficiency percentage (0-100)"
    )
    courses_completed = models.PositiveIntegerField(
        default=0,
        help_text="Number of courses completed that contribute to this skill"
    )
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'skill']
        ordering = ['-proficiency']

    def __str__(self):
        return f"{self.user.email} - {self.skill.name}: {self.proficiency}%"

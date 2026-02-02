from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import SubModuleProgress, Enrollment
from courses.models import SubModule
from skills.models import CourseSkill, UserSkill


@receiver(post_save, sender=SubModuleProgress)
def update_enrollment_status(sender, instance, **kwargs):
    """
    When a submodule is marked complete, check if all submodules are done.
    If so, mark the enrollment as COMPLETED and trigger skill updates.
    """
    if not instance.is_completed:
        return

    enrollment = instance.enrollment
    course = enrollment.course

    # Get total submodules in the course
    total_submodules = SubModule.objects.filter(module__course=course).count()
    if total_submodules == 0:
        return

    # Get completed submodules for this enrollment
    completed_count = enrollment.submodule_progress.filter(is_completed=True).count()

    # Update enrollment status
    if completed_count == total_submodules:
        # Course is complete
        if enrollment.status != Enrollment.Status.COMPLETED:
            enrollment.status = Enrollment.Status.COMPLETED
            enrollment.completed_at = timezone.now()
            enrollment.save()
            # Trigger skill proficiency update
            update_user_skills(enrollment)
    elif completed_count > 0:
        # Course is in progress
        if enrollment.status == Enrollment.Status.NOT_STARTED:
            enrollment.status = Enrollment.Status.IN_PROGRESS
            enrollment.save()


def update_user_skills(enrollment):
    """
    Update user skill proficiency when a course is completed.
    Proficiency is calculated based on all completed courses for each skill.
    """
    user = enrollment.user
    course = enrollment.course
    tenant = enrollment.tenant

    # Get all skills associated with this course
    course_skills = CourseSkill.objects.filter(course=course)

    for course_skill in course_skills:
        skill = course_skill.skill
        weight = float(course_skill.weight)

        # Get or create UserSkill record
        user_skill, created = UserSkill.objects.get_or_create(
            user=user,
            skill=skill,
            tenant=tenant,
            defaults={'proficiency': 0, 'courses_completed': 0}
        )

        # no. of completed courses for this skill
        completed_courses_for_skill = Enrollment.objects.filter(
            user=user,
            status=Enrollment.Status.COMPLETED,
            course__course_skills__skill=skill
        ).distinct().count()

        # Get total courses that teach this skill in the tenant
        total_courses_for_skill = CourseSkill.objects.filter(
            skill=skill,
            tenant=tenant
        ).count()

        # Calculate proficiency as weighted percentage
        if total_courses_for_skill > 0:
            completed_weights = sum(
                float(cs.weight) for cs in CourseSkill.objects.filter(
                    skill=skill,
                    tenant=tenant,
                    course__enrollments__user=user,
                    course__enrollments__status=Enrollment.Status.COMPLETED
                ).distinct()
            )
            total_weights = sum(
                float(cs.weight) for cs in CourseSkill.objects.filter(
                    skill=skill,
                    tenant=tenant
                )
            )
            proficiency = (completed_weights / total_weights) * 100 if total_weights > 0 else 0
        else:
            proficiency = 0

        # Update UserSkill
        user_skill.proficiency = min(proficiency, 100)  # Cap at 100%
        user_skill.courses_completed = completed_courses_for_skill
        user_skill.save()

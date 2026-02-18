from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta
from .models import Enrollment, SubModuleProgress
from .serializers import (
    EnrollmentListSerializer,
    EnrollmentDetailSerializer,
    EnrollmentCreateSerializer,
    AdminAssignCourseSerializer,
    SubModuleProgressSerializer,
    MarkCompleteSerializer
)
from accounts.permissions import IsTenantAdmin, RolePermission 
from courses.models import SubModule

class EnrollmentViewSet(viewsets.ModelViewSet):
    """
    - TenantUser: Self-enroll in free courses, view own enrollments
    - TenantAdmin: Assign courses, view all tenant enrollments
    - SuperAdmin: View all enrollments
    """
    queryset = Enrollment.objects.all()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return EnrollmentCreateSerializer
        if self.action == 'retrieve':
            return EnrollmentDetailSerializer
        if self.action == 'assign_course':
            return AdminAssignCourseSerializer
        return EnrollmentListSerializer

    def get_permissions(self):
        if self.action == 'assign_course':
            return [IsTenantAdmin()]
        return [RolePermission()]

    def get_queryset(self):
        return Enrollment.objects.for_current_user().select_related('course','user','assigned_by').prefetch_related('submodule_progress__submodule').annotate(
            completed_submodules=Count('submodule_progress',filter=Q(
                submodule_progress__is_completed=True,
                submodule_progress__tenant=self.request.tenant,
                submodule_progress__user=self.request.user,
               ),distinct=True),
            total_submodules=Count('course__modules__submodules',filter=Q(
                course__tenant=self.request.tenant,
                ),distinct=True)

        ).annotate(
            progress_percentage=Case(
                When(total_submodules=0, then=Value(0.0)),
                default=Cast(F('completed_submodules'), FloatField()) / Cast(F('total_submodules'), FloatField()) * 100,
                output_field=FloatField()
            )
        )

    @action(detail=False, methods=['post'])
    def assign_course(self, request):
        """
        Admin action to assign a course to a user.
        Bypasses payment for paid courses.
        """
        serializer = AdminAssignCourseSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        course = serializer.validated_data['course']
        if course.status == "ARCHIVED":
            return Response(
                {'error': 'Course is archived'},
                status=status.HTTP_400_BAD_REQUEST
            )
        enrollment = Enrollment.objects.create(
            tenant=request.user.tenant,
            user=user,
            course=course,
            assigned_by=request.user
        )

        return Response(
            EnrollmentListSerializer(enrollment).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['get'])
    def progress(self, request, pk=None):
        enrollment = self.get_object()
        serializer = EnrollmentDetailSerializer(enrollment)
        return Response(serializer.data)


class SubModuleProgressViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for tracking submodule progress.
    - TenantUser: View and update own progress
    - TenantAdmin: View all progress in tenant
    """
    queryset = SubModuleProgress.objects.all()
    serializer_class = SubModuleProgressSerializer

    def get_permissions(self):
        return [RolePermission()]

    def get_queryset(self):
        return SubModuleProgress.objects.for_current_user()

    @action(detail=False, methods=['post'], url_path='mark-complete')
    def mark_complete(self, request):
        """
        Mark a submodule as complete for the current user's enrollment.
        """
        enrollment_id = request.data.get('enrollment_id')
        submodule_id = request.data.get('submodule_id')

        if not enrollment_id or not submodule_id:
            return Response(
                {'error': 'enrollment_id and submodule_id are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate enrollment belongs to user
        try:
            enrollment = Enrollment.objects.get(id=enrollment_id)
        except Enrollment.DoesNotExist:
            return Response(
                {'error': 'Enrollment not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check permission
        user = request.user
        if user.role_name == 'TENANT_USER' and enrollment.user != user:
            return Response(
                {'error': 'You can only update your own progress'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Validate submodule belongs to the course
        try:
            submodule = SubModule.objects.get(id=submodule_id, module__course=enrollment.course)
        except SubModule.DoesNotExist:
            return Response(
                {'error': 'Submodule not found or does not belong to this course'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Parse optional data
        mark_serializer = MarkCompleteSerializer(data=request.data)
        mark_serializer.is_valid(raise_exception=True)
        score = mark_serializer.validated_data.get('score')
        time_spent_seconds = mark_serializer.validated_data.get('time_spent_seconds')

        # Create or update progress
        progress, created = SubModuleProgress.objects.get_or_create(
            enrollment=enrollment,
            submodule=submodule,
            tenant=enrollment.tenant,
            defaults={
                'is_completed': True,
                'completed_at': timezone.now(),
                'score': score if submodule.type == 'assignment' else None,
                'time_spent': timedelta(seconds=time_spent_seconds) if submodule.type == 'assignment' else None
            }
        )

        if not created and not progress.is_completed:
            progress.is_completed = True
            progress.completed_at = timezone.now()
            if score is not None:
                progress.score = score
            if time_spent_seconds is not None:
                progress.time_spent = timedelta(seconds=time_spent_seconds)
            progress.save()

        return Response(SubModuleProgressSerializer(progress).data)

from django.db import migrations


def seed_role_permissions(apps, schema_editor):
    """
    Assign default permissions to the 3 built-in roles.
    
    SUPER_ADMIN  → bypasses checks in code (no DB perms needed, but we
                   assign all for visibility in the admin panel)
    TENANT_ADMIN → all CRUD on courses, modules, submodules, catalogues,
                   users within their tenant, enrollments, skills, payments
    TENANT_USER  → view courses, modules, submodules, catalogues, enroll
    """
    Role = apps.get_model('accounts', 'Role')
    Permission = apps.get_model('auth', 'Permission')

    # --- SUPER_ADMIN: all permissions ---
    try:
        super_admin = Role.objects.get(name='SUPER_ADMIN')
        all_perms = Permission.objects.all()
        super_admin.permissions.set(all_perms)
    except Role.DoesNotExist:
        pass

    # --- TENANT_ADMIN: manage everything within tenant scope ---
    tenant_admin_codenames = [
        # Users
        'add_user', 'change_user', 'delete_user', 'view_user',
        # Courses
        'add_course', 'change_course', 'delete_course', 'view_course',
        # Modules
        'add_module', 'change_module', 'delete_module', 'view_module',
        # Submodules
        'add_submodule', 'change_submodule', 'delete_submodule', 'view_submodule',
        # Catalogues
        'add_catalogue', 'change_catalogue', 'delete_catalogue', 'view_catalogue',
        # Enrollments
        'add_enrollment', 'change_enrollment', 'delete_enrollment', 'view_enrollment',
        'view_submoduleprogress', 'change_submoduleprogress',
        # Skills
        'add_skill', 'change_skill', 'delete_skill', 'view_skill',
        'add_courseskill', 'change_courseskill', 'delete_courseskill', 'view_courseskill',
        'view_userskill',
        # Payments
        'view_payment',
        # Roles
        'view_role',
        # Audit Logs
        'view_auditlog',
    ]
    try:
        tenant_admin = Role.objects.get(name='TENANT_ADMIN')
        perms = Permission.objects.filter(codename__in=tenant_admin_codenames)
        tenant_admin.permissions.set(perms)
    except Role.DoesNotExist:
        pass

    # --- TENANT_USER: read-only + enroll ---
    tenant_user_codenames = [
        # Courses (view only)
        'view_course', 'view_module', 'view_submodule',
        # Catalogues (view only)
        'view_catalogue',
        # Enrollments (can enroll and view)
        'add_enrollment', 'view_enrollment',
        'view_submoduleprogress', 'change_submoduleprogress',
        # Skills (view own)
        'view_userskill', 'view_skill',
        # Payments (view own)
        'view_payment',
        # Users (view own profile)
        'view_user',
    ]
    try:
        tenant_user = Role.objects.get(name='TENANT_USER')
        perms = Permission.objects.filter(codename__in=tenant_user_codenames)
        tenant_user.permissions.set(perms)
    except Role.DoesNotExist:
        pass


def reverse_seed(apps, schema_editor):
    """Clear all role permissions."""
    Role = apps.get_model('accounts', 'Role')
    for role in Role.objects.all():
        role.permissions.clear()


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0006_role_permissions'),
    ]

    operations = [
        migrations.RunPython(seed_role_permissions, reverse_seed),
    ]

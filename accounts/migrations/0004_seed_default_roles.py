from django.db import migrations


def seed_roles_and_migrate_data(apps, schema_editor):
    """Create default roles and migrate existing user role strings to FK references."""
    Role = apps.get_model('accounts', 'Role')
    User = apps.get_model('accounts', 'User')

    # Create the 3 default roles
    super_admin, _ = Role.objects.get_or_create(name='SUPER_ADMIN', defaults={'description': 'Super Admin — full platform access'})
    tenant_admin, _ = Role.objects.get_or_create(name='TENANT_ADMIN', defaults={'description': 'Tenant Admin — manages a single tenant'})
    tenant_user, _ = Role.objects.get_or_create(name='TENANT_USER', defaults={'description': 'Tenant User — standard user within a tenant'})

    role_map = {
        'SUPER_ADMIN': super_admin,
        'TENANT_ADMIN': tenant_admin,
        'TENANT_USER': tenant_user,
    }

    # Migrate existing users: copy old role string -> new FK
    for user in User.objects.all():
        old_role = user.role  # This is still the old CharField value
        if old_role in role_map:
            user.role_fk = role_map[old_role]
            user.save(update_fields=['role_fk'])


def reverse_migration(apps, schema_editor):
    """Reverse: copy FK name back to old CharField."""
    User = apps.get_model('accounts', 'User')
    for user in User.objects.select_related('role_fk').all():
        if user.role_fk:
            user.role = user.role_fk.name
            user.save(update_fields=['role'])


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_role_alter_user_role'),
    ]

    operations = [
        migrations.RunPython(seed_roles_and_migrate_data, reverse_migration),
    ]

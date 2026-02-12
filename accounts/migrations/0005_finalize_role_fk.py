import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_seed_default_roles'),
    ]

    operations = [
        # Step 1: Remove the old CharField `role`
        migrations.RemoveField(
            model_name='user',
            name='role',
        ),
        # Step 2: Rename `role_fk` -> `role`
        migrations.RenameField(
            model_name='user',
            old_name='role_fk',
            new_name='role',
        ),
        # Step 3: Update field to match the final model definition
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='users',
                to='accounts.role',
            ),
        ),
    ]

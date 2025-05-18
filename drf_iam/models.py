from django.db import models
from django.conf import settings
from django.apps import apps
from django.core.exceptions import ImproperlyConfigured

"""
Provides the database models for drf-iam.

This module defines:
- `AbstractRole`: An abstract base class for role models. If you want to use a
  custom role model, it should inherit from this class.
- `Role`: The default concrete role model. The `drf_iam_role` table for this
  model will always be created.
- `Policy`: Represents a permission (an action on a resource type).
- `RolePolicy`: The through model for the many-to-many relationship between
  roles and policies.
- `get_role_model()`: A utility function to retrieve the active Role model.

Configurable Role Model:
------------------------
This application uses `drf_iam.Role` as the default model for roles.
To use a custom Role model:

1. Define your custom Role model, inheriting from `drf_iam.models.AbstractRole`.
   For example, in `your_app/models.py`:

   ```python
   from django.db import models
   from drf_iam.models import AbstractRole # Note: Policy & RolePolicy not needed here for definition

   class CustomRole(AbstractRole):
       # Your custom fields
       department = models.CharField(max_length=100, blank=True)

       # The 'policies' ManyToManyField is inherited from AbstractRole.
       # You do not need to redefine it unless you want to change its parameters.
       # If you need to use the reverse relation from the Policy model, the
       # related_name will be dynamically generated, e.g., for this CustomRole model
       # in 'your_app', it would be 'your_app_customrole_policies'.

       class Meta(AbstractRole.Meta): # Inherit base meta options
           verbose_name = "Custom Role"
           verbose_name_plural = "Custom Roles"
           # Add other Meta options as needed, e.g., db_table if you want to rename

       def __str__(self):
           return self.name
   ```

2. In your Django project's `settings.py`, set `DRF_IAM_ROLE_MODEL` to point
   to your custom model:
   ```python
   DRF_IAM_ROLE_MODEL = 'your_app.CustomRole'
   ```
   If you do not set `DRF_IAM_ROLE_MODEL` in your project's settings, the system
   will default to using `'drf_iam.Role'`.

   If `DRF_IAM_ROLE_MODEL` is set but points to an invalid or uninstalled model,
   an `ImproperlyConfigured` error will be raised when `get_role_model()` is called
   or when the `RolePolicy` model (which uses this setting) is loaded.

3. Ensure `your_app` (containing `CustomRole`) and `drf_iam` are in your
   `INSTALLED_APPS`.

The `RolePolicy` model and any internal `drf-iam` logic (via `get_role_model()`)
that needs to refer to the Role model will use the model specified by
`DRF_IAM_ROLE_MODEL` (or its default 'drf_iam.Role').
"""


class AbstractRole(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    # Moved policies M2M here from the concrete Role model
    policies = models.ManyToManyField(
        'Policy',
        through='RolePolicy',
        blank=True,
        # Dynamic related_name and related_query_name for abstract model M2M
        related_name="%(app_label)s_%(class)s_policies",
        related_query_name="%(app_label)s_%(class)s_policy",
        db_index=True
    )

    class Meta:
        abstract = True
        ordering = ['name']
        verbose_name_plural = 'Roles'
        verbose_name = 'Role'


class Role(AbstractRole):
    # 'policies' field is now inherited from AbstractRole

    class Meta(AbstractRole.Meta):
        pass # No longer swappable in the Django Meta sense

    def __str__(self):
        return self.name


class Policy(models.Model):
    policy_name = models.CharField(max_length=255, blank=True, null=True)
    action = models.CharField(max_length=100)
    resource_type = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.action} on {self.resource_type}"

    class Meta:
        unique_together = ('action', 'resource_type')
        ordering = ['action', 'resource_type']
        verbose_name_plural = 'policies'
        verbose_name = 'policy'


class RolePolicy(models.Model):
    # Determine the Role model string, defaulting if not set
    _role_model_name = getattr(settings, 'DRF_IAM_ROLE_MODEL', 'drf_iam.Role')

    role = models.ForeignKey(_role_model_name, on_delete=models.CASCADE, db_index=True)
    policy = models.ForeignKey(Policy, on_delete=models.CASCADE, db_index=True)

    class Meta:
        unique_together = ('role', 'policy')
        ordering = ['role', 'policy']
        verbose_name_plural = 'role policies'
        verbose_name = 'role policy'

    def __str__(self):
        return f"{self.role.name} - {self.policy}"


def get_role_model():
    """
    Return the Role model that is active in this project.

    It uses the model specified by the DRF_IAM_ROLE_MODEL setting.
    If DRF_IAM_ROLE_MODEL is not set, it defaults to 'drf_iam.Role'.

    Raises ImproperlyConfigured if DRF_IAM_ROLE_MODEL is set but
    points to an invalid or uninstalled model.
    """
    try:
        model_string = settings.DRF_IAM_ROLE_MODEL
    except AttributeError:
        # If the setting is not defined, default to 'drf_iam.Role'
        model_string = 'drf_iam.Role'

    try:
        return apps.get_model(model_string, require_ready=False)
    except ValueError:
        raise ImproperlyConfigured(
            f"DRF_IAM_ROLE_MODEL must be of the form 'app_label.model_name', "
            f"but got '{model_string}'."
        )
    except LookupError:
        raise ImproperlyConfigured(
            f"DRF_IAM_ROLE_MODEL refers to model '{model_string}' "
            f"that has not been installed."
        )

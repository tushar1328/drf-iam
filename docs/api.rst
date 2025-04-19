API Reference
=============

This document provides detailed API reference for DRF-IAM.

Core Components
-------------

Models
~~~~~~

Role
^^^^

.. code-block:: python

    class Role(models.Model):
        name = models.CharField(max_length=100, unique=True)
        description = models.TextField(blank=True)
        created_at = models.DateTimeField(auto_now_add=True)
        updated_at = models.DateTimeField(auto_now=True)

Permission
^^^^^^^^^

.. code-block:: python

    class Permission(models.Model):
        role = models.ForeignKey(Role, on_delete=models.CASCADE)
        policy_name = models.CharField(max_length=100)
        can_create = models.BooleanField(default=False)
        can_read = models.BooleanField(default=False)
        can_update = models.BooleanField(default=False)
        can_delete = models.BooleanField(default=False)

Permissions
----------

IAMPermission
~~~~~~~~~~~~

.. code-block:: python

    class IAMPermission(BasePermission):
        """
        Permission class for Role-Based Access Control.
        """
        def has_permission(self, request, view):
            # Check if user has required permission based on their role
            pass

Settings
-------

Available settings with their default values:

.. code-block:: python

    DRF_IAM = {
        'DEFAULT_POLICY_NAME': 'resource',
        'CASE_SENSITIVE_POLICIES': False,
        'STRICT_MODE': True,
    }

Utilities
--------

Helper functions and utilities provided by DRF-IAM:

.. code-block:: python

    from drf_iam.utils import get_user_permissions

    # Get all permissions for a user
    permissions = get_user_permissions(user)

    # Check specific permission
    has_permission = get_user_permissions(user, policy_name="articles", action="read")

Exceptions
---------

Custom exceptions raised by DRF-IAM:

.. code-block:: python

    class PolicyNotFoundError(Exception):
        """Raised when a policy is not found and STRICT_MODE is True."""
        pass

    class InvalidRoleError(Exception):
        """Raised when an invalid role is assigned to a user."""
        pass

Signals
------

Available signals for tracking permission changes:

.. code-block:: python

    from drf_iam.signals import permission_changed

    @receiver(permission_changed)
    def handle_permission_change(sender, instance, **kwargs):
        # Handle permission change event
        pass

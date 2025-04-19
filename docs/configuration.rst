Configuration
=============

DRF-IAM provides several configuration options to customize its behavior according to your needs.

Settings
--------

You can configure DRF-IAM by adding settings to your Django settings file:

.. code-block:: python

    DRF_IAM = {
        'DEFAULT_POLICY_NAME': 'resource',  # Default policy name if not specified
        'CASE_SENSITIVE_POLICIES': False,   # Whether policy names are case sensitive
        'STRICT_MODE': True,               # Raise error if policy not found
    }

Policy Names
-----------

Policy names can be configured in two ways:

1. Using the ``iam_policy_name`` attribute in viewsets:

.. code-block:: python

    class UserViewSet(viewsets.ModelViewSet):
        permission_classes = [IAMPermission]
        iam_policy_name = "users"

2. Using the default policy name from settings:

.. code-block:: python

    # If no iam_policy_name is specified, uses DEFAULT_POLICY_NAME
    class ResourceViewSet(viewsets.ModelViewSet):
        permission_classes = [IAMPermission]

Role Configuration
----------------

Roles can be configured with different permission levels:

.. code-block:: python

    from drf_iam.models import Role, Permission

    # Create role with full access
    admin = Role.objects.create(name="admin")
    Permission.objects.create(
        role=admin,
        policy_name="*",  # Wildcard for all policies
        can_create=True,
        can_read=True,
        can_update=True,
        can_delete=True
    )

    # Create role with limited access
    viewer = Role.objects.create(name="viewer")
    Permission.objects.create(
        role=viewer,
        policy_name="users",
        can_read=True,  # Only read access
        can_create=False,
        can_update=False,
        can_delete=False
    )

Advanced Configuration
-------------------

For more advanced use cases, you can:

* Create custom permission classes
* Implement policy inheritance
* Define role hierarchies

These topics are covered in detail in the :doc:`api` documentation.

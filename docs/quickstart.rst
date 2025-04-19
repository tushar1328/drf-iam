Quick Start Guide
===============

This guide will help you get started with DRF-IAM quickly. We'll cover the basics of setting up permissions and roles in your Django REST Framework project.

Basic Usage
----------

1. Set up permissions in your viewsets:

.. code-block:: python

    from rest_framework import viewsets
    from drf_iam.permissions import IAMPermission

    class UserViewSet(viewsets.ModelViewSet):
        permission_classes = [IAMPermission]
        iam_policy_name = "users"  # Optional: Custom policy name for this viewset

2. Create roles and permissions:

.. code-block:: python

    from drf_iam.models import Role, Permission

    # Create a role
    admin_role = Role.objects.create(name="admin")

    # Create permissions
    Permission.objects.create(
        role=admin_role,
        policy_name="users",  # Matches the iam_policy_name in viewset
        can_create=True,
        can_read=True,
        can_update=True,
        can_delete=True
    )

3. Assign role to a user:

.. code-block:: python

    user.role = admin_role
    user.save()

Custom Policy Names
-----------------

You can customize the policy name for each viewset:

.. code-block:: python

    class ProductViewSet(viewsets.ModelViewSet):
        permission_classes = [IAMPermission]
        iam_policy_name = "products"  # Custom policy name

    class OrderViewSet(viewsets.ModelViewSet):
        permission_classes = [IAMPermission]
        iam_policy_name = "orders"  # Different policy name

This allows you to:

* Group similar resources under the same policy
* Have different permissions for different resource types
* Organize permissions logically by resource

Next Steps
---------

* Learn about advanced :doc:`configuration` options
* Check the :doc:`api` reference for detailed information
* Read about best practices in the :doc:`usage` guide

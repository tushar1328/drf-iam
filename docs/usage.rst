Usage
=====

Using in Views
------------

.. code-block:: python

    from rest_framework import viewsets
    from drf_iam.permissions import IAMPermission

    class UserViewSet(viewsets.ModelViewSet):
        permission_classes = [IAMPermission]
        iam_policy_name = "users"  # Optional: Custom policy name for this viewset

Each viewset can have a custom name by configuring ``iam_policy_name`` (Optional).

Project Configuration
------------------

1. Add ``drf_iam`` to your ``INSTALLED_APPS`` in ``settings.py``:

.. code-block:: python

    INSTALLED_APPS = [
        ...
        'drf_iam',
    ]

2. Add the Role relationship to your User model:

.. code-block:: python

    from django.contrib.auth.models import AbstractUser
    from drf_iam.models import Role

    class User(AbstractUser):
        role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True)

3. Run migrations:

.. code-block:: bash

    python manage.py makemigrations
    python manage.py migrate

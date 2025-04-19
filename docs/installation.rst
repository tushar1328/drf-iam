Installation
============

Quick Installation
----------------

.. code-block:: bash

    pip install drf-iam

Project Configuration
-------------------

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

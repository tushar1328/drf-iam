Installation
============

Requirements
-----------

* Python >= 3.6
* Django >= 3.2
* Django REST Framework >= 3.12

Quick Installation
----------------

You can install DRF-IAM using pip:

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

3. Run migrations:

.. code-block:: bash

    python manage.py makemigrations
    python manage.py migrate

Next Steps
---------

After installation, you might want to:

* Check out the :doc:`quickstart` guide for basic usage
* Learn about :doc:`configuration` options
* Read the :doc:`api` documentation for detailed reference

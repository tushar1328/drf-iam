# DRF-IAM (Django REST Framework - Identity and Access Management)

[![PyPI version](https://badge.fury.io/py/drf-iam.svg)](https://badge.fury.io/py/drf-iam)
[![Documentation Status](https://readthedocs.org/projects/drf-iam/badge/?version=latest)](https://drf-iam.readthedocs.io/en/latest/?badge=latest)

A powerful Django application that provides Role-Based Access Control (RBAC) for Django REST Framework applications. Easily manage permissions and roles across your API endpoints.

## Features

- 🔒 Role-Based Access Control (RBAC)
- 🎯 Custom policy names for viewsets
- 🔄 Seamless integration with Django's User model
- ⚡ Easy to set up and configure
- 📚 Comprehensive documentation

## Installation

```bash
pip install drf-iam
```

## Quick Start

1. Add `drf_iam` to your `INSTALLED_APPS` in `settings.py`:

```python
INSTALLED_APPS = [
    ...
    'drf_iam',
]
```

2. Add the Role relationship to your User model:

```python
from django.contrib.auth.models import AbstractUser
from drf_iam.models import Role

class User(AbstractUser):
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True)
```

3. Run migrations:

```bash
python manage.py makemigrations
python manage.py migrate
```

4. Use in your viewsets:

```python
from rest_framework import viewsets
from drf_iam.permissions import IAMPermission

class UserViewSet(viewsets.ModelViewSet):
    permission_classes = [IAMPermission]
    iam_policy_name = "users"  # Optional: Custom policy name for this viewset
```

## Documentation

For detailed documentation, visit [https://drf-iam.readthedocs.io/](https://drf-iam.readthedocs.io/)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
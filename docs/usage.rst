Usage
=====

Quick Start
----------

1. Add "drf_iam" to your INSTALLED_APPS setting:

.. code-block:: python

    INSTALLED_APPS = [
        ...
        'drf_iam',
    ]

2. Include the DRF-IAM URLconf in your project urls.py:

.. code-block:: python

    path('iam/', include('drf_iam.urls')),

3. Configure your settings:

.. code-block:: python

    DRF_IAM = {
        # Your configuration here
    }

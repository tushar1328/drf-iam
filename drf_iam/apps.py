import logging

from django.apps import AppConfig
from django.db.models.signals import post_migrate

logger = logging.getLogger(__name__)

class DrfIamConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "drf_iam"

    def ready(self):
        if not hasattr(self, 'already_loaded'):
            from drf_iam.utils.load_viewset_permissions import load_permissions_from_urls
            post_migrate.connect(
                load_permissions_from_urls,
                dispatch_uid="drf_iam.utils.load_permissions_from_urls",
            )
            self.already_loaded = True
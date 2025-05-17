"""Configuration for the drf_iam Django app."""

import logging

from django.apps import AppConfig
from django.conf import settings
from django.db.models.signals import post_migrate
from typing import Any

# Attempt to use the colorful logger setup, fallback to standard logger
try:
    from drf_iam.utils.logging_utils import setup_colorful_logger
    logger = setup_colorful_logger(__name__)
except ImportError:
    logger = logging.getLogger(__name__)
    # Basic configuration if colorful logger isn't available or during early app loading
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO) # Default level


class DrfIamConfig(AppConfig):
    """Django AppConfig for drf_iam."""
    default_auto_field = "django.db.models.BigAutoField"
    name = "drf_iam"
    verbose_name = "DRF IAM"

    _already_run_ready = False # Class attribute to track if ready() logic has run

    def ready(self) -> None:
        """Performs initialization tasks when the app is ready.

        Connects the permission loading utility to the post_migrate signal
        if DRF_IAM_AUTO_LOAD_PERMISSIONS setting is True.
        Ensures this setup runs only once.
        """
        if DrfIamConfig._already_run_ready:
            return

        # Check Django settings for whether to auto-load permissions
        auto_load_enabled = getattr(settings, 'DRF_IAM_AUTO_LOAD_PERMISSIONS', True)

        if auto_load_enabled:
            from drf_iam.utils.load_viewset_permissions import load_permissions_from_urls

            def _robust_load_permissions(sender: AppConfig, **kwargs: Any) -> None:
                """Signal receiver to load permissions, with error handling."""
                try:
                    logger.info("🚀 Attempting to load/synchronize DRF-IAM permissions post-migrate...")
                    load_permissions_from_urls()
                    logger.info("🎉 Successfully loaded/synchronized DRF-IAM permissions.")
                except Exception as e:
                    logger.error(
                        f"❌ Error during DRF-IAM permission loading post-migrate: {e}",
                        exc_info=True
                    )
                    # Decide if you want to re-raise. For post_migrate, often it's better
                    # to log and continue, rather than breaking the migration process.

            post_migrate.connect(
                _robust_load_permissions,
                sender=self, # Connect to migrations for this app only
                dispatch_uid="drf_iam.utils._robust_load_permissions",
            )
            logger.info(
                f"{self.verbose_name}: 🔌 Permission auto-loading signal connected (DRF_IAM_AUTO_LOAD_PERMISSIONS=True)."
            )
        else:
            logger.info(
                f"{self.verbose_name}: 🚫 Permission auto-loading disabled via DRF_IAM_AUTO_LOAD_PERMISSIONS setting."
            )
        
        DrfIamConfig._already_run_ready = True
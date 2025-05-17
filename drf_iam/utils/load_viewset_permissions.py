import inspect
import logging
from dataclasses import dataclass
from typing import List, Dict, Any, Set, Tuple, Iterator, Type, Optional

from django.conf import settings
from django.urls import get_resolver, URLPattern, URLResolver
from rest_framework.viewsets import ViewSetMixin

from drf_iam.models import Policy
from .logging_utils import setup_colorful_logger

logger = setup_colorful_logger("drf_iam.permissions", level=logging.INFO)


@dataclass
class PolicyDetail:
    """Represents the details of a policy to be created or updated."""
    action: str
    resource_type: str
    policy_name: str
    description: str
    id: Optional[int] = None  # For existing policies that might be updated

    def __hash__(self):
        return hash((self.action, self.resource_type))

    def __eq__(self, other):
        if not isinstance(other, PolicyDetail):
            return NotImplemented
        return (self.action, self.resource_type) == (other.action, other.resource_type)


def is_viewset(cls: Any) -> bool:
    """Checks if the given class is a DRF ViewSet."""
    return isinstance(cls, type) and issubclass(cls, ViewSetMixin)


def get_viewset_actions(viewset_cls: Type[ViewSetMixin]) -> Set[str]:
    """Extracts all actions (default and custom) from a ViewSet class.
    
    Checks Django settings for 'DRF_IAM_DEFAULT_VIEWSET_ACTIONS'.
    """
    actions: Set[str] = set()
    
    fallback_default_actions = {
        'list', 'retrieve', 'create', 'update', 'partial_update', 'destroy'
    }
    default_actions = getattr(settings, 'DRF_IAM_DEFAULT_VIEWSET_ACTIONS', fallback_default_actions)

    for action_name in default_actions:
        if hasattr(viewset_cls, action_name):
            actions.add(action_name)
    for name, method in inspect.getmembers(viewset_cls, predicate=inspect.isfunction):
        if hasattr(method, 'mapping'):
            actions.add(name)
    return actions


class PermissionLoader:
    """Handles the synchronization of permissions from URL patterns to the database."""

    def __init__(self):
        self.urlpatterns: List[Any] = get_resolver().url_patterns
        self.desired_policies: List[PolicyDetail] = []
        self.current_db_policies: List[PolicyDetail] = []

    def _extract_viewsets_from_urlpatterns(
            self,
            urlpatterns: List[Any],
            prefix: str = ''
    ) -> Iterator[Dict[str, Any]]:
        """Recursively extracts ViewSet details from Django URL patterns."""
        for pattern in urlpatterns:
            if isinstance(pattern, URLResolver):
                yield from self._extract_viewsets_from_urlpatterns(
                    pattern.url_patterns, prefix + str(pattern.pattern)
                )
            elif isinstance(pattern, URLPattern):
                callback = pattern.callback
                viewset_class = getattr(callback, 'cls', None)
                if is_viewset(viewset_class):
                    yield {
                        'prefix': prefix,
                        'pattern': pattern.pattern,
                        'viewset': viewset_class,
                        'callback': callback,
                    }

    def _generate_policy_details_from_viewsets(self) -> None:
        """Generates a list of desired PolicyDetail objects from URL patterns."""
        raw_policy_details: List[Dict[str, Any]] = []
        for entry in self._extract_viewsets_from_urlpatterns(self.urlpatterns):
            viewset_cls: Type[ViewSetMixin] = entry['viewset']
            basename = getattr(viewset_cls, "iam_policy_name", None) or \
                       viewset_cls.__name__.lower().replace('viewset', '')

            exclude_from_permissions = getattr(viewset_cls, "drf_iam_exclude_from_permissions", False)
            if exclude_from_permissions:
                continue

            actions = get_viewset_actions(viewset_cls)

            for action_name in actions:
                action_method = getattr(viewset_cls, action_name, None)
                policy_name_override = action_name
                description = f"Permission for {action_name} on {basename}"

                if action_method:
                    if getattr(action_method, 'exclude_from_iam', False):
                        continue
                    policy_name_override = getattr(action_method, 'policy_name', policy_name_override)
                    description = getattr(action_method, 'policy_description', description)

                raw_policy_details.append({
                    'action': f"{basename}:{action_name}",
                    'resource_type': basename,
                    'policy_name': policy_name_override,
                    'description': description
                })

        seen_policies: Set[Tuple[str, str]] = set()
        unique_policy_details: List[PolicyDetail] = []
        for detail_dict in raw_policy_details:
            key = (detail_dict['action'], detail_dict['resource_type'])
            if key not in seen_policies:
                seen_policies.add(key)
                unique_policy_details.append(
                    PolicyDetail(
                        action=detail_dict['action'],
                        resource_type=detail_dict['resource_type'],
                        policy_name=detail_dict['policy_name'],
                        description=detail_dict['description'],
                    )
                )
        self.desired_policies = unique_policy_details

    def _get_current_policies_from_db(self) -> None:
        """Fetches all current policies from the database."""
        self.current_db_policies = [
            PolicyDetail(
                id=p.id,
                action=p.action,
                resource_type=p.resource_type,
                policy_name=p.policy_name,
                description=p.description,
            )
            for p in Policy.objects.all()
        ]

    def _calculate_policy_changes(
            self
    ) -> Tuple[List[PolicyDetail], List[PolicyDetail], List[PolicyDetail]]:
        """Compares desired and current policies to determine changes."""
        desired_set = set(self.desired_policies)
        current_set = set(self.current_db_policies)

        to_create = list(desired_set - current_set)

        policies_to_delete_with_id: List[PolicyDetail] = []
        current_map_for_delete = {(p.action, p.resource_type): p.id for p in self.current_db_policies if p.id is not None}
        policies_to_delete_stubs = current_set - desired_set
        for policy_stub in policies_to_delete_stubs:
            policy_id = current_map_for_delete.get((policy_stub.action, policy_stub.resource_type))
            if policy_id is not None:
                policies_to_delete_with_id.append(
                    PolicyDetail(action=policy_stub.action, resource_type=policy_stub.resource_type, policy_name='',
                                 description='', id=policy_id))

        to_update: List[PolicyDetail] = []
        current_map_for_update = {(p.action, p.resource_type): p for p in self.current_db_policies}

        for desired_policy in desired_set & current_set:
            current_policy_match = current_map_for_update.get((desired_policy.action, desired_policy.resource_type))
            if current_policy_match and (
                    current_policy_match.policy_name != desired_policy.policy_name or \
                    current_policy_match.description != desired_policy.description
            ):
                to_update.append(PolicyDetail(
                    id=current_policy_match.id,
                    action=desired_policy.action,
                    resource_type=desired_policy.resource_type,
                    policy_name=desired_policy.policy_name,
                    description=desired_policy.description
                ))
        return to_create, policies_to_delete_with_id, to_update

    def _apply_policy_changes(
            self,
            policies_to_create: List[PolicyDetail],
            policies_to_delete: List[PolicyDetail],
            policies_to_update: List[PolicyDetail],
    ) -> None:
        """Applies the calculated policy changes to the database."""
        if policies_to_delete:
            delete_ids = [p.id for p in policies_to_delete if p.id is not None]
            if delete_ids:
                Policy.objects.filter(id__in=delete_ids).delete()
                logger.info(f"🗑️  Deleted {len(delete_ids)} policies.")

        if policies_to_create:
            Policy.objects.bulk_create([
                Policy(
                    action=p.action,
                    resource_type=p.resource_type,
                    policy_name=p.policy_name,
                    description=p.description
                ) for p in policies_to_create
            ])
            logger.info(f"✨ Created {len(policies_to_create)} new policies.")

        if policies_to_update:
            update_batch = []
            for p_update in policies_to_update:
                if p_update.id is not None:
                    policy_obj = Policy(
                        id=p_update.id,
                        action=p_update.action,
                        resource_type=p_update.resource_type,
                        policy_name=p_update.policy_name,
                        description=p_update.description
                    )
                    update_batch.append(policy_obj)

            if update_batch:
                Policy.objects.bulk_update(update_batch, fields=['policy_name', 'description'])
                logger.info(f"🔄 Updated {len(update_batch)} policies.")

    def sync_permissions(self) -> None:
        """Main method to synchronize permissions."""
        logger.info("🚀 Starting permission synchronization...")

        self._generate_policy_details_from_viewsets()
        logger.info(f"🔍 Discovered {len(self.desired_policies)} desired policies from URL patterns.")

        self._get_current_policies_from_db()
        logger.info(f"💾 Found {len(self.current_db_policies)} existing policies in the database.")

        to_create, to_delete, to_update = self._calculate_policy_changes()
        logger.info(f"➕ Policies to create: {len(to_create)}")
        logger.info(f"➖ Policies to delete: {len(to_delete)}")
        logger.info(f"🔧 Policies to update: {len(to_update)}")

        self._apply_policy_changes(to_create, to_delete, to_update)
        logger.info("🎉 Successfully finished permission synchronization.")


def load_permissions_from_urls(**kwargs: Any) -> None:
    """Loads permissions from URL patterns and synchronizes them with the database.
       This function instantiates and uses the PermissionLoader class.
    """
    loader = PermissionLoader()
    loader.sync_permissions()

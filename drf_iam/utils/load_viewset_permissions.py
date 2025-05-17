import inspect
import logging
from dataclasses import dataclass
from typing import List, Dict, Any, Set, Tuple, Iterator, Type, Optional

from django.conf import settings
from django.urls import get_resolver, URLPattern, URLResolver
from rest_framework.views import APIView
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
    return isinstance(cls, type) and (issubclass(cls, ViewSetMixin))


def is_api_view(cls: Any) -> bool:
    """Checks if the given class is a DRF APIView."""
    return isinstance(cls, type) and issubclass(cls, APIView)


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
                if (is_viewset(viewset_class) or is_api_view(viewset_class)) and getattr(viewset_class,"drf_iam_enabled", True):
                    yield {
                        'prefix': prefix,
                        'pattern': pattern.pattern,
                        'viewset': viewset_class,
                        'callback': callback,
                        'name': pattern.name
                    }

    def _validate_conflicting_definitions(
            self,
            action_method: Any,
            action_name: str,
            iam_perms_for_action: Dict[str, Any]
    ) -> None:
        """
        Validates that IAM-related attributes are not defined in conflicting ways
        (e.g., both in drf_iam_permissions dict and as a direct method attribute).

        Raises:
            Exception: If any attribute is defined in both locations.
        """
        conflicts: List[str] = []
        error_message_template = (
            "Attribute '{}' for action '{}' on ViewSet '{}' cannot be defined in both "
            "'drf_iam_permissions' dictionary and as a direct method attribute (e.g., via decorator). "
            "Please choose a single source of truth."
        )

        viewset_name = action_method.__self__.__class__.__name__ if hasattr(action_method,
                                                                            '__self__') else 'UnknownViewSet'

        # Check for 'policy_name'
        if iam_perms_for_action.get("policy_name") and hasattr(action_method, 'policy_name'):
            conflicts.append(error_message_template.format('policy_name', action_name, viewset_name))

        # Check for 'policy_description' (key 'description' in dict, attribute 'policy_description' on method)
        if iam_perms_for_action.get("description") and hasattr(action_method, 'policy_description'):
            conflicts.append(
                error_message_template.format('policy_description (dict key "description")', action_name, viewset_name))

        # Check for 'exclude_from_iam'
        if iam_perms_for_action.get("exclude_from_iam") is not None and \
                hasattr(action_method, 'exclude_from_iam'):
            conflicts.append(error_message_template.format('exclude_from_iam', action_name, viewset_name))

        if conflicts:
            raise Exception("\n".join(conflicts))

    def _generate_policy_details_from_viewsets(self) -> None:
        """Generates a list of desired PolicyDetail objects from URL patterns."""
        raw_policy_details: List[Dict[str, Any]] = []
        resource_type_name_cache: Dict[Type[ViewSetMixin], str] = {}

        for viewset_info in self._extract_viewsets_from_urlpatterns(self.urlpatterns):
            viewset_cls = viewset_info['callback'].cls
            actions = get_viewset_actions(viewset_cls)

            # Cache resource type name
            if viewset_cls not in resource_type_name_cache:
                resource_type_name_cache[viewset_cls] = getattr(
                    viewset_cls,
                    "iam_policy_name",
                    None
                ) or viewset_cls.__name__.lower().replace('viewset',
                                                          '')

            resource_type_name = resource_type_name_cache[viewset_cls]

            drf_iam_permissions = getattr(viewset_cls, "drf_iam_permissions", {})

            for action_name in actions:
                action_method = getattr(viewset_cls, action_name, None)
                iam_perms_for_action = drf_iam_permissions.get(action_name, {})

                if action_method:  # Ensure the method actually exists
                    self._validate_conflicting_definitions(
                        action_method,
                        action_name,
                        iam_perms_for_action
                    )

                # Determine if the action should be excluded
                # Precedence: method attribute > dict setting > default (False)
                excluded = False
                if hasattr(action_method, 'exclude_from_iam'):
                    excluded = getattr(action_method, 'exclude_from_iam')
                elif "exclude_from_iam" in iam_perms_for_action:
                    excluded = iam_perms_for_action.get("exclude_from_iam", False)

                if excluded:
                    logger.debug(
                        f"Action '{action_name}' on ViewSet "
                        f"'{viewset_cls.__name__}' is excluded from IAM policies."
                    )
                    continue

                # Determine policy_name
                # Precedence: method attribute > dict setting > default generated name
                policy_name_str: str
                if hasattr(action_method, 'policy_name'):
                    policy_name_str = getattr(action_method, 'policy_name')
                elif "policy_name" in iam_perms_for_action:
                    policy_name_str = iam_perms_for_action["policy_name"]
                else:
                    policy_name_str = f"{action_name.replace('_', ' ').title()} {resource_type_name.replace('_', ' ').title()}"

                # Determine description
                # Precedence: method attribute 'policy_description' > dict setting 'description' > default generated description
                description_str: str
                if hasattr(action_method, 'policy_description'):
                    description_str = getattr(action_method, 'policy_description')
                elif "description" in iam_perms_for_action:
                    description_str = iam_perms_for_action["description"]
                else:
                    description_str = f"Allows to {action_name.replace('_', ' ')} for {resource_type_name.replace('_', ' ')}"

                raw_policy_details.append({
                    "action": action_name,  # Just the action name
                    "resource_type": resource_type_name,
                    "policy_name": policy_name_str,
                    "description": description_str,
                })

        # Remove duplicates and create PolicyDetail objects
        # Ensures that if multiple URL patterns point to the same viewset action,
        # we only consider one policy detail for it based on action and resource_type.
        unique_policy_details_set = {
            (p["action"], p["resource_type"]): p for p in raw_policy_details
        }.values()

        self.desired_policies = [
            PolicyDetail(
                action=p["action"],
                resource_type=p["resource_type"],
                policy_name=p["policy_name"],
                description=p["description"],
            )
            for p in unique_policy_details_set
        ]

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
        current_map_for_delete = {(p.action, p.resource_type): p.id for p in self.current_db_policies if
                                  p.id is not None}
        policies_to_delete_stubs = current_set - desired_set
        for policy_stub in policies_to_delete_stubs:
            policy_id = current_map_for_delete.get((policy_stub.action, policy_stub.resource_type))
            if policy_id is not None:
                policies_to_delete_with_id.append(
                    PolicyDetail(action=policy_stub.action, resource_type=policy_stub.resource_type, policy_name='',
                                 description='', id=policy_id))

        to_update: List[PolicyDetail] = []
        current_map_for_update = {(p.action, p.resource_type): p for p in self.current_db_policies}

        for desired_policy in current_set & desired_set:
            current_policy_match = current_map_for_update.get((desired_policy.action, desired_policy.resource_type))
            if current_policy_match and (
                    current_policy_match.policy_name != desired_policy.policy_name or
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

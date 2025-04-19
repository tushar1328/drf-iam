from rest_framework import permissions

class DRFIamPermission(permissions.IsAuthenticated):
    def has_permission(self, request, view):
        user = request.user
        role = getattr(user, 'role', None)
        if not role:
            return False
        if not hasattr(user, '_cached_policy_actions'):
            user._cached_policy_actions = set(
                role.policies.values_list('action', flat=True)
            )
        policy_actions = user._cached_policy_actions
        # Resolve view name
        view_name = getattr(view, 'iam_policy_name', None)
        if not view_name:
            view_class_name = view.__class__.__name__.lower()
            view_name = view_class_name.replace('viewset', '')

        # Resolve action (DRF view.action or fallback to HTTP method)
        action = getattr(view, 'action', request.method.lower())
        policy_action = f"{view_name}:{action}"

        return policy_action in policy_actions

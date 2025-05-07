import inspect

from django.template.base import kwarg_re
from django.urls.resolvers import URLPattern, URLResolver
from rest_framework.viewsets import ViewSetMixin
from rest_framework.decorators import action

from django.urls import get_resolver
from ..models import Policy


def is_viewset(cls):
    return isinstance(cls, type) and issubclass(cls, ViewSetMixin)


def get_viewset_actions(viewset_cls):
    actions = set()

    # Default ViewSet methods
    default_actions = {'list', 'retrieve', 'create', 'update', 'partial_update', 'destroy'}
    for action_name in default_actions:
        if hasattr(viewset_cls, action_name):
            actions.add(action_name)

    # Custom @action methods
    for name, method in inspect.getmembers(viewset_cls, predicate=inspect.isfunction):
        if hasattr(method, 'mapping'):
            for http_method in method.mapping:
                actions.add(f"{name}")

    return actions


def extract_viewsets_from_urlpatterns(urlpatterns, prefix=''):
    for pattern in urlpatterns:
        if isinstance(pattern, URLResolver):
            # Recurse into included URLConfs
            yield from extract_viewsets_from_urlpatterns(pattern.url_patterns, prefix + str(pattern.pattern))
        elif isinstance(pattern, URLPattern):
            callback = pattern.callback
            cls = getattr(callback, 'cls', None)
            if is_viewset(cls):
                yield {
                    'prefix': prefix,
                    'pattern': pattern.pattern,
                    'viewset': cls,
                    'callback': callback
                }


def load_permissions_from_urls(**kwargs):
    urlpatterns = get_resolver().url_patterns
    for entry in extract_viewsets_from_urlpatterns(urlpatterns):
        viewset_cls = entry['viewset']
        basename = getattr(viewset_cls,"iam_policy_name") or viewset_cls.__name__.lower().replace('viewset', '')
        exclude_from_permissions = getattr(viewset_cls, "drf_iam_exclude_from_permissions", False)
        if exclude_from_permissions:
            continue
        actions = get_viewset_actions(viewset_cls)

        for action in actions:
            full_action = f"{basename}:{action}"
            Policy.objects.get_or_create(
                action=full_action,
                resource_type=basename,
                defaults={
                    'description': f"Permission for {full_action} on {basename}"
                }
            )

import functools

def action_permissions_config(policy_name=None,policy_description=None,exclude_from_iam=False):
    """
    A decorator for viewset actions to attach custom arguments and keyword arguments.
    This data can be retrieved by permission-loading utilities to implement custom logic.

    Usage:
        from drf_iam.decorators import action_permissions_config

        class MyViewSet(ViewSet):
            @action_permissions_config('can_read_special_data', project_level=True)
            def my_action(self, request):
                # ...
                pass
    """
    def decorator(func_to_decorate):
        @functools.wraps(func_to_decorate)
        def wrapper_func(*view_args, **view_kwargs):
            return func_to_decorate(*view_args, **view_kwargs)

        setattr(wrapper_func, 'policy_name', policy_name)
        setattr(wrapper_func, 'exclude_from_iam', exclude_from_iam)
        setattr(wrapper_func, 'policy_description', policy_description)
        
        return wrapper_func
    return decorator

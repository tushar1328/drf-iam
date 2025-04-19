Usage Guide
===========

This guide covers common usage patterns and best practices for DRF-IAM.

Basic Concepts
------------

DRF-IAM implements Role-Based Access Control (RBAC) with three main components:

1. **Roles**: Define user types (e.g., admin, editor, viewer)
2. **Policies**: Resource-specific permission rules
3. **Permissions**: Define what actions a role can perform on a policy

Common Use Cases
--------------

Setting Up Basic RBAC
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Create roles
    admin_role = Role.objects.create(name="admin")
    editor_role = Role.objects.create(name="editor")
    viewer_role = Role.objects.create(name="viewer")

    # Set up permissions
    Permission.objects.create(
        role=admin_role,
        policy_name="*",  # Wildcard for all policies
        can_create=True, can_read=True,
        can_update=True, can_delete=True
    )

    Permission.objects.create(
        role=editor_role,
        policy_name="articles",
        can_create=True, can_read=True,
        can_update=True, can_delete=False
    )

    Permission.objects.create(
        role=viewer_role,
        policy_name="articles",
        can_read=True,  # Only read permission
        can_create=False, can_update=False, can_delete=False
    )

Using in Views
~~~~~~~~~~~~

.. code-block:: python

    class ArticleViewSet(viewsets.ModelViewSet):
        queryset = Article.objects.all()
        serializer_class = ArticleSerializer
        permission_classes = [IAMPermission]
        iam_policy_name = "articles"

Best Practices
------------

1. **Policy Naming**:
   - Use clear, descriptive names
   - Keep names consistent across related resources
   - Use plural forms for resource collections

2. **Role Design**:
   - Start with broad roles
   - Refine as needed
   - Document role purposes

3. **Permission Management**:
   - Grant minimum required permissions
   - Use wildcards sparingly
   - Regularly audit permissions

4. **Security Considerations**:
   - Always validate role assignments
   - Implement role-based middleware if needed
   - Log permission changes

Example Scenarios
--------------

Blog Application
~~~~~~~~~~~~~~

.. code-block:: python

    # Models
    class Article(models.Model):
        title = models.CharField(max_length=200)
        content = models.TextField()
        author = models.ForeignKey(User, on_delete=models.CASCADE)

    # Views
    class ArticleViewSet(viewsets.ModelViewSet):
        permission_classes = [IAMPermission]
        iam_policy_name = "articles"

    class CommentViewSet(viewsets.ModelViewSet):
        permission_classes = [IAMPermission]
        iam_policy_name = "comments"

    # Permissions
    def setup_blog_permissions():
        # Author role
        author_role = Role.objects.create(name="author")
        Permission.objects.create(
            role=author_role,
            policy_name="articles",
            can_create=True,
            can_read=True,
            can_update=True,
            can_delete=True
        )
        Permission.objects.create(
            role=author_role,
            policy_name="comments",
            can_read=True,
            can_delete=True
        )

        # Commenter role
        commenter_role = Role.objects.create(name="commenter")
        Permission.objects.create(
            role=commenter_role,
            policy_name="comments",
            can_create=True,
            can_read=True
        )

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

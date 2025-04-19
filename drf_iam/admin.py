from django.contrib import admin

from drf_iam.models import Policy, Role, RolePolicy


@admin.register(Policy)
class PolicyAdmin(admin.ModelAdmin):
    list_display = ('action', 'resource_type', 'description')
    search_fields = ('action', 'resource_type')
    list_filter = ('action', 'resource_type')

class PoliciesInline(admin.TabularInline):
    model = Role.policies.through

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name', 'description')
    list_filter = ('name', 'description')
    inlines = [PoliciesInline]


@admin.register(RolePolicy)
class RolePolicyAdmin(admin.ModelAdmin):
    list_display = ('role', 'policy')
    search_fields = ('role', 'policy')
    list_filter = ('role', 'policy')



from django.db import models


class Role(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    policies = models.ManyToManyField('Policy', through='RolePolicy', blank=True, related_name='policies',
                                      related_query_name='policies', db_index=True)

    def __str__(self):
        return self.name


class Policy(models.Model):
    action = models.CharField(max_length=100)
    resource_type = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.action} on {self.resource_type}"

    class Meta:
        unique_together = ('action', 'resource_type')
        ordering = ['action', 'resource_type']
        verbose_name_plural = 'policies'
        verbose_name = 'policy'


class RolePolicy(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE, db_index=True)
    policy = models.ForeignKey(Policy, on_delete=models.CASCADE, db_index=True)

    class Meta:
        unique_together = ('role', 'policy')
        ordering = ['role', 'policy']
        verbose_name_plural = 'role policies'
        verbose_name = 'role policy'

    def __str__(self):
        return f"{self.role.name} - {self.policy}"

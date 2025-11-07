from django.db import models
import uuid

# Create your models here.

class Profile(models.Model):
    id = models.UUIDField(primary_key=True, editable=False)
    user_id = models.UUIDField()
    xp = models.IntegerField(default=0)
    level = models.IntegerField(default=1)
    badges = models.JSONField(default=list)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = "profiles"
        managed = False

class Transaction(models.Model):
    id = models.UUIDField(primary_key=True, editable=False)
    user_id = models.UUIDField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="USD")
    category = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    occurred_at = models.DateTimeField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = "transactions"
        managed = False

class Goal(models.Model):
    STATUS_ACTIVE = "active"
    STATUS_PAUSED = "paused"
    STATUS_COMPLETED = "completed"
    STATUS_ARCHIVED = "archived"
    STATUS_CHOICES = [
        (STATUS_ACTIVE, "active"),
        (STATUS_PAUSED, "paused"),
        (STATUS_COMPLETED, "completed"),
        (STATUS_ARCHIVED, "archived"),
    ]

    id = models.UUIDField(primary_key=True, editable=False)
    user_id = models.UUIDField()
    name = models.TextField()
    target_amount = models.DecimalField(max_digits=12, decimal_places=2)
    current_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    deadline = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = "goals"
        managed = False

class XPLog(models.Model):
    id = models.UUIDField(primary_key=True, editable=False)
    user_id = models.UUIDField()
    xp_delta = models.IntegerField()
    reason = models.TextField()
    related_entity_type = models.TextField(null=True, blank=True)
    related_entity_id = models.UUIDField(null=True, blank=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = "xp_log"
        managed = False

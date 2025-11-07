from decimal import Decimal
from rest_framework import serializers


class UUIDStrField(serializers.UUIDField):
    def to_representation(self, value):
        return str(value)


class ProfileSerializer(serializers.Serializer):
    id = UUIDStrField(read_only=True)
    user_id = UUIDStrField(required=True)
    xp = serializers.IntegerField(required=False, default=0, min_value=0)
    level = serializers.IntegerField(required=False, default=1, min_value=1)
    badges = serializers.JSONField(required=False, default=list)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    is_deleted = serializers.BooleanField(required=False, default=False)


class TransactionSerializer(serializers.Serializer):
    id = UUIDStrField(read_only=True)
    user_id = UUIDStrField(required=True)
    type = serializers.ChoiceField(choices=["income", "expense"], default="expense")
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    currency = serializers.CharField(max_length=3, default="USD")
    category = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    description = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    occurred_at = serializers.DateTimeField()
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    is_deleted = serializers.BooleanField(required=False, default=False)

    def validate_amount(self, value):
        if value is None or Decimal(value) <= Decimal("0"):
            raise serializers.ValidationError("Amount must be > 0.")
        return value

    def validate_currency(self, value):
        if not value or len(value) != 3:
            raise serializers.ValidationError("Currency must be a 3-letter ISO code.")
        return value.upper()


class GoalSerializer(serializers.Serializer):
    id = UUIDStrField(read_only=True)
    user_id = UUIDStrField(required=True)
    name = serializers.CharField()
    target_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    current_amount = serializers.DecimalField(max_digits=12, decimal_places=2, default=0)
    deadline = serializers.DateField(required=False, allow_null=True)
    status = serializers.ChoiceField(choices=["active", "paused", "completed", "archived"], default="active")
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    is_deleted = serializers.BooleanField(required=False, default=False)

    def validate_target_amount(self, value):
        if value is None or Decimal(value) <= Decimal("0"):
            raise serializers.ValidationError("target_amount must be > 0.")
        return value

    def validate_current_amount(self, value):
        if value is None or Decimal(value) < Decimal("0"):
            raise serializers.ValidationError("current_amount must be >= 0.")
        return value


class XPLogSerializer(serializers.Serializer):
    id = UUIDStrField(read_only=True)
    user_id = UUIDStrField(required=True)
    xp_delta = serializers.IntegerField()
    reason = serializers.CharField()
    related_entity_type = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    related_entity_id = UUIDStrField(required=False, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    is_deleted = serializers.BooleanField(required=False, default=False)

    def validate_reason(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("reason is required.")
        return value

"""
Subscription and Billing Models
"""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    JSON,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.tenant import Tenant


class BillingInterval(str, enum.Enum):
    """Billing interval options"""
    MONTHLY = "monthly"
    YEARLY = "yearly"
    QUARTERLY = "quarterly"
    WEEKLY = "weekly"


class SubscriptionStatus(str, enum.Enum):
    """Subscription status options"""
    TRIALING = "trialing"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    UNPAID = "unpaid"
    INCOMPLETE = "incomplete"
    PAUSED = "paused"


class InvoiceStatus(str, enum.Enum):
    """Invoice status options"""
    DRAFT = "draft"
    OPEN = "open"
    PAID = "paid"
    VOID = "void"
    UNCOLLECTIBLE = "uncollectible"


class SubscriptionPlan(Base):
    """Subscription plans available to tenants"""

    __tablename__ = "subscription_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Plan Details
    name = Column(String(100), nullable=False)
    slug = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)

    # Pricing
    price = Column(Numeric(10, 2), nullable=False)  # Base price
    currency = Column(String(3), default="USD", nullable=False)
    billing_interval = Column(SQLEnum(BillingInterval), default=BillingInterval.MONTHLY, nullable=False)

    # Trial
    trial_days = Column(Integer, default=0, nullable=False)

    # Features & Limits
    features = Column(JSON, nullable=True)  # List of features
    max_users = Column(Integer, nullable=True)
    max_storage_gb = Column(Integer, nullable=True)
    max_api_calls = Column(Integer, nullable=True)

    # Stripe Integration
    stripe_price_id = Column(String(255), nullable=True, index=True)
    stripe_product_id = Column(String(255), nullable=True)

    # Paystack Integration
    paystack_plan_code = Column(String(255), nullable=True)

    # Plan Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_public = Column(Boolean, default=True, nullable=False)  # Visible to new signups

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    subscriptions = relationship("Subscription", back_populates="plan")

    def __repr__(self):
        return f"<SubscriptionPlan {self.name}>"


class Subscription(Base):
    """Tenant subscriptions"""

    __tablename__ = "subscriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("subscription_plans.id", ondelete="SET NULL"), nullable=True)

    # Subscription Status
    status = Column(SQLEnum(SubscriptionStatus), default=SubscriptionStatus.TRIALING, nullable=False, index=True)

    # Pricing
    current_period_start = Column(DateTime(timezone=True), nullable=True)
    current_period_end = Column(DateTime(timezone=True), nullable=True)
    cancel_at_period_end = Column(Boolean, default=False, nullable=False)

    # Trial
    trial_start = Column(DateTime(timezone=True), nullable=True)
    trial_end = Column(DateTime(timezone=True), nullable=True)

    # Payment Provider IDs
    stripe_subscription_id = Column(String(255), nullable=True, unique=True, index=True)
    stripe_customer_id = Column(String(255), nullable=True, index=True)
    paystack_subscription_code = Column(String(255), nullable=True)
    paystack_customer_code = Column(String(255), nullable=True)

    # Cancellation
    canceled_at = Column(DateTime(timezone=True), nullable=True)
    cancellation_reason = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    plan = relationship("SubscriptionPlan", back_populates="subscriptions")
    invoices = relationship("Invoice", back_populates="subscription", cascade="all, delete-orphan")
    usage_records = relationship("UsageRecord", back_populates="subscription", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Subscription {self.tenant_id} - {self.status}>"

    @property
    def is_trial(self) -> bool:
        """Check if subscription is in trial period"""
        return self.status == SubscriptionStatus.TRIALING

    @property
    def is_active(self) -> bool:
        """Check if subscription is active"""
        return self.status in [SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING]

    @property
    def days_until_renewal(self) -> int:
        """Calculate days until next renewal"""
        if self.current_period_end:
            delta = self.current_period_end - datetime.utcnow()
            return max(0, delta.days)
        return 0


class Invoice(Base):
    """Billing invoices"""

    __tablename__ = "invoices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    subscription_id = Column(UUID(as_uuid=True), ForeignKey("subscriptions.id", ondelete="CASCADE"), nullable=False, index=True)

    # Invoice Details
    invoice_number = Column(String(50), unique=True, nullable=False, index=True)
    status = Column(SQLEnum(InvoiceStatus), default=InvoiceStatus.DRAFT, nullable=False, index=True)

    # Amounts
    subtotal = Column(Numeric(10, 2), nullable=False)
    tax = Column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    discount = Column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    total = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="USD", nullable=False)

    # Payment Provider
    stripe_invoice_id = Column(String(255), nullable=True, unique=True, index=True)
    paystack_invoice_id = Column(String(255), nullable=True)

    # Invoice Items (JSON array)
    line_items = Column(JSON, nullable=True)

    # Dates
    invoice_date = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    due_date = Column(DateTime(timezone=True), nullable=True)
    paid_at = Column(DateTime(timezone=True), nullable=True)

    # PDF
    pdf_url = Column(String(512), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    subscription = relationship("Subscription", back_populates="invoices")

    def __repr__(self):
        return f"<Invoice {self.invoice_number} - {self.status}>"


class PaymentMethod(Base):
    """Stored payment methods"""

    __tablename__ = "payment_methods"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)

    # Payment Method Type
    type = Column(String(50), nullable=False)  # card, bank_account, etc.

    # Card Details (masked)
    card_brand = Column(String(50), nullable=True)  # visa, mastercard, etc.
    card_last4 = Column(String(4), nullable=True)
    card_exp_month = Column(Integer, nullable=True)
    card_exp_year = Column(Integer, nullable=True)

    # Provider IDs
    stripe_payment_method_id = Column(String(255), nullable=True, unique=True, index=True)
    paystack_authorization_code = Column(String(255), nullable=True)

    # Status
    is_default = Column(Boolean, default=False, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    def __repr__(self):
        return f"<PaymentMethod {self.type} - {self.card_last4}>"


class UsageRecord(Base):
    """Track usage for metered billing"""

    __tablename__ = "usage_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subscription_id = Column(UUID(as_uuid=True), ForeignKey("subscriptions.id", ondelete="CASCADE"), nullable=False, index=True)

    # Usage Metrics
    metric_name = Column(String(100), nullable=False, index=True)  # api_calls, storage, users, etc.
    quantity = Column(Integer, nullable=False)
    unit = Column(String(50), nullable=True)  # requests, GB, users, etc.

    # Billing Period
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)

    # Metadata
    usage_metadata = Column("metadata", JSON, nullable=True)

    # Timestamps
    recorded_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    subscription = relationship("Subscription", back_populates="usage_records")

    def __repr__(self):
        return f"<UsageRecord {self.metric_name}: {self.quantity}>"


class Coupon(Base):
    """Promotional coupons and discounts"""

    __tablename__ = "coupons"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Coupon Details
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)

    # Discount
    discount_type = Column(String(20), nullable=False)  # percentage or fixed
    discount_value = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), nullable=True)  # For fixed discounts

    # Limits
    max_redemptions = Column(Integer, nullable=True)
    times_redeemed = Column(Integer, default=0, nullable=False)
    duration = Column(String(20), nullable=False)  # once, repeating, forever
    duration_in_months = Column(Integer, nullable=True)  # For repeating

    # Validity
    valid_from = Column(DateTime(timezone=True), nullable=True)
    valid_until = Column(DateTime(timezone=True), nullable=True)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)

    # Provider IDs
    stripe_coupon_id = Column(String(255), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    def __repr__(self):
        return f"<Coupon {self.code}>"

    @property
    def is_valid(self) -> bool:
        """Check if coupon is currently valid"""
        now = datetime.utcnow()

        if not self.is_active:
            return False

        if self.valid_from and now < self.valid_from:
            return False

        if self.valid_until and now > self.valid_until:
            return False

        if self.max_redemptions and self.times_redeemed >= self.max_redemptions:
            return False

        return True

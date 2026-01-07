"""
Domain Entities - Core business objects with identity.
Following Domain-Driven Design principles.
"""

from datetime import datetime
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field, validator
import uuid


class AccountType(str, Enum):
    CHECKING = "checking"
    SAVINGS = "savings"
    CREDIT = "credit"


class AccountStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CLOSED = "closed"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class KYCStatus(str, Enum):
    VERIFIED = "verified"
    PENDING = "pending"
    FAILED = "failed"


class TransactionType(str, Enum):
    TRANSFER = "transfer"
    WITHDRAWAL = "withdrawal"
    DEPOSIT = "deposit"
    PAYMENT = "payment"


class TransactionStatus(str, Enum):
    COMPLETED = "completed"
    PENDING = "pending"
    FAILED = "failed"
    REVERSED = "reversed"


class TransactionChannel(str, Enum):
    ONLINE = "online"
    ATM = "atm"
    BRANCH = "branch"
    MOBILE = "mobile"


class Account(BaseModel):
    """Bank Account Entity"""
    account_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    account_number: str
    account_type: AccountType
    status: AccountStatus = AccountStatus.ACTIVE
    created_date: datetime = Field(default_factory=datetime.utcnow)
    risk_score: float = Field(default=0.0, ge=0.0, le=100.0)
    country: str
    currency: str = "USD"
    balance: float = 0.0

    class Config:
        use_enum_values = True


class Customer(BaseModel):
    """Customer Entity"""
    customer_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    first_name: str
    last_name: str
    email: str
    phone: str
    date_of_birth: datetime
    ssn_hash: str
    address: str
    city: str
    country: str
    customer_since: datetime = Field(default_factory=datetime.utcnow)
    kyc_status: KYCStatus = KYCStatus.PENDING
    risk_level: RiskLevel = RiskLevel.LOW

    class Config:
        use_enum_values = True

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @validator('email')
    def validate_email(cls, v):
        if '@' not in v:
            raise ValueError('Invalid email address')
        return v.lower()


class Transaction(BaseModel):
    """Transaction Entity"""
    transaction_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    amount: float = Field(gt=0)
    currency: str = "USD"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    transaction_type: TransactionType
    status: TransactionStatus = TransactionStatus.COMPLETED
    channel: TransactionChannel
    description: str = ""
    is_flagged: bool = False
    fraud_score: float = Field(default=0.0, ge=0.0, le=1.0)
    from_account_id: Optional[str] = None
    to_account_id: Optional[str] = None
    merchant_id: Optional[str] = None
    device_id: Optional[str] = None
    ip_address: Optional[str] = None

    class Config:
        use_enum_values = True


class Device(BaseModel):
    """Device Entity"""
    device_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    device_type: str  # mobile, desktop, tablet
    os: str
    browser: Optional[str] = None
    first_seen: datetime = Field(default_factory=datetime.utcnow)
    last_seen: datetime = Field(default_factory=datetime.utcnow)
    is_trusted: bool = False


class IPAddress(BaseModel):
    """IP Address Entity"""
    ip_address: str
    country: str
    city: str = ""
    is_proxy: bool = False
    is_vpn: bool = False
    risk_score: float = Field(default=0.0, ge=0.0, le=1.0)
    first_seen: datetime = Field(default_factory=datetime.utcnow)
    last_seen: datetime = Field(default_factory=datetime.utcnow)

    @validator('ip_address')
    def validate_ip(cls, v):
        parts = v.split('.')
        if len(parts) != 4:
            raise ValueError('Invalid IP address format')
        return v


class Merchant(BaseModel):
    """Merchant Entity"""
    merchant_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    merchant_name: str
    category: str  # retail, gambling, crypto, etc.
    country: str
    risk_level: RiskLevel = RiskLevel.LOW
    is_verified: bool = True

    class Config:
        use_enum_values = True


class FraudRingStatus(str, Enum):
    INVESTIGATING = "investigating"
    CONFIRMED = "confirmed"
    FALSE_POSITIVE = "false_positive"
    RESOLVED = "resolved"


class FraudRing(BaseModel):
    """Fraud Ring Entity - Represents a detected group of related fraudulent activities"""
    ring_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    detected_date: datetime = Field(default_factory=datetime.utcnow)
    confidence_score: float = Field(ge=0.0, le=1.0)
    status: FraudRingStatus = FraudRingStatus.INVESTIGATING
    total_amount: float = 0.0
    member_count: int = 0
    pattern_type: str = ""  # circular, fan_out, fan_in, mule_network
    description: str = ""

    class Config:
        use_enum_values = True


class Alert(BaseModel):
    """Alert Entity - Represents a fraud alert"""
    alert_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    alert_type: str  # velocity, circular_flow, shared_device, etc.
    severity: RiskLevel
    created_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    is_resolved: bool = False
    assigned_to: Optional[str] = None
    notes: str = ""
    related_entities: List[str] = Field(default_factory=list)

    class Config:
        use_enum_values = True

"""
Value Objects - Immutable domain concepts without identity.
Following Domain-Driven Design principles.
"""

from typing import Optional
from pydantic import BaseModel, Field, validator
from datetime import datetime


class Money(BaseModel):
    """Value Object representing money"""
    amount: float = Field(ge=0)
    currency: str = Field(default="USD")

    class Config:
        frozen = True  # Immutable

    def __str__(self) -> str:
        return f"{self.currency} {self.amount:.2f}"

    def __add__(self, other: 'Money') -> 'Money':
        if self.currency != other.currency:
            raise ValueError(f"Cannot add different currencies: {self.currency} and {other.currency}")
        return Money(amount=self.amount + other.amount, currency=self.currency)

    def __sub__(self, other: 'Money') -> 'Money':
        if self.currency != other.currency:
            raise ValueError(f"Cannot subtract different currencies: {self.currency} and {other.currency}")
        if self.amount < other.amount:
            raise ValueError("Cannot have negative money")
        return Money(amount=self.amount - other.amount, currency=self.currency)


class Address(BaseModel):
    """Value Object representing a physical address"""
    street: str
    city: str
    state: Optional[str] = None
    postal_code: str
    country: str

    class Config:
        frozen = True

    def __str__(self) -> str:
        parts = [self.street, self.city]
        if self.state:
            parts.append(self.state)
        parts.extend([self.postal_code, self.country])
        return ", ".join(parts)


class DateRange(BaseModel):
    """Value Object representing a date range"""
    start_date: datetime
    end_date: datetime

    class Config:
        frozen = True

    @validator('end_date')
    def validate_end_after_start(cls, v, values):
        if 'start_date' in values and v < values['start_date']:
            raise ValueError('end_date must be after start_date')
        return v

    def contains(self, date: datetime) -> bool:
        return self.start_date <= date <= self.end_date

    def duration_days(self) -> int:
        return (self.end_date - self.start_date).days


class RiskScore(BaseModel):
    """Value Object representing a risk score with explanation"""
    score: float = Field(ge=0.0, le=100.0)
    factors: list[str] = Field(default_factory=list)
    calculated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        frozen = True

    @property
    def risk_level(self) -> str:
        if self.score < 30:
            return "LOW"
        elif self.score < 60:
            return "MEDIUM"
        elif self.score < 85:
            return "HIGH"
        else:
            return "CRITICAL"


class TransactionPattern(BaseModel):
    """Value Object describing a transaction pattern"""
    pattern_type: str  # velocity, circular, fan_out, fan_in, etc.
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[str] = Field(default_factory=list)
    detected_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        frozen = True


class GeographicLocation(BaseModel):
    """Value Object representing a geographic location"""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    city: str
    country: str
    country_code: str

    class Config:
        frozen = True

    @validator('latitude')
    def validate_latitude(cls, v):
        if v is not None and not -90 <= v <= 90:
            raise ValueError('Latitude must be between -90 and 90')
        return v

    @validator('longitude')
    def validate_longitude(cls, v):
        if v is not None and not -180 <= v <= 180:
            raise ValueError('Longitude must be between -180 and 180')
        return v


class DeviceFingerprint(BaseModel):
    """Value Object representing a unique device fingerprint"""
    user_agent: str
    screen_resolution: Optional[str] = None
    timezone: str
    language: str
    plugins: list[str] = Field(default_factory=list)

    class Config:
        frozen = True

    def generate_hash(self) -> str:
        """Generate a hash of the fingerprint for identification"""
        import hashlib
        fingerprint_str = f"{self.user_agent}{self.screen_resolution}{self.timezone}{self.language}"
        return hashlib.sha256(fingerprint_str.encode()).hexdigest()


class ConnectionStrength(BaseModel):
    """Value Object representing the strength of a connection between entities"""
    strength: float = Field(ge=0.0, le=1.0)
    basis: list[str] = Field(default_factory=list)  # shared_device, shared_ip, transaction_pattern
    first_observed: datetime
    last_observed: datetime

    class Config:
        frozen = True

    @property
    def is_strong(self) -> bool:
        return self.strength > 0.7

    @property
    def is_weak(self) -> bool:
        return self.strength < 0.3

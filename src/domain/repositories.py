"""
Repository Interfaces (Ports) - Abstract interfaces for data access.
Following Domain-Driven Design and Hexagonal Architecture principles.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from .entities import (
    Account, Customer, Transaction, Device, IPAddress,
    Merchant, FraudRing, Alert
)


class IAccountRepository(ABC):
    """Interface for Account persistence"""

    @abstractmethod
    def save(self, account: Account) -> Account:
        """Save an account"""
        pass

    @abstractmethod
    def find_by_id(self, account_id: str) -> Optional[Account]:
        """Find account by ID"""
        pass

    @abstractmethod
    def find_by_account_number(self, account_number: str) -> Optional[Account]:
        """Find account by account number"""
        pass

    @abstractmethod
    def find_by_customer(self, customer_id: str) -> List[Account]:
        """Find all accounts owned by a customer"""
        pass

    @abstractmethod
    def find_high_risk_accounts(self, threshold: float = 70.0) -> List[Account]:
        """Find accounts with risk score above threshold"""
        pass

    @abstractmethod
    def update_risk_score(self, account_id: str, risk_score: float) -> None:
        """Update account risk score"""
        pass


class ICustomerRepository(ABC):
    """Interface for Customer persistence"""

    @abstractmethod
    def save(self, customer: Customer) -> Customer:
        """Save a customer"""
        pass

    @abstractmethod
    def find_by_id(self, customer_id: str) -> Optional[Customer]:
        """Find customer by ID"""
        pass

    @abstractmethod
    def find_by_email(self, email: str) -> Optional[Customer]:
        """Find customer by email"""
        pass

    @abstractmethod
    def find_connected_customers(self, customer_id: str, depth: int = 2) -> List[Customer]:
        """Find customers connected through shared devices, addresses, etc."""
        pass


class ITransactionRepository(ABC):
    """Interface for Transaction persistence"""

    @abstractmethod
    def save(self, transaction: Transaction) -> Transaction:
        """Save a transaction"""
        pass

    @abstractmethod
    def find_by_id(self, transaction_id: str) -> Optional[Transaction]:
        """Find transaction by ID"""
        pass

    @abstractmethod
    def find_by_account(self, account_id: str, start_date: Optional[datetime] = None,
                       end_date: Optional[datetime] = None) -> List[Transaction]:
        """Find all transactions for an account within date range"""
        pass

    @abstractmethod
    def find_flagged_transactions(self, limit: int = 100) -> List[Transaction]:
        """Find flagged transactions"""
        pass

    @abstractmethod
    def find_circular_transactions(self, min_cycle_length: int = 3,
                                   max_cycle_length: int = 8) -> List[List[Transaction]]:
        """Find circular money flows"""
        pass

    @abstractmethod
    def count_transactions_in_timeframe(self, account_id: str,
                                       minutes: int = 60) -> int:
        """Count transactions for an account in last N minutes (velocity check)"""
        pass


class IDeviceRepository(ABC):
    """Interface for Device persistence"""

    @abstractmethod
    def save(self, device: Device) -> Device:
        """Save a device"""
        pass

    @abstractmethod
    def find_by_id(self, device_id: str) -> Optional[Device]:
        """Find device by ID"""
        pass

    @abstractmethod
    def find_shared_devices(self, min_users: int = 2) -> List[tuple[Device, int]]:
        """Find devices shared by multiple users"""
        pass


class IIPAddressRepository(ABC):
    """Interface for IP Address persistence"""

    @abstractmethod
    def save(self, ip: IPAddress) -> IPAddress:
        """Save an IP address"""
        pass

    @abstractmethod
    def find_by_address(self, ip_address: str) -> Optional[IPAddress]:
        """Find IP by address"""
        pass

    @abstractmethod
    def find_high_risk_ips(self, threshold: float = 0.7) -> List[IPAddress]:
        """Find high-risk IP addresses"""
        pass


class IMerchantRepository(ABC):
    """Interface for Merchant persistence"""

    @abstractmethod
    def save(self, merchant: Merchant) -> Merchant:
        """Save a merchant"""
        pass

    @abstractmethod
    def find_by_id(self, merchant_id: str) -> Optional[Merchant]:
        """Find merchant by ID"""
        pass

    @abstractmethod
    def find_by_name(self, name: str) -> List[Merchant]:
        """Find merchants by name"""
        pass


class IFraudRingRepository(ABC):
    """Interface for Fraud Ring persistence"""

    @abstractmethod
    def save(self, fraud_ring: FraudRing) -> FraudRing:
        """Save a fraud ring"""
        pass

    @abstractmethod
    def find_by_id(self, ring_id: str) -> Optional[FraudRing]:
        """Find fraud ring by ID"""
        pass

    @abstractmethod
    def find_active_rings(self) -> List[FraudRing]:
        """Find all active fraud rings under investigation"""
        pass

    @abstractmethod
    def link_customer_to_ring(self, ring_id: str, customer_id: str, role: str) -> None:
        """Link a customer to a fraud ring"""
        pass

    @abstractmethod
    def link_account_to_ring(self, ring_id: str, account_id: str, role: str) -> None:
        """Link an account to a fraud ring"""
        pass


class IAlertRepository(ABC):
    """Interface for Alert persistence"""

    @abstractmethod
    def save(self, alert: Alert) -> Alert:
        """Save an alert"""
        pass

    @abstractmethod
    def find_by_id(self, alert_id: str) -> Optional[Alert]:
        """Find alert by ID"""
        pass

    @abstractmethod
    def find_unresolved_alerts(self) -> List[Alert]:
        """Find all unresolved alerts"""
        pass

    @abstractmethod
    def find_by_severity(self, severity: str) -> List[Alert]:
        """Find alerts by severity level"""
        pass


class IGraphQueryRepository(ABC):
    """Interface for complex graph queries"""

    @abstractmethod
    def detect_fan_out_pattern(self, min_recipients: int = 5,
                              timeframe_hours: int = 24) -> List[Dict[str, Any]]:
        """
        Detect fan-out patterns: one account sending to many in short time
        Returns list of suspicious source accounts with their recipients
        """
        pass

    @abstractmethod
    def detect_fan_in_pattern(self, min_senders: int = 5,
                             timeframe_hours: int = 24) -> List[Dict[str, Any]]:
        """
        Detect fan-in patterns: many accounts sending to one in short time
        Returns list of suspicious destination accounts with their senders
        """
        pass

    @abstractmethod
    def detect_mule_accounts(self, min_throughput: float = 10000,
                           max_hold_time_hours: int = 48) -> List[Account]:
        """
        Detect money mule accounts: receive and quickly forward funds
        """
        pass

    @abstractmethod
    def find_shared_infrastructure(self, entity_type: str = "device") -> List[Dict[str, Any]]:
        """
        Find accounts sharing infrastructure (devices, IPs, addresses)
        entity_type: 'device', 'ip', or 'address'
        """
        pass

    @abstractmethod
    def calculate_connection_path(self, from_entity_id: str, to_entity_id: str,
                                 max_depth: int = 5) -> Optional[List[Dict[str, Any]]]:
        """
        Find shortest path between two entities in the graph
        Returns path with nodes and relationships
        """
        pass

    @abstractmethod
    def get_entity_neighborhood(self, entity_id: str, entity_type: str,
                               depth: int = 2) -> Dict[str, Any]:
        """
        Get the neighborhood graph around an entity
        Returns nodes and edges within specified depth
        """
        pass

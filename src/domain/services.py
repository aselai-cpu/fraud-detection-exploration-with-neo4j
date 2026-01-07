"""
Domain Services - Business logic that doesn't belong to a single entity.
Following Domain-Driven Design principles.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone
from .entities import (
    Account, Customer, Transaction, RiskLevel,
    FraudRing, FraudRingStatus, Alert
)
from .value_objects import RiskScore, TransactionPattern
from .repositories import (
    IAccountRepository, ICustomerRepository, ITransactionRepository,
    IFraudRingRepository, IGraphQueryRepository
)


class RiskScoringService:
    """Service for calculating risk scores for accounts and customers"""

    def __init__(self, transaction_repo: ITransactionRepository,
                 account_repo: IAccountRepository):
        self.transaction_repo = transaction_repo
        self.account_repo = account_repo

    def calculate_account_risk(self, account: Account) -> RiskScore:
        """Calculate comprehensive risk score for an account"""
        factors = []
        score = 0.0

        # Factor 1: Transaction velocity (30%)
        velocity_count = self.transaction_repo.count_transactions_in_timeframe(
            account.account_id, minutes=60
        )
        if velocity_count > 10:
            velocity_score = min(30.0, velocity_count * 2)
            score += velocity_score
            factors.append(f"High transaction velocity: {velocity_count} in last hour")

        # Factor 2: Recent flagged transactions (25%)
        recent_transactions = self.transaction_repo.find_by_account(
            account.account_id,
            start_date=datetime.now(timezone.utc) - timedelta(days=7)
        )
        flagged_count = sum(1 for t in recent_transactions if t.is_flagged)
        if flagged_count > 0:
            flagged_score = min(25.0, flagged_count * 5)
            score += flagged_score
            factors.append(f"Flagged transactions: {flagged_count}")

        # Factor 3: Account age (15%) - newer accounts are riskier
        account_age_days = (datetime.now(timezone.utc) - account.created_date).days
        if account_age_days < 30:
            age_score = 15.0 - (account_age_days * 0.5)
            score += age_score
            factors.append(f"New account: {account_age_days} days old")

        # Factor 4: Account status (20%)
        status_val = account.status if isinstance(account.status, str) else account.status.value
        if status_val == "suspended":
            score += 20.0
            factors.append("Account suspended")

        # Factor 5: High-value transactions (10%)
        high_value_count = sum(1 for t in recent_transactions if t.amount > 10000)
        if high_value_count > 0:
            value_score = min(10.0, high_value_count * 2)
            score += value_score
            factors.append(f"High-value transactions: {high_value_count}")

        return RiskScore(score=min(100.0, score), factors=factors)

    def calculate_customer_risk(self, customer: Customer,
                               accounts: List[Account]) -> RiskScore:
        """Calculate comprehensive risk score for a customer"""
        factors = []
        score = 0.0

        # Factor 1: KYC status (25%)
        kyc_status_val = customer.kyc_status if isinstance(customer.kyc_status, str) else customer.kyc_status.value
        if kyc_status_val == "failed":
            score += 25.0
            factors.append("KYC verification failed")
        elif kyc_status_val == "pending":
            score += 15.0
            factors.append("KYC verification pending")

        # Factor 2: Account risk scores (30%)
        if accounts:
            avg_account_risk = sum(a.risk_score for a in accounts) / len(accounts)
            account_risk_score = (avg_account_risk / 100) * 30
            score += account_risk_score
            if avg_account_risk > 50:
                factors.append(f"High average account risk: {avg_account_risk:.1f}")

        # Factor 3: Customer age (15%)
        customer_age_days = (datetime.now(timezone.utc) - customer.customer_since).days
        if customer_age_days < 60:
            age_score = 15.0 - (customer_age_days * 0.25)
            score += age_score
            factors.append(f"New customer: {customer_age_days} days")

        # Factor 4: Number of accounts (10%)
        if len(accounts) > 5:
            account_count_score = min(10.0, (len(accounts) - 5) * 2)
            score += account_count_score
            factors.append(f"Multiple accounts: {len(accounts)}")

        return RiskScore(score=min(100.0, score), factors=factors)


class FraudDetectionService:
    """Service for detecting fraud patterns"""

    def __init__(self, graph_query_repo: IGraphQueryRepository,
                 transaction_repo: ITransactionRepository,
                 account_repo: IAccountRepository):
        self.graph_query_repo = graph_query_repo
        self.transaction_repo = transaction_repo
        self.account_repo = account_repo

    def detect_circular_flow(self, min_cycle_length: int = 3) -> List[TransactionPattern]:
        """Detect circular money flow patterns"""
        patterns = []
        cycles = self.transaction_repo.find_circular_transactions(
            min_cycle_length=min_cycle_length,
            max_cycle_length=8
        )

        for cycle in cycles:
            total_amount = sum(t.amount for t in cycle)
            evidence = [f"Transaction {t.transaction_id}: {t.amount}" for t in cycle]

            pattern = TransactionPattern(
                pattern_type="circular_flow",
                confidence=0.8,
                evidence=evidence
            )
            patterns.append(pattern)

        return patterns

    def detect_fan_out(self, min_recipients: int = 5) -> List[TransactionPattern]:
        """Detect fan-out patterns (one account to many)"""
        patterns = []
        results = self.graph_query_repo.detect_fan_out_pattern(
            min_recipients=min_recipients,
            timeframe_hours=24
        )

        for result in results:
            pattern = TransactionPattern(
                pattern_type="fan_out",
                confidence=min(0.9, result['recipient_count'] / 10),
                evidence=[
                    f"Account {result['account_id']} sent to {result['recipient_count']} accounts",
                    f"Total amount: {result['total_amount']}"
                ]
            )
            patterns.append(pattern)

        return patterns

    def detect_fan_in(self, min_senders: int = 5) -> List[TransactionPattern]:
        """Detect fan-in patterns (many accounts to one)"""
        patterns = []
        results = self.graph_query_repo.detect_fan_in_pattern(
            min_senders=min_senders,
            timeframe_hours=24
        )

        for result in results:
            pattern = TransactionPattern(
                pattern_type="fan_in",
                confidence=min(0.9, result['sender_count'] / 10),
                evidence=[
                    f"Account {result['account_id']} received from {result['sender_count']} accounts",
                    f"Total amount: {result['total_amount']}"
                ]
            )
            patterns.append(pattern)

        return patterns

    def detect_mule_accounts(self) -> List[Account]:
        """Detect potential money mule accounts"""
        return self.graph_query_repo.detect_mule_accounts(
            min_throughput=10000,
            max_hold_time_hours=48
        )

    def detect_shared_infrastructure(self) -> Dict[str, List[Dict[str, Any]]]:
        """Detect accounts sharing devices, IPs, etc."""
        return {
            'shared_devices': self.graph_query_repo.find_shared_infrastructure('device'),
            'shared_ips': self.graph_query_repo.find_shared_infrastructure('ip')
        }


class FraudRingAnalysisService:
    """Service for analyzing and managing fraud rings"""

    def __init__(self, fraud_ring_repo: IFraudRingRepository,
                 fraud_detection_service: FraudDetectionService):
        self.fraud_ring_repo = fraud_ring_repo
        self.fraud_detection_service = fraud_detection_service

    def create_fraud_ring_from_pattern(self, pattern: TransactionPattern,
                                      related_entities: List[str]) -> FraudRing:
        """Create a fraud ring from a detected pattern"""
        ring = FraudRing(
            confidence_score=pattern.confidence,
            pattern_type=pattern.pattern_type,
            description=f"Detected {pattern.pattern_type} pattern",
            member_count=len(related_entities)
        )

        saved_ring = self.fraud_ring_repo.save(ring)

        # Link entities to the ring
        for entity_id in related_entities:
            # Assuming these are account IDs
            self.fraud_ring_repo.link_account_to_ring(
                saved_ring.ring_id,
                entity_id,
                "participant"
            )

        return saved_ring

    def update_ring_status(self, ring_id: str, status: FraudRingStatus,
                          notes: str = "") -> Optional[FraudRing]:
        """Update fraud ring investigation status"""
        ring = self.fraud_ring_repo.find_by_id(ring_id)
        if ring:
            ring.status = status
            if notes:
                ring.description += f"\n{datetime.now(timezone.utc)}: {notes}"
            return self.fraud_ring_repo.save(ring)
        return None


class AlertService:
    """Service for managing fraud alerts"""

    def __init__(self, risk_scoring_service: RiskScoringService):
        self.risk_scoring_service = risk_scoring_service

    def create_alert_from_pattern(self, pattern: TransactionPattern,
                                  related_entities: List[str]) -> Alert:
        """Create an alert from a detected fraud pattern"""
        severity = self._determine_severity(pattern.confidence)

        alert = Alert(
            alert_type=pattern.pattern_type,
            severity=severity,
            notes=f"Detected {pattern.pattern_type}. Confidence: {pattern.confidence:.2f}",
            related_entities=related_entities
        )

        return alert

    def _determine_severity(self, confidence: float) -> RiskLevel:
        """Determine alert severity based on confidence score"""
        if confidence >= 0.9:
            return RiskLevel.CRITICAL
        elif confidence >= 0.7:
            return RiskLevel.HIGH
        elif confidence >= 0.5:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

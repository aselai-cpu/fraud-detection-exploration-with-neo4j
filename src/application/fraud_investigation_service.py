"""
Fraud Investigation Service - High-level service for fraud analysts.
Orchestrates fraud detection and investigation workflows.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone

from ..domain.entities import Account, Customer, Transaction, FraudRing, Alert, RiskLevel
from ..domain.services import (
    RiskScoringService, FraudDetectionService,
    FraudRingAnalysisService, AlertService
)
from ..domain.repositories import (
    IAccountRepository, ICustomerRepository, ITransactionRepository,
    IFraudRingRepository, IGraphQueryRepository, IAlertRepository
)
from ..infrastructure.neo4j_repositories import (
    Neo4jAccountRepository, Neo4jCustomerRepository,
    Neo4jTransactionRepository, Neo4jFraudRingRepository,
    Neo4jGraphQueryRepository, Neo4jAlertRepository
)


class FraudInvestigationService:
    """High-level service for fraud investigation operations"""

    @staticmethod
    def get_risk_category(risk_score: float) -> str:
        """Convert risk score to categorical risk level"""
        if risk_score >= 80:
            return "CRITICAL"
        elif risk_score >= 60:
            return "HIGH"
        elif risk_score >= 40:
            return "MEDIUM"
        else:
            return "LOW"

    def __init__(self):
        # Initialize repositories
        self.account_repo = Neo4jAccountRepository()
        self.customer_repo = Neo4jCustomerRepository()
        self.transaction_repo = Neo4jTransactionRepository()
        self.fraud_ring_repo = Neo4jFraudRingRepository()
        self.graph_query_repo = Neo4jGraphQueryRepository()
        self.alert_repo = Neo4jAlertRepository()

        # Initialize domain services
        self.risk_scoring_service = RiskScoringService(
            self.transaction_repo,
            self.account_repo
        )
        self.fraud_detection_service = FraudDetectionService(
            self.graph_query_repo,
            self.transaction_repo,
            self.account_repo
        )
        self.fraud_ring_service = FraudRingAnalysisService(
            self.fraud_ring_repo,
            self.fraud_detection_service
        )
        self.alert_service = AlertService(self.risk_scoring_service)

    def get_dashboard_summary(self) -> Dict[str, Any]:
        """Get summary statistics for analyst dashboard"""
        flagged_transactions = self.transaction_repo.find_flagged_transactions(limit=1000)
        high_risk_accounts = self.account_repo.find_high_risk_accounts(threshold=70.0)
        active_rings = self.fraud_ring_repo.find_active_rings()
        unresolved_alerts = self.alert_repo.find_unresolved_alerts()

        return {
            'flagged_transactions_count': len(flagged_transactions),
            'high_risk_accounts_count': len(high_risk_accounts),
            'active_fraud_rings': len(active_rings),
            'unresolved_alerts': len(unresolved_alerts),
            'critical_alerts': len([a for a in unresolved_alerts
                                   if a.severity == RiskLevel.CRITICAL]),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

    def investigate_account(self, account_id: str) -> Dict[str, Any]:
        """Investigate a specific account"""
        account = self.account_repo.find_by_id(account_id)
        if not account:
            return {'error': 'Account not found'}

        # Get account transactions
        recent_transactions = self.transaction_repo.find_by_account(
            account_id,
            start_date=datetime.now(timezone.utc) - timedelta(days=30)
        )

        # Calculate risk score
        risk_score = self.risk_scoring_service.calculate_account_risk(account)

        # Get transaction velocity
        velocity_1h = self.transaction_repo.count_transactions_in_timeframe(
            account_id, minutes=60
        )
        velocity_24h = self.transaction_repo.count_transactions_in_timeframe(
            account_id, minutes=1440
        )

        # Get neighborhood graph
        neighborhood = self.graph_query_repo.get_entity_neighborhood(
            account_id, 'account', depth=2
        )

        return {
            'account': account.dict(),
            'risk_score': risk_score.dict(),
            'transaction_count_30d': len(recent_transactions),
            'flagged_transactions': len([t for t in recent_transactions if t.is_flagged]),
            'velocity': {
                '1_hour': velocity_1h,
                '24_hours': velocity_24h
            },
            'recent_transactions': [t.dict() for t in recent_transactions[:10]],
            'neighborhood': neighborhood
        }

    def investigate_customer(self, customer_id: str) -> Dict[str, Any]:
        """Investigate a specific customer"""
        customer = self.customer_repo.find_by_id(customer_id)
        if not customer:
            return {'error': 'Customer not found'}

        # Get customer accounts
        accounts = self.account_repo.find_by_customer(customer_id)

        # Calculate customer risk
        risk_score = self.risk_scoring_service.calculate_customer_risk(customer, accounts)

        # Find connected customers
        connected_customers = self.customer_repo.find_connected_customers(
            customer_id, depth=2
        )

        return {
            'customer': customer.dict(),
            'risk_score': risk_score.dict(),
            'accounts': [acc.dict() for acc in accounts],
            'account_count': len(accounts),
            'total_balance': sum(acc.balance for acc in accounts),
            'connected_customers_count': len(connected_customers),
            'connected_customers': [c.dict() for c in connected_customers[:5]]
        }

    def detect_fraud_patterns(self) -> Dict[str, Any]:
        """Run fraud detection algorithms and return results"""
        results = {}

        # Detect circular flows
        circular_patterns = self.fraud_detection_service.detect_circular_flow(
            min_cycle_length=3
        )
        results['circular_flow'] = [{
            'pattern_type': p.pattern_type,
            'confidence': p.confidence,
            'evidence_count': len(p.evidence)
        } for p in circular_patterns]

        # Detect fan-out patterns
        fan_out_patterns = self.fraud_detection_service.detect_fan_out(min_recipients=5)
        results['fan_out'] = [{
            'pattern_type': p.pattern_type,
            'confidence': p.confidence,
            'evidence_count': len(p.evidence)
        } for p in fan_out_patterns]

        # Detect fan-in patterns
        fan_in_patterns = self.fraud_detection_service.detect_fan_in(min_senders=5)
        results['fan_in'] = [{
            'pattern_type': p.pattern_type,
            'confidence': p.confidence,
            'evidence_count': len(p.evidence)
        } for p in fan_in_patterns]

        # Detect mule accounts
        mule_accounts = self.fraud_detection_service.detect_mule_accounts()
        results['mule_accounts'] = [{
            'account_id': acc.account_id,
            'account_number': acc.account_number,
            'risk_score': acc.risk_score
        } for acc in mule_accounts]

        # Detect shared infrastructure
        shared_infra = self.fraud_detection_service.detect_shared_infrastructure()
        results['shared_infrastructure'] = {
            'shared_devices_count': len(shared_infra.get('shared_devices', [])),
            'shared_ips_count': len(shared_infra.get('shared_ips', []))
        }

        # Calculate and update risk scores for accounts with flagged transactions
        flagged_transactions = self.transaction_repo.find_flagged_transactions(limit=1000)

        # Get unique account IDs from flagged transactions
        account_ids = set()
        for txn in flagged_transactions:
            if txn.from_account_id:
                account_ids.add(txn.from_account_id)
            if txn.to_account_id:
                account_ids.add(txn.to_account_id)

        # Calculate and update risk scores for each account
        high_risk_count = 0
        updated_accounts = []
        for account_id in account_ids:
            account = self.account_repo.find_by_id(account_id)
            if account:
                risk_score = self.risk_scoring_service.calculate_account_risk(account)
                self.account_repo.update_risk_score(account_id, risk_score.score)

                updated_accounts.append({
                    'account_id': account_id,
                    'risk_score': risk_score.score
                })

                if risk_score.score >= 70.0:
                    high_risk_count += 1

        results['risk_scoring'] = {
            'accounts_evaluated': len(account_ids),
            'accounts_updated': len(updated_accounts),
            'high_risk_accounts': high_risk_count,
            'flagged_transactions_processed': len(flagged_transactions)
        }

        return results

    def find_connection_path(self, from_entity_id: str, to_entity_id: str) -> Optional[List[Dict]]:
        """Find connection path between two entities"""
        return self.graph_query_repo.calculate_connection_path(
            from_entity_id, to_entity_id, max_depth=5
        )

    def get_high_risk_accounts(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get list of high-risk accounts"""
        accounts = self.account_repo.find_high_risk_accounts(threshold=60.0)[:limit]

        results = []
        for account in accounts:
            # Get some transaction stats
            recent_txns = self.transaction_repo.find_by_account(
                account.account_id,
                start_date=datetime.now(timezone.utc) - timedelta(days=7)
            )

            results.append({
                'account_id': account.account_id,
                'account_number': account.account_number,
                'risk_score': account.risk_score,
                'risk_category': self.get_risk_category(account.risk_score),
                'status': account.status,
                'balance': account.balance,
                'recent_transaction_count': len(recent_txns),
                'flagged_count': len([t for t in recent_txns if t.is_flagged])
            })

        return results

    def get_flagged_transactions(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get flagged transactions"""
        transactions = self.transaction_repo.find_flagged_transactions(limit=limit)

        return [{
            'transaction_id': t.transaction_id,
            'amount': t.amount,
            'currency': t.currency,
            'timestamp': t.timestamp.isoformat(),
            'transaction_type': t.transaction_type,
            'fraud_score': t.fraud_score,
            'from_account_id': t.from_account_id,
            'to_account_id': t.to_account_id,
            'description': t.description
        } for t in transactions]

    def get_circular_flow_accounts(self) -> List[Dict[str, Any]]:
        """Get accounts involved in circular flow patterns"""
        circular_patterns = self.fraud_detection_service.detect_circular_flow(min_cycle_length=3)

        # Extract unique account IDs from circular flow patterns
        account_ids = set()
        for pattern in circular_patterns:
            # Evidence contains transaction IDs - we need to get the transactions
            for evidence_str in pattern.evidence:
                # Extract transaction ID from evidence string
                if 'Transaction' in evidence_str:
                    txn_id = evidence_str.split(':')[0].replace('Transaction ', '').strip()
                    txn = self.transaction_repo.find_by_id(txn_id)
                    if txn:
                        if txn.from_account_id:
                            account_ids.add(txn.from_account_id)
                        if txn.to_account_id:
                            account_ids.add(txn.to_account_id)

        return self._get_account_details(account_ids)

    def get_fan_out_accounts(self) -> List[Dict[str, Any]]:
        """Get accounts involved in fan-out patterns"""
        fan_out_patterns = self.fraud_detection_service.detect_fan_out(min_recipients=5)

        account_ids = set()
        for pattern in fan_out_patterns:
            for evidence_str in pattern.evidence:
                if 'Account' in evidence_str:
                    # Extract account ID from evidence
                    parts = evidence_str.split()
                    for part in parts:
                        if len(part) == 36 and '-' in part:  # UUID format
                            account_ids.add(part)

        return self._get_account_details(account_ids)

    def get_fan_in_accounts(self) -> List[Dict[str, Any]]:
        """Get accounts involved in fan-in patterns"""
        fan_in_patterns = self.fraud_detection_service.detect_fan_in(min_senders=5)

        account_ids = set()
        for pattern in fan_in_patterns:
            for evidence_str in pattern.evidence:
                if 'Account' in evidence_str:
                    parts = evidence_str.split()
                    for part in parts:
                        if len(part) == 36 and '-' in part:
                            account_ids.add(part)

        return self._get_account_details(account_ids)

    def get_mule_accounts_details(self) -> List[Dict[str, Any]]:
        """Get detailed information about mule accounts"""
        mule_accounts = self.fraud_detection_service.detect_mule_accounts()

        results = []
        for account in mule_accounts:
            # Get recent transactions
            recent_txns = self.transaction_repo.find_by_account(
                account.account_id,
                start_date=datetime.now(timezone.utc) - timedelta(days=7)
            )

            results.append({
                'account_id': account.account_id,
                'account_number': account.account_number,
                'risk_score': account.risk_score,
                'risk_category': self.get_risk_category(account.risk_score),
                'status': account.status,
                'balance': account.balance,
                'recent_transaction_count': len(recent_txns),
                'flagged_count': len([t for t in recent_txns if t.is_flagged])
            })

        return results

    def _get_account_details(self, account_ids: set) -> List[Dict[str, Any]]:
        """Helper method to get detailed account information"""
        results = []
        for account_id in account_ids:
            account = self.account_repo.find_by_id(account_id)
            if account:
                recent_txns = self.transaction_repo.find_by_account(
                    account_id,
                    start_date=datetime.now(timezone.utc) - timedelta(days=7)
                )

                results.append({
                    'account_id': account.account_id,
                    'account_number': account.account_number,
                    'risk_score': account.risk_score,
                    'risk_category': self.get_risk_category(account.risk_score),
                    'status': account.status,
                    'balance': account.balance,
                    'recent_transaction_count': len(recent_txns),
                    'flagged_count': len([t for t in recent_txns if t.is_flagged])
                })

        # Sort by risk score descending
        results.sort(key=lambda x: x['risk_score'], reverse=True)
        return results

    def get_active_fraud_rings(self) -> List[Dict[str, Any]]:
        """Get active fraud rings under investigation"""
        rings = self.fraud_ring_repo.find_active_rings()

        return [{
            'ring_id': ring.ring_id,
            'detected_date': ring.detected_date.isoformat(),
            'confidence_score': ring.confidence_score,
            'status': ring.status,
            'total_amount': ring.total_amount,
            'member_count': ring.member_count,
            'pattern_type': ring.pattern_type,
            'description': ring.description
        } for ring in rings]

    def create_investigation_report(self, entity_id: str,
                                   entity_type: str = 'account') -> Dict[str, Any]:
        """Create comprehensive investigation report"""
        now = datetime.now(timezone.utc)
        report = {
            'report_id': f"RPT-{now.strftime('%Y%m%d%H%M%S')}",
            'generated_at': now.isoformat(),
            'entity_type': entity_type,
            'entity_id': entity_id
        }

        if entity_type == 'account':
            report['investigation'] = self.investigate_account(entity_id)
        elif entity_type == 'customer':
            report['investigation'] = self.investigate_customer(entity_id)

        # Add fraud pattern detection results
        report['detected_patterns'] = self.detect_fraud_patterns()

        return report

    def get_shared_infrastructure_details(self, infrastructure_type: str = 'device') -> List[Dict[str, Any]]:
        """Get details about shared infrastructure (devices/IPs)"""
        shared = self.graph_query_repo.find_shared_infrastructure(infrastructure_type)

        results = []
        for item in shared:
            results.append({
                'infrastructure_id': item.get('infrastructure_id'),
                'shared_by_count': len(item.get('customer_ids', []) or item.get('account_ids', [])),
                'entity_ids': item.get('customer_ids', []) or item.get('account_ids', [])
            })

        return results

    def search_entities(self, query: str, entity_type: str = 'account') -> List[Dict[str, Any]]:
        """Search for entities by query string"""
        # Simplified search - in production would use full-text indexing
        if entity_type == 'account':
            # Search by account number or ID
            account = self.account_repo.find_by_account_number(query)
            if account:
                return [account.dict()]
            account = self.account_repo.find_by_id(query)
            if account:
                return [account.dict()]
        elif entity_type == 'customer':
            # Search by email or ID
            customer = self.customer_repo.find_by_email(query)
            if customer:
                return [customer.dict()]
            customer = self.customer_repo.find_by_id(query)
            if customer:
                return [customer.dict()]

        return []

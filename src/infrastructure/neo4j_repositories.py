"""
Neo4j Repository Implementations - Anti-corruption layer.
Implements domain repository interfaces using Neo4j.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, timezone
from neo4j import Session

from ..domain.entities import (
    Account, Customer, Transaction, Device, IPAddress,
    Merchant, FraudRing, Alert, AccountType, AccountStatus,
    RiskLevel, KYCStatus, TransactionType, TransactionStatus,
    TransactionChannel, FraudRingStatus
)
from ..domain.repositories import (
    IAccountRepository, ICustomerRepository, ITransactionRepository,
    IDeviceRepository, IIPAddressRepository, IMerchantRepository,
    IFraudRingRepository, IAlertRepository, IGraphQueryRepository
)
from .neo4j_connection import Neo4jConnection


class Neo4jAccountRepository(IAccountRepository):
    """Neo4j implementation of Account repository"""

    def __init__(self):
        self.connection = Neo4jConnection()

    def save(self, account: Account) -> Account:
        with self.connection.get_session() as session:
            query = """
            MERGE (a:Account {account_id: $account_id})
            SET a.account_number = $account_number,
                a.account_type = $account_type,
                a.status = $status,
                a.created_date = datetime($created_date),
                a.risk_score = $risk_score,
                a.country = $country,
                a.currency = $currency,
                a.balance = $balance
            RETURN a
            """
            session.run(query, **account.dict())
            return account

    def find_by_id(self, account_id: str) -> Optional[Account]:
        with self.connection.get_session() as session:
            query = "MATCH (a:Account {account_id: $account_id}) RETURN a"
            result = session.run(query, account_id=account_id)
            record = result.single()
            if record:
                return self._node_to_account(record['a'])
            return None

    def find_by_account_number(self, account_number: str) -> Optional[Account]:
        with self.connection.get_session() as session:
            query = "MATCH (a:Account {account_number: $account_number}) RETURN a"
            result = session.run(query, account_number=account_number)
            record = result.single()
            if record:
                return self._node_to_account(record['a'])
            return None

    def find_by_customer(self, customer_id: str) -> List[Account]:
        with self.connection.get_session() as session:
            query = """
            MATCH (c:Customer {customer_id: $customer_id})-[:OWNS]->(a:Account)
            RETURN a
            """
            result = session.run(query, customer_id=customer_id)
            return [self._node_to_account(record['a']) for record in result]

    def find_high_risk_accounts(self, threshold: float = 70.0) -> List[Account]:
        with self.connection.get_session() as session:
            query = """
            MATCH (a:Account)
            WHERE a.risk_score >= $threshold
            RETURN a
            ORDER BY a.risk_score DESC
            """
            result = session.run(query, threshold=threshold)
            return [self._node_to_account(record['a']) for record in result]

    def update_risk_score(self, account_id: str, risk_score: float) -> None:
        with self.connection.get_session() as session:
            query = """
            MATCH (a:Account {account_id: $account_id})
            SET a.risk_score = $risk_score
            """
            session.run(query, account_id=account_id, risk_score=risk_score)

    def _node_to_account(self, node) -> Account:
        """Convert Neo4j node to Account entity"""
        data = dict(node)
        # Convert datetime objects
        if 'created_date' in data and hasattr(data['created_date'], 'to_native'):
            data['created_date'] = data['created_date'].to_native()
        return Account(**data)


class Neo4jCustomerRepository(ICustomerRepository):
    """Neo4j implementation of Customer repository"""

    def __init__(self):
        self.connection = Neo4jConnection()

    def save(self, customer: Customer) -> Customer:
        with self.connection.get_session() as session:
            query = """
            MERGE (c:Customer {customer_id: $customer_id})
            SET c.first_name = $first_name,
                c.last_name = $last_name,
                c.email = $email,
                c.phone = $phone,
                c.date_of_birth = datetime($date_of_birth),
                c.ssn_hash = $ssn_hash,
                c.address = $address,
                c.city = $city,
                c.country = $country,
                c.customer_since = datetime($customer_since),
                c.kyc_status = $kyc_status,
                c.risk_level = $risk_level
            RETURN c
            """
            session.run(query, **customer.dict())
            return customer

    def find_by_id(self, customer_id: str) -> Optional[Customer]:
        with self.connection.get_session() as session:
            query = "MATCH (c:Customer {customer_id: $customer_id}) RETURN c"
            result = session.run(query, customer_id=customer_id)
            record = result.single()
            if record:
                return self._node_to_customer(record['c'])
            return None

    def find_by_email(self, email: str) -> Optional[Customer]:
        with self.connection.get_session() as session:
            query = "MATCH (c:Customer {email: $email}) RETURN c"
            result = session.run(query, email=email.lower())
            record = result.single()
            if record:
                return self._node_to_customer(record['c'])
            return None

    def find_connected_customers(self, customer_id: str, depth: int = 2) -> List[Customer]:
        with self.connection.get_session() as session:
            query = f"""
            MATCH path = (c1:Customer {{customer_id: $customer_id}})-[*1..{depth}]-(c2:Customer)
            WHERE c1 <> c2
            RETURN DISTINCT c2
            """
            result = session.run(query, customer_id=customer_id)
            return [self._node_to_customer(record['c2']) for record in result]

    def _node_to_customer(self, node) -> Customer:
        """Convert Neo4j node to Customer entity"""
        data = dict(node)
        # Convert datetime objects
        for field in ['date_of_birth', 'customer_since']:
            if field in data and hasattr(data[field], 'to_native'):
                data[field] = data[field].to_native()
        return Customer(**data)


class Neo4jTransactionRepository(ITransactionRepository):
    """Neo4j implementation of Transaction repository"""

    def __init__(self):
        self.connection = Neo4jConnection()

    def save(self, transaction: Transaction) -> Transaction:
        with self.connection.get_session() as session:
            # Create transaction node
            query = """
            CREATE (t:Transaction {
                transaction_id: $transaction_id,
                amount: $amount,
                currency: $currency,
                timestamp: datetime($timestamp),
                transaction_type: $transaction_type,
                status: $status,
                channel: $channel,
                description: $description,
                is_flagged: $is_flagged,
                fraud_score: $fraud_score
            })
            """
            session.run(query, **{
                'transaction_id': transaction.transaction_id,
                'amount': transaction.amount,
                'currency': transaction.currency,
                'timestamp': transaction.timestamp.isoformat(),
                'transaction_type': transaction.transaction_type,
                'status': transaction.status,
                'channel': transaction.channel,
                'description': transaction.description,
                'is_flagged': transaction.is_flagged,
                'fraud_score': transaction.fraud_score
            })

            # Create relationships
            if transaction.from_account_id:
                session.run("""
                    MATCH (t:Transaction {transaction_id: $transaction_id})
                    MATCH (a:Account {account_id: $from_account_id})
                    MERGE (t)-[:DEBITED_FROM]->(a)
                """, transaction_id=transaction.transaction_id,
                           from_account_id=transaction.from_account_id)

            if transaction.to_account_id:
                session.run("""
                    MATCH (t:Transaction {transaction_id: $transaction_id})
                    MATCH (a:Account {account_id: $to_account_id})
                    MERGE (t)-[:CREDITED_TO]->(a)
                """, transaction_id=transaction.transaction_id,
                           to_account_id=transaction.to_account_id)

            return transaction

    def find_by_id(self, transaction_id: str) -> Optional[Transaction]:
        with self.connection.get_session() as session:
            query = """
            MATCH (t:Transaction {transaction_id: $transaction_id})
            OPTIONAL MATCH (t)-[:DEBITED_FROM]->(from_account:Account)
            OPTIONAL MATCH (t)-[:CREDITED_TO]->(to_account:Account)
            RETURN t, from_account.account_id as from_account_id,
                   to_account.account_id as to_account_id
            """
            result = session.run(query, transaction_id=transaction_id)
            record = result.single()
            if record:
                return self._record_to_transaction(record)
            return None

    def find_by_account(self, account_id: str, start_date: Optional[datetime] = None,
                       end_date: Optional[datetime] = None) -> List[Transaction]:
        with self.connection.get_session() as session:
            query = """
            MATCH (t:Transaction)-[:DEBITED_FROM|CREDITED_TO]->(a:Account {account_id: $account_id})
            WHERE ($start_date IS NULL OR t.timestamp >= datetime($start_date))
              AND ($end_date IS NULL OR t.timestamp <= datetime($end_date))
            OPTIONAL MATCH (t)-[:DEBITED_FROM]->(from_account:Account)
            OPTIONAL MATCH (t)-[:CREDITED_TO]->(to_account:Account)
            RETURN t, from_account.account_id as from_account_id,
                   to_account.account_id as to_account_id
            ORDER BY t.timestamp DESC
            """
            params = {
                'account_id': account_id,
                'start_date': start_date.isoformat() if start_date else None,
                'end_date': end_date.isoformat() if end_date else None
            }
            result = session.run(query, **params)
            return [self._record_to_transaction(record) for record in result]

    def find_flagged_transactions(self, limit: int = 100) -> List[Transaction]:
        with self.connection.get_session() as session:
            query = """
            MATCH (t:Transaction {is_flagged: true})
            OPTIONAL MATCH (t)-[:DEBITED_FROM]->(from_account:Account)
            OPTIONAL MATCH (t)-[:CREDITED_TO]->(to_account:Account)
            RETURN t, from_account.account_id as from_account_id,
                   to_account.account_id as to_account_id
            ORDER BY t.timestamp DESC
            LIMIT $limit
            """
            result = session.run(query, limit=limit)
            return [self._record_to_transaction(record) for record in result]

    def find_circular_transactions(self, min_cycle_length: int = 3,
                                   max_cycle_length: int = 8) -> List[List[Transaction]]:
        """Find circular transaction patterns (A -> B -> C -> A)

        Detects cycles where money flows through multiple accounts and returns to origin.
        """
        with self.connection.get_session() as session:
            # Query to find circular flows through transaction chains
            # We look for patterns where transactions create a cycle back to the starting account
            query = """
            MATCH path = (start:Account)
                <-[:DEBITED_FROM]-(t1:Transaction)-[:CREDITED_TO]->
                (a2:Account)<-[:DEBITED_FROM]-(t2:Transaction)-[:CREDITED_TO]->
                (a3:Account)<-[:DEBITED_FROM]-(t3:Transaction)-[:CREDITED_TO]->(start)
            WHERE t1.is_flagged = true
              AND t2.is_flagged = true
              AND t3.is_flagged = true
              AND start <> a2
              AND start <> a3
              AND a2 <> a3
            WITH [t1, t2, t3] as cycle_transactions, start.account_id as start_account
            RETURN cycle_transactions
            LIMIT 100
            """
            result = session.run(query)

            cycles = []
            for record in result:
                txn_nodes = record['cycle_transactions']
                if txn_nodes:
                    transactions = []
                    for txn_node in txn_nodes:
                        txn_data = dict(txn_node)
                        # Convert datetime if needed
                        if 'timestamp' in txn_data and hasattr(txn_data['timestamp'], 'to_native'):
                            txn_data['timestamp'] = txn_data['timestamp'].to_native()

                        transactions.append(Transaction(**txn_data))

                    if len(transactions) >= min_cycle_length:
                        cycles.append(transactions)

            return cycles

    def count_transactions_in_timeframe(self, account_id: str, minutes: int = 60) -> int:
        with self.connection.get_session() as session:
            cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=minutes)
            query = """
            MATCH (t:Transaction)-[:DEBITED_FROM|CREDITED_TO]->(a:Account {account_id: $account_id})
            WHERE t.timestamp >= datetime($cutoff_time)
            RETURN count(t) as count
            """
            result = session.run(query, account_id=account_id,
                               cutoff_time=cutoff_time.isoformat())
            record = result.single()
            return record['count'] if record else 0

    def _record_to_transaction(self, record) -> Transaction:
        """Convert Neo4j record to Transaction entity"""
        data = dict(record['t'])
        if 'timestamp' in data and hasattr(data['timestamp'], 'to_native'):
            data['timestamp'] = data['timestamp'].to_native()

        # Add account IDs from relationships
        if record.get('from_account_id'):
            data['from_account_id'] = record['from_account_id']
        if record.get('to_account_id'):
            data['to_account_id'] = record['to_account_id']

        return Transaction(**data)


class Neo4jGraphQueryRepository(IGraphQueryRepository):
    """Neo4j implementation of complex graph queries"""

    def __init__(self):
        self.connection = Neo4jConnection()

    def detect_fan_out_pattern(self, min_recipients: int = 5,
                              timeframe_hours: int = 24) -> List[Dict[str, Any]]:
        with self.connection.get_session() as session:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=timeframe_hours)
            query = """
            MATCH (from_account:Account)<-[:DEBITED_FROM]-(t:Transaction)-[:CREDITED_TO]->(to_account:Account)
            WHERE t.timestamp >= datetime($cutoff_time)
            WITH from_account, count(DISTINCT to_account) as recipient_count, sum(t.amount) as total_amount
            WHERE recipient_count >= $min_recipients
            RETURN from_account.account_id as account_id, recipient_count, total_amount
            ORDER BY recipient_count DESC
            """
            result = session.run(query, cutoff_time=cutoff_time.isoformat(),
                               min_recipients=min_recipients)
            return [dict(record) for record in result]

    def detect_fan_in_pattern(self, min_senders: int = 5,
                             timeframe_hours: int = 24) -> List[Dict[str, Any]]:
        with self.connection.get_session() as session:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=timeframe_hours)
            query = """
            MATCH (from_account:Account)<-[:DEBITED_FROM]-(t:Transaction)-[:CREDITED_TO]->(to_account:Account)
            WHERE t.timestamp >= datetime($cutoff_time)
            WITH to_account, count(DISTINCT from_account) as sender_count, sum(t.amount) as total_amount
            WHERE sender_count >= $min_senders
            RETURN to_account.account_id as account_id, sender_count, total_amount
            ORDER BY sender_count DESC
            """
            result = session.run(query, cutoff_time=cutoff_time.isoformat(),
                               min_senders=min_senders)
            return [dict(record) for record in result]

    def detect_mule_accounts(self, min_throughput: float = 10000,
                           max_hold_time_hours: int = 48) -> List[Account]:
        with self.connection.get_session() as session:
            query = """
            MATCH (a:Account)<-[:CREDITED_TO]-(t_in:Transaction)
            MATCH (a)<-[:DEBITED_FROM]-(t_out:Transaction)
            WHERE duration.between(t_in.timestamp, t_out.timestamp).hours <= $max_hold_time_hours
            WITH a, sum(t_in.amount) as total_in, sum(t_out.amount) as total_out
            WHERE total_in >= $min_throughput AND abs(total_in - total_out) / total_in < 0.1
            RETURN a
            """
            result = session.run(query, min_throughput=min_throughput,
                               max_hold_time_hours=max_hold_time_hours)
            accounts = []
            account_repo = Neo4jAccountRepository()
            for record in result:
                account = account_repo._node_to_account(record['a'])
                accounts.append(account)
            return accounts

    def find_shared_infrastructure(self, entity_type: str = "device") -> List[Dict[str, Any]]:
        with self.connection.get_session() as session:
            if entity_type == "device":
                query = """
                MATCH (c1:Customer)-[:USED_DEVICE]->(d:Device)<-[:USED_DEVICE]-(c2:Customer)
                WHERE c1.customer_id < c2.customer_id
                RETURN d.device_id as infrastructure_id,
                       collect(DISTINCT c1.customer_id) + collect(DISTINCT c2.customer_id) as customer_ids,
                       count(DISTINCT c1) + count(DISTINCT c2) as user_count
                """
            else:  # ip
                query = """
                MATCH (t1:Transaction)-[:FROM_IP]->(ip:IPAddress)<-[:FROM_IP]-(t2:Transaction)
                MATCH (t1)-[:DEBITED_FROM|CREDITED_TO]-(a1:Account)
                MATCH (t2)-[:DEBITED_FROM|CREDITED_TO]-(a2:Account)
                WHERE a1.account_id < a2.account_id
                RETURN ip.ip_address as infrastructure_id,
                       collect(DISTINCT a1.account_id) + collect(DISTINCT a2.account_id) as account_ids
                """
            result = session.run(query)
            return [dict(record) for record in result]

    def calculate_connection_path(self, from_entity_id: str, to_entity_id: str,
                                 max_depth: int = 5) -> Optional[List[Dict[str, Any]]]:
        with self.connection.get_session() as session:
            query = f"""
            MATCH path = shortestPath((from)-[*1..{max_depth}]-(to))
            WHERE from.account_id = $from_entity_id OR from.customer_id = $from_entity_id
              AND to.account_id = $to_entity_id OR to.customer_id = $to_entity_id
            RETURN path
            """
            result = session.run(query, from_entity_id=from_entity_id,
                               to_entity_id=to_entity_id)
            record = result.single()
            if record:
                # Simplified - would need to process path properly
                return [{'path': 'found'}]
            return None

    def get_entity_neighborhood(self, entity_id: str, entity_type: str,
                               depth: int = 2) -> Dict[str, Any]:
        with self.connection.get_session() as session:
            query = f"""
            MATCH path = (n)-[*1..{depth}]-(connected)
            WHERE n.{entity_type}_id = $entity_id
            RETURN nodes(path) as nodes, relationships(path) as relationships
            LIMIT 100
            """
            result = session.run(query, entity_id=entity_id)
            # Simplified - would need to process properly
            return {'nodes': [], 'edges': []}


# Placeholder implementations for other repositories
class Neo4jDeviceRepository(IDeviceRepository):
    def __init__(self):
        self.connection = Neo4jConnection()

    def save(self, device: Device) -> Device:
        # Implementation similar to above
        return device

    def find_by_id(self, device_id: str) -> Optional[Device]:
        return None

    def find_shared_devices(self, min_users: int = 2) -> List[tuple[Device, int]]:
        return []


class Neo4jIPAddressRepository(IIPAddressRepository):
    def __init__(self):
        self.connection = Neo4jConnection()

    def save(self, ip: IPAddress) -> IPAddress:
        return ip

    def find_by_address(self, ip_address: str) -> Optional[IPAddress]:
        return None

    def find_high_risk_ips(self, threshold: float = 0.7) -> List[IPAddress]:
        return []


class Neo4jMerchantRepository(IMerchantRepository):
    def __init__(self):
        self.connection = Neo4jConnection()

    def save(self, merchant: Merchant) -> Merchant:
        return merchant

    def find_by_id(self, merchant_id: str) -> Optional[Merchant]:
        return None

    def find_by_name(self, name: str) -> List[Merchant]:
        return []


class Neo4jFraudRingRepository(IFraudRingRepository):
    def __init__(self):
        self.connection = Neo4jConnection()

    def save(self, fraud_ring: FraudRing) -> FraudRing:
        return fraud_ring

    def find_by_id(self, ring_id: str) -> Optional[FraudRing]:
        return None

    def find_active_rings(self) -> List[FraudRing]:
        return []

    def link_customer_to_ring(self, ring_id: str, customer_id: str, role: str) -> None:
        pass

    def link_account_to_ring(self, ring_id: str, account_id: str, role: str) -> None:
        pass


class Neo4jAlertRepository(IAlertRepository):
    def __init__(self):
        self.connection = Neo4jConnection()

    def save(self, alert: Alert) -> Alert:
        return alert

    def find_by_id(self, alert_id: str) -> Optional[Alert]:
        return None

    def find_unresolved_alerts(self) -> List[Alert]:
        return []

    def find_by_severity(self, severity: str) -> List[Alert]:
        return []

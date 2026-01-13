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

            # Create relationships to accounts
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

            # Create relationship to merchant
            if transaction.merchant_id:
                session.run("""
                    MATCH (t:Transaction {transaction_id: $transaction_id})
                    MATCH (m:Merchant {merchant_id: $merchant_id})
                    MERGE (t)-[:SENT_TO {timestamp: t.timestamp}]->(m)
                """, transaction_id=transaction.transaction_id,
                           merchant_id=transaction.merchant_id)

            # Create relationship to device
            if transaction.device_id:
                session.run("""
                    MATCH (t:Transaction {transaction_id: $transaction_id})
                    MATCH (d:Device {device_id: $device_id})
                    MERGE (t)-[:FROM_DEVICE {timestamp: t.timestamp}]->(d)
                    SET d.last_seen = t.timestamp
                """, transaction_id=transaction.transaction_id,
                           device_id=transaction.device_id)

            # Create relationship to IP address
            if transaction.ip_address:
                session.run("""
                    MATCH (t:Transaction {transaction_id: $transaction_id})
                    MATCH (ip:IPAddress {ip_address: $ip_address})
                    MERGE (t)-[:FROM_IP {timestamp: t.timestamp}]->(ip)
                    SET ip.last_seen = t.timestamp
                """, transaction_id=transaction.transaction_id,
                           ip_address=transaction.ip_address)

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
    """Neo4j implementation of Device repository"""

    def __init__(self):
        self.connection = Neo4jConnection()

    def save(self, device: Device) -> Device:
        """Save a device to Neo4j"""
        with self.connection.get_session() as session:
            query = """
            MERGE (d:Device {device_id: $device_id})
            SET d.device_type = $device_type,
                d.os = $os,
                d.browser = $browser,
                d.first_seen = datetime($first_seen),
                d.last_seen = datetime($last_seen),
                d.is_trusted = $is_trusted
            RETURN d
            """
            params = {
                'device_id': device.device_id,
                'device_type': device.device_type,
                'os': device.os,
                'browser': device.browser,
                'first_seen': device.first_seen.isoformat(),
                'last_seen': device.last_seen.isoformat(),
                'is_trusted': device.is_trusted
            }
            session.run(query, **params)
            return device

    def find_by_id(self, device_id: str) -> Optional[Device]:
        """Find device by ID"""
        with self.connection.get_session() as session:
            query = "MATCH (d:Device {device_id: $device_id}) RETURN d"
            result = session.run(query, device_id=device_id)
            record = result.single()
            if record:
                return self._node_to_device(record['d'])
            return None

    def find_shared_devices(self, min_users: int = 2) -> List[tuple[Device, int]]:
        """Find devices shared by multiple users (customers)"""
        with self.connection.get_session() as session:
            query = """
            MATCH (c:Customer)-[:USED_DEVICE]->(d:Device)
            WITH d, count(DISTINCT c) as user_count
            WHERE user_count >= $min_users
            RETURN d, user_count
            ORDER BY user_count DESC
            """
            result = session.run(query, min_users=min_users)
            shared_devices = []
            for record in result:
                device = self._node_to_device(record['d'])
                user_count = record['user_count']
                shared_devices.append((device, user_count))
            return shared_devices

    def _node_to_device(self, node) -> Device:
        """Convert Neo4j node to Device entity"""
        data = dict(node)
        # Convert datetime objects
        for field in ['first_seen', 'last_seen']:
            if field in data and hasattr(data[field], 'to_native'):
                data[field] = data[field].to_native()
        return Device(**data)


class Neo4jIPAddressRepository(IIPAddressRepository):
    """Neo4j implementation of IP Address repository"""

    def __init__(self):
        self.connection = Neo4jConnection()

    def save(self, ip: IPAddress) -> IPAddress:
        """Save an IP address to Neo4j"""
        with self.connection.get_session() as session:
            query = """
            MERGE (ip:IPAddress {ip_address: $ip_address})
            SET ip.country = $country,
                ip.city = $city,
                ip.is_proxy = $is_proxy,
                ip.is_vpn = $is_vpn,
                ip.risk_score = $risk_score,
                ip.first_seen = datetime($first_seen),
                ip.last_seen = datetime($last_seen)
            RETURN ip
            """
            params = {
                'ip_address': ip.ip_address,
                'country': ip.country,
                'city': ip.city,
                'is_proxy': ip.is_proxy,
                'is_vpn': ip.is_vpn,
                'risk_score': ip.risk_score,
                'first_seen': ip.first_seen.isoformat(),
                'last_seen': ip.last_seen.isoformat()
            }
            session.run(query, **params)
            return ip

    def find_by_address(self, ip_address: str) -> Optional[IPAddress]:
        """Find IP address by IP address string"""
        with self.connection.get_session() as session:
            query = "MATCH (ip:IPAddress {ip_address: $ip_address}) RETURN ip"
            result = session.run(query, ip_address=ip_address)
            record = result.single()
            if record:
                return self._node_to_ip_address(record['ip'])
            return None

    def find_high_risk_ips(self, threshold: float = 0.7) -> List[IPAddress]:
        """Find IP addresses with risk score above threshold"""
        with self.connection.get_session() as session:
            query = """
            MATCH (ip:IPAddress)
            WHERE ip.risk_score >= $threshold
            RETURN ip
            ORDER BY ip.risk_score DESC
            """
            result = session.run(query, threshold=threshold)
            return [self._node_to_ip_address(record['ip']) for record in result]

    def _node_to_ip_address(self, node) -> IPAddress:
        """Convert Neo4j node to IPAddress entity"""
        data = dict(node)
        # Convert datetime objects
        for field in ['first_seen', 'last_seen']:
            if field in data and hasattr(data[field], 'to_native'):
                data[field] = data[field].to_native()
        return IPAddress(**data)


class Neo4jMerchantRepository(IMerchantRepository):
    """Neo4j implementation of Merchant repository"""

    def __init__(self):
        self.connection = Neo4jConnection()

    def save(self, merchant: Merchant) -> Merchant:
        """Save a merchant to Neo4j"""
        with self.connection.get_session() as session:
            query = """
            MERGE (m:Merchant {merchant_id: $merchant_id})
            SET m.merchant_name = $merchant_name,
                m.category = $category,
                m.country = $country,
                m.risk_level = $risk_level,
                m.is_verified = $is_verified
            RETURN m
            """
            params = {
                'merchant_id': merchant.merchant_id,
                'merchant_name': merchant.merchant_name,
                'category': merchant.category,
                'country': merchant.country,
                'risk_level': merchant.risk_level,
                'is_verified': merchant.is_verified
            }
            session.run(query, **params)
            return merchant

    def find_by_id(self, merchant_id: str) -> Optional[Merchant]:
        """Find merchant by ID"""
        with self.connection.get_session() as session:
            query = "MATCH (m:Merchant {merchant_id: $merchant_id}) RETURN m"
            result = session.run(query, merchant_id=merchant_id)
            record = result.single()
            if record:
                return self._node_to_merchant(record['m'])
            return None

    def find_by_name(self, name: str) -> List[Merchant]:
        """Find merchants by name (case-insensitive partial match)"""
        with self.connection.get_session() as session:
            query = """
            MATCH (m:Merchant)
            WHERE toLower(m.merchant_name) CONTAINS toLower($name)
            RETURN m
            ORDER BY m.merchant_name
            """
            result = session.run(query, name=name)
            return [self._node_to_merchant(record['m']) for record in result]

    def _node_to_merchant(self, node) -> Merchant:
        """Convert Neo4j node to Merchant entity"""
        data = dict(node)
        return Merchant(**data)


class Neo4jFraudRingRepository(IFraudRingRepository):
    """Neo4j implementation of Fraud Ring repository"""

    def __init__(self):
        self.connection = Neo4jConnection()

    def save(self, fraud_ring: FraudRing) -> FraudRing:
        """Save a fraud ring to Neo4j"""
        with self.connection.get_session() as session:
            query = """
            MERGE (r:FraudRing {ring_id: $ring_id})
            SET r.detected_date = datetime($detected_date),
                r.confidence_score = $confidence_score,
                r.status = $status,
                r.total_amount = $total_amount,
                r.member_count = $member_count,
                r.pattern_type = $pattern_type,
                r.description = $description
            RETURN r
            """
            params = {
                'ring_id': fraud_ring.ring_id,
                'detected_date': fraud_ring.detected_date.isoformat(),
                'confidence_score': fraud_ring.confidence_score,
                'status': fraud_ring.status,
                'total_amount': fraud_ring.total_amount,
                'member_count': fraud_ring.member_count,
                'pattern_type': fraud_ring.pattern_type,
                'description': fraud_ring.description
            }
            session.run(query, **params)
            return fraud_ring

    def find_by_id(self, ring_id: str) -> Optional[FraudRing]:
        """Find fraud ring by ID"""
        with self.connection.get_session() as session:
            query = "MATCH (r:FraudRing {ring_id: $ring_id}) RETURN r"
            result = session.run(query, ring_id=ring_id)
            record = result.single()
            if record:
                return self._node_to_fraud_ring(record['r'])
            return None

    def find_active_rings(self) -> List[FraudRing]:
        """Find all active fraud rings under investigation"""
        with self.connection.get_session() as session:
            query = """
            MATCH (r:FraudRing)
            WHERE r.status IN ['investigating', 'confirmed']
            RETURN r
            ORDER BY r.detected_date DESC
            """
            result = session.run(query)
            return [self._node_to_fraud_ring(record['r']) for record in result]

    def link_customer_to_ring(self, ring_id: str, customer_id: str, role: str) -> None:
        """Link a customer to a fraud ring"""
        with self.connection.get_session() as session:
            query = """
            MATCH (c:Customer {customer_id: $customer_id})
            MATCH (r:FraudRing {ring_id: $ring_id})
            MERGE (c)-[rel:MEMBER_OF]->(r)
            SET rel.role = $role,
                rel.joined_date = coalesce(rel.joined_date, datetime())
            WITH r
            MATCH (r)<-[:MEMBER_OF]-(member:Customer)
            SET r.member_count = count(DISTINCT member)
            """
            session.run(query, customer_id=customer_id, ring_id=ring_id, role=role)

    def link_account_to_ring(self, ring_id: str, account_id: str, role: str) -> None:
        """Link an account to a fraud ring"""
        with self.connection.get_session() as session:
            query = """
            MATCH (a:Account {account_id: $account_id})
            MATCH (r:FraudRing {ring_id: $ring_id})
            MERGE (a)-[rel:USED_IN]->(r)
            SET rel.role = $role,
                rel.linked_date = coalesce(rel.linked_date, datetime())
            """
            session.run(query, account_id=account_id, ring_id=ring_id, role=role)

    def _node_to_fraud_ring(self, node) -> FraudRing:
        """Convert Neo4j node to FraudRing entity"""
        data = dict(node)
        # Convert datetime objects
        if 'detected_date' in data and hasattr(data['detected_date'], 'to_native'):
            data['detected_date'] = data['detected_date'].to_native()
        return FraudRing(**data)


class Neo4jAlertRepository(IAlertRepository):
    """Neo4j implementation of Alert repository"""

    def __init__(self):
        self.connection = Neo4jConnection()

    def save(self, alert: Alert) -> Alert:
        """Save an alert to Neo4j"""
        with self.connection.get_session() as session:
            query = """
            MERGE (a:Alert {alert_id: $alert_id})
            SET a.alert_type = $alert_type,
                a.severity = $severity,
                a.created_at = datetime($created_at),
                a.resolved_at = CASE WHEN $resolved_at IS NOT NULL THEN datetime($resolved_at) ELSE null END,
                a.is_resolved = $is_resolved,
                a.assigned_to = $assigned_to,
                a.notes = $notes,
                a.related_entities = $related_entities
            RETURN a
            """
            params = {
                'alert_id': alert.alert_id,
                'alert_type': alert.alert_type,
                'severity': alert.severity,
                'created_at': alert.created_at.isoformat(),
                'resolved_at': alert.resolved_at.isoformat() if alert.resolved_at else None,
                'is_resolved': alert.is_resolved,
                'assigned_to': alert.assigned_to,
                'notes': alert.notes,
                'related_entities': alert.related_entities
            }
            session.run(query, **params)
            return alert

    def find_by_id(self, alert_id: str) -> Optional[Alert]:
        """Find alert by ID"""
        with self.connection.get_session() as session:
            query = "MATCH (a:Alert {alert_id: $alert_id}) RETURN a"
            result = session.run(query, alert_id=alert_id)
            record = result.single()
            if record:
                return self._node_to_alert(record['a'])
            return None

    def find_unresolved_alerts(self) -> List[Alert]:
        """Find all unresolved alerts"""
        with self.connection.get_session() as session:
            query = """
            MATCH (a:Alert)
            WHERE a.is_resolved = false
            RETURN a
            ORDER BY a.created_at DESC
            """
            result = session.run(query)
            return [self._node_to_alert(record['a']) for record in result]

    def find_by_severity(self, severity: str) -> List[Alert]:
        """Find alerts by severity level"""
        with self.connection.get_session() as session:
            query = """
            MATCH (a:Alert)
            WHERE a.severity = $severity
            RETURN a
            ORDER BY a.created_at DESC
            """
            result = session.run(query, severity=severity)
            return [self._node_to_alert(record['a']) for record in result]

    def _node_to_alert(self, node) -> Alert:
        """Convert Neo4j node to Alert entity"""
        data = dict(node)
        # Convert datetime objects
        for field in ['created_at', 'resolved_at']:
            if field in data and data[field] is not None and hasattr(data[field], 'to_native'):
                data[field] = data[field].to_native()
        # Ensure related_entities is a list
        if 'related_entities' in data and data['related_entities'] is None:
            data['related_entities'] = []
        return Alert(**data)

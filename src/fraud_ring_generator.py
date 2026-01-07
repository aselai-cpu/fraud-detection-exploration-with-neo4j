"""
Fraud Ring Data Generator
Generates sophisticated fraud ring patterns with coordinated actors,
shared infrastructure, and organized fraud schemes.
"""

import random
from datetime import datetime, timedelta
from typing import List, Dict, Set, Tuple
from faker import Faker
import hashlib

from .domain.entities import (
    Account, Customer, Transaction, Device, IPAddress, Merchant,
    AccountType, AccountStatus, RiskLevel, KYCStatus,
    TransactionType, TransactionStatus, TransactionChannel
)
from .infrastructure.neo4j_repositories import (
    Neo4jAccountRepository, Neo4jCustomerRepository,
    Neo4jTransactionRepository
)
from .infrastructure.neo4j_connection import Neo4jConnection


class FraudRing:
    """Represents a coordinated fraud ring"""

    def __init__(self, ring_id: str, ring_type: str):
        self.ring_id = ring_id
        self.ring_type = ring_type  # e.g., 'money_mule', 'synthetic_id', 'account_takeover'
        self.members: List[Customer] = []
        self.accounts: List[Account] = []
        self.shared_devices: List[Device] = []
        self.shared_ips: List[str] = []
        self.created_date = datetime.now()


class FraudRingGenerator:
    """Generates sophisticated fraud ring networks"""

    def __init__(self):
        self.faker = Faker()
        self.account_repo = Neo4jAccountRepository()
        self.customer_repo = Neo4jCustomerRepository()
        self.transaction_repo = Neo4jTransactionRepository()
        self.connection = Neo4jConnection()

        # Track created entities
        self.fraud_rings: List[FraudRing] = []
        self.legitimate_customers: List[Customer] = []
        self.legitimate_accounts: List[Account] = []
        self.merchants: List[Merchant] = []
        self.devices: List[Device] = []

    def generate_fraud_ring_dataset(self,
                                   num_rings: int = 5,
                                   num_legitimate_customers: int = 50):
        """Generate complete dataset with fraud rings and legitimate customers"""

        print(f"\n=== Fraud Ring Data Generator ===\n")

        # Generate supporting entities
        print(f"Generating {num_legitimate_customers} legitimate customers...")
        self._generate_legitimate_customers(num_legitimate_customers)

        print(f"Generating merchants...")
        self._generate_merchants(15)

        print(f"Generating devices...")
        self._generate_devices(30)

        # Generate fraud rings
        print(f"\nGenerating {num_rings} fraud rings...")
        self._generate_money_mule_ring()
        self._generate_synthetic_identity_ring()
        self._generate_account_takeover_ring()
        self._generate_bust_out_ring()
        self._generate_layering_ring()

        # Create transactions
        print(f"\nGenerating legitimate transactions...")
        self._generate_legitimate_transactions(200)

        print(f"Generating fraud ring transactions...")
        self._generate_fraud_ring_transactions()

        # Create relationships
        print(f"Creating fraud ring relationships...")
        self._create_fraud_ring_relationships()

        print("\n=== Fraud Ring Generation Complete ===")
        self._print_summary()

    def _generate_legitimate_customers(self, count: int):
        """Generate legitimate customers for contrast"""
        for _ in range(count):
            customer = Customer(
                first_name=self.faker.first_name(),
                last_name=self.faker.last_name(),
                email=self.faker.email(),
                phone=self.faker.phone_number(),
                date_of_birth=self.faker.date_of_birth(minimum_age=18, maximum_age=80),
                ssn_hash=hashlib.sha256(self.faker.ssn().encode()).hexdigest(),
                address=self.faker.street_address(),
                city=self.faker.city(),
                country=self.faker.country(),
                customer_since=self.faker.date_time_between(start_date='-5y', end_date='-1y'),
                kyc_status=KYCStatus.VERIFIED,
                risk_level=RiskLevel.LOW
            )
            saved_customer = self.customer_repo.save(customer)
            self.legitimate_customers.append(saved_customer)

            # Create 1-2 accounts per customer
            num_accounts = random.randint(1, 2)
            for _ in range(num_accounts):
                account = Account(
                    account_number=self.faker.bban(),
                    account_type=random.choice([AccountType.CHECKING, AccountType.SAVINGS]),
                    status=AccountStatus.ACTIVE,
                    created_date=customer.customer_since + timedelta(days=random.randint(0, 180)),
                    country=customer.country,
                    balance=random.uniform(1000, 50000)
                )
                saved_account = self.account_repo.save(account)
                self.legitimate_accounts.append(saved_account)
                self._create_ownership(customer.customer_id, account.account_id)

    def _generate_merchants(self, count: int):
        """Generate merchant records"""
        categories = ['retail', 'restaurant', 'online', 'gambling', 'crypto', 'travel']
        for _ in range(count):
            self.merchants.append(Merchant(
                merchant_name=self.faker.company(),
                category=random.choice(categories),
                country=self.faker.country(),
                risk_level=random.choices(
                    [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH],
                    weights=[0.7, 0.2, 0.1]
                )[0],
                is_verified=random.choice([True, True, False])
            ))

    def _generate_devices(self, count: int):
        """Generate device records"""
        device_types = ['mobile', 'desktop', 'tablet']
        oses = ['iOS', 'Android', 'Windows', 'MacOS']
        browsers = ['Chrome', 'Safari', 'Firefox', 'Edge']

        for _ in range(count):
            self.devices.append(Device(
                device_type=random.choice(device_types),
                os=random.choice(oses),
                browser=random.choice(browsers),
                first_seen=self.faker.date_time_between(start_date='-2y', end_date='now'),
                is_trusted=True
            ))

    def _generate_money_mule_ring(self):
        """Generate a money mule fraud ring"""
        ring = FraudRing(ring_id=f"ring_{len(self.fraud_rings) + 1}",
                        ring_type="money_mule")

        print(f"  Creating money mule ring...")

        # Create ring leader (recruiter)
        leader = self._create_synthetic_customer(
            "Michael", "Rodriguez",
            kyc_status=KYCStatus.VERIFIED,
            risk_level=RiskLevel.CRITICAL
        )
        ring.members.append(leader)

        # Create 5-8 mule accounts (often vulnerable individuals)
        num_mules = random.randint(5, 8)
        for i in range(num_mules):
            # Mules often have similar characteristics
            mule = self._create_synthetic_customer(
                self.faker.first_name(),
                self.faker.last_name(),
                kyc_status=random.choice([KYCStatus.VERIFIED, KYCStatus.PENDING]),
                risk_level=RiskLevel.HIGH,
                customer_since_days=random.randint(30, 180)  # Newer accounts
            )
            ring.members.append(mule)

            # Each mule has 1-2 accounts
            for _ in range(random.randint(1, 2)):
                account = self._create_account(mule, AccountStatus.ACTIVE)
                ring.accounts.append(account)

        # Shared infrastructure (mules recruited from same location)
        ring.shared_devices = random.sample(self.devices, 3)
        ring.shared_ips = [self.faker.ipv4() for _ in range(2)]

        self.fraud_rings.append(ring)

    def _generate_synthetic_identity_ring(self):
        """Generate synthetic identity fraud ring"""
        ring = FraudRing(ring_id=f"ring_{len(self.fraud_rings) + 1}",
                        ring_type="synthetic_identity")

        print(f"  Creating synthetic identity ring...")

        # Create 4-6 synthetic identities (mixed real/fake info)
        num_synthetic = random.randint(4, 6)

        # Use similar addresses (same building/area)
        base_address = self.faker.street_address()
        base_city = self.faker.city()

        for i in range(num_synthetic):
            # Synthetic IDs often have similar patterns
            synthetic = Customer(
                first_name=self.faker.first_name(),
                last_name=self.faker.last_name(),
                email=f"{self.faker.user_name()}{random.randint(100,999)}@{random.choice(['gmail.com', 'yahoo.com', 'outlook.com'])}",
                phone=self.faker.phone_number(),
                date_of_birth=self.faker.date_of_birth(minimum_age=18, maximum_age=35),  # Younger
                ssn_hash=hashlib.sha256(f"SYNTHETIC_{i}_{random.randint(1000,9999)}".encode()).hexdigest(),
                address=f"{base_address} Apt {chr(65+i)}",  # Same building, different units
                city=base_city,
                country="United States",
                customer_since=datetime.now() - timedelta(days=random.randint(60, 365)),
                kyc_status=KYCStatus.PENDING,  # Often stuck in pending
                risk_level=RiskLevel.HIGH
            )
            saved = self.customer_repo.save(synthetic)
            ring.members.append(saved)

            # Multiple accounts per synthetic identity
            for _ in range(random.randint(2, 4)):
                account = self._create_account(saved, AccountStatus.ACTIVE)
                ring.accounts.append(account)

        # Same device used for all applications
        ring.shared_devices = [random.choice(self.devices)]
        ring.shared_ips = [self.faker.ipv4()]  # Same IP for all applications

        self.fraud_rings.append(ring)

    def _generate_account_takeover_ring(self):
        """Generate account takeover fraud ring"""
        ring = FraudRing(ring_id=f"ring_{len(self.fraud_rings) + 1}",
                        ring_type="account_takeover")

        print(f"  Creating account takeover ring...")

        # Select 3-5 legitimate customers whose accounts will be "taken over"
        victims = random.sample(self.legitimate_customers, min(5, len(self.legitimate_customers)))

        # Create fraudster profile
        fraudster = self._create_synthetic_customer(
            "Alex", "Chen",
            kyc_status=KYCStatus.FAILED,
            risk_level=RiskLevel.CRITICAL
        )
        ring.members.append(fraudster)

        # Fraudster uses new device to access victim accounts
        takeover_device = Device(
            device_type='desktop',
            os='Windows',
            browser='Chrome',
            first_seen=datetime.now() - timedelta(days=7),
            is_trusted=False
        )
        ring.shared_devices = [takeover_device]

        # Same IP for all takeover attempts
        ring.shared_ips = [self.faker.ipv4()]

        # Mark victim accounts (we'll create suspicious transactions later)
        for victim in victims:
            # Get victim's accounts
            victim_accounts = [acc for acc in self.legitimate_accounts
                             if self._is_owned_by(acc, victim)]
            ring.accounts.extend(victim_accounts[:1])  # Take one account per victim

        self.fraud_rings.append(ring)

    def _generate_bust_out_ring(self):
        """Generate bust-out fraud ring (credit abuse)"""
        ring = FraudRing(ring_id=f"ring_{len(self.fraud_rings) + 1}",
                        ring_type="bust_out")

        print(f"  Creating bust-out fraud ring...")

        # Create 3-4 customers who will max out credit then disappear
        num_members = random.randint(3, 4)

        for i in range(num_members):
            member = self._create_synthetic_customer(
                self.faker.first_name(),
                self.faker.last_name(),
                kyc_status=KYCStatus.VERIFIED,  # Initially legitimate-looking
                risk_level=RiskLevel.MEDIUM,
                customer_since_days=random.randint(365, 1095)  # Older accounts (built credit)
            )
            ring.members.append(member)

            # Credit accounts
            credit_account = Account(
                account_number=self.faker.bban(),
                account_type=AccountType.CREDIT,
                status=AccountStatus.ACTIVE,
                created_date=member.customer_since + timedelta(days=30),
                country=member.country,
                balance=-random.uniform(15000, 50000),  # Maxed out negative balance
                credit_limit=50000.0
            )
            saved_account = self.account_repo.save(credit_account)
            ring.accounts.append(saved_account)
            self._create_ownership(member.customer_id, credit_account.account_id)

        # Coordinated from same location
        ring.shared_devices = random.sample(self.devices, 2)
        ring.shared_ips = [self.faker.ipv4()]

        self.fraud_rings.append(ring)

    def _generate_layering_ring(self):
        """Generate layering fraud ring (complex money movement)"""
        ring = FraudRing(ring_id=f"ring_{len(self.fraud_rings) + 1}",
                        ring_type="layering")

        print(f"  Creating layering/structuring ring...")

        # Create 6-10 accounts for layering money
        num_layers = random.randint(6, 10)

        for i in range(num_layers):
            member = self._create_synthetic_customer(
                self.faker.first_name(),
                self.faker.last_name(),
                kyc_status=random.choice([KYCStatus.VERIFIED, KYCStatus.PENDING]),
                risk_level=RiskLevel.HIGH
            )
            ring.members.append(member)

            # Multiple accounts per member for complex layering
            for _ in range(random.randint(1, 3)):
                account = self._create_account(member, AccountStatus.ACTIVE)
                ring.accounts.append(account)

        # Controlled from central location
        ring.shared_devices = [random.choice(self.devices)]
        ring.shared_ips = [self.faker.ipv4()]

        self.fraud_rings.append(ring)

    def _generate_fraud_ring_transactions(self):
        """Generate transactions for each fraud ring"""

        for ring in self.fraud_rings:
            if ring.ring_type == "money_mule":
                self._generate_money_mule_transactions(ring)
            elif ring.ring_type == "synthetic_identity":
                self._generate_synthetic_id_transactions(ring)
            elif ring.ring_type == "account_takeover":
                self._generate_takeover_transactions(ring)
            elif ring.ring_type == "bust_out":
                self._generate_bust_out_transactions(ring)
            elif ring.ring_type == "layering":
                self._generate_layering_transactions(ring)

    def _generate_money_mule_transactions(self, ring: FraudRing):
        """Generate money mule pattern: receive -> hold briefly -> forward"""

        if len(ring.accounts) < 2:
            return

        base_time = datetime.now() - timedelta(days=random.randint(1, 30))

        # Pattern: External source -> Mule 1 -> Mule 2 -> ... -> Final destination
        for i in range(len(ring.accounts) - 1):
            from_account = ring.accounts[i]
            to_account = ring.accounts[i + 1]

            # Money arrives
            amount = random.uniform(8000, 25000)

            transaction = Transaction(
                amount=amount,
                timestamp=base_time + timedelta(hours=i * 4),
                transaction_type=TransactionType.TRANSFER,
                channel=TransactionChannel.ONLINE,
                description="Payment received",
                from_account_id=from_account.account_id,
                to_account_id=to_account.account_id,
                device_id=ring.shared_devices[0].device_id if ring.shared_devices else None,
                ip_address=ring.shared_ips[0] if ring.shared_ips else self.faker.ipv4(),
                is_flagged=True,
                fraud_score=random.uniform(0.75, 0.95)
            )
            self.transaction_repo.save(transaction)

    def _generate_synthetic_id_transactions(self, ring: FraudRing):
        """Generate synthetic identity pattern: build credit then bust out"""

        base_time = datetime.now() - timedelta(days=random.randint(30, 90))

        for account in ring.accounts:
            # Small legitimate-looking transactions first (building trust)
            for i in range(5):
                if self.legitimate_accounts:
                    legitimate_target = random.choice(self.legitimate_accounts)
                    transaction = Transaction(
                        amount=random.uniform(50, 500),
                        timestamp=base_time + timedelta(days=i * 7),
                        transaction_type=TransactionType.PAYMENT,
                        channel=TransactionChannel.ONLINE,
                        description="Purchase",
                        from_account_id=account.account_id,
                        to_account_id=legitimate_target.account_id,
                        merchant_id=random.choice(self.merchants).merchant_id if self.merchants else None,
                        device_id=ring.shared_devices[0].device_id if ring.shared_devices else None,
                        ip_address=ring.shared_ips[0] if ring.shared_ips else self.faker.ipv4(),
                        is_flagged=False,
                        fraud_score=random.uniform(0.3, 0.5)
                    )
                    self.transaction_repo.save(transaction)

            # Then sudden large fraudulent transactions
            for i in range(3):
                if self.legitimate_accounts:
                    target = random.choice(self.legitimate_accounts)
                    transaction = Transaction(
                        amount=random.uniform(5000, 15000),
                        timestamp=base_time + timedelta(days=45 + i),
                        transaction_type=TransactionType.WITHDRAWAL,
                        channel=TransactionChannel.ATM,
                        description="Cash withdrawal",
                        from_account_id=account.account_id,
                        to_account_id=target.account_id,
                        device_id=ring.shared_devices[0].device_id if ring.shared_devices else None,
                        ip_address=ring.shared_ips[0] if ring.shared_ips else self.faker.ipv4(),
                        is_flagged=True,
                        fraud_score=random.uniform(0.8, 0.98)
                    )
                    self.transaction_repo.save(transaction)

    def _generate_takeover_transactions(self, ring: FraudRing):
        """Generate account takeover pattern: sudden unusual activity"""

        takeover_time = datetime.now() - timedelta(days=random.randint(1, 7))

        for account in ring.accounts:
            # Multiple rapid transactions from new location/device
            for i in range(random.randint(5, 12)):
                if self.legitimate_accounts:
                    target = random.choice(self.legitimate_accounts)
                    transaction = Transaction(
                        amount=random.uniform(2000, 9000),
                        timestamp=takeover_time + timedelta(minutes=i * 15),
                        transaction_type=TransactionType.TRANSFER,
                        channel=TransactionChannel.ONLINE,
                        description="Transfer to new recipient",
                        from_account_id=account.account_id,
                        to_account_id=target.account_id,
                        device_id=ring.shared_devices[0].device_id if ring.shared_devices else None,
                        ip_address=ring.shared_ips[0] if ring.shared_ips else self.faker.ipv4(),
                        is_flagged=True,
                        fraud_score=random.uniform(0.85, 0.99)
                    )
                    self.transaction_repo.save(transaction)

    def _generate_bust_out_transactions(self, ring: FraudRing):
        """Generate bust-out pattern: max out credit in coordinated manner"""

        bust_out_time = datetime.now() - timedelta(days=random.randint(1, 3))

        for account in ring.accounts:
            # Rapid maxing out of credit
            remaining_credit = abs(account.balance) if account.balance else 10000
            num_transactions = random.randint(8, 15)

            for i in range(num_transactions):
                amount = remaining_credit / num_transactions
                if self.merchants:
                    merchant = random.choice(self.merchants)
                    transaction = Transaction(
                        amount=amount,
                        timestamp=bust_out_time + timedelta(hours=i * 2),
                        transaction_type=TransactionType.PAYMENT,
                        channel=TransactionChannel.ONLINE,
                        description=f"Purchase at {merchant.merchant_name}",
                        from_account_id=account.account_id,
                        to_account_id=None,
                        merchant_id=merchant.merchant_id,
                        device_id=ring.shared_devices[0].device_id if ring.shared_devices else None,
                        ip_address=ring.shared_ips[0] if ring.shared_ips else self.faker.ipv4(),
                        is_flagged=True,
                        fraud_score=random.uniform(0.7, 0.92)
                    )
                    self.transaction_repo.save(transaction)

    def _generate_layering_transactions(self, ring: FraudRing):
        """Generate complex layering pattern with multiple hops"""

        base_time = datetime.now() - timedelta(days=random.randint(7, 30))

        # Create complex multi-hop transactions
        num_layers = min(len(ring.accounts), 8)
        layer_accounts = random.sample(ring.accounts, num_layers)

        base_amount = random.uniform(50000, 200000)

        # Money flows through multiple layers
        for i in range(num_layers - 1):
            from_acc = layer_accounts[i]
            to_acc = layer_accounts[i + 1]

            # Amount decreases slightly each hop (fees/withdrawal)
            amount = base_amount * (0.85 ** i) * random.uniform(0.95, 1.0)

            transaction = Transaction(
                amount=amount,
                timestamp=base_time + timedelta(hours=i * 6, minutes=random.randint(0, 60)),
                transaction_type=TransactionType.TRANSFER,
                channel=TransactionChannel.ONLINE,
                description=random.choice(["Transfer", "Payment", "Settlement", "Wire transfer"]),
                from_account_id=from_acc.account_id,
                to_account_id=to_acc.account_id,
                device_id=ring.shared_devices[0].device_id if ring.shared_devices else None,
                ip_address=ring.shared_ips[0] if ring.shared_ips else self.faker.ipv4(),
                is_flagged=True,
                fraud_score=random.uniform(0.65, 0.88)
            )
            self.transaction_repo.save(transaction)

    def _generate_legitimate_transactions(self, count: int):
        """Generate normal transactions for legitimate customers"""

        for _ in range(count):
            if len(self.legitimate_accounts) < 2:
                continue

            from_account = random.choice(self.legitimate_accounts)
            to_account = random.choice([acc for acc in self.legitimate_accounts
                                       if acc.account_id != from_account.account_id])

            transaction = Transaction(
                amount=random.uniform(10, 2000),
                timestamp=self.faker.date_time_between(start_date='-60d', end_date='now'),
                transaction_type=random.choice(list(TransactionType)),
                channel=random.choice(list(TransactionChannel)),
                description=self.faker.sentence(nb_words=4),
                from_account_id=from_account.account_id,
                to_account_id=to_account.account_id,
                merchant_id=random.choice(self.merchants).merchant_id if self.merchants else None,
                device_id=random.choice(self.devices).device_id if self.devices else None,
                ip_address=self.faker.ipv4(),
                is_flagged=False,
                fraud_score=random.uniform(0.0, 0.3)
            )
            self.transaction_repo.save(transaction)

    def _create_fraud_ring_relationships(self):
        """Create explicit fraud ring relationships in Neo4j"""

        with self.connection.get_session() as session:
            for ring in self.fraud_rings:
                # Create FRAUD_RING node
                session.run("""
                    CREATE (r:FraudRing {
                        ring_id: $ring_id,
                        ring_type: $ring_type,
                        created_date: datetime($created_date),
                        num_members: $num_members,
                        num_accounts: $num_accounts,
                        status: 'active'
                    })
                """,
                ring_id=ring.ring_id,
                ring_type=ring.ring_type,
                created_date=ring.created_date.isoformat(),
                num_members=len(ring.members),
                num_accounts=len(ring.accounts))

                # Link members to ring
                for member in ring.members:
                    session.run("""
                        MATCH (c:Customer {customer_id: $customer_id})
                        MATCH (r:FraudRing {ring_id: $ring_id})
                        MERGE (c)-[:MEMBER_OF {
                            joined_date: datetime(),
                            role: $role
                        }]->(r)
                    """,
                    customer_id=member.customer_id,
                    ring_id=ring.ring_id,
                    role='leader' if ring.members.index(member) == 0 else 'member')

                # Link accounts to ring
                for account in ring.accounts:
                    session.run("""
                        MATCH (a:Account {account_id: $account_id})
                        MATCH (r:FraudRing {ring_id: $ring_id})
                        MERGE (a)-[:USED_IN]->(r)
                    """,
                    account_id=account.account_id,
                    ring_id=ring.ring_id)

                # Create shared device relationships
                for device in ring.shared_devices:
                    for member in ring.members:
                        session.run("""
                            MATCH (c:Customer {customer_id: $customer_id})
                            MERGE (d:Device {device_id: $device_id})
                            ON CREATE SET d.device_type = $device_type,
                                        d.os = $os,
                                        d.browser = $browser,
                                        d.first_seen = datetime($first_seen),
                                        d.is_trusted = $is_trusted
                            MERGE (c)-[:USED_DEVICE {
                                first_used: datetime(),
                                shared_with_ring: true
                            }]->(d)
                        """,
                        customer_id=member.customer_id,
                        device_id=device.device_id,
                        device_type=device.device_type,
                        os=device.os,
                        browser=device.browser,
                        first_seen=device.first_seen.isoformat(),
                        is_trusted=device.is_trusted)

    def _create_synthetic_customer(self, first_name: str, last_name: str,
                                  kyc_status: KYCStatus = KYCStatus.VERIFIED,
                                  risk_level: RiskLevel = RiskLevel.HIGH,
                                  customer_since_days: int = 180) -> Customer:
        """Helper to create a customer"""
        customer = Customer(
            first_name=first_name,
            last_name=last_name,
            email=f"{first_name.lower()}.{last_name.lower()}{random.randint(1,999)}@{random.choice(['gmail.com', 'yahoo.com'])}",
            phone=self.faker.phone_number(),
            date_of_birth=self.faker.date_of_birth(minimum_age=18, maximum_age=65),
            ssn_hash=hashlib.sha256(f"{first_name}{last_name}{random.randint(1000,9999)}".encode()).hexdigest(),
            address=self.faker.street_address(),
            city=self.faker.city(),
            country=random.choice(["United States", "Canada", "United Kingdom"]),
            customer_since=datetime.now() - timedelta(days=customer_since_days),
            kyc_status=kyc_status,
            risk_level=risk_level
        )
        return self.customer_repo.save(customer)

    def _create_account(self, customer: Customer, status: AccountStatus) -> Account:
        """Helper to create an account"""
        account = Account(
            account_number=self.faker.bban(),
            account_type=random.choice(list(AccountType)),
            status=status,
            created_date=customer.customer_since + timedelta(days=random.randint(1, 60)),
            country=customer.country,
            balance=random.uniform(100, 10000)
        )
        saved_account = self.account_repo.save(account)
        self._create_ownership(customer.customer_id, account.account_id)
        return saved_account

    def _create_ownership(self, customer_id: str, account_id: str):
        """Create OWNS relationship"""
        with self.connection.get_session() as session:
            session.run("""
                MATCH (c:Customer {customer_id: $customer_id})
                MATCH (a:Account {account_id: $account_id})
                MERGE (c)-[:OWNS {
                    since_date: datetime(),
                    relationship_type: 'primary'
                }]->(a)
            """, customer_id=customer_id, account_id=account_id)

    def _is_owned_by(self, account: Account, customer: Customer) -> bool:
        """Check if account is owned by customer"""
        with self.connection.get_session() as session:
            result = session.run("""
                MATCH (c:Customer {customer_id: $customer_id})-[:OWNS]->(a:Account {account_id: $account_id})
                RETURN count(*) as count
            """, customer_id=customer.customer_id, account_id=account.account_id)
            record = result.single()
            return record and record['count'] > 0

    def _print_summary(self):
        """Print generation summary"""
        print(f"\nTotal Fraud Rings: {len(self.fraud_rings)}")
        for ring in self.fraud_rings:
            print(f"  - {ring.ring_type}: {len(ring.members)} members, {len(ring.accounts)} accounts")
        print(f"\nTotal Legitimate Customers: {len(self.legitimate_customers)}")
        print(f"Total Legitimate Accounts: {len(self.legitimate_accounts)}")
        print(f"Total Merchants: {len(self.merchants)}")
        print(f"Total Devices: {len(self.devices)}")


def main():
    """Main function to run fraud ring generation"""

    generator = FraudRingGenerator()

    # Generate fraud ring dataset
    generator.generate_fraud_ring_dataset(
        num_rings=5,
        num_legitimate_customers=50
    )

    print("\n=== Fraud Ring Data Generation Complete ===")
    print("\nYou can now:")
    print("1. Query Neo4j to explore fraud rings")
    print("2. Run fraud detection algorithms")
    print("3. Investigate connected accounts and customers")
    print("\nExample Cypher query:")
    print("  MATCH (r:FraudRing)<-[:MEMBER_OF]-(c:Customer)")
    print("  RETURN r.ring_type, collect(c.first_name + ' ' + c.last_name) as members")


if __name__ == "__main__":
    main()

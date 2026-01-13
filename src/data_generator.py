"""
Sample Data Generator for Fraud Detection System
Generates realistic banking data with embedded fraud patterns.
"""

import random
from datetime import datetime, timedelta, timezone
from typing import List, Tuple, Dict
from faker import Faker
import hashlib
import sys
import os

# Add parent directory to path to allow imports when running directly
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Use absolute imports for better debugging support
try:
    from src.domain.entities import (
        Account, Customer, Transaction, Device, IPAddress, Merchant,
        AccountType, AccountStatus, RiskLevel, KYCStatus,
        TransactionType, TransactionStatus, TransactionChannel
    )
    from src.infrastructure.neo4j_repositories import (
        Neo4jAccountRepository, Neo4jCustomerRepository,
        Neo4jTransactionRepository, Neo4jDeviceRepository,
        Neo4jMerchantRepository, Neo4jIPAddressRepository
    )
except ImportError:
    # Fallback to relative imports if running as a module
    from .domain.entities import (
        Account, Customer, Transaction, Device, IPAddress, Merchant,
        AccountType, AccountStatus, RiskLevel, KYCStatus,
        TransactionType, TransactionStatus, TransactionChannel
    )
    from .infrastructure.neo4j_repositories import (
        Neo4jAccountRepository, Neo4jCustomerRepository,
        Neo4jTransactionRepository, Neo4jDeviceRepository,
        Neo4jMerchantRepository, Neo4jIPAddressRepository
    )


class FraudDataGenerator:
    """Generates sample data with embedded fraud patterns"""

    def __init__(self, fraud_percentage: float = 0.05):
        self.faker = Faker()
        self.fraud_percentage = fraud_percentage
        self.account_repo = Neo4jAccountRepository()
        self.customer_repo = Neo4jCustomerRepository()
        self.transaction_repo = Neo4jTransactionRepository()
        self.device_repo = Neo4jDeviceRepository()
        self.merchant_repo = Neo4jMerchantRepository()
        self.ip_repo = Neo4jIPAddressRepository()

        # Keep track of created entities
        self.customers: List[Customer] = []
        self.accounts: List[Account] = []
        self.devices: List[Device] = []
        self.merchants: List[Merchant] = []
        self.ip_addresses: Dict[str, IPAddress] = {}  # Track IPs by address string

    def generate_complete_dataset(self, num_customers: int = 100,
                                 num_transactions: int = 1000):
        """Generate complete dataset with customers, accounts, and transactions"""
        print(f"Generating {num_customers} customers...")
        self._generate_customers(num_customers)

        print(f"Generating accounts...")
        self._generate_accounts()

        print(f"Generating merchants...")
        self._generate_merchants(20)

        print(f"Generating devices...")
        self._generate_devices(50)

        print(f"Generating {num_transactions} transactions...")
        self._generate_transactions(num_transactions)

        print(f"Injecting fraud patterns...")
        self._inject_fraud_patterns()

        print("Data generation complete!")

    def _generate_customers(self, count: int):
        """Generate customer records"""
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
                customer_since=self.faker.date_time_between(start_date='-5y', end_date='now'),
                kyc_status=random.choices(
                    [KYCStatus.VERIFIED, KYCStatus.PENDING, KYCStatus.FAILED],
                    weights=[0.85, 0.10, 0.05]
                )[0],
                risk_level=random.choices(
                    [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL],
                    weights=[0.70, 0.20, 0.08, 0.02]
                )[0]
            )
            saved_customer = self.customer_repo.save(customer)
            self.customers.append(saved_customer)

    def _generate_accounts(self):
        """Generate accounts for customers"""
        for customer in self.customers:
            # Each customer has 1-3 accounts
            num_accounts = random.choices([1, 2, 3], weights=[0.6, 0.3, 0.1])[0]

            for _ in range(num_accounts):
                account = Account(
                    account_number=self.faker.bban(),
                    account_type=random.choice(list(AccountType)),
                    status=random.choices(
                        [AccountStatus.ACTIVE, AccountStatus.SUSPENDED, AccountStatus.CLOSED],
                        weights=[0.90, 0.05, 0.05]
                    )[0],
                    created_date=customer.customer_since + timedelta(days=random.randint(0, 365)),
                    country=customer.country,
                    balance=random.uniform(100, 50000)
                )
                saved_account = self.account_repo.save(account)
                self.accounts.append(saved_account)

                # Create OWNS relationship
                self._create_ownership(customer.customer_id, account.account_id)

    def _generate_merchants(self, count: int):
        """Generate merchant records and save to Neo4j"""
        merchant_categories = ['retail', 'restaurant', 'online', 'gambling',
                              'crypto', 'travel', 'entertainment']

        for _ in range(count):
            merchant = Merchant(
                merchant_name=self.faker.company(),
                category=random.choice(merchant_categories),
                country=self.faker.country(),
                risk_level=random.choices(
                    [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH],
                    weights=[0.7, 0.2, 0.1]
                )[0],
                is_verified=random.choice([True, True, True, False])  # 75% verified
            )
            saved_merchant = self.merchant_repo.save(merchant)
            self.merchants.append(saved_merchant)

    def _generate_devices(self, count: int):
        """Generate device records, save to Neo4j, and link to customers"""
        device_types = ['mobile', 'desktop', 'tablet']
        operating_systems = ['iOS', 'Android', 'Windows', 'MacOS', 'Linux']
        browsers = ['Chrome', 'Safari', 'Firefox', 'Edge']

        for _ in range(count):
            device = Device(
                device_type=random.choice(device_types),
                os=random.choice(operating_systems),
                browser=random.choice(browsers),
                first_seen=self.faker.date_time_between(start_date='-2y', end_date='now'),
                last_seen=self.faker.date_time_between(start_date='-30d', end_date='now'),
                is_trusted=random.choice([True, True, True, False])  # 75% trusted
            )
            saved_device = self.device_repo.save(device)
            self.devices.append(saved_device)
            
            # Link device to 1-3 random customers
            num_customers = random.randint(1, min(3, len(self.customers)))
            if self.customers:
                linked_customers = random.sample(self.customers, num_customers)
                for customer in linked_customers:
                    self._link_customer_to_device(customer.customer_id, device.device_id)

    def _generate_transactions(self, count: int):
        """Generate normal transaction patterns"""
        for _ in range(count):
            # Select random accounts
            from_account = random.choice(self.accounts)
            to_account = random.choice([acc for acc in self.accounts
                                       if acc.account_id != from_account.account_id])

            # Select merchant (for payment transactions)
            merchant = None
            if random.random() < 0.4 and self.merchants:  # 40% of transactions have merchants
                merchant = random.choice(self.merchants)

            # Select device (for online/mobile transactions)
            device = None
            if random.random() < 0.6 and self.devices:  # 60% of transactions use devices
                device = random.choice(self.devices)

            # Generate IP address
            ip_address_str = self.faker.ipv4()
            ip_address = self._get_or_create_ip_address(ip_address_str)

            transaction = Transaction(
                amount=self._generate_transaction_amount(),
                timestamp=self.faker.date_time_between(start_date='-90d', end_date='now'),
                transaction_type=random.choice(list(TransactionType)),
                channel=random.choice(list(TransactionChannel)),
                description=self.faker.sentence(nb_words=6),
                from_account_id=from_account.account_id,
                to_account_id=to_account.account_id,
                merchant_id=merchant.merchant_id if merchant else None,
                device_id=device.device_id if device else None,
                ip_address=ip_address_str
            )

            # Save transaction - repository will automatically create all relationships
            self.transaction_repo.save(transaction)

    def _generate_transaction_amount(self) -> float:
        """Generate realistic transaction amounts"""
        # Most transactions are small, some are medium, few are large
        category = random.choices(['small', 'medium', 'large'],
                                 weights=[0.7, 0.25, 0.05])[0]

        if category == 'small':
            return round(random.uniform(10, 500), 2)
        elif category == 'medium':
            return round(random.uniform(500, 5000), 2)
        else:
            return round(random.uniform(5000, 50000), 2)

    def _inject_fraud_patterns(self):
        """Inject various fraud patterns into the data"""
        num_fraud_patterns = int(len(self.accounts) * self.fraud_percentage)

        print(f"  Injecting circular flow patterns...")
        self._inject_circular_flow(num_fraud_patterns // 4)

        print(f"  Injecting fan-out patterns...")
        self._inject_fan_out(num_fraud_patterns // 4)

        print(f"  Injecting fan-in patterns...")
        self._inject_fan_in(num_fraud_patterns // 4)

        print(f"  Injecting velocity patterns...")
        self._inject_velocity_pattern(num_fraud_patterns // 4)

    def _inject_circular_flow(self, count: int):
        """Create circular money flow patterns (A -> B -> C -> A)

        This simulates money laundering where funds move in a circle to obscure origin.
        Multiple rounds of circulation make the pattern more obvious for detection.
        """
        for _ in range(count):
            # Select 3-5 accounts for the circle
            circle_size = random.randint(3, 7)
            circle_accounts = random.sample(self.accounts, circle_size)

            # Use shared device/IP for fraud pattern (suspicious)
            shared_device = random.choice(self.devices) if self.devices else None
            shared_ip = self._get_or_create_ip_address(self.faker.ipv4(), is_suspicious=True)

            base_time = datetime.now(timezone.utc) - timedelta(days=random.randint(1, 7))
            initial_amount = random.uniform(5000, 20000)

            # Create multiple rounds of circulation (2-3 rounds) to make pattern more obvious
            num_rounds = random.randint(2, 3)

            for round_num in range(num_rounds):
                # Each round, money circulates through all accounts
                for i in range(circle_size):
                    from_acc = circle_accounts[i]
                    to_acc = circle_accounts[(i + 1) % circle_size]

                    # Amount decreases slightly each time (transaction fees simulation)
                    round_multiplier = 0.95 ** round_num
                    amount = initial_amount * round_multiplier * random.uniform(0.98, 1.02)

                    # Time progresses with each transaction
                    time_offset = (round_num * circle_size + i) * 2  # 2 hours between each

                    transaction = Transaction(
                        amount=amount,
                        timestamp=base_time + timedelta(hours=time_offset),
                        transaction_type=TransactionType.TRANSFER,
                        channel=TransactionChannel.ONLINE,
                        description=f"Transfer - Round {round_num + 1}",
                        from_account_id=from_acc.account_id,
                        to_account_id=to_acc.account_id,
                        device_id=shared_device.device_id if shared_device else None,
                        ip_address=shared_ip.ip_address,
                        is_flagged=True,
                        fraud_score=random.uniform(0.75, 0.95)
                    )
                    # Save transaction - repository will automatically create all relationships
                    self.transaction_repo.save(transaction)

    def _inject_fan_out(self, count: int):
        """Create fan-out patterns (one account to many)"""
        for _ in range(count):
            source_account = random.choice(self.accounts)
            num_recipients = random.randint(5, 15)
            recipient_accounts = random.sample(
                [acc for acc in self.accounts if acc.account_id != source_account.account_id],
                num_recipients
            )

            # Use same device/IP for all transactions (suspicious pattern)
            shared_device = random.choice(self.devices) if self.devices else None
            shared_ip = self._get_or_create_ip_address(self.faker.ipv4(), is_suspicious=True)

            base_time = datetime.now(timezone.utc) - timedelta(days=random.randint(1, 7))
            base_amount = random.uniform(10000, 50000)

            for i, recipient in enumerate(recipient_accounts):
                transaction = Transaction(
                    amount=base_amount / num_recipients,
                    timestamp=base_time + timedelta(minutes=i * 5),
                    transaction_type=TransactionType.TRANSFER,
                    channel=TransactionChannel.ONLINE,
                    description="Distribution",
                    from_account_id=source_account.account_id,
                    to_account_id=recipient.account_id,
                    device_id=shared_device.device_id if shared_device else None,
                    ip_address=shared_ip.ip_address,
                    is_flagged=True,
                    fraud_score=random.uniform(0.6, 0.9)
                )
                # Save transaction - repository will automatically create all relationships
                self.transaction_repo.save(transaction)

    def _inject_fan_in(self, count: int):
        """Create fan-in patterns (many accounts to one)"""
        for _ in range(count):
            destination_account = random.choice(self.accounts)
            num_senders = random.randint(5, 15)
            sender_accounts = random.sample(
                [acc for acc in self.accounts if acc.account_id != destination_account.account_id],
                num_senders
            )

            # Use high-risk merchant for some transactions
            high_risk_merchant = random.choice([m for m in self.merchants if m.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]]) if self.merchants else None
            if not high_risk_merchant and self.merchants:
                high_risk_merchant = random.choice(self.merchants)

            base_time = datetime.now(timezone.utc) - timedelta(days=random.randint(1, 7))

            for i, sender in enumerate(sender_accounts):
                # Vary devices/IPs slightly but some overlap (suspicious)
                device = random.choice(self.devices) if self.devices and random.random() < 0.7 else None
                ip = self._get_or_create_ip_address(self.faker.ipv4(), is_suspicious=random.random() < 0.5)

                transaction = Transaction(
                    amount=random.uniform(500, 2000),
                    timestamp=base_time + timedelta(minutes=i * 10),
                    transaction_type=TransactionType.TRANSFER,
                    channel=TransactionChannel.ONLINE,
                    description="Collection",
                    from_account_id=sender.account_id,
                    to_account_id=destination_account.account_id,
                    merchant_id=high_risk_merchant.merchant_id if high_risk_merchant and random.random() < 0.3 else None,
                    device_id=device.device_id if device else None,
                    ip_address=ip.ip_address,
                    is_flagged=True,
                    fraud_score=random.uniform(0.6, 0.9)
                )
                # Save transaction - repository will automatically create all relationships
                self.transaction_repo.save(transaction)

    def _inject_velocity_pattern(self, count: int):
        """Create high-velocity transaction patterns"""
        for _ in range(count):
            account = random.choice(self.accounts)
            base_time = datetime.now(timezone.utc) - timedelta(hours=2)

            # Use same device for all rapid transactions (suspicious)
            device = random.choice(self.devices) if self.devices else None
            # Use same or similar IPs (suspicious)
            base_ip = self._get_or_create_ip_address(self.faker.ipv4(), is_suspicious=True)

            # Create 10-20 transactions in quick succession
            num_transactions = random.randint(10, 20)

            for i in range(num_transactions):
                to_account = random.choice([acc for acc in self.accounts
                                           if acc.account_id != account.account_id])

                # Sometimes use same IP, sometimes vary slightly
                ip = base_ip if random.random() < 0.7 else self._get_or_create_ip_address(self.faker.ipv4())

                transaction = Transaction(
                    amount=random.uniform(100, 1000),
                    timestamp=base_time + timedelta(minutes=i * 3),
                    transaction_type=TransactionType.TRANSFER,
                    channel=TransactionChannel.ONLINE,
                    description="Quick transfer",
                    from_account_id=account.account_id,
                    to_account_id=to_account.account_id,
                    device_id=device.device_id if device else None,
                    ip_address=ip.ip_address,
                    is_flagged=True,
                    fraud_score=random.uniform(0.5, 0.8)
                )
                # Save transaction - repository will automatically create all relationships
                self.transaction_repo.save(transaction)

    def _create_ownership(self, customer_id: str, account_id: str):
        """Create OWNS relationship between customer and account"""
        try:
            from src.infrastructure.neo4j_connection import Neo4jConnection
        except ImportError:
            from .infrastructure.neo4j_connection import Neo4jConnection
        connection = Neo4jConnection()

        with connection.get_session() as session:
            session.run("""
                MATCH (c:Customer {customer_id: $customer_id})
                MATCH (a:Account {account_id: $account_id})
                MERGE (c)-[:OWNS {since_date: datetime(), relationship_type: 'primary'}]->(a)
            """, customer_id=customer_id, account_id=account_id)

    def _get_or_create_ip_address(self, ip_address_str: str, is_suspicious: bool = False) -> IPAddress:
        """Get existing IP address or create a new one"""
        if ip_address_str in self.ip_addresses:
            return self.ip_addresses[ip_address_str]
        
        # Create new IP address
        ip_address = IPAddress(
            ip_address=ip_address_str,
            country=self.faker.country(),
            city=self.faker.city(),
            is_proxy=is_suspicious and random.random() < 0.3,  # 30% of suspicious IPs are proxies
            is_vpn=is_suspicious and random.random() < 0.2,  # 20% of suspicious IPs are VPNs
            risk_score=random.uniform(0.6, 0.95) if is_suspicious else random.uniform(0.0, 0.4),
            first_seen=self.faker.date_time_between(start_date='-90d', end_date='now'),
            last_seen=datetime.now(timezone.utc)
        )
        saved_ip = self.ip_repo.save(ip_address)
        self.ip_addresses[ip_address_str] = saved_ip
        return saved_ip

    def _link_customer_to_device(self, customer_id: str, device_id: str):
        """Create USED_DEVICE relationship between customer and device"""
        try:
            from src.infrastructure.neo4j_connection import Neo4jConnection
        except ImportError:
            from .infrastructure.neo4j_connection import Neo4jConnection
        connection = Neo4jConnection()

        with connection.get_session() as session:
            session.run("""
                MATCH (c:Customer {customer_id: $customer_id})
                MATCH (d:Device {device_id: $device_id})
                MERGE (c)-[rel:USED_DEVICE]->(d)
                ON CREATE SET rel.first_used = datetime(),
                             rel.last_used = datetime(),
                             rel.usage_count = 1
                ON MATCH SET rel.last_used = datetime(),
                            rel.usage_count = rel.usage_count + 1
            """, customer_id=customer_id, device_id=device_id)

    def _link_transaction_to_merchant(self, transaction_id: str, merchant_id: str):
        """Create SENT_TO relationship between transaction and merchant"""
        try:
            from src.infrastructure.neo4j_connection import Neo4jConnection
        except ImportError:
            from .infrastructure.neo4j_connection import Neo4jConnection
        connection = Neo4jConnection()

        with connection.get_session() as session:
            session.run("""
                MATCH (t:Transaction {transaction_id: $transaction_id})
                MATCH (m:Merchant {merchant_id: $merchant_id})
                MERGE (t)-[:SENT_TO {timestamp: t.timestamp}]->(m)
            """, transaction_id=transaction_id, merchant_id=merchant_id)

    def _link_transaction_to_device(self, transaction_id: str, device_id: str):
        """Create FROM_DEVICE relationship between transaction and device"""
        try:
            from src.infrastructure.neo4j_connection import Neo4jConnection
        except ImportError:
            from .infrastructure.neo4j_connection import Neo4jConnection
        connection = Neo4jConnection()

        with connection.get_session() as session:
            session.run("""
                MATCH (t:Transaction {transaction_id: $transaction_id})
                MATCH (d:Device {device_id: $device_id})
                MERGE (t)-[:FROM_DEVICE {timestamp: t.timestamp}]->(d)
            """, transaction_id=transaction_id, device_id=device_id)
            
            # Update device last_seen
            session.run("""
                MATCH (d:Device {device_id: $device_id})
                MATCH (t:Transaction {transaction_id: $transaction_id})
                SET d.last_seen = t.timestamp
            """, device_id=device_id, transaction_id=transaction_id)

    def _link_transaction_to_ip(self, transaction_id: str, ip_address: str):
        """Create FROM_IP relationship between transaction and IP address"""
        try:
            from src.infrastructure.neo4j_connection import Neo4jConnection
        except ImportError:
            from .infrastructure.neo4j_connection import Neo4jConnection
        connection = Neo4jConnection()

        with connection.get_session() as session:
            session.run("""
                MATCH (t:Transaction {transaction_id: $transaction_id})
                MATCH (ip:IPAddress {ip_address: $ip_address})
                MERGE (t)-[:FROM_IP {timestamp: t.timestamp}]->(ip)
            """, transaction_id=transaction_id, ip_address=ip_address)
            
            # Update IP last_seen
            session.run("""
                MATCH (ip:IPAddress {ip_address: $ip_address})
                MATCH (t:Transaction {transaction_id: $transaction_id})
                SET ip.last_seen = t.timestamp
            """, ip_address=ip_address, transaction_id=transaction_id)


def main():
    """Main function to run data generation"""
    print("=== Fraud Detection Data Generator ===\n")

    generator = FraudDataGenerator(fraud_percentage=0.25)

    # Generate dataset
    generator.generate_complete_dataset(
        num_customers=100,
        num_transactions=1000
    )

    print("\n=== Generation Complete ===")
    print(f"Total Customers: {len(generator.customers)}")
    print(f"Total Accounts: {len(generator.accounts)}")
    print(f"Total Merchants: {len(generator.merchants)}")
    print(f"Total Devices: {len(generator.devices)}")


if __name__ == "__main__":
    main()

"""
Sample Data Generator for Fraud Detection System
Generates realistic banking data with embedded fraud patterns.
"""

import random
from datetime import datetime, timedelta, timezone
from typing import List, Tuple
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


class FraudDataGenerator:
    """Generates sample data with embedded fraud patterns"""

    def __init__(self, fraud_percentage: float = 0.05):
        self.faker = Faker()
        self.fraud_percentage = fraud_percentage
        self.account_repo = Neo4jAccountRepository()
        self.customer_repo = Neo4jCustomerRepository()
        self.transaction_repo = Neo4jTransactionRepository()

        # Keep track of created entities
        self.customers: List[Customer] = []
        self.accounts: List[Account] = []
        self.devices: List[Device] = []
        self.merchants: List[Merchant] = []

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
        """Generate merchant records"""
        merchant_categories = ['retail', 'restaurant', 'online', 'gambling',
                              'crypto', 'travel', 'entertainment']

        for _ in range(count):
            self.merchants.append(Merchant(
                merchant_name=self.faker.company(),
                category=random.choice(merchant_categories),
                country=self.faker.country(),
                risk_level=random.choices(
                    [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH],
                    weights=[0.7, 0.2, 0.1]
                )[0],
                is_verified=random.choice([True, True, True, False])  # 75% verified
            ))

    def _generate_devices(self, count: int):
        """Generate device records"""
        device_types = ['mobile', 'desktop', 'tablet']
        operating_systems = ['iOS', 'Android', 'Windows', 'MacOS', 'Linux']
        browsers = ['Chrome', 'Safari', 'Firefox', 'Edge']

        for _ in range(count):
            self.devices.append(Device(
                device_type=random.choice(device_types),
                os=random.choice(operating_systems),
                browser=random.choice(browsers),
                first_seen=self.faker.date_time_between(start_date='-2y', end_date='now'),
                is_trusted=random.choice([True, True, True, False])  # 75% trusted
            ))

    def _generate_transactions(self, count: int):
        """Generate normal transaction patterns"""
        for _ in range(count):
            # Select random accounts
            from_account = random.choice(self.accounts)
            to_account = random.choice([acc for acc in self.accounts
                                       if acc.account_id != from_account.account_id])

            transaction = Transaction(
                amount=self._generate_transaction_amount(),
                timestamp=self.faker.date_time_between(start_date='-90d', end_date='now'),
                transaction_type=random.choice(list(TransactionType)),
                channel=random.choice(list(TransactionChannel)),
                description=self.faker.sentence(nb_words=6),
                from_account_id=from_account.account_id,
                to_account_id=to_account.account_id,
                merchant_id=random.choice(self.merchants).merchant_id if self.merchants else None,
                device_id=random.choice(self.devices).device_id if self.devices else None,
                ip_address=self.faker.ipv4()
            )

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
            circle_size = random.randint(3, 5)
            circle_accounts = random.sample(self.accounts, circle_size)

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
                        is_flagged=True,
                        fraud_score=random.uniform(0.75, 0.95)
                    )
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
                    is_flagged=True,
                    fraud_score=random.uniform(0.6, 0.9)
                )
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

            base_time = datetime.now(timezone.utc) - timedelta(days=random.randint(1, 7))

            for i, sender in enumerate(sender_accounts):
                transaction = Transaction(
                    amount=random.uniform(500, 2000),
                    timestamp=base_time + timedelta(minutes=i * 10),
                    transaction_type=TransactionType.TRANSFER,
                    channel=TransactionChannel.ONLINE,
                    description="Collection",
                    from_account_id=sender.account_id,
                    to_account_id=destination_account.account_id,
                    is_flagged=True,
                    fraud_score=random.uniform(0.6, 0.9)
                )
                self.transaction_repo.save(transaction)

    def _inject_velocity_pattern(self, count: int):
        """Create high-velocity transaction patterns"""
        for _ in range(count):
            account = random.choice(self.accounts)
            base_time = datetime.now(timezone.utc) - timedelta(hours=2)

            # Create 10-20 transactions in quick succession
            num_transactions = random.randint(10, 20)

            for i in range(num_transactions):
                to_account = random.choice([acc for acc in self.accounts
                                           if acc.account_id != account.account_id])

                transaction = Transaction(
                    amount=random.uniform(100, 1000),
                    timestamp=base_time + timedelta(minutes=i * 3),
                    transaction_type=TransactionType.TRANSFER,
                    channel=TransactionChannel.ONLINE,
                    description="Quick transfer",
                    from_account_id=account.account_id,
                    to_account_id=to_account.account_id,
                    is_flagged=True,
                    fraud_score=random.uniform(0.5, 0.8)
                )
                self.transaction_repo.save(transaction)

    def _create_ownership(self, customer_id: str, account_id: str):
        """Create OWNS relationship between customer and account"""
        from .infrastructure.neo4j_connection import Neo4jConnection
        connection = Neo4jConnection()

        with connection.get_session() as session:
            session.run("""
                MATCH (c:Customer {customer_id: $customer_id})
                MATCH (a:Account {account_id: $account_id})
                MERGE (c)-[:OWNS {since_date: datetime(), relationship_type: 'primary'}]->(a)
            """, customer_id=customer_id, account_id=account_id)


def main():
    """Main function to run data generation"""
    print("=== Fraud Detection Data Generator ===\n")

    generator = FraudDataGenerator(fraud_percentage=0.05)

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

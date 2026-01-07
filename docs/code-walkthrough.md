# Code Walkthrough - Fraud Detection System

## Project Structure

```
fraud-detection/
├── src/
│   ├── __init__.py
│   ├── domain/                    # Domain Layer (Business Logic)
│   │   ├── __init__.py
│   │   ├── entities.py           # Domain entities
│   │   ├── value_objects.py      # Immutable value objects
│   │   ├── repositories.py       # Repository interfaces (ports)
│   │   └── services.py           # Domain services
│   ├── infrastructure/            # Infrastructure Layer
│   │   ├── __init__.py
│   │   ├── neo4j_connection.py   # Database connection manager
│   │   └── neo4j_repositories.py # Repository implementations (adapters)
│   ├── application/               # Application Layer
│   │   ├── __init__.py
│   │   └── fraud_investigation_service.py  # Use case orchestration
│   ├── web/                       # Presentation Layer
│   │   ├── app.py                # Flask application
│   │   └── templates/
│   │       └── dashboard.html    # Web UI
│   └── data_generator.py         # Sample data generation
├── docs/                          # Documentation
│   ├── architecture/              # Architecture diagrams
│   ├── novice-guide.md
│   ├── professional-guide.md
│   └── ...
├── requirements.txt
├── .env.example
└── README.md
```

## Domain Layer Deep Dive

### 1. Entities (src/domain/entities.py)

#### Customer Entity

```python
class Customer(BaseModel):
    customer_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    first_name: str
    last_name: str
    email: str
    # ... other fields

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @validator('email')
    def validate_email(cls, v):
        if '@' not in v:
            raise ValueError('Invalid email address')
        return v.lower()
```

**Key Points**:
- Uses Pydantic for validation
- UUID auto-generated for identity
- Email validator ensures data quality
- Property method for derived data
- Immutable after creation (BaseModel default)

#### Account Entity

```python
class Account(BaseModel):
    account_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    account_number: str
    account_type: AccountType  # Enum
    risk_score: float = Field(default=0.0, ge=0.0, le=100.0)
    # ... other fields
```

**Key Points**:
- `Field` constraints ensure risk_score is 0-100
- Enums provide type safety for account_type
- Default values for optional fields

#### Transaction Entity

```python
class Transaction(BaseModel):
    transaction_id: str
    amount: float = Field(gt=0)  # Must be positive
    fraud_score: float = Field(default=0.0, ge=0.0, le=1.0)
    from_account_id: Optional[str] = None
    to_account_id: Optional[str] = None
```

**Key Points**:
- Amount must be positive (gt=0)
- Fraud score normalized to 0-1
- Optional account IDs (for deposits/withdrawals)

### 2. Value Objects (src/domain/value_objects.py)

#### Money Value Object

```python
class Money(BaseModel):
    amount: float = Field(ge=0)
    currency: str = Field(default="USD")

    class Config:
        frozen = True  # Immutable!

    def __add__(self, other: 'Money') -> 'Money':
        if self.currency != other.currency:
            raise ValueError("Cannot add different currencies")
        return Money(amount=self.amount + other.amount, currency=self.currency)
```

**Why This Design?**:
- **Immutable** (`frozen=True`): Thread-safe, cacheable
- **Type-safe**: Can't accidentally add money to a number
- **Currency validation**: Prevents mixing USD and EUR

**Usage**:
```python
price = Money(amount=100, currency="USD")
tax = Money(amount=10, currency="USD")
total = price + tax  # Returns new Money(110, "USD")

# price is unchanged (immutable)
print(price.amount)  # Still 100
```

#### RiskScore Value Object

```python
class RiskScore(BaseModel):
    score: float = Field(ge=0.0, le=100.0)
    factors: list[str] = Field(default_factory=list)
    calculated_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def risk_level(self) -> str:
        if self.score < 30:
            return "LOW"
        elif self.score < 60:
            return "MEDIUM"
        # ... etc
```

**Why This Design?**:
- Combines quantitative (score) with qualitative (factors) data
- Self-documenting: `factors` list explains the score
- Computed property for risk level categorization

### 3. Repository Interfaces (src/domain/repositories.py)

#### Account Repository Interface

```python
class IAccountRepository(ABC):
    @abstractmethod
    def save(self, account: Account) -> Account:
        """Save an account"""
        pass

    @abstractmethod
    def find_by_id(self, account_id: str) -> Optional[Account]:
        """Find account by ID"""
        pass

    @abstractmethod
    def find_high_risk_accounts(self, threshold: float = 70.0) -> List[Account]:
        """Find accounts with risk score above threshold"""
        pass
```

**Why This Design?**:
- **Abstraction**: Domain doesn't know about Neo4j
- **Testability**: Can mock for tests
- **Flexibility**: Can swap databases without changing domain
- **Clear contracts**: Explicit method signatures

### 4. Domain Services (src/domain/services.py)

#### RiskScoringService

```python
class RiskScoringService:
    def __init__(self, transaction_repo: ITransactionRepository,
                 account_repo: IAccountRepository):
        self.transaction_repo = transaction_repo
        self.account_repo = account_repo

    def calculate_account_risk(self, account: Account) -> RiskScore:
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
        # ... more factors

        return RiskScore(score=min(100.0, score), factors=factors)
```

**Why This Design?**:
- **Dependency Injection**: Repositories passed in constructor
- **Single Responsibility**: Only calculates risk
- **Explainability**: Returns factors with score
- **Composable**: Can be used by other services

**Flow**:
```
RiskScoringService
    ↓ (uses)
ITransactionRepository interface
    ↓ (implemented by)
Neo4jTransactionRepository
    ↓ (queries)
Neo4j Database
```

#### FraudDetectionService

```python
class FraudDetectionService:
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
```

**Pattern**: Algorithm + Data Access
1. Call repository to get raw data
2. Apply business logic (pattern detection)
3. Return domain objects (TransactionPattern)

## Infrastructure Layer Deep Dive

### 1. Neo4j Connection (src/infrastructure/neo4j_connection.py)

#### Singleton Pattern

```python
class Neo4jConnection:
    _instance: Optional['Neo4jConnection'] = None
    _driver = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
```

**Why Singleton?**:
- **Resource management**: Only one database connection pool
- **Configuration**: Single point for connection settings
- **Thread safety**: Shared across application

#### Connection Management

```python
def connect(self):
    try:
        self._driver = GraphDatabase.driver(
            self._uri,
            auth=(self._user, self._password)
        )
        # Test connection
        with self._driver.session() as session:
            session.run("RETURN 1")
        print(f"Successfully connected to Neo4j at {self._uri}")
    except Exception as e:
        print(f"Failed to connect to Neo4j: {e}")
        raise
```

**Key Points**:
- Tests connection immediately
- Raises exception if fails (fail-fast)
- Uses context manager for session

### 2. Neo4j Repositories (src/infrastructure/neo4j_repositories.py)

#### Neo4jAccountRepository Implementation

```python
class Neo4jAccountRepository(IAccountRepository):
    def __init__(self):
        self.connection = Neo4jConnection()

    def save(self, account: Account) -> Account:
        with self.connection.get_session() as session:
            query = """
            MERGE (a:Account {account_id: $account_id})
            SET a.account_number = $account_number,
                a.account_type = $account_type,
                a.risk_score = $risk_score
                // ... other properties
            RETURN a
            """
            session.run(query, **account.dict())
            return account
```

**Design Patterns**:
- **MERGE**: Upsert operation (create or update)
- **Parameter binding**: Prevents Cypher injection
- **Context manager**: Automatic session cleanup

#### Converting Between Domain and Database

```python
def _node_to_account(self, node) -> Account:
    """Convert Neo4j node to Account entity"""
    data = dict(node)
    # Convert datetime objects from Neo4j to Python
    if 'created_date' in data and hasattr(data['created_date'], 'to_native'):
        data['created_date'] = data['created_date'].to_native()
    return Account(**data)
```

**Anti-Corruption Layer in Action**:
- Neo4j has its own datetime type
- We convert to Python datetime
- Domain never sees Neo4j types

#### Complex Graph Queries

```python
def detect_fan_out_pattern(self, min_recipients: int = 5,
                          timeframe_hours: int = 24) -> List[Dict[str, Any]]:
    with self.connection.get_session() as session:
        cutoff_time = datetime.utcnow() - timedelta(hours=timeframe_hours)
        query = """
        MATCH (from:Account)<-[:DEBITED_FROM]-(t:Transaction)-[:CREDITED_TO]->(to:Account)
        WHERE t.timestamp >= datetime($cutoff_time)
        WITH from, count(DISTINCT to) as recipient_count, sum(t.amount) as total_amount
        WHERE recipient_count >= $min_recipients
        RETURN from.account_id as account_id, recipient_count, total_amount
        ORDER BY recipient_count DESC
        """
        result = session.run(query, cutoff_time=cutoff_time.isoformat(),
                           min_recipients=min_recipients)
        return [dict(record) for record in result]
```

**Cypher Patterns**:
- `MATCH`: Find pattern
- `WHERE`: Filter
- `WITH`: Aggregate (like SQL GROUP BY)
- `RETURN`: Project results

## Application Layer Deep Dive

### FraudInvestigationService (src/application/fraud_investigation_service.py)

#### Orchestration Pattern

```python
class FraudInvestigationService:
    def __init__(self):
        # Initialize all repositories
        self.account_repo = Neo4jAccountRepository()
        self.transaction_repo = Neo4jTransactionRepository()
        # ... etc

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
```

**Role**: **Orchestrates** domain services and repositories to implement use cases

#### Use Case: Investigate Account

```python
def investigate_account(self, account_id: str) -> Dict[str, Any]:
    # 1. Get account
    account = self.account_repo.find_by_id(account_id)
    if not account:
        return {'error': 'Account not found'}

    # 2. Get transactions
    recent_transactions = self.transaction_repo.find_by_account(
        account_id,
        start_date=datetime.utcnow() - timedelta(days=30)
    )

    # 3. Calculate risk
    risk_score = self.risk_scoring_service.calculate_account_risk(account)

    # 4. Get velocity
    velocity_1h = self.transaction_repo.count_transactions_in_timeframe(
        account_id, minutes=60
    )

    # 5. Get neighborhood
    neighborhood = self.graph_query_repo.get_entity_neighborhood(
        account_id, 'account', depth=2
    )

    # 6. Assemble result
    return {
        'account': account.dict(),
        'risk_score': risk_score.dict(),
        'transaction_count_30d': len(recent_transactions),
        'velocity': {'1_hour': velocity_1h},
        'neighborhood': neighborhood
    }
```

**Pattern**: Facade + Orchestration
- Hides complexity from web layer
- Coordinates multiple services
- Returns DTO (dictionary) for serialization

## Web Layer Deep Dive

### Flask Application (src/web/app.py)

#### Endpoint Structure

```python
@app.route('/api/accounts/<account_id>/investigate', methods=['GET'])
def investigate_account(account_id):
    """Investigate specific account"""
    try:
        result = investigation_service.investigate_account(account_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

**Pattern**: Thin controllers
- Minimal logic
- Delegate to application service
- Handle HTTP concerns only (routing, JSON, status codes)

#### Error Handling

```python
try:
    # Business logic
    result = investigation_service.detect_fraud_patterns()
    return jsonify(result)
except Exception as e:
    # Generic error handler
    return jsonify({'error': str(e)}), 500
```

**Production Enhancement**: Add specific exception types
```python
except EntityNotFoundError as e:
    return jsonify({'error': str(e)}), 404
except ValidationError as e:
    return jsonify({'error': str(e)}), 400
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    return jsonify({'error': 'Internal server error'}), 500
```

## Data Generator Deep Dive

### Fraud Pattern Injection (src/data_generator.py)

#### Circular Flow Generation

```python
def _inject_circular_flow(self, count: int):
    for _ in range(count):
        # Select 3-5 accounts for the circle
        circle_size = random.randint(3, 5)
        circle_accounts = random.sample(self.accounts, circle_size)

        base_time = datetime.utcnow() - timedelta(days=random.randint(1, 30))
        amount = random.uniform(5000, 20000)

        # Create circular transactions
        for i in range(circle_size):
            from_acc = circle_accounts[i]
            to_acc = circle_accounts[(i + 1) % circle_size]  # Wraps around!

            transaction = Transaction(
                amount=amount * random.uniform(0.95, 1.05),
                timestamp=base_time + timedelta(hours=i * 2),
                from_account_id=from_acc.account_id,
                to_account_id=to_acc.account_id,
                is_flagged=True,
                fraud_score=random.uniform(0.7, 0.95)
            )
            self.transaction_repo.save(transaction)
```

**Key Techniques**:
- Modulo arithmetic for circular: `(i + 1) % circle_size`
- Time spacing: `timedelta(hours=i * 2)`
- Amount variation: `amount * random.uniform(0.95, 1.05)`
- Pre-flagged for testing

## Data Flow Example: Investigating an Account

Let's trace a complete request:

```
1. User clicks account in dashboard
   ↓
2. JavaScript: fetch('/api/accounts/123/investigate')
   ↓
3. Flask app.py:
   @app.route('/api/accounts/<account_id>/investigate')
   def investigate_account(account_id):
       result = investigation_service.investigate_account(account_id)
   ↓
4. fraud_investigation_service.py:
   def investigate_account(self, account_id):
       account = self.account_repo.find_by_id(account_id)
   ↓
5. neo4j_repositories.py:
   def find_by_id(self, account_id):
       session.run("MATCH (a:Account {account_id: $id}) RETURN a")
   ↓
6. Neo4j Database:
   Returns account node
   ↓
7. neo4j_repositories.py:
   return self._node_to_account(record['a'])
   ↓
8. fraud_investigation_service.py:
   risk_score = self.risk_scoring_service.calculate_account_risk(account)
   ↓
9. services.py (RiskScoringService):
   Calculate risk based on transactions, patterns, etc.
   ↓
10. fraud_investigation_service.py:
    return {account, risk_score, transactions, ...}
    ↓
11. app.py:
    return jsonify(result)
    ↓
12. JavaScript receives JSON, updates UI
```

## Key Design Patterns Used

### 1. Repository Pattern
**Location**: `domain/repositories.py`, `infrastructure/neo4j_repositories.py`
**Purpose**: Abstract data access

### 2. Dependency Injection
**Location**: Throughout services
**Example**: RiskScoringService receives repositories in constructor

### 3. Factory Pattern
**Location**: Entity creation with UUID generation
**Example**: `Field(default_factory=lambda: str(uuid.uuid4()))`

### 4. Facade Pattern
**Location**: FraudInvestigationService
**Purpose**: Simplify complex subsystem

### 5. Singleton Pattern
**Location**: Neo4jConnection
**Purpose**: Single database connection

### 6. Value Object Pattern
**Location**: Money, RiskScore, TransactionPattern
**Purpose**: Immutable, behavior-rich objects

### 7. Entity Pattern
**Location**: Customer, Account, Transaction
**Purpose**: Objects with identity

## Testing Strategy

### Unit Test Example

```python
def test_risk_calculation():
    # Arrange
    mock_transaction_repo = Mock(ITransactionRepository)
    mock_transaction_repo.count_transactions_in_timeframe.return_value = 15

    service = RiskScoringService(mock_transaction_repo, Mock())

    account = Account(account_id="test", ...)

    # Act
    risk = service.calculate_account_risk(account)

    # Assert
    assert risk.score > 0
    assert any("velocity" in factor.lower() for factor in risk.factors)
```

### Integration Test Example

```python
def test_account_investigation():
    # Arrange
    service = FraudInvestigationService()  # Real repositories

    # Act
    result = service.investigate_account("known_test_id")

    # Assert
    assert result['account']['account_id'] == "known_test_id"
    assert 'risk_score' in result
    assert isinstance(result['recent_transactions'], list)
```

## Performance Considerations in Code

### 1. Connection Pooling
```python
# Neo4j driver handles connection pooling automatically
self._driver = GraphDatabase.driver(uri, auth=(user, password))
```

### 2. Batch Operations
```python
# Instead of N queries:
for account in accounts:
    save_account(account)  # N database calls

# Use batch:
query = """
UNWIND $accounts as account_data
MERGE (a:Account {account_id: account_data.id})
SET a += account_data.properties
"""
session.run(query, accounts=[a.dict() for a in accounts])  # 1 database call
```

### 3. Index Usage
```python
# Repository methods use indexed fields
def find_by_id(self, account_id: str):  # Uses account_id index
    query = "MATCH (a:Account {account_id: $id}) RETURN a"  # Fast lookup
```

## Common Code Patterns

### Pattern: Try-Except with Logging

```python
try:
    result = risky_operation()
except SpecificError as e:
    logger.error(f"Expected error: {e}")
    # Handle gracefully
except Exception as e:
    logger.exception(f"Unexpected error: {e}")
    raise  # Re-raise unexpected errors
```

### Pattern: Context Managers

```python
# Always use context managers for sessions
with self.connection.get_session() as session:
    # Session automatically closed
    result = session.run(query)
```

### Pattern: Dictionary Unpacking

```python
# Clean way to pass entity properties to database
session.run(query, **account.dict())

# Instead of:
session.run(query,
           account_id=account.account_id,
           account_number=account.account_number,
           # ... 20 more lines
)
```

## Code Organization Best Practices

1. **One class per file** (mostly): Makes files manageable
2. **Grouped imports**: stdlib, third-party, local
3. **Type hints**: Enable static analysis
4. **Docstrings**: Explain complex methods
5. **Constants**: ALL_CAPS, defined at module level

## Next Steps for Code Understanding

1. Start with domain entities - understand the business model
2. Read repository interfaces - see what operations are needed
3. Look at domain services - see business logic
4. Check infrastructure - see technical implementation
5. Trace a request end-to-end using debugger

## Debugging Tips

### 1. Add Logging

```python
import logging
logger = logging.getLogger(__name__)

def investigate_account(self, account_id):
    logger.info(f"Investigating account: {account_id}")
    # ... code
    logger.debug(f"Risk calculated: {risk_score.score}")
```

### 2. Use Neo4j Browser

Open http://localhost:7474 and run queries directly:
```cypher
MATCH (a:Account {account_id: "123"}) RETURN a
```

### 3. Python Debugger

```python
import pdb; pdb.set_trace()  # Breakpoint
```

### 4. Print Cypher Queries

```python
print(f"Query: {query}")
print(f"Params: {params}")
result = session.run(query, **params)
```

This walkthrough should give you a solid understanding of how the code is structured and why design decisions were made. Happy coding!

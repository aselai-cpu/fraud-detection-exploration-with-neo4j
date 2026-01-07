# Fraud Detection System - Professional Documentation

## Executive Summary

This document provides comprehensive technical documentation for the Graph Database-based Fraud Detection System. The system leverages Neo4j's graph database capabilities combined with Domain-Driven Design (DDD) principles to detect and investigate financial fraud patterns.

## System Architecture

### Architectural Principles

The system follows:
1. **Domain-Driven Design (DDD)**: Business logic is modeled in the domain layer
2. **Hexagonal Architecture**: Clean separation between domain and infrastructure
3. **Repository Pattern**: Abstract data access behind interfaces
4. **Anti-Corruption Layer**: Neo4j implementation details isolated from domain
5. **SOLID Principles**: Maintainable, testable, extensible code

### Layer Architecture

```
┌─────────────────────────────────────────┐
│         Presentation Layer              │
│     (Flask Web App + REST API)          │
└─────────────────────────────────────────┘
                  │
┌─────────────────────────────────────────┐
│        Application Layer                │
│  (FraudInvestigationService, etc.)      │
└─────────────────────────────────────────┘
                  │
┌─────────────────────────────────────────┐
│          Domain Layer                   │
│  (Entities, Value Objects, Services,    │
│   Repository Interfaces)                │
└─────────────────────────────────────────┘
                  │
┌─────────────────────────────────────────┐
│       Infrastructure Layer              │
│  (Neo4j Repositories, Database          │
│   Connection - Anti-Corruption Layer)   │
└─────────────────────────────────────────┘
                  │
┌─────────────────────────────────────────┐
│         Neo4j Graph Database            │
└─────────────────────────────────────────┘
```

## Domain Model

### Core Entities

#### Customer Entity
- **Identity**: customer_id (UUID)
- **Invariants**:
  - Email must be unique and valid
  - KYC status must be verified before high-value transactions
- **Relationships**: Owns multiple accounts, uses devices

#### Account Entity
- **Identity**: account_id (UUID)
- **Invariants**:
  - Risk score must be 0-100
  - Status transitions follow state machine
- **Relationships**: Owned by customer, involved in transactions

#### Transaction Entity
- **Identity**: transaction_id (UUID)
- **Invariants**:
  - Amount must be positive
  - Must have valid from/to accounts
- **Relationships**: Debited from account, credited to account, uses device/IP

### Value Objects

Value objects are immutable and have no identity:

- **Money**: Encapsulates amount and currency with arithmetic operations
- **RiskScore**: Combines score with explanation factors
- **TransactionPattern**: Describes detected fraud pattern with evidence
- **Address**: Complete address information
- **DateRange**: Time period with validation

### Domain Services

Services contain business logic that doesn't belong to a single entity:

#### RiskScoringService
Calculates risk scores based on multiple factors:
- Transaction velocity (30% weight)
- Unusual patterns (25% weight)
- Shared infrastructure with known fraud (20% weight)
- Geographic anomalies (15% weight)
- Device/IP risk (10% weight)

#### FraudDetectionService
Implements graph-based fraud detection algorithms:
- Circular flow detection using cycle finding
- Fan-out/fan-in pattern detection
- Mule account detection based on throughput
- Shared infrastructure analysis

#### FraudRingAnalysisService
Manages fraud ring lifecycle:
- Creates rings from detected patterns
- Links entities (customers/accounts) to rings
- Updates investigation status

## Graph Database Design

### Node Types

```cypher
// Customer Node
(:Customer {
  customer_id: String,
  first_name: String,
  last_name: String,
  email: String,
  kyc_status: String,
  risk_level: String
})

// Account Node
(:Account {
  account_id: String,
  account_number: String,
  account_type: String,
  status: String,
  risk_score: Float,
  balance: Float
})

// Transaction Node
(:Transaction {
  transaction_id: String,
  amount: Float,
  timestamp: DateTime,
  transaction_type: String,
  is_flagged: Boolean,
  fraud_score: Float
})
```

### Relationship Types

```cypher
// Ownership
(Customer)-[:OWNS {since_date: DateTime, relationship_type: String}]->(Account)

// Transaction Flow
(Transaction)-[:DEBITED_FROM {balance_before: Float, balance_after: Float}]->(Account)
(Transaction)-[:CREDITED_TO {balance_before: Float, balance_after: Float}]->(Account)

// Device Usage
(Customer)-[:USED_DEVICE {first_used: DateTime, usage_count: Int}]->(Device)
(Transaction)-[:FROM_DEVICE]->(Device)

// Geographic
(Transaction)-[:FROM_IP]->(IPAddress)

// Fraud Patterns
(Transaction)-[:SIMILAR_TO {similarity_score: Float}]->(Transaction)
(Account)-[:LINKED_ACCOUNT {link_type: String, strength: Float}]->(Account)

// Fraud Rings
(Customer)-[:MEMBER_OF {role: String}]->(FraudRing)
(FraudRing)-[:INVOLVES_ACCOUNT]->(Account)
```

### Indexes

Critical indexes for performance:

```cypher
CREATE INDEX account_id_idx FOR (a:Account) ON (a.account_id);
CREATE INDEX customer_id_idx FOR (c:Customer) ON (c.customer_id);
CREATE INDEX transaction_id_idx FOR (t:Transaction) ON (t.transaction_id);
CREATE INDEX transaction_timestamp_idx FOR (t:Transaction) ON (t.timestamp);
CREATE INDEX transaction_flagged_idx FOR (t:Transaction) ON (t.is_flagged);
```

## Fraud Detection Algorithms

### 1. Circular Flow Detection

**Algorithm**:
```python
def detect_circular_flow(min_cycle_length=3, max_cycle_length=8):
    """
    Find cycles in transaction graph using Cypher path matching
    Time Complexity: O(N * D^L) where N=nodes, D=degree, L=cycle length
    """
    query = """
    MATCH path = (a:Account)-[:DEBITED_FROM|CREDITED_TO*{min}..{max}]-(a)
    WHERE ALL(r IN relationships(path)
              WHERE r.timestamp > datetime() - duration({{days: 30}}))
    RETURN path
    """
```

**Complexity**: O(N * D^L) where:
- N = number of accounts
- D = average degree (connections per account)
- L = cycle length

**Optimization**: Limit time window to last 30-90 days

### 2. Fan-Out Detection

**Algorithm**:
```python
def detect_fan_out(min_recipients=5, timeframe_hours=24):
    """
    Detect one-to-many transaction patterns
    Uses graph aggregation
    Time Complexity: O(N + E) where E=edges (transactions)
    """
    query = """
    MATCH (from:Account)<-[:DEBITED_FROM]-(t:Transaction)-[:CREDITED_TO]->(to:Account)
    WHERE t.timestamp >= datetime() - duration({{hours: {timeframe}}})
    WITH from, count(DISTINCT to) as recipient_count, sum(t.amount) as total
    WHERE recipient_count >= {min_recipients}
    RETURN from, recipient_count, total
    ORDER BY recipient_count DESC
    """
```

**Complexity**: O(N + E) - linear in transactions

### 3. Money Mule Detection

**Criteria**:
- High throughput (> $10,000 in/out)
- Short hold time (< 48 hours)
- Balanced in/out (difference < 10%)

**Algorithm**:
```python
def detect_mule_accounts(min_throughput=10000, max_hold_hours=48):
    """
    Detect accounts with rapid in/out money flow
    Time Complexity: O(A * T) where A=accounts, T=transactions per account
    """
    query = """
    MATCH (a:Account)<-[:CREDITED_TO]-(t_in:Transaction)
    MATCH (a)<-[:DEBITED_FROM]-(t_out:Transaction)
    WHERE duration.between(t_in.timestamp, t_out.timestamp).hours <= {max_hold}
    WITH a, sum(t_in.amount) as total_in, sum(t_out.amount) as total_out
    WHERE total_in >= {min_throughput}
      AND abs(total_in - total_out) / total_in < 0.1
    RETURN a
    """
```

### 4. Shared Infrastructure Detection

**Purpose**: Find accounts controlled by same entity

**Algorithm**:
```python
def find_shared_devices():
    """
    Find devices used by multiple customers
    Indicates potential synthetic identities or fraud rings
    """
    query = """
    MATCH (c1:Customer)-[:USED_DEVICE]->(d:Device)<-[:USED_DEVICE]-(c2:Customer)
    WHERE c1.customer_id < c2.customer_id
    WITH d, collect(DISTINCT c1) + collect(DISTINCT c2) as customers
    WHERE size(customers) >= 2
    RETURN d, customers
    """
```

## Risk Scoring Model

### Account Risk Score Formula

```
RiskScore = (0.30 × VelocityScore) +
            (0.25 × PatternScore) +
            (0.20 × InfrastructureScore) +
            (0.15 × GeographicScore) +
            (0.10 × DeviceScore)
```

Each component ranges 0-100.

### Component Calculations

**Velocity Score**:
```python
velocity_score = min(30, transaction_count_1h * 2)
```

**Pattern Score**:
```python
pattern_score = min(25, flagged_transactions * 5)
```

**Infrastructure Score**:
```python
if shared_with_known_fraudster:
    infrastructure_score = 20
elif shared_with_high_risk:
    infrastructure_score = 15
else:
    infrastructure_score = 0
```

## API Endpoints

### Investigation APIs

```
GET /api/dashboard/summary
Returns: Overview statistics for dashboard

GET /api/accounts/high-risk?limit=50
Returns: List of high-risk accounts

GET /api/accounts/{account_id}/investigate
Returns: Detailed account investigation data

GET /api/customers/{customer_id}/investigate
Returns: Customer investigation with all accounts

POST /api/fraud-patterns/detect
Returns: Results of fraud detection run

GET /api/fraud-rings/active
Returns: Active fraud rings under investigation

GET /api/transactions/flagged?limit=100
Returns: Flagged transactions

GET /api/connection/path?from={id}&to={id}
Returns: Connection path between entities

GET /api/infrastructure/shared?type=device|ip
Returns: Shared infrastructure analysis

POST /api/report/generate
Body: {entity_id, entity_type}
Returns: Comprehensive investigation report
```

### Response Formats

All responses follow standard JSON format:

```json
{
  "data": { ... },
  "metadata": {
    "timestamp": "ISO-8601",
    "request_id": "UUID"
  },
  "errors": []
}
```

## Performance Considerations

### Database Optimization

1. **Index Strategy**: Create indexes on frequently queried properties
2. **Query Optimization**: Use PROFILE/EXPLAIN to analyze query plans
3. **Batch Operations**: Use UNWIND for bulk inserts
4. **Connection Pooling**: Reuse database connections
5. **Query Caching**: Cache frequently run queries

### Scalability

**Horizontal Scaling**:
- Neo4j Enterprise supports sharding via Fabric
- Read replicas for query distribution
- Separate write and read workloads

**Vertical Scaling**:
- Increase heap memory for larger graphs
- SSD storage for better I/O
- More CPU cores for parallel queries

### Performance Benchmarks

| Operation | Dataset Size | Time |
|-----------|--------------|------|
| Circular Flow Detection | 1M transactions | 2-5 sec |
| Fan-Out Detection | 1M transactions | 1-3 sec |
| Risk Score Calculation | 10K accounts | 5-10 sec |
| Path Finding (depth 5) | 100K nodes | 0.1-1 sec |

## Security Considerations

### Data Protection

1. **Encryption at Rest**: Enable Neo4j encryption
2. **Encryption in Transit**: Use TLS for all connections
3. **Sensitive Data**: Hash SSNs, encrypt PII
4. **Access Control**: Role-based access in Neo4j
5. **Audit Logging**: Log all access and modifications

### Authentication & Authorization

```python
# Example RBAC
roles = {
    'analyst': ['read', 'investigate'],
    'senior_analyst': ['read', 'investigate', 'update_status'],
    'admin': ['read', 'investigate', 'update_status', 'delete']
}
```

## Testing Strategy

### Unit Tests
- Test domain entities and value objects
- Test domain services logic
- Mock repositories for isolation

### Integration Tests
- Test repository implementations with test database
- Test API endpoints with test client
- Test fraud detection algorithms with known patterns

### Performance Tests
- Load test with large datasets
- Measure query performance
- Test concurrent user scenarios

## Deployment

### Prerequisites

- Python 3.8+
- Neo4j 4.x or 5.x
- 8GB+ RAM recommended
- SSD storage recommended

### Environment Configuration

```bash
# .env file
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=secure_password
FLASK_PORT=5000
FLASK_DEBUG=False
```

### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/ ./src/
COPY .env .env

CMD ["python", "-m", "src.web.app"]
```

### Production Checklist

- [ ] Set DEBUG=False
- [ ] Use strong database passwords
- [ ] Enable SSL/TLS
- [ ] Configure logging
- [ ] Set up monitoring
- [ ] Configure backup strategy
- [ ] Set up alerting
- [ ] Load balancing configured
- [ ] Rate limiting enabled

## Monitoring & Observability

### Key Metrics

1. **Application Metrics**:
   - Request latency (p50, p95, p99)
   - Error rate
   - Fraud detection duration

2. **Database Metrics**:
   - Query execution time
   - Connection pool usage
   - Cache hit rate
   - Transaction throughput

3. **Business Metrics**:
   - Fraud detection rate
   - False positive rate
   - Average investigation time
   - Pattern distribution

### Logging

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('fraud_detection.log'),
        logging.StreamHandler()
    ]
)
```

## Extending the System

### Adding New Fraud Patterns

1. Create detection method in `FraudDetectionService`
2. Implement Cypher query in `IGraphQueryRepository`
3. Add concrete implementation in `Neo4jGraphQueryRepository`
4. Update API endpoint in Flask app
5. Add unit and integration tests

### Adding New Entity Types

1. Define entity in `domain/entities.py`
2. Create repository interface in `domain/repositories.py`
3. Implement in `infrastructure/neo4j_repositories.py`
4. Add to data generator if needed
5. Update documentation

## References

- Neo4j Documentation: https://neo4j.com/docs/
- Domain-Driven Design: Eric Evans
- Clean Architecture: Robert C. Martin
- Graph Algorithms: Neo4j Graph Data Science Library

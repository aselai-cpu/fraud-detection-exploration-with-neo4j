# Fraud Detection Graph Database Ontology

## Core Entities (Nodes)

### 1. Account
Represents a bank account in the system.

**Properties:**
- `account_id` (string): Unique identifier
- `account_number` (string): Account number
- `account_type` (string): checking, savings, credit
- `status` (string): active, suspended, closed
- `created_date` (datetime): Account creation date
- `risk_score` (float): Current risk assessment (0-100)
- `country` (string): Country of origin
- `currency` (string): Primary currency

### 2. Customer
Represents an individual or entity owning accounts.

**Properties:**
- `customer_id` (string): Unique identifier
- `first_name` (string)
- `last_name` (string)
- `email` (string)
- `phone` (string)
- `date_of_birth` (date)
- `ssn_hash` (string): Hashed SSN for privacy
- `address` (string)
- `city` (string)
- `country` (string)
- `customer_since` (datetime)
- `kyc_status` (string): verified, pending, failed
- `risk_level` (string): low, medium, high, critical

### 3. Transaction
Represents a financial transaction.

**Properties:**
- `transaction_id` (string): Unique identifier
- `amount` (float): Transaction amount
- `currency` (string)
- `timestamp` (datetime)
- `transaction_type` (string): transfer, withdrawal, deposit, payment
- `status` (string): completed, pending, failed, reversed
- `channel` (string): online, atm, branch, mobile
- `description` (string)
- `is_flagged` (boolean): Fraud flag
- `fraud_score` (float): ML-based fraud probability (0-1)

### 4. Device
Represents a device used for transactions.

**Properties:**
- `device_id` (string): Unique device fingerprint
- `device_type` (string): mobile, desktop, tablet
- `os` (string): Operating system
- `browser` (string)
- `first_seen` (datetime)
- `last_seen` (datetime)
- `is_trusted` (boolean)

### 5. IPAddress
Represents an IP address used in transactions.

**Properties:**
- `ip_address` (string)
- `country` (string)
- `city` (string)
- `is_proxy` (boolean)
- `is_vpn` (boolean)
- `risk_score` (float)
- `first_seen` (datetime)
- `last_seen` (datetime)

### 6. Merchant
Represents a merchant/payee in transactions.

**Properties:**
- `merchant_id` (string)
- `merchant_name` (string)
- `category` (string): retail, gambling, crypto, etc.
- `country` (string)
- `risk_level` (string)
- `is_verified` (boolean)

### 7. FraudRing
Represents a detected group of related fraudulent activities.

**Properties:**
- `ring_id` (string)
- `detected_date` (datetime)
- `confidence_score` (float): 0-1
- `status` (string): investigating, confirmed, false_positive
- `total_amount` (float): Total fraudulent amount
- `member_count` (int): Number of members

## Relationships (Edges)

### Customer-Account Relationships
- **OWNS** (Customer -> Account)
  - Properties: `ownership_percentage`, `since_date`, `relationship_type` (primary, joint, beneficiary)

- **AUTHORIZED_USER** (Customer -> Account)
  - Properties: `granted_date`, `permission_level`

### Transaction Relationships
- **DEBITED_FROM** (Transaction -> Account)
  - Properties: `balance_before`, `balance_after`

- **CREDITED_TO** (Transaction -> Account)
  - Properties: `balance_before`, `balance_after`

- **INITIATED_BY** (Transaction -> Customer)
  - Properties: `authentication_method`, `ip_address`

- **SENT_TO** (Transaction -> Merchant)
  - Properties: `merchant_reference`

### Device & Access Relationships
- **USED_DEVICE** (Customer -> Device)
  - Properties: `first_used`, `last_used`, `usage_count`

- **FROM_IP** (Transaction -> IPAddress)
  - Properties: `timestamp`

- **FROM_DEVICE** (Transaction -> Device)
  - Properties: `timestamp`

### Fraud Pattern Relationships
- **SIMILAR_TO** (Transaction -> Transaction)
  - Properties: `similarity_score`, `pattern_type` (amount, timing, device)

- **LINKED_ACCOUNT** (Account -> Account)
  - Properties: `link_type` (shared_device, shared_ip, transfer_pattern), `strength` (0-1)

- **ASSOCIATED_WITH** (Customer -> Customer)
  - Properties: `association_type` (shared_address, shared_device, family), `confidence`

- **MEMBER_OF** (Customer -> FraudRing)
  - Properties: `role` (organizer, mule, victim), `joined_date`

- **INVOLVES_ACCOUNT** (FraudRing -> Account)
  - Properties: `account_role`, `total_fraudulent_amount`

## Fraud Detection Patterns

### 1. Velocity Patterns
- Multiple transactions in short time period
- Query: Find accounts with >N transactions in M minutes

### 2. Circular Money Flow
- Money flowing in a circle between accounts
- Query: Detect cycles in DEBITED_FROM/CREDITED_TO relationships

### 3. Fan-out/Fan-in Patterns
- One account distributing to many (fan-out)
- Many accounts collecting to one (fan-in)
- Query: Find nodes with high out-degree or in-degree in transaction graph

### 4. Shared Infrastructure
- Multiple accounts sharing devices, IPs, or addresses
- Query: Find accounts connected via USED_DEVICE or FROM_IP paths

### 5. Mule Account Detection
- Accounts that receive and quickly forward funds
- Query: Find accounts with balanced in/out transactions within short timeframes

### 6. Synthetic Identity
- New accounts with limited history showing suspicious patterns
- Query: Find recently created customers with high-risk activities

## Graph Traversal Queries for Fraud Detection

### Find First-Party Fraud
```cypher
MATCH (c:Customer)-[:OWNS]->(a:Account)-[:DEBITED_FROM]-(t:Transaction)
WHERE t.is_flagged = true
RETURN c, a, t
```

### Detect Money Mule Networks
```cypher
MATCH path = (a1:Account)-[:CREDITED_TO]-(t1:Transaction)-[:DEBITED_FROM]-(a2:Account)
              -[:CREDITED_TO]-(t2:Transaction)-[:DEBITED_FROM]-(a3:Account)
WHERE t1.timestamp - t2.timestamp < duration({hours: 24})
  AND a1 <> a3
RETURN path
```

### Find Fraud Rings via Shared Infrastructure
```cypher
MATCH (a1:Account)<-[:OWNS]-(c1:Customer)-[:USED_DEVICE]->(d:Device)<-[:USED_DEVICE]-(c2:Customer)-[:OWNS]->(a2:Account)
WHERE c1 <> c2
  AND (a1)-[:DEBITED_FROM|CREDITED_TO]-(:Transaction)-[:DEBITED_FROM|CREDITED_TO]-(a2)
RETURN a1, c1, d, c2, a2
```

### Detect Circular Money Flow
```cypher
MATCH path = (a:Account)-[:DEBITED_FROM|CREDITED_TO*4..8]-(a)
WHERE ALL(r IN relationships(path) WHERE r.timestamp > datetime() - duration({days: 30}))
RETURN path
```

## Risk Scoring Strategy

### Account Risk Score Components
1. Transaction velocity (30%)
2. Unusual transaction patterns (25%)
3. Shared infrastructure with known fraud (20%)
4. Geographic anomalies (15%)
5. Device/IP risk (10%)

### Customer Risk Score Components
1. KYC verification status (25%)
2. Account history and age (20%)
3. Transaction patterns across all accounts (25%)
4. Connections to known fraudsters (20%)
5. Behavioral anomalies (10%)

## Data Model Benefits for Fraud Detection

1. **Relationship Discovery**: Graph structure naturally reveals hidden connections
2. **Pattern Matching**: Graph queries excel at detecting complex fraud patterns
3. **Real-time Analysis**: Efficient traversal enables real-time fraud detection
4. **Explainability**: Graph paths provide clear evidence trails for investigations
5. **Adaptability**: Easy to add new entity types and relationships as fraud evolves

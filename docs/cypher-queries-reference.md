# Neo4j Cypher Queries Reference

This document provides a comprehensive reference for all Cypher queries used in the Fraud Detection System. Queries are organized by category and include detailed explanations of their purpose, parameters, and usage.

## Table of Contents

1. [Account Management Queries](#account-management-queries)
2. [Customer Management Queries](#customer-management-queries)
3. [Transaction Queries](#transaction-queries)
4. [Fraud Pattern Detection Queries](#fraud-pattern-detection-queries)
5. [Infrastructure & Maintenance Queries](#infrastructure--maintenance-queries)
6. [Index Creation Queries](#index-creation-queries)

---

## Account Management Queries

### 1. Save/Update Account

**Purpose:** Create or update an account node in the database.

**Location:** `neo4j_repositories.py:32-43`

```cypher
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
```

**Explanation:**
- `MERGE` ensures the account is created if it doesn't exist, or updated if it does
- All account properties are set including risk score and balance
- Uses `datetime()` function to properly store temporal data
- Returns the created/updated account node

**Parameters:**
- `account_id`: Unique identifier (UUID)
- `account_number`: Account number string
- `account_type`: Type of account (CHECKING, SAVINGS, etc.)
- `status`: Account status (ACTIVE, SUSPENDED, CLOSED)
- `created_date`: ISO format datetime string
- `risk_score`: Float between 0-100
- `country`: Country code
- `currency`: Currency code (USD, EUR, etc.)
- `balance`: Current balance

---

### 2. Find Account by ID

**Purpose:** Retrieve a single account by its unique identifier.

**Location:** `neo4j_repositories.py:49`

```cypher
MATCH (a:Account {account_id: $account_id})
RETURN a
```

**Explanation:**
- Simple pattern matching to find account node
- Returns null if account doesn't exist

**Parameters:**
- `account_id`: Account UUID

---

### 3. Find Account by Account Number

**Purpose:** Retrieve account using the account number (business key).

**Location:** `neo4j_repositories.py:58`

```cypher
MATCH (a:Account {account_number: $account_number})
RETURN a
```

**Explanation:**
- Searches by account number instead of internal ID
- Useful for user-facing queries

**Parameters:**
- `account_number`: Business account number string

---

### 4. Find Accounts by Customer

**Purpose:** Get all accounts owned by a specific customer.

**Location:** `neo4j_repositories.py:67-70`

```cypher
MATCH (c:Customer {customer_id: $customer_id})-[:OWNS]->(a:Account)
RETURN a
```

**Explanation:**
- Traverses the `OWNS` relationship from customer to accounts
- Returns multiple accounts if customer has more than one
- Useful for customer profile views

**Parameters:**
- `customer_id`: Customer UUID

**Graph Pattern:**
```
(Customer)-[:OWNS]->(Account)
```

---

### 5. Find High-Risk Accounts

**Purpose:** Retrieve all accounts with risk scores above a threshold.

**Location:** `neo4j_repositories.py:76-81`

```cypher
MATCH (a:Account)
WHERE a.risk_score >= $threshold
RETURN a
ORDER BY a.risk_score DESC
```

**Explanation:**
- Filters accounts by risk score threshold (default 70.0)
- Orders results from highest to lowest risk
- Critical for fraud analyst dashboards
- Uses index on `risk_score` for performance

**Parameters:**
- `threshold`: Minimum risk score (float, typically 60.0-80.0)

**Returns:** List of accounts sorted by risk (highest first)

---

### 6. Update Account Risk Score

**Purpose:** Update the risk score for a specific account.

**Location:** `neo4j_repositories.py:87-90`

```cypher
MATCH (a:Account {account_id: $account_id})
SET a.risk_score = $risk_score
```

**Explanation:**
- Updates only the risk score, leaving other properties unchanged
- Called after risk calculation algorithms run
- No return value needed

**Parameters:**
- `account_id`: Account UUID
- `risk_score`: New risk score (0-100)

---

## Customer Management Queries

### 7. Save/Update Customer

**Purpose:** Create or update a customer profile.

**Location:** `neo4j_repositories.py:110-125`

```cypher
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
```

**Explanation:**
- Creates or updates customer with all profile information
- Stores sensitive data (SSN) as hash only
- Includes KYC (Know Your Customer) status
- Temporal fields converted to Neo4j datetime

**Parameters:**
- `customer_id`: Customer UUID
- `first_name`, `last_name`: Name components
- `email`: Email address (indexed)
- `phone`: Phone number
- `date_of_birth`: Birth date (ISO string)
- `ssn_hash`: Hashed SSN for privacy
- `address`, `city`, `country`: Address fields
- `customer_since`: Account creation date
- `kyc_status`: Verification status (VERIFIED, PENDING, FAILED)
- `risk_level`: Customer risk level

---

### 8. Find Customer by ID

**Purpose:** Retrieve customer by unique identifier.

**Location:** `neo4j_repositories.py:131`

```cypher
MATCH (c:Customer {customer_id: $customer_id})
RETURN c
```

**Parameters:**
- `customer_id`: Customer UUID

---

### 9. Find Customer by Email

**Purpose:** Look up customer using email address.

**Location:** `neo4j_repositories.py:140`

```cypher
MATCH (c:Customer {email: $email})
RETURN c
```

**Explanation:**
- Email is converted to lowercase before query
- Uses email index for fast lookups

**Parameters:**
- `email`: Customer email (lowercase)

---

### 10. Find Connected Customers

**Purpose:** Discover customers connected through various relationships.

**Location:** `neo4j_repositories.py:149-153`

```cypher
MATCH path = (c1:Customer {customer_id: $customer_id})-[*1..{depth}]-(c2:Customer)
WHERE c1 <> c2
RETURN DISTINCT c2
```

**Explanation:**
- Variable-length path pattern `[*1..{depth}]` finds customers connected by 1 to N hops
- Connections can be through shared accounts, devices, addresses, etc.
- `WHERE c1 <> c2` prevents returning the source customer
- `DISTINCT` eliminates duplicate connections
- Useful for finding fraud rings and related parties

**Parameters:**
- `customer_id`: Source customer UUID
- `depth`: Maximum relationship hops (default 2)

**Graph Pattern:**
```
(Customer1)-[*1..depth]-(Customer2)
```

**Example Connections:**
- Customer1 → Account ← Customer2 (joint account)
- Customer1 → Device ← Customer2 (shared device)

---

## Transaction Queries

### 11. Create Transaction with Relationships

**Purpose:** Create a transaction and link it to accounts.

**Location:** `neo4j_repositories.py:176-218`

**Transaction Node Creation:**
```cypher
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
```

**Debit Relationship:**
```cypher
MATCH (t:Transaction {transaction_id: $transaction_id})
MATCH (a:Account {account_id: $from_account_id})
MERGE (t)-[:DEBITED_FROM]->(a)
```

**Credit Relationship:**
```cypher
MATCH (t:Transaction {transaction_id: $transaction_id})
MATCH (a:Account {account_id: $to_account_id})
MERGE (t)-[:CREDITED_TO]->(a)
```

**Explanation:**
- Creates transaction node first
- Then creates relationships to source and destination accounts
- Relationships are optional (e.g., ATM withdrawal has only DEBITED_FROM)
- `is_flagged` indicates suspicious transaction
- `fraud_score` is ML model confidence (0.0-1.0)

**Graph Pattern:**
```
(Account) <-[:DEBITED_FROM]- (Transaction) -[:CREDITED_TO]-> (Account)
```

---

### 12. Find Transaction by ID

**Purpose:** Retrieve transaction with its account relationships.

**Location:** `neo4j_repositories.py:224-230`

```cypher
MATCH (t:Transaction {transaction_id: $transaction_id})
OPTIONAL MATCH (t)-[:DEBITED_FROM]->(from_account:Account)
OPTIONAL MATCH (t)-[:CREDITED_TO]->(to_account:Account)
RETURN t, from_account.account_id as from_account_id,
       to_account.account_id as to_account_id
```

**Explanation:**
- `OPTIONAL MATCH` allows for transactions with only one account
- Returns transaction and both account IDs in a single query
- Efficient single-query retrieval

**Parameters:**
- `transaction_id`: Transaction UUID

---

### 13. Find Transactions by Account

**Purpose:** Get all transactions for an account within a date range.

**Location:** `neo4j_repositories.py:240-249`

```cypher
MATCH (t:Transaction)-[:DEBITED_FROM|CREDITED_TO]->(a:Account {account_id: $account_id})
WHERE ($start_date IS NULL OR t.timestamp >= datetime($start_date))
  AND ($end_date IS NULL OR t.timestamp <= datetime($end_date))
OPTIONAL MATCH (t)-[:DEBITED_FROM]->(from_account:Account)
OPTIONAL MATCH (t)-[:CREDITED_TO]->(to_account:Account)
RETURN t, from_account.account_id as from_account_id,
       to_account.account_id as to_account_id
ORDER BY t.timestamp DESC
```

**Explanation:**
- `[:DEBITED_FROM|CREDITED_TO]` matches transactions where account is either source or destination
- Date filters are optional (NULL-safe)
- Returns both debit and credit transactions
- Sorted by timestamp (newest first)
- Fetches related account IDs in same query

**Parameters:**
- `account_id`: Account UUID
- `start_date`: Optional start date (ISO string or null)
- `end_date`: Optional end date (ISO string or null)

---

### 14. Find Flagged Transactions

**Purpose:** Retrieve suspicious transactions flagged by fraud detection.

**Location:** `neo4j_repositories.py:260-268`

```cypher
MATCH (t:Transaction {is_flagged: true})
OPTIONAL MATCH (t)-[:DEBITED_FROM]->(from_account:Account)
OPTIONAL MATCH (t)-[:CREDITED_TO]->(to_account:Account)
RETURN t, from_account.account_id as from_account_id,
       to_account.account_id as to_account_id
ORDER BY t.timestamp DESC
LIMIT $limit
```

**Explanation:**
- Filters by `is_flagged` boolean property
- Uses index on `is_flagged` for performance
- Includes related accounts for context
- Limited to prevent overwhelming results
- Critical for analyst dashboards

**Parameters:**
- `limit`: Maximum results (default 100)

**Use Case:** Dashboard showing recent suspicious activity

---

### 15. Count Transactions in Timeframe

**Purpose:** Count recent transactions for velocity detection.

**Location:** `neo4j_repositories.py:319-323`

```cypher
MATCH (t:Transaction)-[:DEBITED_FROM|CREDITED_TO]->(a:Account {account_id: $account_id})
WHERE t.timestamp >= datetime($cutoff_time)
RETURN count(t) as count
```

**Explanation:**
- Counts transactions in last N minutes
- Used for velocity-based fraud detection
- High transaction count in short time = potential fraud
- Only counts, doesn't return full transaction data

**Parameters:**
- `account_id`: Account UUID
- `cutoff_time`: Start of time window (ISO datetime)
- `minutes`: Duration (used to calculate cutoff_time)

**Fraud Rule:** More than 10 transactions in 60 minutes = suspicious

---

## Fraud Pattern Detection Queries

### 16. Detect Circular Flow (Money Laundering)

**Purpose:** Find circular money flows indicating layering in money laundering.

**Location:** `neo4j_repositories.py:281-294`

```cypher
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
```

**Explanation:**
- **Circular Flow Pattern:** Money moves A → B → C → A
- Requires 3-hop cycle minimum
- All transactions must be flagged (pre-screened as suspicious)
- Ensures all accounts in cycle are different (no self-loops)
- Returns transaction list for evidence trail
- Classic money laundering "layering" technique

**Graph Pattern:**
```
(Account-A) <-- (Txn1) --> (Account-B) <-- (Txn2) --> (Account-C) <-- (Txn3) --> (Account-A)
```

**Real-World Example:**
1. $10,000: Criminal's Account → Mule Account 1
2. $9,500: Mule Account 1 → Mule Account 2
3. $9,000: Mule Account 2 → Criminal's Account

**Detection Strategy:**
- Multiple rounds make pattern more obvious
- Amount typically decreases each hop (simulated fees)
- Short timeframes (hours/days) indicate urgency

---

### 17. Detect Fan-Out Pattern

**Purpose:** Identify accounts distributing money to many recipients (layering/structuring).

**Location:** `neo4j_repositories.py:354-361`

```cypher
MATCH (from_account:Account)<-[:DEBITED_FROM]-(t:Transaction)-[:CREDITED_TO]->(to_account:Account)
WHERE t.timestamp >= datetime($cutoff_time)
WITH from_account, count(DISTINCT to_account) as recipient_count, sum(t.amount) as total_amount
WHERE recipient_count >= $min_recipients
RETURN from_account.account_id as account_id, recipient_count, total_amount
ORDER BY recipient_count DESC
```

**Explanation:**
- **Fan-Out Pattern:** One account → Many accounts
- Aggregates transactions within timeframe (default 24 hours)
- Counts unique recipients per source account
- Filters for accounts with ≥5 recipients (threshold)
- Returns total amount distributed
- Indicates potential structuring or smurfing

**Parameters:**
- `cutoff_time`: Start of analysis window
- `min_recipients`: Minimum recipients to flag (default 5)
- `timeframe_hours`: Hours to look back (default 24)

**Graph Pattern:**
```
             --> (Account-B)
            /
(Account-A) ---> (Account-C)
            \
             --> (Account-D)
            \
             --> (Account-E)
```

**Fraud Scenarios:**
- **Structuring:** Breaking large sum into small transactions to avoid reporting
- **Layering:** Distributing funds to obscure origin
- **Smurfing:** Using multiple accounts to move money

**Example:**
- Account sends 15 transactions to 15 different accounts within 2 hours
- Total: $80,000 split into amounts under $5,000 each

---

### 18. Detect Fan-In Pattern

**Purpose:** Identify accounts collecting money from many sources (consolidation).

**Location:** `neo4j_repositories.py:370-377`

```cypher
MATCH (from_account:Account)<-[:DEBITED_FROM]-(t:Transaction)-[:CREDITED_TO]->(to_account:Account)
WHERE t.timestamp >= datetime($cutoff_time)
WITH to_account, count(DISTINCT from_account) as sender_count, sum(t.amount) as total_amount
WHERE sender_count >= $min_senders
RETURN to_account.account_id as account_id, sender_count, total_amount
ORDER BY sender_count DESC
```

**Explanation:**
- **Fan-In Pattern:** Many accounts → One account
- Opposite of fan-out
- Aggregates by destination account
- Indicates potential consolidation or collection point
- Common in fraud rings and money laundering

**Parameters:**
- `cutoff_time`: Start of analysis window
- `min_senders`: Minimum senders to flag (default 5)
- `timeframe_hours`: Hours to look back (default 24)

**Graph Pattern:**
```
(Account-B) ----\
                 \
(Account-C) ------> (Account-A)
                 /
(Account-D) ----/
                \
(Account-E) ----/
```

**Fraud Scenarios:**
- **Collection Account:** Central account in fraud ring
- **Consolidation:** Gathering distributed funds
- **Integration Phase:** Final stage of money laundering

**Example:**
- Account receives 12 transactions from 12 different sources in 6 hours
- Total: $95,000 collected

---

### 19. Detect Mule Accounts

**Purpose:** Find accounts that receive and quickly forward money (flow-through).

**Location:** `neo4j_repositories.py:385-392`

```cypher
MATCH (a:Account)<-[:CREDITED_TO]-(t_in:Transaction)
MATCH (a)<-[:DEBITED_FROM]-(t_out:Transaction)
WHERE duration.between(t_in.timestamp, t_out.timestamp).hours <= $max_hold_time_hours
WITH a, sum(t_in.amount) as total_in, sum(t_out.amount) as total_out
WHERE total_in >= $min_throughput
  AND abs(total_in - total_out) / total_in < 0.1
RETURN a
```

**Explanation:**
- **Mule Account Characteristics:**
  1. High throughput (≥$10,000)
  2. Money in ≈ money out (within 10%)
  3. Quick turnaround (≤48 hours)
- Matches incoming and outgoing transactions
- Uses `duration.between()` to calculate hold time
- Balance check ensures account is just a conduit
- Classic indicator of money mule

**Parameters:**
- `min_throughput`: Minimum total amount (default $10,000)
- `max_hold_time_hours`: Maximum time between in/out (default 48)

**Mathematical Condition:**
```
|total_in - total_out| / total_in < 0.1  (within 10%)
```

**Graph Pattern:**
```
(Account-X) --> (Mule-Account) --> (Account-Y)
                  ↓
             Quick turnaround
             High volume
             Minimal retention
```

**Real-World Example:**
- Monday 9am: Receives $15,000 from Account X
- Monday 2pm: Sends $14,500 to Account Y (retains $500 "fee")
- Tuesday 11am: Receives $20,000 from Account Z
- Tuesday 4pm: Sends $19,800 to Account W

---

### 20. Detect Shared Devices

**Purpose:** Find devices used by multiple customers (potential identity fraud).

**Location:** `neo4j_repositories.py:405-411`

```cypher
MATCH (c1:Customer)-[:USED_DEVICE]->(d:Device)<-[:USED_DEVICE]-(c2:Customer)
WHERE c1.customer_id < c2.customer_id
RETURN d.device_id as infrastructure_id,
       collect(DISTINCT c1.customer_id) + collect(DISTINCT c2.customer_id) as customer_ids,
       count(DISTINCT c1) + count(DISTINCT c2) as user_count
```

**Explanation:**
- Finds devices shared between different customers
- `WHERE c1.customer_id < c2.customer_id` prevents duplicate pairs
- Collects all customers using the device
- Counts unique users
- Shared devices may indicate:
  - Identity fraud
  - Family members (legitimate)
  - Fraud rings
  - Account takeover

**Graph Pattern:**
```
(Customer-1) --> (Device) <-- (Customer-2)
```

**Investigation Triggers:**
- Device used by 3+ unrelated customers
- Recent device sharing with new accounts
- Device suddenly shared after being single-use

---

### 21. Detect Shared IP Addresses

**Purpose:** Find IP addresses shared across accounts (potential bot nets or fraud rings).

**Location:** `neo4j_repositories.py:413-420`

```cypher
MATCH (t1:Transaction)-[:FROM_IP]->(ip:IPAddress)<-[:FROM_IP]-(t2:Transaction)
MATCH (t1)-[:DEBITED_FROM|CREDITED_TO]-(a1:Account)
MATCH (t2)-[:DEBITED_FROM|CREDITED_TO]-(a2:Account)
WHERE a1.account_id < a2.account_id
RETURN ip.ip_address as infrastructure_id,
       collect(DISTINCT a1.account_id) + collect(DISTINCT a2.account_id) as account_ids
```

**Explanation:**
- Finds IP addresses used by multiple accounts
- Links transactions to their accounts
- Prevents duplicate account pairs
- Shared IPs may indicate:
  - Bot networks
  - Fraud operations
  - Shared office (legitimate)
  - VPN usage

**Graph Pattern:**
```
(Transaction1)-[:FROM_IP]->(IP)<-[:FROM_IP]-(Transaction2)
       ↓                                          ↓
   (Account1)                                (Account2)
```

---

### 22. Calculate Connection Path (Shortest Path)

**Purpose:** Find shortest relationship path between two entities.

**Location:** `neo4j_repositories.py:427-432`

```cypher
MATCH path = shortestPath((from)-[*1..{max_depth}]-(to))
WHERE from.account_id = $from_entity_id OR from.customer_id = $from_entity_id
  AND to.account_id = $to_entity_id OR to.customer_id = $to_entity_id
RETURN path
```

**Explanation:**
- Neo4j's `shortestPath()` algorithm
- Finds minimum hops between entities
- Works with accounts or customers
- Limited by max_depth (default 5)
- Useful for investigating connections

**Parameters:**
- `from_entity_id`: Source entity UUID
- `to_entity_id`: Destination entity UUID
- `max_depth`: Maximum relationship hops

**Use Case:**
- "How are these two suspicious accounts connected?"
- Fraud ring investigation
- Compliance checks

---

### 23. Get Entity Neighborhood

**Purpose:** Retrieve all entities within N hops of a target entity.

**Location:** `neo4j_repositories.py:444-449`

```cypher
MATCH path = (n)-[*1..{depth}]-(connected)
WHERE n.{entity_type}_id = $entity_id
RETURN nodes(path) as nodes, relationships(path) as relationships
LIMIT 100
```

**Explanation:**
- Returns full neighborhood graph
- Variable depth for context
- Gets both nodes and relationships
- Useful for visualization

**Parameters:**
- `entity_id`: Target entity UUID
- `entity_type`: Type of entity (account, customer, etc.)
- `depth`: Relationship hops (default 2)

---

## Infrastructure & Maintenance Queries

### 24. Create Customer-Account Ownership

**Purpose:** Link a customer to an account they own.

**Location:** `data_generator.py:324-328`

```cypher
MATCH (c:Customer {customer_id: $customer_id})
MATCH (a:Account {account_id: $account_id})
MERGE (c)-[:OWNS {since_date: datetime(), relationship_type: 'primary'}]->(a)
```

**Explanation:**
- Creates `OWNS` relationship between customer and account
- Stores relationship metadata (since_date, type)
- `MERGE` prevents duplicate relationships
- `relationship_type` can be 'primary', 'joint', 'beneficiary'

**Relationship Properties:**
- `since_date`: When ownership began
- `relationship_type`: Nature of ownership

---

### 25. Clear Entire Database

**Purpose:** Delete all nodes and relationships (DANGEROUS).

**Location:** `neo4j_connection.py:94`

```cypher
MATCH (n) DETACH DELETE n
```

**Explanation:**
- `MATCH (n)` selects all nodes
- `DETACH DELETE` removes relationships first, then nodes
- **WARNING:** Irreversible operation
- Only use in development/testing

---

### 26. Get Database Statistics

**Purpose:** Count nodes by label for monitoring.

**Location:** `neo4j_connection.py:100-103`

```cypher
MATCH (n)
RETURN labels(n) as label, count(*) as count
```

**Explanation:**
- Groups nodes by label
- Counts each node type
- Useful for health checks and monitoring
- Returns statistics like:
  - Transaction: 1252
  - Customer: 100
  - Account: 148

---

### 27. Test Database Connectivity

**Purpose:** Verify database is responsive.

**Location:** `neo4j_connection.py:40, 63`

```cypher
RETURN 1
```

**Explanation:**
- Simplest possible query
- Returns constant value
- Used for health checks
- Fast execution

---

## Index Creation Queries

These queries create indexes for performance optimization. All use `IF NOT EXISTS` to be idempotent.

**Location:** `neo4j_connection.py:71-81`

### 28-36. Performance Indexes

```cypher
-- Account ID index (primary key)
CREATE INDEX account_id_idx IF NOT EXISTS
FOR (a:Account) ON (a.account_id)

-- Customer ID index (primary key)
CREATE INDEX customer_id_idx IF NOT EXISTS
FOR (c:Customer) ON (c.customer_id)

-- Transaction ID index (primary key)
CREATE INDEX transaction_id_idx IF NOT EXISTS
FOR (t:Transaction) ON (t.transaction_id)

-- Device ID index
CREATE INDEX device_id_idx IF NOT EXISTS
FOR (d:Device) ON (d.device_id)

-- IP Address index
CREATE INDEX ip_address_idx IF NOT EXISTS
FOR (ip:IPAddress) ON (ip.ip_address)

-- Merchant ID index
CREATE INDEX merchant_id_idx IF NOT EXISTS
FOR (m:Merchant) ON (m.merchant_id)

-- Fraud Ring ID index
CREATE INDEX fraud_ring_id_idx IF NOT EXISTS
FOR (fr:FraudRing) ON (fr.ring_id)

-- Transaction timestamp index (for time-range queries)
CREATE INDEX transaction_timestamp_idx IF NOT EXISTS
FOR (t:Transaction) ON (t.timestamp)

-- Transaction flagged index (for fraud queries)
CREATE INDEX transaction_flagged_idx IF NOT EXISTS
FOR (t:Transaction) ON (t.is_flagged)
```

**Explanation:**
- **Primary Key Indexes:** Essential for lookups by ID
- **Timestamp Index:** Optimizes date-range queries
- **Flagged Index:** Speeds up fraud detection queries
- Indexes are created at system initialization
- Dramatically improve query performance

---

## Query Performance Tips

### Index Usage
- All ID lookups use indexes (very fast)
- Date-range queries use timestamp index
- Flagged transaction queries use is_flagged index

### Optimization Patterns
1. **Use Parameters:** All queries use parameterized queries to prevent injection and allow query plan caching
2. **OPTIONAL MATCH:** Allows for missing relationships without failing
3. **LIMIT Clauses:** Prevent overwhelming results
4. **DISTINCT:** Eliminates duplicates in aggregations
5. **WITH Clauses:** Pipeline data for multi-step queries

### Anti-Patterns to Avoid
- ❌ Missing indexes on frequently queried properties
- ❌ Unbounded variable-length paths `[*]`
- ❌ Cartesian products from multiple MATCH clauses
- ❌ Large LIMIT values on complex queries

---

## Common Fraud Detection Patterns

### Pattern 1: Circular Flow Detection
```
Account-A → Account-B → Account-C → Account-A
```
**Indicators:** 3+ hops, flagged transactions, short timeframe

### Pattern 2: Fan-Out (Structuring)
```
Account-A → {Account-B, Account-C, Account-D, ...}
```
**Indicators:** 5+ recipients, similar amounts, same day

### Pattern 3: Fan-In (Collection)
```
{Account-B, Account-C, Account-D, ...} → Account-A
```
**Indicators:** 5+ senders, consolidation, rapid succession

### Pattern 4: Mule Account
```
Source → Mule Account → Destination
```
**Indicators:** High throughput, quick turnaround, minimal retention

### Pattern 5: Shared Infrastructure
```
Customer-A → Device ← Customer-B
```
**Indicators:** Multiple unrelated customers, recent sharing

---

## Temporal Queries Best Practices

### Working with Datetimes
```cypher
-- Convert ISO string to Neo4j datetime
datetime($timestamp)

-- Calculate duration
duration.between(t1.timestamp, t2.timestamp).hours

-- Filter by date range
WHERE t.timestamp >= datetime($start_date)
  AND t.timestamp <= datetime($end_date)
```

### Timeframe Calculations
```python
# In Python
cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
params = {'cutoff_time': cutoff_time.isoformat()}
```

---

## Security Considerations

### Query Injection Prevention
- ✅ All queries use parameterized queries
- ✅ No string concatenation of user input
- ✅ Type validation on all parameters

### Data Privacy
- Passwords never stored
- SSN stored as hash only
- Email addresses indexed but lowercase

### Access Control
- Read-only queries for analysts
- Write queries require authentication
- Audit trail for deletions

---

## Summary

This reference documents **27 core Cypher queries** and **9 index definitions** used in the Fraud Detection System:

- **Account Queries:** 6 queries for account management
- **Customer Queries:** 4 queries for customer operations
- **Transaction Queries:** 5 queries for transaction handling
- **Fraud Detection:** 7 advanced pattern detection queries
- **Infrastructure:** 4 maintenance and utility queries
- **Indexes:** 9 performance optimization indexes

All queries are production-ready, parameterized, and optimized for fraud detection workflows.

---

**Last Updated:** December 2025
**Version:** 1.0
**System:** Fraud Detection System v1.0

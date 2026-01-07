# Fraud Detection System - Beginner's Guide

## What is This System?

This is a fraud detection system that helps financial institutions identify suspicious activities and fraud rings in banking transactions. Think of it as a detective tool that automatically finds connections between suspicious accounts and transactions.

## Core Concepts for Beginners

### 1. What is Fraud Detection?

Fraud detection is the process of identifying suspicious activities in financial transactions. Fraudsters often:
- Move money quickly through multiple accounts
- Use the same devices or IP addresses with different accounts
- Create circular money flows to confuse tracking
- Distribute money to many accounts (fan-out) or collect from many (fan-in)

### 2. What is a Graph Database?

Imagine your social network - you have friends, who have friends, who have friends. A graph database stores information this way, showing connections between things.

In our system:
- **Nodes (dots)** = Things like accounts, customers, transactions
- **Edges (lines)** = Relationships like "owns account" or "transferred to"

### 3. Why Use Graph Databases for Fraud?

Traditional databases store data in tables (like Excel). But fraud is all about connections:
- "Which accounts share the same device?"
- "How is money moving between accounts?"
- "Are these customers connected somehow?"

Graph databases make these questions easy to answer!

## Understanding Key Components

### Entities (The Building Blocks)

1. **Customer**: A person or business with bank accounts
   - Has name, email, address, etc.
   - Can own multiple accounts

2. **Account**: A bank account
   - Checking, savings, or credit account
   - Has balance and risk score

3. **Transaction**: Money moving between accounts
   - Amount, timestamp, type (transfer, withdrawal, etc.)
   - Can be flagged as suspicious

4. **Device**: Computer or phone used to access accounts
   - Mobile, desktop, or tablet
   - Tracks which customers use which devices

5. **IP Address**: Internet address used in transactions
   - Shows geographic location
   - Can detect if using VPN or proxy

6. **Fraud Ring**: Group of connected fraudulent activities
   - Detected pattern (circular flow, fan-out, etc.)
   - Confidence score showing how sure we are

### Fraud Patterns We Detect

#### 1. Circular Money Flow
Money goes in a circle: Account A → Account B → Account C → Account A

**Why it's suspicious**: Legitimate transactions don't loop back. This could be money laundering.

**Example**:
```
Alice's account → Bob's account ($10,000)
Bob's account → Charlie's account ($9,500)
Charlie's account → Alice's account ($9,000)
```

#### 2. Fan-Out Pattern
One account sends money to many accounts quickly

**Why it's suspicious**: Could be distributing stolen money or money laundering

**Example**:
```
Main Account → 15 different accounts (within 1 hour)
```

#### 3. Fan-In Pattern
Many accounts send money to one account quickly

**Why it's suspicious**: Could be collecting fraudulent funds

**Example**:
```
20 different accounts → Central Account (within 24 hours)
```

#### 4. Velocity Pattern
Too many transactions in short time

**Why it's suspicious**: Normal users don't make 20 transactions in an hour

#### 5. Money Mule Accounts
Accounts that receive money and quickly forward it

**Why it's suspicious**: Money mules help move illegal funds

**Characteristics**:
- Receives large amount
- Forwards it within 24-48 hours
- Keeps small commission

#### 6. Shared Infrastructure
Multiple accounts using same device or IP address

**Why it's suspicious**: Could be one person controlling multiple accounts

## How the System Works

### Simple Flow:

1. **Data Collection**: System collects information about customers, accounts, and transactions

2. **Graph Creation**: Stores this data in Neo4j graph database with all the connections

3. **Pattern Detection**: Runs algorithms to find suspicious patterns

4. **Risk Scoring**: Calculates how risky each account is (0-100)

5. **Alert Generation**: Creates alerts for fraud analysts to investigate

6. **Investigation**: Analysts use the web dashboard to explore suspicious activities

## Risk Scoring Explained

Every account gets a risk score from 0-100:

- **0-30 (Low)**: Normal, safe account
- **30-60 (Medium)**: Some suspicious signs, monitor closely
- **60-85 (High)**: Very suspicious, investigate
- **85-100 (Critical)**: Almost certainly fraudulent, take action

Risk score considers:
- Transaction velocity (how many, how fast)
- Flagged transactions
- Account age (new accounts are riskier)
- High-value transactions
- Connections to known fraudsters

## Using the System (Analyst Dashboard)

### Dashboard Overview

When you open the web interface, you see:

1. **Statistics Cards**:
   - Flagged transactions count
   - High-risk accounts count
   - Active fraud rings being investigated
   - Critical alerts needing attention

2. **High-Risk Accounts Table**:
   - Accounts sorted by risk score
   - Click to investigate details

3. **Flagged Transactions Table**:
   - Recent suspicious transactions
   - Shows fraud score and amount

4. **Investigation Search**:
   - Search by account ID, customer ID, or email
   - Get detailed investigation results

### Running Fraud Detection

Click "Run Fraud Detection" button to:
- Scan all data for patterns
- Create fraud rings from detected patterns
- Update risk scores
- Generate new alerts

### Investigating an Account

Click on any account to see:
- Account details and risk score
- Recent transactions (last 30 days)
- Flagged transactions
- Transaction velocity (1 hour, 24 hours)
- Connected accounts and customers (neighborhood graph)
- Risk factors explaining the risk score

## Technology Stack (Simplified)

- **Python**: Programming language used for the system
- **Neo4j**: Graph database storing all the data
- **Flask**: Web framework for the analyst dashboard
- **HTML/CSS/JavaScript**: Frontend for the web interface

## Getting Started

### Prerequisites

You need to install:
1. Python 3.8 or higher
2. Neo4j database
3. Python packages (listed in requirements.txt)

### Setup Steps

1. **Install Neo4j**:
   - Download from neo4j.com
   - Start Neo4j server
   - Note your username and password

2. **Configure Environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your Neo4j credentials
   ```

3. **Install Python Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Generate Sample Data**:
   ```bash
   python -m src.data_generator
   ```

5. **Start Web Application**:
   ```bash
   python -m src.web.app
   ```

6. **Open Dashboard**:
   - Go to http://localhost:5000 in your browser

## Common Questions

### How much data can it handle?
The system can handle millions of accounts and billions of transactions using Neo4j's graph algorithms.

### How fast is fraud detection?
Pattern detection runs in seconds to minutes depending on data size.

### Can I customize the fraud patterns?
Yes! You can add new detection algorithms in the FraudDetectionService.

### Is the data secure?
Yes, customer SSNs are hashed, and the system follows security best practices.

### Can I integrate with existing systems?
Yes, you can modify the data generator to pull from your banking system's API.

## Key Terminology

- **Node**: A thing in the graph (account, customer, etc.)
- **Edge/Relationship**: Connection between nodes
- **Cypher**: Query language for Neo4j (like SQL for graph databases)
- **DDD**: Domain-Driven Design - organizing code around business concepts
- **Repository**: Layer that handles database access
- **Entity**: Business object with unique identity
- **Value Object**: Business concept without identity (like Money, RiskScore)

## Next Steps

After understanding the basics:
1. Read the Professional Documentation for technical details
2. Explore the code walkthrough to understand implementation
3. Try the Analyst Guide to learn investigation techniques
4. Read FAQ for common scenarios

## Helpful Resources

- Neo4j Documentation: https://neo4j.com/docs/
- Python Documentation: https://docs.python.org/
- Flask Documentation: https://flask.palletsprojects.com/
- Domain-Driven Design: Book by Eric Evans

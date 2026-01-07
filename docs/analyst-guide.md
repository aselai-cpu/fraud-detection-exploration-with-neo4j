# Fraud Analyst Guide - Discovering Fraud Through the System

## Introduction

This guide is designed for fraud analysts - the professionals who investigate suspicious activities and make decisions about potential fraud cases. You'll learn how to effectively use the Fraud Detection System to uncover fraud rings, investigate suspicious accounts, and build cases for further action.

## Understanding Your Role

As a fraud analyst using this system, your job is to:
1. **Triage** automated fraud detection alerts
2. **Investigate** suspicious accounts and transactions
3. **Connect the dots** to uncover fraud rings
4. **Document** evidence for legal/compliance teams
5. **Provide feedback** to improve detection algorithms

You are the critical human element that validates and contextualizes what the machine detects.

## Getting Started

### Accessing the Dashboard

1. Open your browser to: `http://localhost:5000` (or your organization's URL)
2. The dashboard loads automatically with current statistics

### Dashboard Overview

The main dashboard shows four key metrics:

**Flagged Transactions**: Number of transactions the system considers suspicious
- High number = need to triage
- Sudden spike = possible attack in progress

**High Risk Accounts**: Accounts with risk score > 60
- Your primary investigation queue
- Sorted by risk score (highest first)

**Active Fraud Rings**: Fraud rings currently under investigation
- Groups of connected suspicious accounts
- Track ongoing cases

**Critical Alerts**: Alerts marked as critical (risk level: CRITICAL)
- Immediate attention required
- Typically high-value or high-confidence fraud

## Daily Workflow

### Morning Routine

1. **Review Dashboard Metrics**
   - Any unusual spikes?
   - Critical alerts needing immediate attention?

2. **Run Fraud Detection** (if not automated)
   - Click "Run Fraud Detection" button
   - Wait for patterns to be detected
   - Review summary of findings

3. **Triage Critical Alerts**
   - Start with CRITICAL severity
   - Move to HIGH, then MEDIUM

### Investigation Process

## How to Investigate Suspicious Accounts

### Step 1: Initial Review

Click on a high-risk account in the dashboard. You'll see:

```
Account Investigation Panel
-------------------------
Account Number: 1234567890
Risk Score: 85.2 (CRITICAL)
Status: ACTIVE
Balance: $45,231.00

Risk Factors:
- High transaction velocity: 18 txns in last hour
- Shared device with known fraudster
- New account: only 12 days old
- Fan-out pattern detected: sent to 15 accounts

Transactions (Last 30 days): 234
Flagged Transactions: 47
```

### Step 2: Analyze Risk Factors

Each factor tells a story:

**High Transaction Velocity**
- Normal: 1-5 transactions per day
- Suspicious: 10+ transactions per hour
- Question: Why the sudden activity?

**Shared Infrastructure**
- Same device/IP as known fraudster = Strong signal
- Same device/IP as family member = Weak signal (investigate further)

**Account Age**
- New accounts + high activity = Synthetic identity or money mule
- Old accounts + sudden change = Compromised account

**Patterns (Fan-out, Fan-in, Circular)**
- See "Fraud Pattern Guide" below

### Step 3: Examine Transactions

Review recent transactions looking for:

1. **Amount Patterns**
   - Just under reporting thresholds ($9,999 instead of $10,000)?
   - Round numbers (exactly $5,000, $10,000)?
   - Unusual for this account?

2. **Timing Patterns**
   - All at unusual hours (3am-5am)?
   - Rapid succession (every 2-3 minutes)?
   - Weekends/holidays only?

3. **Destination Patterns**
   - Multiple transfers to new accounts?
   - International transfers to high-risk countries?
   - Merchant categories that don't fit profile?

### Step 4: Explore the Network

Click "View Neighborhood" to see connected entities:

```
Network View:
- Account A (Current)
  ├─ Used Device D123 (SHARED with Account B)
  ├─ Sent to Account B ($10,000)
  ├─ Sent to Account C ($9,500)
  └─ Received from Account D ($50,000)

- Account B
  ├─ Used Device D123 (SHARED)
  ├─ Sent to Account E ($9,000)
  └─ Customer: John Smith (KYC: FAILED)

- Account C
  ├─ Sent to Account A ($8,500) <- CIRCULAR FLOW!
  └─ Customer: Jane Doe (KYC: VERIFIED)
```

**Red flags in network**:
- Shared devices across "unrelated" accounts
- Circular money flows
- Failed KYC in the network
- Geographic anomalies (NYC account using London IP)

### Step 5: Build the Case

Document your findings:

1. **Suspicious Indicators** (what you found)
2. **Supporting Evidence** (transactions, patterns, connections)
3. **Confidence Level** (LOW, MEDIUM, HIGH)
4. **Recommended Action** (freeze, investigate further, close case)

Use the "Generate Report" button to create a formal investigation report.

## Understanding Fraud Patterns

### Pattern 1: Circular Money Flow

**What it is**: Money moving in a circle through multiple accounts

**Example**:
```
Account A → $10,000 → Account B
Account B → $9,500 → Account C  (5% fee taken)
Account C → $9,000 → Account A  (another 5% fee)
```

**Why it's fraud**:
- Laundering: Clean dirty money through legitimate-looking transfers
- Fee skimming: Each hop extracts a small fee
- Confusion: Complex path hides original source

**How to detect**:
- Look for money returning to source
- Check if accounts are "unrelated" but tightly connected
- Same timing pattern (each hop within hours)

**Investigation checklist**:
- [ ] Verify accounts belong to different people
- [ ] Check if legitimate business relationship exists
- [ ] Examine purpose of transfers
- [ ] Calculate total fees extracted
- [ ] Identify the "organizer" account

### Pattern 2: Fan-Out (Structuring)

**What it is**: One account distributing money to many accounts rapidly

**Example**:
```
Main Account ($100,000)
  ├─ $6,000 → Account 1
  ├─ $5,500 → Account 2
  ├─ $7,200 → Account 3
  ├─ $5,800 → Account 4
  ... (15 more accounts)
```

**Why it's fraud**:
- **Structuring**: Breaking large amount into small amounts to avoid reporting
- **Money mule payment**: Distributing to "employees" who will cash out
- **Rapid distribution**: Fraudster wants to move money before account frozen

**How to detect**:
- Many outbound transfers in short time (< 24 hours)
- Amounts just under reporting threshold ($9,000-$9,999)
- Recipient accounts newly created
- Geographic spread (recipients across country)

**Investigation checklist**:
- [ ] Check if recipients are real people (synthetic IDs?)
- [ ] Verify source of funds in main account
- [ ] Look for similar past patterns from this account
- [ ] Check if recipients have cashed out already
- [ ] Identify any that can be frozen

### Pattern 3: Fan-In (Collection)

**What it is**: Many accounts sending money to one account rapidly

**Example**:
```
Central Account
  ← $1,500 from Account 1
  ← $2,000 from Account 2
  ← $1,800 from Account 3
  ... (20 source accounts)
```

**Why it's fraud**:
- **Mule account collection**: Central account collecting from money mules
- **Carding**: Multiple stolen cards funding one account
- **Aggregation**: Collecting ill-gotten gains before cashout

**How to detect**:
- Many inbound transfers in short time
- Source accounts show signs of compromise
- Central account created recently
- Quick withdrawal after collection

**Investigation checklist**:
- [ ] Contact source account owners (victims?)
- [ ] Check if central account has legitimate business
- [ ] Look for withdrawal patterns after collection
- [ ] Identify beneficiary of central account
- [ ] Check for international wire after collection

### Pattern 4: Money Mule Accounts

**What it is**: Accounts that receive and quickly forward funds

**Example**:
```
Day 1: Receives $15,000 from Account X
Day 2: Sends $14,000 to Account Y (keeps $1,000 "fee")
Balance: Near zero before and after
```

**Why it's fraud**:
- **Witting mules**: Know they're helping fraud, want quick money
- **Unwitting mules**: Recruited via job scams, think it's legitimate
- **Purpose**: Create distance between fraud source and destination

**How to detect**:
- Receive → Forward within 24-48 hours
- Keeps 5-10% as "commission"
- Account mostly dormant except for mule activities
- Young account holder (18-25) common for unwitting mules

**Investigation checklist**:
- [ ] Contact account holder (witting or unwitting?)
- [ ] Check recruitment method (job ad, social media?)
- [ ] Trace backward to fraud source
- [ ] Trace forward to beneficiary
- [ ] Educate if unwitting victim

### Pattern 5: Shared Infrastructure

**What it is**: Multiple accounts controlled from same device or IP

**Example**:
```
Device D123:
  - Used by Customer A (Account 1, 2)
  - Used by Customer B (Account 3)
  - Used by Customer C (Account 4, 5, 6)

All 6 accounts showing suspicious activity
All "customers" claim to be unrelated
```

**Why it's fraud**:
- **Synthetic identity**: One person created fake identities
- **Account takeover**: Fraudster controlling multiple compromised accounts
- **Organized ring**: Team working from same location

**How to detect**:
- Device fingerprint matches
- Same IP address for transactions
- Login times correlate
- Similar typing patterns (advanced)

**Investigation checklist**:
- [ ] Verify if customers actually know each other
- [ ] Check if physical addresses match
- [ ] Review KYC documents (same photo in different applications?)
- [ ] Check account creation dates (all created same day?)
- [ ] Examine transaction patterns (coordinated?)

## Investigation Techniques

### Technique 1: Follow the Money

**Start**: Suspicious transaction
**Process**:
1. Where did the money come from? (trace backward)
2. Where did the money go? (trace forward)
3. Continue for 3-5 hops
4. Look for patterns

**Example**:
```
Stolen card → Mule Account 1 → Mule Account 2 → Bitcoin Exchange → Fraudster
```

Use the "Find Connection Path" feature:
```
From: suspicious_account_123
To: known_fraudster_456
Results: Path found in 4 hops
```

### Technique 2: Time-Based Analysis

**Look for**:
- Transactions at unusual hours (fraudsters work at night)
- Burst patterns (rapid activity after account compromise)
- Patterns tied to external events (data breach news → spike in fraud)

**Dashboard feature**: Filter transactions by time range

### Technique 3: Amount Analysis

**Red flags**:
- Amounts just under thresholds (structuring)
- Very round numbers ($10,000 not $10,247.89)
- Consistent amounts (always $5,000)
- Incremental testing ($10, $100, $1000, then $10,000)

### Technique 4: Geographic Analysis

**Questions**:
- Account in NYC, transactions from Moscow?
- Sudden change in location?
- Multiple countries in same day?
- High-risk jurisdiction involvement?

**Check**: IP address country vs account address

### Technique 5: Behavioral Profiling

**Establish baseline**: Normal behavior for this account
- Typical transaction amount
- Typical transaction frequency
- Typical merchants
- Typical time of day

**Flag deviations**:
- 2x above normal = investigate
- 5x above normal = freeze

## Making Decisions

### When to Flag as Fraud

**High Confidence Indicators** (2+ present):
- Matches known fraud pattern exactly
- Connected to confirmed fraud ring
- Customer admits to unauthorized transactions
- Clear evidence of synthetic identity
- Money trail leads to known fraudster

**Action**: Mark as CONFIRMED FRAUD, freeze account, file SAR

### When to Mark as False Positive

**Legitimate Explanations**:
- Customer verifies transactions
- Legitimate business reason exists
- Seasonal/expected behavior
- System misconfigured (threshold too low)

**Action**: Mark as FALSE POSITIVE, document reason, adjust thresholds

### When to Investigate Further

**Uncertain Cases**:
- Some indicators but not conclusive
- Need customer contact
- Awaiting external information
- Complex case requiring deep analysis

**Action**: Keep in INVESTIGATING status, set follow-up date

## Working with Fraud Rings

### Identifying a Fraud Ring

A fraud ring is a group of accounts working together. Indicators:

1. **Shared infrastructure**: Same devices, IPs, addresses
2. **Coordinated timing**: Transactions happen in sequence
3. **Money flows**: Circular or hierarchical money movement
4. **Relationship**: Accounts "know" each other in graph

### Analyzing a Fraud Ring

When you identify a ring:

1. **Map the structure**:
   - Who's the organizer? (hub with most connections)
   - Who are the mules? (pass-through accounts)
   - Who are the victims? (source of funds)
   - Who's the beneficiary? (final destination)

2. **Calculate impact**:
   - Total amount moved
   - Number of victims
   - Number of accounts involved
   - Duration of operation

3. **Find evidence**:
   - Transaction records
   - Device logs
   - IP addresses
   - Communication (if available)

### Disrupting a Fraud Ring

**Immediate actions**:
- Freeze all accounts in ring
- Stop in-flight transactions
- Alert other institutions (if multi-bank)

**Follow-up**:
- Contact victims
- File SARs for all involved accounts
- Coordinate with law enforcement
- Update detection rules to catch similar rings

## Using the API for Advanced Analysis

For power users, use the API directly:

### Get High-Risk Accounts
```bash
curl http://localhost:5000/api/accounts/high-risk?limit=50
```

### Investigate Specific Account
```bash
curl http://localhost:5000/api/accounts/{account_id}/investigate
```

### Find Connection Between Accounts
```bash
curl "http://localhost:5000/api/connection/path?from=account1&to=account2"
```

### Run Fraud Detection
```bash
curl -X POST http://localhost:5000/api/fraud-patterns/detect
```

### Generate Report
```bash
curl -X POST http://localhost:5000/api/report/generate \
  -H "Content-Type: application/json" \
  -d '{"entity_id": "account_123", "entity_type": "account"}'
```

## Best Practices

### Do's

1. **Document everything**: Every investigation step
2. **Follow hunches**: Your intuition is valuable
3. **Verify before acting**: Freeze accounts only with good cause
4. **Collaborate**: Share findings with team
5. **Provide feedback**: Tell developers about missed cases
6. **Stay updated**: Learn new fraud techniques
7. **Balance speed and accuracy**: Fast triage, thorough investigation

### Don'ts

1. **Don't ignore context**: Numbers alone don't tell the story
2. **Don't assume**: Verify everything
3. **Don't tunnel vision**: Look at the bigger picture
4. **Don't forget privacy**: Handle customer data responsibly
5. **Don't work in isolation**: Fraud rings require team effort
6. **Don't fear false alarms**: Better safe than sorry
7. **Don't stop learning**: Fraud evolves constantly

## Performance Metrics

Track your effectiveness:

### Individual Metrics
- **Cases reviewed per day**: Throughput
- **True positive rate**: Accuracy
- **False positive rate**: Efficiency
- **Average investigation time**: Speed
- **Amount of fraud prevented**: Impact

### Team Metrics
- **Fraud detection rate**: % of fraud caught
- **Time to detection**: Speed of response
- **Recovery rate**: Money recovered
- **SAR filing rate**: Compliance

## Case Studies

### Case Study 1: Synthetic Identity Ring

**Alert**: High-risk account with failed KYC

**Investigation**:
1. Account opened 5 days ago
2. Immediately received $25,000 from 3 different accounts
3. Started distributing to 10 accounts
4. All accounts shared Device D789

**Discovery**:
- Device D789 used by 15 different "customers"
- All KYC documents used same photo
- All addresses were vacant lots
- Social security numbers were fabricated

**Outcome**:
- Froze all 15 accounts
- Recovered $180,000
- Filed SARs
- Updated KYC verification process

**Lesson**: Shared device + failed KYC + rapid activity = synthetic identity ring

### Case Study 2: Business Email Compromise

**Alert**: Large wire transfer to new beneficiary

**Investigation**:
1. Corporate account sent $500,000 to overseas account
2. Transfer initiated from new IP address
3. Beneficiary account created 2 days prior
4. Email showed slight domain misspelling

**Discovery**:
- CFO's email compromised
- Fraudster used look-alike domain
- Sent fake invoice
- AP clerk didn't verify (assumed legitimate)

**Outcome**:
- Stopped transfer (caught in 2 hours)
- All funds recovered
- Company improved email security

**Lesson**: Large amount + new beneficiary + unusual IP = potential BEC

### Case Study 3: Money Mule Network

**Alert**: Fan-in pattern detected

**Investigation**:
1. Central account received funds from 25 accounts
2. All source accounts showed signs of compromise
3. Central account holder was 22-year-old student
4. Found online recruitment ad for "payment processor"

**Discovery**:
- Unwitting money mule recruited via job scam
- Thought it was legitimate work-from-home job
- Paid $500 per $10,000 processed
- Source accounts were victims of account takeover

**Outcome**:
- Contacted mule (educated, not prosecuted)
- Returned funds to 25 victims
- Traced to organized fraud group
- Shut down 3 similar mule operations

**Lesson**: Young account holder + job scam + fan-in = mule recruitment

## Continuous Learning

### Stay Sharp

1. **Weekly case reviews**: Team discusses interesting cases
2. **Industry news**: Follow fraud trends
3. **Training**: Attend fraud conferences, webinars
4. **Certifications**: CFE (Certified Fraud Examiner)
5. **Share knowledge**: Mentor junior analysts

### Improve the System

**Feedback loop**:
- Found fraud the system missed? → Document why
- Too many false positives? → Recommend threshold adjustment
- New fraud technique? → Request new detection pattern
- UI confusing? → Suggest improvements

Your frontline experience is invaluable for system evolution.

## Conclusion

Fraud detection is part art, part science. This system provides the science (automated pattern detection, risk scoring, graph analysis). You provide the art (intuition, context, judgment).

Use the tools, trust your instincts, and remember: behind every suspicious transaction is a potential victim. Your work protects them.

## Quick Reference

### Investigation Checklist
- [ ] Review risk score and factors
- [ ] Examine recent transactions
- [ ] Check account history and age
- [ ] Explore neighborhood graph
- [ ] Look for patterns (circular, fan-out, fan-in)
- [ ] Verify customer information
- [ ] Check for shared infrastructure
- [ ] Trace money flow (backward and forward)
- [ ] Document findings
- [ ] Make decision (fraud, false positive, investigate further)
- [ ] Take action (freeze, contact, file SAR)

### Risk Score Guide
- **0-30**: Low risk - routine monitoring
- **30-60**: Medium risk - review when time permits
- **60-85**: High risk - investigate within 24 hours
- **85-100**: Critical risk - investigate immediately

### Pattern Quick Reference
- **Circular**: A→B→C→A (laundering)
- **Fan-out**: A→{B,C,D,E...} (structuring)
- **Fan-in**: {A,B,C,D...}→Z (collection)
- **Mule**: A→B→C (rapid forward)
- **Shared**: Accounts using same device/IP

### Contact Information
- **Compliance Team**: compliance@company.com
- **Law Enforcement Liaison**: leo@company.com
- **System Support**: support@company.com
- **Escalation**: manager@company.com

---

**Remember**: You're the last line of defense. Trust the system, but verify everything. When in doubt, investigate further. Better safe than sorry.

**Version**: 1.0.0
**Last Updated**: 2024

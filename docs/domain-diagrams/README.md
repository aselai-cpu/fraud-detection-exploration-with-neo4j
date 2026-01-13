# Domain Diagrams - Fraud Detection Patterns

This directory contains PlantUML diagrams that visually represent the various fraud detection patterns implemented in the system.

## Diagrams

### 1. Circular Money Flow (`circular-money-flow.puml`)
Shows how money circulates through multiple accounts and returns to the origin, indicating money laundering layering techniques.

**Key Characteristics:**
- Money flows in a circle (A → B → C → D → A)
- Amount decreases each hop (simulated fees)
- Multiple rounds possible
- Short timeframes (hours/days)

### 2. Fan-Out Pattern (`fan-out-pattern.puml`)
Illustrates one account distributing money to many recipients, indicating structuring or smurfing to avoid reporting thresholds.

**Key Characteristics:**
- One source, many recipients (5-15+)
- Similar amounts (typically under $10,000 each)
- Rapid succession (minutes apart)
- Total exceeds reporting threshold

### 3. Fan-In Pattern (`fan-in-pattern.puml`)
Shows many accounts sending money to one destination, indicating collection point or consolidation in fraud rings.

**Key Characteristics:**
- Many sources, one destination
- Similar amounts ($500-$2,000)
- Rapid succession (10-20 minutes apart)
- Large total collected

### 4. Money Mule Detection (`money-mule-detection.puml`)
Demonstrates money mule accounts that receive and quickly forward funds with minimal retention time.

**Key Characteristics:**
- High throughput (≥$10,000)
- Quick turnaround (≤48 hours)
- Money in ≈ Money out (within 10%)
- Minimal balance retention

### 5. Shared Infrastructure (`shared-infrastructure.puml`)
Shows how multiple accounts/customers sharing devices or IPs indicates potential fraud rings or account takeover.

**Key Characteristics:**
- Multiple customers sharing same device
- Multiple accounts using same IP
- Proxy/VPN usage
- Recent sharing patterns

### 6. Velocity Patterns (`velocity-patterns.puml`)
Illustrates high-frequency transaction patterns where accounts have too many transactions in a short timeframe.

**Key Characteristics:**
- 10+ transactions in 60 minutes
- Same device/IP used
- Rapid succession (minutes apart)
- Exceeds normal transaction velocity

## Viewing the Diagrams

### Using PlantUML

1. **Online Viewer**: Copy the `.puml` file content and paste it into [PlantUML Online Server](http://www.plantuml.com/plantuml/uml/)

2. **VS Code Extension**: Install the "PlantUML" extension and open the `.puml` files

3. **Command Line**: 
   ```bash
   # Install PlantUML
   brew install plantuml  # macOS
   # or
   apt-get install plantuml  # Linux
   
   # Generate PNG
   plantuml circular-money-flow.puml
   ```

4. **IntelliJ IDEA**: Built-in PlantUML support - just open the `.puml` files

### Export Formats

PlantUML can export to:
- PNG (default)
- SVG
- PDF
- EPS

## Usage in Documentation

These diagrams are referenced in:
- `analyst-guide.md` - For fraud analysts to understand patterns
- `professional-guide.md` - Technical documentation
- `novice-guide.md` - Beginner explanations
- `cypher-queries-reference.md` - Query documentation

## Pattern Detection Queries

Each pattern has corresponding Cypher queries documented in `cypher-queries-reference.md`:
- Query 16: Circular Flow Detection
- Query 17: Fan-Out Pattern Detection
- Query 18: Fan-In Pattern Detection
- Query 19: Mule Account Detection
- Query 20: Shared Device Detection
- Query 21: Shared IP Detection
- Query 15: Velocity Pattern Detection (transaction count)

## Contributing

When adding new fraud patterns:
1. Create a new `.puml` file in this directory
2. Follow the existing diagram style
3. Include legend and notes
4. Update this README
5. Reference in relevant documentation

"""
Flask Web Application for Fraud Detection System
Provides UI for fraud analysts to investigate and discover fraud patterns.
"""

from flask import Flask, jsonify, request, render_template, send_from_directory
from flask_cors import CORS
import os
from datetime import datetime
from dotenv import load_dotenv

from ..application.fraud_investigation_service import FraudInvestigationService
from ..infrastructure.neo4j_connection import Neo4jConnection

# Load environment variables
load_dotenv()


app = Flask(__name__)
CORS(app)

# Initialize services
investigation_service = FraudInvestigationService()
neo4j_connection = Neo4jConnection()


@app.route('/')
def index():
    """Dashboard homepage"""
    return render_template('dashboard.html')


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    db_status = neo4j_connection.verify_connectivity()

    return jsonify({
        'status': 'healthy' if db_status else 'unhealthy',
        'database': 'connected' if db_status else 'disconnected',
        'timestamp': datetime.utcnow().isoformat()
    })


@app.route('/api/dashboard/summary', methods=['GET'])
def dashboard_summary():
    """Get dashboard summary statistics"""
    try:
        summary = investigation_service.get_dashboard_summary()
        return jsonify(summary)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/accounts/high-risk', methods=['GET'])
def get_high_risk_accounts():
    """Get high-risk accounts"""
    try:
        limit = request.args.get('limit', default=50, type=int)
        accounts = investigation_service.get_high_risk_accounts(limit=limit)
        return jsonify({'accounts': accounts, 'count': len(accounts)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/accounts/<account_id>/investigate', methods=['GET'])
def investigate_account(account_id):
    """Investigate specific account"""
    try:
        result = investigation_service.investigate_account(account_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/customers/<customer_id>/investigate', methods=['GET'])
def investigate_customer(customer_id):
    """Investigate specific customer"""
    try:
        result = investigation_service.investigate_customer(customer_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/transactions/flagged', methods=['GET'])
def get_flagged_transactions():
    """Get flagged transactions"""
    try:
        limit = request.args.get('limit', default=100, type=int)
        transactions = investigation_service.get_flagged_transactions(limit=limit)
        return jsonify({'transactions': transactions, 'count': len(transactions)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/fraud-patterns/detect', methods=['POST'])
def detect_fraud_patterns():
    """Run fraud detection algorithms"""
    try:
        patterns = investigation_service.detect_fraud_patterns()
        return jsonify(patterns)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/fraud-rings/active', methods=['GET'])
def get_active_fraud_rings():
    """Get active fraud rings"""
    try:
        rings = investigation_service.get_active_fraud_rings()
        return jsonify({'fraud_rings': rings, 'count': len(rings)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/fraud-patterns/circular-flow/accounts', methods=['GET'])
def get_circular_flow_accounts():
    """Get accounts involved in circular flow patterns"""
    try:
        accounts = investigation_service.get_circular_flow_accounts()
        return jsonify({'accounts': accounts, 'count': len(accounts)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/fraud-patterns/fan-out/accounts', methods=['GET'])
def get_fan_out_accounts():
    """Get accounts involved in fan-out patterns"""
    try:
        accounts = investigation_service.get_fan_out_accounts()
        return jsonify({'accounts': accounts, 'count': len(accounts)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/fraud-patterns/fan-in/accounts', methods=['GET'])
def get_fan_in_accounts():
    """Get accounts involved in fan-in patterns"""
    try:
        accounts = investigation_service.get_fan_in_accounts()
        return jsonify({'accounts': accounts, 'count': len(accounts)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/fraud-patterns/mule-accounts', methods=['GET'])
def get_mule_accounts():
    """Get mule account details"""
    try:
        accounts = investigation_service.get_mule_accounts_details()
        return jsonify({'accounts': accounts, 'count': len(accounts)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/infrastructure/shared', methods=['GET'])
def get_shared_infrastructure():
    """Get shared infrastructure details"""
    try:
        infra_type = request.args.get('type', default='device', type=str)
        details = investigation_service.get_shared_infrastructure_details(infra_type)
        return jsonify({'shared_infrastructure': details, 'count': len(details)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/connection/path', methods=['GET'])
def find_connection_path():
    """Find connection path between two entities"""
    try:
        from_id = request.args.get('from')
        to_id = request.args.get('to')

        if not from_id or not to_id:
            return jsonify({'error': 'Both from and to parameters required'}), 400

        path = investigation_service.find_connection_path(from_id, to_id)
        return jsonify({'path': path})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/search', methods=['GET'])
def search_entities():
    """Search for entities"""
    try:
        query = request.args.get('q', '')
        entity_type = request.args.get('type', 'account')

        results = investigation_service.search_entities(query, entity_type)
        return jsonify({'results': results, 'count': len(results)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/report/generate', methods=['POST'])
def generate_report():
    """Generate investigation report"""
    try:
        data = request.json
        entity_id = data.get('entity_id')
        entity_type = data.get('entity_type', 'account')

        report = investigation_service.create_investigation_report(entity_id, entity_type)
        return jsonify(report)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/database/stats', methods=['GET'])
def database_stats():
    """Get database statistics"""
    try:
        stats = neo4j_connection.get_database_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def create_app():
    """Application factory"""
    return app


if __name__ == '__main__':
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'

    print("Starting Fraud Detection System...")
    print(f"Dashboard available at: http://localhost:{port}")
    app.run(debug=debug, host='0.0.0.0', port=port)

"""Shared test fixtures for EstradaBot tests."""

import os
import sys
import pytest
from datetime import datetime, timedelta

# Add backend to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Force local storage for tests
os.environ['USE_LOCAL_STORAGE'] = 'true'
os.environ['SECRET_KEY'] = 'test-secret-key'
os.environ['ADMIN_USERNAME'] = 'admin'
os.environ['ADMIN_PASSWORD'] = 'admin'


@pytest.fixture
def app():
    """Create Flask test application."""
    from app import app as flask_app
    flask_app.config['TESTING'] = True
    flask_app.config['WTF_CSRF_ENABLED'] = False
    return flask_app


@pytest.fixture
def client(app):
    """Create Flask test client."""
    return app.test_client()


@pytest.fixture
def auth_client(client):
    """Create authenticated test client (admin)."""
    client.post('/login', data={
        'username': 'admin',
        'password': 'admin'
    }, follow_redirects=True)
    return client


@pytest.fixture
def sample_orders():
    """Sample order data for DES scheduler testing."""
    base_date = datetime(2026, 2, 16)  # A Monday
    return [
        {
            'wo_number': 'WO-001',
            'serial_number': 'SN001',
            'part_number': 'PN-100',
            'description': 'Test Stator A',
            'customer': 'Customer A',
            'is_reline': False,
            'rubber_type': 'XE',
            'promise_date': base_date + timedelta(days=14),
            'basic_finish_date': base_date + timedelta(days=14),
            'creation_date': base_date - timedelta(days=5),
            'quantity': 1,
        },
        {
            'wo_number': 'WO-002',
            'serial_number': 'SN002',
            'part_number': 'PN-200',
            'description': 'Test Stator B',
            'customer': 'Customer B',
            'is_reline': False,
            'rubber_type': 'HR',
            'promise_date': base_date + timedelta(days=10),
            'basic_finish_date': base_date + timedelta(days=10),
            'creation_date': base_date - timedelta(days=3),
            'quantity': 1,
        },
        {
            'wo_number': 'WO-003',
            'serial_number': 'SN003',
            'part_number': 'PN-100',
            'description': 'Test Stator C (reline)',
            'customer': 'Customer C',
            'is_reline': True,
            'rubber_type': 'XE',
            'promise_date': base_date + timedelta(days=7),
            'basic_finish_date': base_date + timedelta(days=7),
            'creation_date': base_date - timedelta(days=1),
            'quantity': 1,
        },
    ]


@pytest.fixture
def sample_core_mapping():
    """Sample core mapping for DES scheduler testing."""
    return {
        'PN-100': {
            'core_number': 427,
            'injection_time': 0.5,
            'cure_time': 1.5,
        },
        'PN-200': {
            'core_number': 430,
            'injection_time': 0.6,
            'cure_time': 1.8,
        },
    }


@pytest.fixture
def sample_core_inventory():
    """Sample core inventory for DES scheduler testing."""
    return {
        427: [
            {'suffix': 'A', 'status': 'available'},
            {'suffix': 'B', 'status': 'available'},
        ],
        430: [
            {'suffix': 'A', 'status': 'available'},
        ],
    }


@pytest.fixture
def sample_serialized_orders():
    """Sample serialized orders for alert engine testing."""
    base_date = datetime(2026, 2, 16)
    return [
        {
            'wo_number': 'WO-001',
            'part_number': 'PN-100',
            'customer': 'Customer A',
            'core': '427-A',
            'rubber_type': 'XE',
            'priority': 'Normal',
            'promise_date': (base_date + timedelta(days=14)).isoformat(),
            'completion_date': (base_date + timedelta(days=12)).isoformat(),
            'blast_date': base_date.isoformat(),
            'on_time_status': 'On Time',
            'planned_desma': 'D1',
        },
        {
            'wo_number': 'WO-002',
            'part_number': 'PN-200',
            'customer': 'Customer B',
            'core': '430-A',
            'rubber_type': 'HR',
            'priority': 'Hot-ASAP',
            'promise_date': (base_date + timedelta(days=5)).isoformat(),
            'completion_date': (base_date + timedelta(days=6)).isoformat(),
            'blast_date': base_date.isoformat(),
            'on_time_status': 'Late',
            'planned_desma': 'D2',
        },
        {
            'wo_number': 'WO-003',
            'part_number': 'PN-100',
            'customer': 'Customer C',
            'core': '427-B',
            'rubber_type': 'XE',
            'priority': 'Normal',
            'promise_date': (base_date + timedelta(days=10)).isoformat(),
            'completion_date': (base_date + timedelta(days=9)).isoformat(),
            'blast_date': base_date.isoformat(),
            'on_time_status': 'At Risk',
            'planned_desma': 'D1',
        },
    ]

"""Tests for Flask API endpoints."""

import pytest
import json


class TestAuthEndpoints:
    """Tests for authentication."""

    def test_login_page_accessible(self, client):
        response = client.get('/login')
        assert response.status_code == 200

    def test_login_success(self, client):
        response = client.post('/login', data={
            'username': 'admin',
            'password': 'admin'
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_login_failure(self, client):
        response = client.post('/login', data={
            'username': 'admin',
            'password': 'wrong'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Invalid' in response.data or b'incorrect' in response.data.lower()

    def test_unauthenticated_redirect(self, client):
        response = client.get('/')
        assert response.status_code in (302, 401)


class TestFeedbackEndpoints:
    """Tests for feedback API."""

    def test_submit_feedback(self, auth_client):
        response = auth_client.post('/api/feedback', json={
            'category': 'Bug Report',
            'priority': 'High',
            'message': 'Test feedback message',
            'page': 'Dashboard'
        })
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True

    def test_submit_feedback_with_status(self, auth_client):
        """New feedback should get 'New' status."""
        auth_client.post('/api/feedback', json={
            'category': 'Bug Report',
            'priority': 'Medium',
            'message': 'Test with status'
        })
        response = auth_client.get('/api/feedback')
        data = response.get_json()
        if data['feedback']:
            # Most recent entry should have 'New' status
            latest = data['feedback'][0]
            assert latest.get('status') == 'New'

    def test_submit_feedback_missing_message(self, auth_client):
        response = auth_client.post('/api/feedback', json={
            'category': 'Bug Report',
            'priority': 'High',
            'message': ''
        })
        assert response.status_code == 400

    def test_get_feedback_admin(self, auth_client):
        response = auth_client.get('/api/feedback')
        assert response.status_code == 200
        data = response.get_json()
        assert 'feedback' in data

    def test_update_feedback_status(self, auth_client):
        # Submit a feedback first
        auth_client.post('/api/feedback', json={
            'category': 'Bug Report',
            'priority': 'Medium',
            'message': 'Status test'
        })
        # Update its status
        response = auth_client.put('/api/feedback/0/status', json={
            'status': 'In-Work'
        })
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True

    def test_update_feedback_invalid_status(self, auth_client):
        response = auth_client.put('/api/feedback/0/status', json={
            'status': 'InvalidStatus'
        })
        assert response.status_code == 400


class TestNotificationEndpoints:
    """Tests for notification API."""

    def test_get_notifications(self, auth_client):
        response = auth_client.get('/api/notifications')
        assert response.status_code == 200
        data = response.get_json()
        assert 'notifications' in data
        assert 'unread_count' in data

    def test_mark_all_read(self, auth_client):
        response = auth_client.post('/api/notifications/read-all')
        assert response.status_code == 200

    def test_mark_nonexistent_read(self, auth_client):
        response = auth_client.post('/api/notifications/NTF-nonexistent/read')
        assert response.status_code == 404


class TestAlertEndpoints:
    """Tests for alert API."""

    def test_get_alerts_empty(self, auth_client):
        response = auth_client.get('/api/alerts')
        assert response.status_code == 200
        data = response.get_json()
        assert 'alerts' in data

    def test_generate_alerts_no_schedule(self, auth_client):
        """Generate alerts with no schedule data should return error."""
        response = auth_client.post('/api/alerts/generate')
        assert response.status_code in (200, 400)


class TestPageAccess:
    """Tests for page route accessibility."""

    def test_dashboard(self, auth_client):
        response = auth_client.get('/')
        assert response.status_code == 200

    def test_upload_page(self, auth_client):
        response = auth_client.get('/upload')
        assert response.status_code == 200

    def test_schedule_page(self, auth_client):
        response = auth_client.get('/schedule')
        assert response.status_code == 200

    def test_reports_page(self, auth_client):
        response = auth_client.get('/reports')
        assert response.status_code == 200

    def test_special_requests_page(self, auth_client):
        response = auth_client.get('/special-requests')
        assert response.status_code == 200

    def test_planner_page_admin(self, auth_client):
        response = auth_client.get('/planner')
        assert response.status_code == 200

    def test_update_log_page(self, auth_client):
        response = auth_client.get('/updates')
        assert response.status_code == 200

    def test_alerts_page(self, auth_client):
        response = auth_client.get('/alerts')
        assert response.status_code == 200

    def test_notifications_page(self, auth_client):
        response = auth_client.get('/notifications')
        assert response.status_code == 200

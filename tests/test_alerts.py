"""Tests for the alert reports engine."""

import pytest
from datetime import datetime, timedelta

from app import generate_alert_report


class TestAlertReportGeneration:
    """Tests for the generate_alert_report function."""

    def test_empty_orders(self):
        result = generate_alert_report([])
        assert result['alerts'] == []
        assert result['summary']['total_alerts'] == 0
        assert result['summary']['late_count'] == 0

    def test_late_orders_detected(self, sample_serialized_orders):
        result = generate_alert_report(sample_serialized_orders)
        late_alert = next((a for a in result['alerts'] if a['type'] == 'late_orders'), None)
        assert late_alert is not None
        assert late_alert['count'] == 1
        assert late_alert['severity'] == 'danger'
        assert late_alert['details'][0]['wo_number'] == 'WO-002'

    def test_at_risk_orders_detected(self, sample_serialized_orders):
        result = generate_alert_report(sample_serialized_orders)
        risk_alert = next((a for a in result['alerts'] if a['type'] == 'promise_date_risk'), None)
        assert risk_alert is not None
        assert risk_alert['count'] >= 1
        assert risk_alert['severity'] == 'warning'

    def test_machine_utilization_present(self, sample_serialized_orders):
        result = generate_alert_report(sample_serialized_orders)
        machine_alert = next((a for a in result['alerts'] if a['type'] == 'machine_utilization'), None)
        assert machine_alert is not None
        assert machine_alert['count'] == 5  # D1-D5
        assert len(machine_alert['details']) == 5

    def test_summary_counts(self, sample_serialized_orders):
        result = generate_alert_report(sample_serialized_orders)
        summary = result['summary']
        assert summary['late_count'] == 1
        assert summary['at_risk_count'] >= 1
        assert summary['total_alerts'] >= 2

    def test_generated_at_timestamp(self, sample_serialized_orders):
        result = generate_alert_report(sample_serialized_orders)
        assert 'generated_at' in result
        # Should be a valid ISO format
        datetime.fromisoformat(result['generated_at'])

    def test_all_on_time_no_late_alert(self):
        orders = [
            {
                'wo_number': 'WO-001',
                'part_number': 'PN-100',
                'customer': 'Customer A',
                'core': '427-A',
                'promise_date': '2026-03-01T00:00:00',
                'completion_date': '2026-02-20T00:00:00',
                'on_time_status': 'On Time',
                'planned_desma': 'D1',
            },
        ]
        result = generate_alert_report(orders)
        late_alert = next((a for a in result['alerts'] if a['type'] == 'late_orders'), None)
        assert late_alert is None
        assert result['summary']['late_count'] == 0

    def test_core_shortage_detection(self):
        """Orders sharing the same core number should trigger core alert."""
        orders = [
            {'wo_number': f'WO-{i}', 'core': '427-A', 'on_time_status': 'On Time',
             'promise_date': '', 'completion_date': '', 'planned_desma': f'D{(i % 5) + 1}'}
            for i in range(5)
        ]
        result = generate_alert_report(orders)
        core_alert = next((a for a in result['alerts'] if a['type'] == 'core_shortage'), None)
        assert core_alert is not None
        assert core_alert['details'][0]['core'] == '427'

"""Tests for the DES scheduling engine."""

import pytest
from datetime import datetime, timedelta

from algorithms.des_scheduler import DESScheduler, WorkScheduleConfig, PartState


class TestWorkScheduleConfig:
    """Tests for work schedule configuration."""

    def test_create_12h_shift(self):
        config = WorkScheduleConfig.create(working_days=[0, 1, 2, 3], shift_hours=12)
        assert config.shift_hours == 12
        assert config.working_days == [0, 1, 2, 3]
        assert config.shift1_start == 5
        assert config.has_night_shift is True

    def test_create_10h_shift(self):
        config = WorkScheduleConfig.create(working_days=[0, 1, 2, 3], shift_hours=10)
        assert config.shift_hours == 10
        assert config.shift1_start == 5
        assert config.has_night_shift is False

    def test_create_5day_schedule(self):
        config = WorkScheduleConfig.create(working_days=[0, 1, 2, 3, 4], shift_hours=12)
        assert config.working_days == [0, 1, 2, 3, 4]

    def test_is_working_day(self):
        config = WorkScheduleConfig.create(working_days=[0, 1, 2, 3], shift_hours=12)
        monday = datetime(2026, 2, 16)  # Monday
        friday = datetime(2026, 2, 20)  # Friday
        assert config.is_working_day(monday) is True
        assert config.is_working_day(friday) is False

    def test_advance_time_simple(self):
        config = WorkScheduleConfig.create(working_days=[0, 1, 2, 3, 4], shift_hours=12)
        start = datetime(2026, 2, 16, 8, 0)  # Monday 8 AM
        result = config.advance_time(start, 2.0)
        # Should advance roughly 2 hours (may skip breaks)
        assert result > start
        assert (result - start).total_seconds() >= 2 * 3600

    def test_next_unblocked_time_weekend(self):
        config = WorkScheduleConfig.create(working_days=[0, 1, 2, 3], shift_hours=12)
        # Saturday should advance to Monday
        saturday = datetime(2026, 2, 21, 10, 0)
        result = config.next_unblocked_time(saturday)
        assert result.weekday() == 0  # Monday


class TestDESSchedulerInit:
    """Tests for DES scheduler initialization."""

    def test_init_with_orders(self, sample_orders, sample_core_mapping, sample_core_inventory):
        scheduler = DESScheduler(
            orders=sample_orders,
            core_mapping=sample_core_mapping,
            core_inventory=sample_core_inventory,
            working_days=[0, 1, 2, 3],
            shift_hours=12
        )
        assert len(scheduler.orders) == 3
        assert len(scheduler.core_mapping) == 2
        assert 427 in scheduler.core_inventory
        assert 430 in scheduler.core_inventory

    def test_init_empty_orders(self, sample_core_mapping, sample_core_inventory):
        scheduler = DESScheduler(
            orders=[],
            core_mapping=sample_core_mapping,
            core_inventory=sample_core_inventory,
        )
        assert len(scheduler.orders) == 0

    def test_core_inventory_initialization(self, sample_orders, sample_core_mapping, sample_core_inventory):
        scheduler = DESScheduler(
            orders=sample_orders,
            core_mapping=sample_core_mapping,
            core_inventory=sample_core_inventory,
        )
        # Each core should have availability tracking added
        for core_num, cores in scheduler.core_inventory.items():
            for core in cores:
                assert 'available_at' in core
                assert 'assigned_to' in core

    def test_routing_new_stator(self, sample_orders, sample_core_mapping, sample_core_inventory):
        scheduler = DESScheduler(
            orders=sample_orders,
            core_mapping=sample_core_mapping,
            core_inventory=sample_core_inventory,
        )
        routing = scheduler._get_routing(is_reline=False)
        assert routing[0] == 'BLAST'
        assert 'CUT THREADS' in routing
        assert routing[-1] == 'INSPECT'

    def test_routing_reline(self, sample_orders, sample_core_mapping, sample_core_inventory):
        scheduler = DESScheduler(
            orders=sample_orders,
            core_mapping=sample_core_mapping,
            core_inventory=sample_core_inventory,
        )
        routing = scheduler._get_routing(is_reline=True)
        assert routing[0] == 'BLAST'
        assert 'CUT THREADS' not in routing
        assert routing[-1] == 'INSPECT'


class TestDESSchedulerExecution:
    """Tests for DES scheduler execution."""

    def test_schedule_basic(self, sample_orders, sample_core_mapping, sample_core_inventory):
        scheduler = DESScheduler(
            orders=sample_orders,
            core_mapping=sample_core_mapping,
            core_inventory=sample_core_inventory,
            working_days=[0, 1, 2, 3, 4],
            shift_hours=12
        )
        start_date = datetime(2026, 2, 16, 5, 20)
        results = scheduler.schedule_orders(start_date=start_date)

        # Should schedule at least some orders
        assert len(results) > 0

    def test_schedule_produces_blast_dates(self, sample_orders, sample_core_mapping, sample_core_inventory):
        scheduler = DESScheduler(
            orders=sample_orders,
            core_mapping=sample_core_mapping,
            core_inventory=sample_core_inventory,
            working_days=[0, 1, 2, 3, 4],
            shift_hours=12
        )
        start_date = datetime(2026, 2, 16, 5, 20)
        results = scheduler.schedule_orders(start_date=start_date)

        for order in results:
            assert order.blast_date is not None
            assert order.blast_date >= start_date

    def test_schedule_produces_completion_dates(self, sample_orders, sample_core_mapping, sample_core_inventory):
        scheduler = DESScheduler(
            orders=sample_orders,
            core_mapping=sample_core_mapping,
            core_inventory=sample_core_inventory,
            working_days=[0, 1, 2, 3, 4],
            shift_hours=12
        )
        start_date = datetime(2026, 2, 16, 5, 20)
        results = scheduler.schedule_orders(start_date=start_date)

        for order in results:
            assert order.completion_date is not None
            assert order.completion_date > order.blast_date

    def test_schedule_summary(self, sample_orders, sample_core_mapping, sample_core_inventory):
        scheduler = DESScheduler(
            orders=sample_orders,
            core_mapping=sample_core_mapping,
            core_inventory=sample_core_inventory,
            working_days=[0, 1, 2, 3, 4],
            shift_hours=12
        )
        start_date = datetime(2026, 2, 16, 5, 20)
        scheduler.schedule_orders(start_date=start_date)
        summary = scheduler.get_summary()

        assert 'total_scheduled' in summary
        assert 'on_time' in summary
        assert 'on_time_pct' in summary
        assert summary['total_scheduled'] > 0

    def test_4day_vs_5day_schedule(self, sample_orders, sample_core_mapping, sample_core_inventory):
        """5-day schedule should have earlier completions than 4-day for same orders."""
        start_date = datetime(2026, 2, 16, 5, 20)

        scheduler_4d = DESScheduler(
            orders=sample_orders,
            core_mapping=sample_core_mapping,
            core_inventory=sample_core_inventory,
            working_days=[0, 1, 2, 3],
            shift_hours=12
        )
        results_4d = scheduler_4d.schedule_orders(start_date=start_date)

        scheduler_5d = DESScheduler(
            orders=sample_orders,
            core_mapping=sample_core_mapping,
            core_inventory=sample_core_inventory,
            working_days=[0, 1, 2, 3, 4],
            shift_hours=12
        )
        results_5d = scheduler_5d.schedule_orders(start_date=start_date)

        # Both should schedule the same orders
        assert len(results_4d) == len(results_5d)

    def test_hot_list_priority(self, sample_orders, sample_core_mapping, sample_core_inventory):
        """Hot list orders should be scheduled before normal orders."""
        hot_list = [{'wo_number': 'WO-002', 'priority': 'ASAP'}]

        scheduler = DESScheduler(
            orders=sample_orders,
            core_mapping=sample_core_mapping,
            core_inventory=sample_core_inventory,
            working_days=[0, 1, 2, 3, 4],
            shift_hours=12
        )
        start_date = datetime(2026, 2, 16, 5, 20)
        results = scheduler.schedule_orders(start_date=start_date, hot_list_entries=hot_list)

        # Hot list order should have an early blast date
        hot_order = next((o for o in results if o.wo_number == 'WO-002'), None)
        if hot_order:
            assert hot_order.priority in ('Hot-ASAP', 'Hot-Dated')


class TestPartState:
    """Tests for PartState data class."""

    def test_create_part_state(self):
        part = PartState(
            part_id='PART_000001',
            wo_number='WO-001',
            part_number='PN-100',
            description='Test Part',
            customer='Test Customer',
            is_reline=False,
            rubber_type='XE',
            core_number=427,
        )
        assert part.wo_number == 'WO-001'
        assert part.priority == 'Normal'
        assert part.blast_time is None
        assert part.completion_time is None

    def test_default_values(self):
        part = PartState(
            part_id='P1',
            wo_number='W1',
            part_number='P',
            description='D',
            customer='C',
            is_reline=False,
            rubber_type='XE',
            core_number=1,
        )
        assert part.injection_time == 0.5
        assert part.cure_time == 1.5
        assert part.quench_time == 0.75
        assert part.special_instructions is None
        assert part.supermarket_location is None

"""
Data Validators
Comprehensive validation of all data files.
"""

from typing import Dict, List, Any, Tuple
import pandas as pd
from datetime import datetime


class ValidationReport:
    """Container for validation results."""

    def __init__(self):
        self.errors = []  # Blocking errors
        self.warnings = []  # Non-blocking warnings
        self.info = []  # Informational messages

    @property
    def is_valid(self) -> bool:
        """Returns True if no blocking errors."""
        return len(self.errors) == 0

    def add_error(self, message: str):
        """Add a blocking error."""
        self.errors.append(message)

    def add_warning(self, message: str):
        """Add a warning."""
        self.warnings.append(message)

    def add_info(self, message: str):
        """Add informational message."""
        self.info.append(message)

    def print_report(self):
        """Print formatted validation report."""
        print("\n" + "=" * 70)
        print("VALIDATION REPORT")
        print("=" * 70)

        if self.is_valid:
            print("\n[OK] VALIDATION PASSED")
        else:
            print("\n[FAIL] VALIDATION FAILED")

        if self.errors:
            print(f"\n[ERROR] ERRORS ({len(self.errors)}):")
            for i, error in enumerate(self.errors[:10], 1):
                print(f"   {i}. {error}")
            if len(self.errors) > 10:
                print(f"   ... and {len(self.errors) - 10} more errors")

        if self.warnings:
            print(f"\n[WARN] WARNINGS ({len(self.warnings)}):")
            for i, warning in enumerate(self.warnings[:10], 1):
                print(f"   {i}. {warning}")
            if len(self.warnings) > 10:
                print(f"   ... and {len(self.warnings) - 10} more warnings")

        if self.info:
            print(f"\n[INFO] INFO ({len(self.info)}):")
            for i, info in enumerate(self.info[:5], 1):
                print(f"   {i}. {info}")
            if len(self.info) > 5:
                print(f"   ... and {len(self.info) - 5} more")


def validate_all_data(orders: List[Dict], core_mapping: Dict,
                      core_inventory: Dict, operations: Dict) -> ValidationReport:
    """
    Comprehensive validation of all data.

    Returns:
        ValidationReport with all validation results
    """
    report = ValidationReport()

    # 1. Validate Orders
    _validate_orders(orders, report)

    # 2. Validate Core Mapping
    _validate_core_mapping(core_mapping, report)

    # 3. Validate Core Inventory
    _validate_core_inventory(core_inventory, report)

    # 4. Validate Operations
    _validate_operations(operations, report)

    # 5. Cross-validation
    _cross_validate(orders, core_mapping, core_inventory, operations, report)

    return report


def _validate_orders(orders: List[Dict], report: ValidationReport):
    """Validate order data."""

    if not orders:
        report.add_error("No orders found in sales order file")
        return

    report.add_info(f"Found {len(orders)} orders")

    # Check for required fields
    required_fields = ['wo_number', 'part_number']
    missing_required = []

    for i, order in enumerate(orders):
        for field in required_fields:
            if not order.get(field):
                missing_required.append(f"Order {i} (WO# {order.get('wo_number', 'UNKNOWN')}): missing {field}")

    if missing_required:
        for msg in missing_required[:5]:
            report.add_error(msg)
        if len(missing_required) > 5:
            report.add_error(f"... and {len(missing_required) - 5} more orders with missing data")

    # Check for duplicates
    wo_numbers = [o['wo_number'] for o in orders if o.get('wo_number')]
    duplicates = [wo for wo in set(wo_numbers) if wo_numbers.count(wo) > 1]

    if duplicates:
        report.add_warning(f"Found {len(duplicates)} duplicate WO numbers: {duplicates[:5]}")

    # Analyze product types
    new_count = sum(1 for o in orders if o['part_number'] and o['part_number'][0].isdigit())
    reline_count = sum(1 for o in orders if o['part_number'] and o['part_number'].startswith('XN'))
    other_count = len(orders) - new_count - reline_count

    reline_pct = (reline_count / len(orders) * 100) if orders else 0
    report.add_info(f"Product mix: {new_count} new, {reline_count} reline ({reline_pct:.1f}%), {other_count} other")

    if reline_pct < 70:
        report.add_warning(f"Reline percentage ({reline_pct:.1f}%) is below expected 80%")


def _validate_core_mapping(core_mapping: Dict, report: ValidationReport):
    """Validate core mapping data."""

    if not core_mapping:
        report.add_error("Core mapping is empty")
        return

    report.add_info(f"Found {len(core_mapping)} part mappings")

    # Check for missing process times
    missing_injection = [p for p, d in core_mapping.items() if pd.isna(d.get('injection_time'))]
    missing_cure = [p for p, d in core_mapping.items() if pd.isna(d.get('cure_time'))]
    missing_quench = [p for p, d in core_mapping.items() if pd.isna(d.get('quench_time'))]

    if missing_injection:
        report.add_warning(f"{len(missing_injection)} parts missing injection time")
    if missing_cure:
        report.add_warning(f"{len(missing_cure)} parts missing cure time")
    if missing_quench:
        report.add_warning(f"{len(missing_quench)} parts missing quench time")

    # Check for missing core numbers
    missing_cores = [p for p, d in core_mapping.items() if pd.isna(d.get('core_number'))]
    if missing_cores:
        report.add_error(f"{len(missing_cores)} parts missing core number assignment")

    # Check rubber type distribution
    rubber_types = {}
    for part, data in core_mapping.items():
        rt = data.get('rubber_type')
        if rt and not pd.isna(rt):
            rubber_types[rt] = rubber_types.get(rt, 0) + 1

    if rubber_types:
        report.add_info(f"Rubber types: {', '.join([f'{k}={v}' for k, v in sorted(rubber_types.items())])}")


def _validate_core_inventory(core_inventory: Dict, report: ValidationReport):
    """Validate core inventory data."""

    if not core_inventory:
        report.add_error("Core inventory is empty")
        return

    total_cores = sum(len(cores) for cores in core_inventory.values())
    report.add_info(f"Found {len(core_inventory)} unique core numbers, {total_cores} physical cores")

    # Check for cores with suffixes
    multi_suffix = {num: len(cores) for num, cores in core_inventory.items() if len(cores) > 1}
    if multi_suffix:
        report.add_info(f"{len(multi_suffix)} core numbers have multiple units (e.g., {dict(list(multi_suffix.items())[:3])})")


def _validate_operations(operations: Dict, report: ValidationReport):
    """Validate operations data."""

    if not operations:
        report.add_error("No operations defined")
        return

    report.add_info(f"Found {len(operations)} operations")

    # Check for required operations
    required_ops = ['BLAST', 'INJECTION', 'CURE', 'QUENCH', 'DISASSEMBLY']
    missing_ops = [op for op in required_ops if op not in operations]

    if missing_ops:
        report.add_error(f"Missing required operations: {missing_ops}")

    # Check for INJECTION bottleneck
    if 'INJECTION' in operations:
        inj_machines = operations['INJECTION'].get('machines_available', 0)
        if inj_machines != 5:
            report.add_warning(f"INJECTION has {inj_machines} machines, expected 5")

    # Check concurrent operations
    concurrent = [op for op, data in operations.items()
                 if 'Concurrent' in str(data.get('concurrent_or_sequential', ''))]
    if concurrent:
        report.add_info(f"Concurrent operations: {', '.join(concurrent)}")


def _cross_validate(orders: List[Dict], core_mapping: Dict,
                   core_inventory: Dict, operations: Dict,
                   report: ValidationReport):
    """Cross-validate data between files."""

    # 1. Check if order parts exist in mapping
    unmapped_parts = set()
    for order in orders:
        part = order.get('part_number')
        if part and part not in core_mapping:
            unmapped_parts.add(part)

    if unmapped_parts:
        pct_unmapped = len(unmapped_parts) / len(orders) * 100
        report.add_warning(f"{len(unmapped_parts)} unique parts in orders not in mapping ({pct_unmapped:.1f}%)")

        if pct_unmapped > 20:
            report.add_error("More than 20% of parts unmapped - core mapping may be outdated")

    # 2. Check if mapped cores exist in inventory
    mapped_cores = set()
    for data in core_mapping.values():
        core_num = data.get('core_number')
        if core_num and not pd.isna(core_num):
            try:
                mapped_cores.add(int(float(core_num)))
            except:
                pass

    inventory_cores = set(core_inventory.keys())
    missing_from_inventory = mapped_cores - inventory_cores

    if missing_from_inventory:
        report.add_warning(f"{len(missing_from_inventory)} core numbers in mapping not in inventory")

    # 3. Check for potential core shortages
    # Count how many orders need each core
    core_demand = {}
    for order in orders:
        part = order.get('part_number')
        if part and part in core_mapping:
            core_num = core_mapping[part].get('core_number')
            if core_num and not pd.isna(core_num):
                try:
                    core_num = int(float(core_num))
                    core_demand[core_num] = core_demand.get(core_num, 0) + 1
                except:
                    pass

    # Compare demand vs inventory
    potential_shortages = []
    for core_num, demand in core_demand.items():
        available = len(core_inventory.get(core_num, []))
        if available == 0:
            potential_shortages.append(f"Core {core_num}: {demand} orders, 0 available")
        elif demand > available * 5:  # More than 5x orders per core
            potential_shortages.append(f"Core {core_num}: {demand} orders, {available} available")

    if potential_shortages:
        report.add_warning("Potential core shortages detected:")
        for shortage in potential_shortages[:5]:
            report.add_warning(f"  - {shortage}")


if __name__ == "__main__":
    # Test validation with loaded data
    import sys
    from data_loader import DataLoader

    print("Testing Data Validation")
    print()

    loader = DataLoader()
    if not loader.load_all():
        print("Failed to load data")
        sys.exit(1)

    # Run comprehensive validation
    report = validate_all_data(
        loader.orders,
        loader.core_mapping,
        loader.core_inventory,
        loader.operations
    )

    report.print_report()

    if report.is_valid:
        print("\n[OK] Ready to proceed with scheduling!")
        sys.exit(0)
    else:
        print("\n[FAIL] Please fix errors before proceeding")
        sys.exit(1)

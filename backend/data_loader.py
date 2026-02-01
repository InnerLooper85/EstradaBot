"""
Data Loader
Loads and validates all input data files.
"""

import os
from pathlib import Path
from typing import Dict, List, Any, Tuple

from parsers import (
    parse_open_sales_order,
    parse_core_mapping,
    parse_core_inventory,
    parse_process_map,
    validate_orders,
    validate_core_mapping
)


class DataLoader:
    """Manages loading and validation of all data files."""

    def __init__(self, data_dir: str = "../Scheduler Bot Info"):
        self.data_dir = Path(data_dir)
        self.orders = []
        self.core_mapping = {}
        self.core_inventory = {}
        self.operations = {}
        self.validation_results = {}

    def load_all(self) -> bool:
        """
        Load all data files.

        Returns:
            True if successful, False if errors
        """
        print("=" * 70)
        print("LOADING ALL DATA FILES")
        print("=" * 70)

        try:
            # 1. Load Sales Orders
            print("\n[1/4] Loading Open Sales Order...")
            sales_order_file = self.data_dir / "Open_Sales_Order_Example.xlsx"
            self.orders = parse_open_sales_order(str(sales_order_file))

            order_validation = validate_orders(self.orders)
            self.validation_results['orders'] = order_validation

            if not order_validation['is_valid']:
                print("[ERROR] CRITICAL: Sales order validation failed")
                return False

            print(f"[OK] Loaded {len(self.orders)} orders")

            # 2. Load Core Mapping
            print("\n[2/4] Loading Core Mapping...")
            core_mapping_file = self.data_dir / "Core Mapping.xlsx"
            self.core_mapping = parse_core_mapping(str(core_mapping_file))
            self.core_inventory = parse_core_inventory(str(core_mapping_file))

            mapping_validation = validate_core_mapping(self.core_mapping, self.core_inventory)
            self.validation_results['core_mapping'] = mapping_validation

            print(f"[OK] Loaded {len(self.core_mapping)} part mappings")
            print(f"[OK] Loaded {len(self.core_inventory)} unique cores")

            # 3. Load Process Map
            print("\n[3/4] Loading Process Map...")
            process_map_file = self.data_dir / "Stators Process VSM.xlsx"
            self.operations = parse_process_map(str(process_map_file))

            print(f"[OK] Loaded {len(self.operations)} operations")

            # 4. Cross-validate
            print("\n[4/4] Cross-validating data...")
            self._cross_validate()

            return True

        except Exception as e:
            print(f"\n[ERROR] ERROR loading data: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    def _cross_validate(self):
        """Cross-validate data between different files."""

        # Check if order part numbers exist in core mapping
        unmapped_parts = []
        for order in self.orders:
            part = order.get('part_number')
            if part and part not in self.core_mapping:
                unmapped_parts.append(part)

        unique_unmapped = list(set(unmapped_parts))

        if unique_unmapped:
            print(f"\n[WARN]  WARNING: {len(unique_unmapped)} part numbers in orders not found in core mapping")
            print(f"   Examples: {unique_unmapped[:5]}")

            # This is expected for some parts, just inform user
            self.validation_results['unmapped_parts'] = unique_unmapped
        else:
            print("\n[OK] All order part numbers found in core mapping")

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of loaded data."""

        # Analyze orders
        new_count = sum(1 for o in self.orders
                       if o['part_number'] and o['part_number'][0].isdigit())
        reline_count = sum(1 for o in self.orders
                          if o['part_number'] and o['part_number'].startswith('XN'))

        # Analyze cores
        total_cores = sum(len(cores) for cores in self.core_inventory.values())
        multi_core_numbers = sum(1 for cores in self.core_inventory.values() if len(cores) > 1)

        # Analyze operations
        sim_ops = [op for op, data in self.operations.items()
                  if data.get('include_in_simulation') == 'Yes']

        return {
            'orders': {
                'total': len(self.orders),
                'new': new_count,
                'reline': reline_count,
                'reline_percentage': (reline_count / len(self.orders) * 100) if self.orders else 0
            },
            'parts': {
                'total_mapped': len(self.core_mapping),
                'unmapped_in_orders': len(self.validation_results.get('unmapped_parts', []))
            },
            'cores': {
                'unique_numbers': len(self.core_inventory),
                'total_physical_cores': total_cores,
                'numbers_with_multiple_units': multi_core_numbers
            },
            'operations': {
                'total': len(self.operations),
                'in_simulation': len(sim_ops)
            }
        }

    def print_summary(self):
        """Print a formatted summary."""
        summary = self.get_summary()

        print("\n" + "=" * 70)
        print("DATA LOADING SUMMARY")
        print("=" * 70)

        print(f"\n[ORDERS] ORDERS:")
        print(f"   Total: {summary['orders']['total']}")
        print(f"   New stators: {summary['orders']['new']}")
        print(f"   Reline stators: {summary['orders']['reline']} ({summary['orders']['reline_percentage']:.1f}%)")

        print(f"\n[PARTS] PARTS & CORES:")
        print(f"   Parts mapped: {summary['parts']['total_mapped']}")
        print(f"   Unmapped parts: {summary['parts']['unmapped_in_orders']}")
        print(f"   Unique core numbers: {summary['cores']['unique_numbers']}")
        print(f"   Total physical cores: {summary['cores']['total_physical_cores']}")
        print(f"   Core numbers with multiple units: {summary['cores']['numbers_with_multiple_units']}")

        print(f"\n[OPS]  OPERATIONS:")
        print(f"   Total operations: {summary['operations']['total']}")
        print(f"   In simulation: {summary['operations']['in_simulation']}")

        print("\n" + "=" * 70)


if __name__ == "__main__":
    import sys

    print("Testing Data Loader")
    print()

    loader = DataLoader()

    success = loader.load_all()

    if success:
        loader.print_summary()
        print("\n[OK] All data loaded successfully!")
        sys.exit(0)
    else:
        print("\n[ERROR] Data loading failed")
        sys.exit(1)

"""
Core Mapping Parser
Parses the Core Mapping Excel file with part-to-core mappings and process times.
"""

import pandas as pd
from typing import Dict, List, Any, Optional


def parse_core_mapping(filepath: str) -> Dict[str, Dict[str, Any]]:
    """
    Parse the Core Mapping and Process Times sheet.

    Returns:
        Dictionary mapping part numbers to core/process data
    """
    try:
        # Read the Core Mapping sheet
        df = pd.read_excel(filepath, sheet_name='Core Mapping and Process Times')

        print(f"Loaded {len(df)} rows from Core Mapping sheet")
        print(f"Columns: {list(df.columns)}")

        mapping = {}
        errors = []

        for index, row in df.iterrows():
            try:
                # Map both new and reline part numbers
                for part_col in ['New Part Number', 'Reline Part Number']:
                    if pd.notna(row.get(part_col)):
                        part_number = str(row[part_col]).strip()

                        # Create mapping entry
                        mapping[part_number] = {
                            'core_number': row.get('Core Number'),
                            'rubber_type': row.get('Rubber Type'),
                            'injection_time': row.get('Injection Time (hours)'),
                            'cure_time': row.get('Cure Time'),
                            'quench_time': row.get('Quench Time'),
                            'stator_od': row.get('Stator OD'),
                            'lobe_config': row.get('Lobe Configuration'),
                            'stage_count': row.get('Stage Count'),
                            'fit': row.get('Fit'),
                            'description': row.get('DESCRIPTION')
                        }

            except Exception as e:
                errors.append(f"Row {index}: {str(e)}")
                continue

        print(f"\nParsing complete:")
        print(f"  - Mapped {len(mapping)} part numbers")
        print(f"  - Errors: {len(errors)}")

        if errors:
            print("\nFirst 5 errors:")
            for error in errors[:5]:
                print(f"  - {error}")

        return mapping

    except Exception as e:
        print(f"Error reading Core Mapping file: {str(e)}")
        raise


def parse_core_inventory(filepath: str) -> Dict[int, List[Dict[str, Any]]]:
    """
    Parse the Core Inventory sheet.

    Returns:
        Dictionary mapping core numbers to list of available cores (with suffixes)
    """
    try:
        df = pd.read_excel(filepath, sheet_name='Core Inventory')

        print(f"\nLoaded {len(df)} cores from Core Inventory sheet")
        print(f"Columns: {list(df.columns)}")

        inventory = {}

        for index, row in df.iterrows():
            try:
                core_num = row.get('Core Number')
                suffix = row.get('Suffix')

                if pd.isna(core_num):
                    continue

                # Convert to int if possible
                try:
                    core_num = int(float(core_num))
                except:
                    pass

                if core_num not in inventory:
                    inventory[core_num] = []

                inventory[core_num].append({
                    'suffix': suffix,
                    'core_pn': row.get('Core PN#'),
                    'model': row.get('Power Section Model'),
                    'tooling_pn': row.get('Tooling PN#'),
                    'state': 'available'  # Will track: available, oven, in_use, cleaning
                })

            except Exception as e:
                print(f"Row {index} error: {e}")
                continue

        print(f"\nCore Inventory Summary:")
        print(f"  - Unique core numbers: {len(inventory)}")
        print(f"  - Total cores: {sum(len(cores) for cores in inventory.values())}")

        # Show cores with multiple units
        multi_core = {k: len(v) for k, v in inventory.items() if len(v) > 1}
        if multi_core:
            print(f"  - Cores with multiple units: {len(multi_core)}")
            print(f"    Examples: {dict(list(multi_core.items())[:5])}")

        return inventory

    except Exception as e:
        print(f"Error reading Core Inventory: {str(e)}")
        raise


def validate_core_mapping(mapping: Dict[str, Dict], inventory: Dict) -> Dict[str, Any]:
    """
    Validate core mapping data.
    """
    validation = {
        'is_valid': True,
        'errors': [],
        'warnings': []
    }

    # Check for missing process times
    missing_injection = [p for p, d in mapping.items() if pd.isna(d.get('injection_time'))]
    missing_cure = [p for p, d in mapping.items() if pd.isna(d.get('cure_time'))]
    missing_quench = [p for p, d in mapping.items() if pd.isna(d.get('quench_time'))]

    if missing_injection:
        validation['warnings'].append(f"{len(missing_injection)} parts missing injection time")
    if missing_cure:
        validation['warnings'].append(f"{len(missing_cure)} parts missing cure time")
    if missing_quench:
        validation['warnings'].append(f"{len(missing_quench)} parts missing quench time")

    # Check rubber types
    rubber_types = {}
    for part, data in mapping.items():
        rt = data.get('rubber_type')
        if rt and not pd.isna(rt):
            rubber_types[rt] = rubber_types.get(rt, 0) + 1

    print(f"\nRubber Type Distribution:")
    for rt, count in sorted(rubber_types.items(), key=lambda x: -x[1]):
        print(f"  - {rt}: {count} parts")

    # Check for cores in mapping but not in inventory
    mapped_cores = set(d.get('core_number') for d in mapping.values() if pd.notna(d.get('core_number')))
    inventory_cores = set(inventory.keys())

    missing_from_inventory = mapped_cores - inventory_cores
    if missing_from_inventory:
        validation['warnings'].append(
            f"{len(missing_from_inventory)} core numbers in mapping but not in inventory: {list(missing_from_inventory)[:5]}"
        )

    return validation


if __name__ == "__main__":
    import sys

    # Test with your actual file
    test_file = "../../Scheduler Bot Info/Core Mapping.xlsx"

    print("Testing Core Mapping Parser")
    print("=" * 60)

    try:
        # Parse both sheets
        mapping = parse_core_mapping(test_file)
        inventory = parse_core_inventory(test_file)

        # Validate
        validation = validate_core_mapping(mapping, inventory)

        print("\n" + "=" * 60)
        print("Validation Results:")
        if validation['errors']:
            print(f"Errors: {len(validation['errors'])}")
            for error in validation['errors']:
                print(f"  - {error}")

        if validation['warnings']:
            print(f"Warnings: {len(validation['warnings'])}")
            for warning in validation['warnings']:
                print(f"  - {warning}")

        # Show sample mappings
        print("\n" + "=" * 60)
        print("Sample part mappings (first 3):")
        for i, (part, data) in enumerate(list(mapping.items())[:3]):
            print(f"\nPart: {part}")
            for key, value in data.items():
                print(f"  {key}: {value}")

    except Exception as e:
        print(f"\nError: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

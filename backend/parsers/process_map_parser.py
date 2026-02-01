"""
Process Map Parser
Parses the Stators Process VSM Excel file for operation parameters.
"""

import pandas as pd
from typing import Dict, Any


def parse_process_map(filepath: str, sheet_name: str = 'Stators ') -> Dict[str, Dict[str, Any]]:
    """
    Parse the Stators Process VSM file.

    Returns:
        Dictionary of operation parameters
    """
    try:
        df = pd.read_excel(filepath, sheet_name=sheet_name)

        print(f"Loaded process map with {df.shape[1]} operations")

        # The file structure has operations as columns
        # Row 0: SAP Operation Number
        # Row 1: SAP Workcenter Name
        # Row 2: New Stator flag (Yes/No)
        # Row 3: Reline Stator flag (Yes/No)
        # Row 4: Standard Cycle Time (hours)
        # Row 5: Standard Set-Up Time (hours)
        # Row 6: Operator Touch Time
        # Row 7: Machines Available
        # Row 8: Concurrent Capacity per Machine
        # Row 9: Standard WIP (SWIP)
        # Row 10: Include in Completion Date Calculation
        # Row 11: Include in Visual Simulation
        # Row 12: Concurrent or Sequential Operation

        operations = {}

        # Get operation names from first row (column headers after "Process Step")
        op_columns = [col for col in df.columns if col != 'Process Step']

        for col in op_columns:
            try:
                op_name = col

                operation = {
                    'name': op_name,
                    'sap_operation': df.iloc[0][col] if len(df) > 0 else None,
                    'workcenter': df.iloc[1][col] if len(df) > 1 else None,
                    'new_stator': df.iloc[2][col] if len(df) > 2 else None,
                    'reline_stator': df.iloc[3][col] if len(df) > 3 else None,
                    'cycle_time': df.iloc[4][col] if len(df) > 4 else 0,
                    'setup_time': df.iloc[5][col] if len(df) > 5 else 0,
                    'operator_touch_time': df.iloc[6][col] if len(df) > 6 else 0,
                    'machines_available': df.iloc[7][col] if len(df) > 7 else 1,
                    'concurrent_capacity': df.iloc[8][col] if len(df) > 8 else 1,
                    'swip': df.iloc[9][col] if len(df) > 9 else 0,
                    'include_in_completion': df.iloc[10][col] if len(df) > 10 else 'Yes',
                    'include_in_simulation': df.iloc[11][col] if len(df) > 11 else 'Yes',
                    'concurrent_or_sequential': df.iloc[12][col] if len(df) > 12 else 'Sequential'
                }

                # Convert numeric fields
                try:
                    if 'Varies' not in str(operation['cycle_time']):
                        operation['cycle_time'] = float(operation['cycle_time'])
                    else:
                        operation['cycle_time'] = 'VARIABLE'
                except:
                    operation['cycle_time'] = 0

                try:
                    operation['setup_time'] = float(operation['setup_time'])
                except:
                    operation['setup_time'] = 0

                try:
                    operation['machines_available'] = int(float(operation['machines_available']))
                except:
                    operation['machines_available'] = 1

                try:
                    operation['concurrent_capacity'] = int(float(operation['concurrent_capacity']))
                except:
                    operation['concurrent_capacity'] = 1

                try:
                    operation['swip'] = int(float(operation['swip']))
                except:
                    operation['swip'] = 0

                operations[op_name] = operation

            except Exception as e:
                print(f"Error parsing operation {col}: {e}")
                continue

        print(f"\nParsed {len(operations)} operations")

        # Show operations included in simulation
        sim_ops = [op for op, data in operations.items()
                   if data.get('include_in_simulation') == 'Yes']
        print(f"Operations in simulation: {len(sim_ops)}")
        print(f"  {sim_ops}")

        # Show concurrent operations
        concurrent_ops = [op for op, data in operations.items()
                         if 'Concurrent' in str(data.get('concurrent_or_sequential'))]
        if concurrent_ops:
            print(f"\nConcurrent operations:")
            for op in concurrent_ops:
                print(f"  - {op}: {operations[op]['concurrent_or_sequential']}")

        # Show variable time operations
        var_ops = [op for op, data in operations.items()
                  if data.get('cycle_time') == 'VARIABLE']
        if var_ops:
            print(f"\nVariable time operations (get times from Core Mapping):")
            for op in var_ops:
                print(f"  - {op}")

        return operations

    except Exception as e:
        print(f"Error reading process map: {str(e)}")
        raise


def get_routing_for_product(operations: Dict, is_reline: bool) -> list:
    """
    Get the sequence of operations for a product type.

    Args:
        operations: Dictionary of all operations
        is_reline: True if reline stator, False if new

    Returns:
        List of operation names in sequence
    """
    routing = []
    product_type = 'reline_stator' if is_reline else 'new_stator'

    for op_name, op_data in operations.items():
        if op_data.get(product_type) == 'Yes':
            routing.append(op_name)

    return routing


if __name__ == "__main__":
    import sys

    test_file = "../../Scheduler Bot Info/Stators Process VSM.xlsx"

    print("Testing Process Map Parser")
    print("=" * 60)

    try:
        operations = parse_process_map(test_file)

        # Test routing generation
        print("\n" + "=" * 60)
        print("Sample Routings:")

        new_routing = get_routing_for_product(operations, is_reline=False)
        print(f"\nNew Stator routing ({len(new_routing)} operations):")
        for i, op in enumerate(new_routing, 1):
            print(f"  {i}. {op}")

        reline_routing = get_routing_for_product(operations, is_reline=True)
        print(f"\nReline Stator routing ({len(reline_routing)} operations):")
        for i, op in enumerate(reline_routing, 1):
            print(f"  {i}. {op}")

        # Show sample operation details
        print("\n" + "=" * 60)
        print("Sample operation details (INJECTION):")
        if 'INJECTION' in operations:
            for key, value in operations['INJECTION'].items():
                print(f"  {key}: {value}")

    except Exception as e:
        print(f"\nError: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

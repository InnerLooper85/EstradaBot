"""
Order Filters
Functions for classifying product types and filtering orders.
"""

import re
from typing import Optional


def classify_product_type(part_number: Optional[str], description: Optional[str] = None) -> Optional[str]:
    """
    Classify an order's product type based on part number.

    Args:
        part_number: The part/material number
        description: Optional description (not currently used but available for future logic)

    Returns:
        'Stator', 'Reline', or None if unclassified
    """
    if not part_number:
        return None

    part_upper = str(part_number).upper().strip()

    # XN prefix -> Reline
    if part_upper.startswith('XN'):
        return 'Reline'

    # S + digit prefix -> Stator (e.g., S700788, S675783)
    if re.match(r'^S\d', part_upper):
        return 'Stator'

    return None


def should_exclude_order(part_number: Optional[str], description: Optional[str],
                         supply_source: Optional[str] = None) -> Optional[str]:
    """
    Determine if an order should be excluded from scheduling.

    Args:
        part_number: The part/material number
        description: Material description
        supply_source: Supply source field (e.g., 'Inventory')

    Returns:
        Exclusion reason string if should be excluded, None if order should be included
    """
    # Normalize inputs
    part_upper = str(part_number).upper().strip() if part_number else ''
    desc_upper = str(description).upper().strip() if description else ''
    supply_upper = str(supply_source).upper().strip() if supply_source else ''

    # Exclude inventory orders
    if 'INVENTORY' in supply_upper:
        return 'Inventory'

    # Exclude REPAIR parts
    if 'REPAIR' in part_upper or 'REPAIR' in desc_upper:
        return 'Repair'

    # Exclude customer-owned / analysis items
    if 'CUSTOMER OWNED' in desc_upper or 'ANALYSIS' in desc_upper:
        return 'Customer Owned/Analysis'

    # Exclude "STATOR, CUSTOMER" prefix in description
    if desc_upper.startswith('STATOR, CUSTOMER'):
        return 'Stator Customer'

    # Exclude rotors: R/C + digit pattern (e.g., R/C1234, RC1234)
    if re.match(r'^R/?C\d', part_upper):
        return 'Rotor'

    # Exclude housings/blanks
    housing_patterns = ['HSG', 'HOUSING', 'BLNK', 'BLANK']
    for pattern in housing_patterns:
        if pattern in part_upper or pattern in desc_upper:
            return 'Housing/Blank'

    return None


def get_exclusion_summary(excluded_orders: list) -> dict:
    """
    Generate a summary of excluded orders by reason.

    Args:
        excluded_orders: List of tuples (order, reason)

    Returns:
        Dictionary with counts by exclusion reason
    """
    summary = {}
    for order, reason in excluded_orders:
        summary[reason] = summary.get(reason, 0) + 1
    return summary

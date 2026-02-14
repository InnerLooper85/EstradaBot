"""
DCP Report Parser
Parses DCP (Data Collection Point) reports to extract supermarket locations.

The DCP report contains manufacturing data collection events. We extract the
supermarket location (rack/shelf) where each work order's stator is stored,
keyed by WO number.

Expected columns:
    Material, ShopOrder-SN, Operation, Operation Description, Substep,
    Substep Description, DC Parameter, DC Description, DCP Value,
    Min/Max, Expected Value, Reported By, Reported On
"""

import re
from typing import Dict, Optional
from pathlib import Path


def parse_dcp_report(file_path: str) -> Dict[str, str]:
    """
    Parse a DCP report Excel file and extract supermarket locations.

    Args:
        file_path: Path to the DCP report Excel file (.xlsx)

    Returns:
        Dict mapping WO number -> supermarket location string.
        If a WO appears multiple times, the most recent entry wins.
    """
    import pandas as pd

    file_path = Path(file_path)
    if not file_path.exists():
        print(f"[DCP Parser] File not found: {file_path}")
        return {}

    try:
        df = pd.read_excel(file_path, engine='openpyxl')
    except Exception as e:
        print(f"[DCP Parser] Error reading file: {e}")
        return {}

    # Normalize column names (strip whitespace, lowercase for matching)
    df.columns = [str(c).strip() for c in df.columns]
    col_map = {c.lower(): c for c in df.columns}

    # Find required columns
    shop_order_col = _find_column(col_map, ['shoporder-sn', 'shop order-sn', 'shoporder_sn', 'shop_order_sn', 'shoporder'])
    dc_desc_col = _find_column(col_map, ['dc description', 'dc_description', 'dcdescription'])
    dcp_value_col = _find_column(col_map, ['dcp value', 'dcp_value', 'dcpvalue'])
    reported_on_col = _find_column(col_map, ['reported on', 'reported_on', 'reportedon'])

    if not shop_order_col or not dcp_value_col:
        print(f"[DCP Parser] Missing required columns. Found: {list(df.columns)}")
        return {}

    # Filter to supermarket location records if DC Description column exists
    if dc_desc_col:
        mask = df[dc_desc_col].astype(str).str.lower().str.contains('supermarket', na=False)
        df = df[mask]

    if df.empty:
        print("[DCP Parser] No supermarket location records found")
        return {}

    # Sort by reported date (most recent last) so latest overwrites
    if reported_on_col:
        try:
            df[reported_on_col] = pd.to_datetime(df[reported_on_col], errors='coerce')
            df = df.sort_values(reported_on_col, na_position='first')
        except Exception:
            pass

    # Extract WO number from ShopOrder-SN (format: "3000354615-BD25394")
    # WO number is the part before the first dash
    locations = {}
    for _, row in df.iterrows():
        shop_order_sn = str(row.get(shop_order_col, '')).strip()
        dcp_value = str(row.get(dcp_value_col, '')).strip()

        if not shop_order_sn or not dcp_value or dcp_value.lower() in ('nan', ''):
            continue

        wo_number = _extract_wo_number(shop_order_sn)
        if wo_number:
            locations[wo_number] = dcp_value

    print(f"[DCP Parser] Parsed {len(locations)} supermarket locations from {len(df)} records")
    return locations


def _extract_wo_number(shop_order_sn: str) -> Optional[str]:
    """
    Extract WO number from ShopOrder-SN field.
    Format: "3000354615-BD25394" -> "3000354615"
    The WO number is the numeric prefix before the first dash.
    """
    # Match leading digits (WO number pattern)
    match = re.match(r'^(\d{7,})', shop_order_sn)
    if match:
        return match.group(1)
    # Fallback: split on dash and take first part
    parts = shop_order_sn.split('-')
    if parts and parts[0].strip():
        return parts[0].strip()
    return None


def _find_column(col_map: dict, candidates: list) -> Optional[str]:
    """Find a column name from a list of candidates (case-insensitive)."""
    for candidate in candidates:
        if candidate.lower() in col_map:
            return col_map[candidate.lower()]
    return None

# EstradaBot — Data Fields Reference

This document lists every field read from each uploaded input file and how the system uses it. Use this as a reference when creating custom reports, linking to live SAP feeds (MVP 2.0), or troubleshooting data issues.

---

## 1. Open Sales Order Report

**File pattern:** `Open Sales Order*.xlsx`
**Sheet:** `RawData`
**Source:** SAP
**Status:** Required

| Excel Column | Internal Key | Used For |
|---|---|---|
| Work Order | `wo_number` | Primary identifier for scheduling |
| Material | `part_number` | Core mapping lookup, reline detection (XN prefix) |
| Material Description | `description` | Display, part number extraction fallback |
| Supply Source | `supply_source` | Exclusion filter (e.g., external supply) |
| Customer Name | `customer` | Display in schedule and reports |
| Customer Number | `customer_number` | Stored but not currently displayed |
| Core (Work Center) | `core_number` | Core assignment lookup |
| Serial Number | `serial_number` | Display in schedule table and exports |
| Ordered Quantity | `quantity` | Stored (currently 1 per order) |
| Work Order Status | `work_order_status` | Stored for reference |
| Current Operation Description | `current_operation` | Rework detection ("RUBBER REMOVAL") |
| Created On | `created_on` | Fallback for WO creation date |
| Work Order Creation Date | `creation_date` | Turnaround calculation start date |
| Promise Date | `promise_date` | Display, fallback deadline |
| Basic Start Date | `basic_start_date` | Stored for reference |
| Scheduled start | `scheduled_start` | Stored for reference |
| Requested deliv.date | `requested_delivery_date` | Stored for reference |
| Basic finish date | `basic_finish_date` | On-time calculation deadline |

**Scrubbed on upload (not stored):** Unit Price, Net Price, Customer Address, Address

---

## 2. Shop Dispatch Report

**File pattern:** `Shop Dispatch*.XLSX` or `*.xlsx`
**Sheet:** `Sheet1`
**Source:** SAP
**Status:** Optional

| Excel Column | Internal Key | Used For |
|---|---|---|
| Order | `wo_number` | Merge with Sales Order data |
| Material | `part_number` | Core mapping lookup |
| Description | `description` | Display |
| Curr.WC | `current_work_center` | Stored for reference |
| Remaining Work Centers | `remaining_work_centers` | Stored for reference |
| Operation | `current_operation` | Rework detection |
| Operation Quantity | `operation_quantity` | Stored for reference |
| Priority | `priority` | Stored for reference |
| Elapsed Days | `elapsed_days` | Stored for reference |
| Operation Start Date | `operation_start_date` | Stored for reference |

---

## 3. Hot List

**File pattern:** `HOT LIST*.xlsx` or `Hot List*.xlsx`
**Sheet:** First sheet
**Source:** Manual (planning team)
**Status:** Optional

| Excel Column | Internal Key | Used For |
|---|---|---|
| WO# | `wo_number` | Match to sales orders for priority boost |
| NEED BY DATE | `need_by_date` | Hot-Dated priority sorting |
| DATE REQ MADE | `date_req_made` | Stored for reference |
| COMMENTS | `comments` | Rubber override detection ("REDLINE FOR XE/HR/XR/XD/XP INJECTION") |
| CORE | `core` | Stored for reference |
| ITEM | `item` | Stored for reference |
| DESCRIPTION | `description` | Stored for reference |
| CUSTOMER NAME | `customer` | Stored for reference |

**Derived fields:**
- `is_asap` — True if NEED BY DATE is empty (ASAP priority)
- `rubber_override` — Extracted from COMMENTS (e.g., "XE", "HR")

---

## 4. Core Mapping

**File pattern:** `Core Mapping*.xlsx` or `Core_Mapping*.xlsx`
**Source:** Internal maintenance
**Status:** Required

### Sheet: Core Mapping and Process Times

| Excel Column | Internal Key | Used For |
|---|---|---|
| New Part Number | (mapping key) | Maps part numbers to core numbers |
| Reline Part Number | (mapping key) | Maps reline part numbers to core numbers |
| Core Number | `core_number` | Core assignment in scheduling |
| Rubber Type | `rubber_type` | Rubber type alternation, display |
| Injection Time (hours) | `injection_time` | DES simulation timing |
| Cure Time | `cure_time` | DES simulation timing |
| Quench Time | `quench_time` | DES simulation timing |
| Stator OD | `stator_od` | Stored for reference |
| Lobe Configuration | `lobe_config` | Stored for reference |
| Stage Count | `stage_count` | Stored for reference |
| Fit | `fit` | Stored for reference |
| DESCRIPTION | `description` | Stored for reference |

### Sheet: Core Inventory

| Excel Column | Internal Key | Used For |
|---|---|---|
| Core Number | (inventory key) | Core availability tracking |
| Suffix | `suffix` | Identifies individual cores (e.g., 427-A, 427-B) |
| Core PN# | `core_pn` | Stored for reference |
| Power Section Model | `model` | Stored for reference |
| Tooling PN# | `tooling_pn` | Stored for reference |

---

## 5. Process Map (Stators Process VSM)

**File pattern:** `Stators Process VSM*.xlsx` or `Stators_Process_VSM*.xlsx`
**Sheet:** `Stators ` (note: trailing space)
**Source:** Industrial engineering
**Status:** Required

The process map uses a transposed layout — operations are columns, attributes are rows.

| Row | Attribute | Internal Key | Used For |
|---|---|---|---|
| 0 | SAP Operation Number | `sap_operation` | Stored for reference |
| 1 | SAP Workcenter Name | `workcenter` | Stored for reference |
| 2 | New Stator (Yes/No) | `new_stator` | Routing determination |
| 3 | Reline Stator (Yes/No) | `reline_stator` | Routing determination |
| 4 | Standard Cycle Time (hours) | `cycle_time` | DES simulation timing |
| 5 | Standard Set-Up Time (hours) | `setup_time` | Stored for reference |
| 6 | Operator Touch Time | `operator_touch_time` | Stored for reference |
| 7 | Machines Available | `machines_available` | Stored for reference |
| 8 | Concurrent Capacity per Machine | `concurrent_capacity` | Stored for reference |
| 9 | Standard WIP (SWIP) | `swip` | Stored for reference |
| 10 | Include in Completion Date Calc | `include_in_completion` | DES simulation |
| 11 | Include in Visual Simulation | `include_in_simulation` | Visual simulation page |
| 12 | Concurrent or Sequential | `concurrent_or_sequential` | DES simulation |

---

## Fields Produced by the Scheduler (Output Only)

These fields are computed by the DES engine and appear in exports/API but are not from any input file:

| Field | Description |
|---|---|
| `blast_date` | Scheduled BLAST arrival time |
| `completion_date` | Predicted completion time |
| `turnaround_days` | Days from WO creation to completion |
| `on_time` / `on_time_status` | Whether order meets Basic Finish Date |
| `assigned_core` | Core number + suffix assigned (e.g., "427-A") |
| `planned_desma` | Desma injection machine assigned |
| `priority` | Final priority tier (Hot-ASAP, Hot-Dated, Rework, Normal, CAVO) |
| `is_reline` | Whether order is a reline (vs. new stator) |

---

*Last updated: MVP 1.2 — February 2026*

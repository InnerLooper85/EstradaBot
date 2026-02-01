# DD Scheduler Bot

A Discrete Event Simulation (DES) based production scheduling application for stator manufacturing, with a Python backend.

## Features

### Core Scheduling
- **DES (Discrete Event Simulation) Scheduler** - Pipeline-based simulation for accurate production scheduling
- **5-Tier Priority System** - Hot ASAP → Hot Dated → Rework → Normal → CAVO ordering
- **Hot List Processing** - Supports both ASAP and dated priority entries with REDLINE rubber override
- **Rework/Re-BLAST Detection** - Automatically detects orders requiring rework via REMOV RB work center
- **Core Allocation & Lifecycle Tracking** - Manages core assignment and tracks state through operations

### Work Schedule
- 4-day work week support (Monday-Thursday)
- Dual shifts with configurable times
- Break and handover time handling
- Core oven preheat scheduling

### Resource Management
- 5 injection machines with rubber type tracking
- Rubber type assignment (HR, XE, etc.)
- Machine utilization tracking

### Reports & Exports
- Master Schedule (complete order timeline)
- BLAST Schedule (operation sequence)
- Core Oven Schedule (core preheat timing)
- Pending Core Report (core availability)
- Impact Analysis (hot list effect comparison)

## Project Structure

```
DD Scheduler Bot/
├── backend/
│   ├── algorithms/       # DES scheduler implementation
│   ├── data/             # Data storage
│   ├── exporters/        # Excel report generators
│   ├── models/           # Data models
│   ├── parsers/          # File parsing utilities
│   ├── reference/        # Reference files
│   └── utils/            # Utility functions
├── frontend/             # (Not yet implemented)
├── outputs/              # Generated output files
├── Scheduler Bot Info/   # Input Excel files
├── tests/                # Test files
└── requirements.txt      # Python dependencies
```

## Setup

### Backend

1. Create and activate virtual environment:
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Running the Scheduler

From the project root directory:

```bash
# Run full scheduler with all exports
python backend/exporters/excel_exporter.py

# Test data loader only
python backend/data_loader.py

# Test hot list parser
python backend/parsers/hot_list_parser.py "Scheduler Bot Info/HOT LIST STA-ROT.xlsx"
```

### Input Files Required

Place the following Excel files in `Scheduler Bot Info/`:

| File | Description |
|------|-------------|
| `Open Sales Order *.xlsx` | Open work orders with BLAST dates, customers, promise dates |
| `Shop Dispatch *.xlsx` | Shop floor dispatch data with work center operations |
| `Pegging Report *.XLSX` | Pegging report with actual start dates and WO creation dates |
| `HOT LIST STA-ROT.xlsx` | Hot list with priority orders (ASAP or dated) |
| `Core Mapping.xlsx` | Core mapping and process times reference |

### Output Files Generated

Output files are created in `outputs/` with timestamps:

| File | Description |
|------|-------------|
| `Master_Schedule_YYYYMMDD_HHMMSS.xlsx` | Complete schedule with all orders and operation times |
| `BLAST_Schedule_YYYYMMDD_HHMMSS.xlsx` | BLAST operation sequence for shop floor |
| `Core_Oven_Schedule_YYYYMMDD_HHMMSS.xlsx` | Core preheat schedule |
| `Pending_Core_YYYYMMDD_HHMMSS.xlsx` | Orders waiting for core availability |
| `Impact_Analysis_YYYYMMDD_HHMMSS.xlsx` | Comparison of baseline vs hot list schedule (if hot list loaded) |

## Architecture

### Backend Components

1. **Parsers** (`backend/parsers/`)
   - `sales_order_parser.py` - Parses Open Sales Order Excel files
   - `core_mapping_parser.py` - Parses Core Mapping and Core Inventory
   - `shop_dispatch_parser.py` - Parses Shop Dispatch data
   - `pegging_parser.py` - Parses Pegging Report for actual dates
   - `hot_list_parser.py` - Parses Hot List for priority orders
   - `order_filters.py` - Filters orders by status and criteria

2. **Scheduler** (`backend/algorithms/`)
   - `des_scheduler.py` - Discrete Event Simulation scheduler
     - Pipeline-based flow (not queue-based)
     - Handles routing for New Stator vs Reline
     - Core lifecycle management
     - 5-tier priority scheduling

3. **Exporters** (`backend/exporters/`)
   - `excel_exporter.py` - Main export orchestrator, generates all reports
   - `impact_analysis_exporter.py` - Generates hot list impact comparison

4. **Data Loader** (`backend/data_loader.py`)
   - Loads all input files using pattern matching
   - Coordinates parsers and builds unified data model

## Dependencies

- pandas
- openpyxl
- python-dateutil
- watchdog
- flask
- flask-cors

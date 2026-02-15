# Stator Production Scheduling Application - Requirements Document

**Document Version:** 1.2
**Date:** January 31, 2026
**Last Updated:** February 15, 2026
**Project Owner:** Manufacturing Planning Team

---

## Implementation Status (as of February 15, 2026)

> This requirements document describes the original desired functionality for the **Stators** production line. The application is now **live at https://www.estradabot.biz** (MVP 1.7) deployed on Google Cloud Run with Google Cloud Storage for persistent file storage.
>
> **Key implementation decisions that differ from this document:**
> - **Tech stack:** Uses Python Flask + Jinja2 + Bootstrap 5 (not React.js + Node.js as some sections imply)
> - **File storage:** Uses Google Cloud Storage bucket instead of local filesystem monitoring
> - **Core Mapping updates:** Admin re-uploads via web UI (no auto-reload file watcher)
> - **Database:** No database; uses GCS for file persistence and JSON state storage
>
> **Implemented beyond original spec (MVP 1.1–1.7):**
> - 4/5-day schedule toggle with 3-scenario planner comparison (4d/10h, 4d/12h, 5d/12h)
> - Special Requests page with Mode A/B, impact preview, approval queue
> - Order Holds system, Special Instructions column (from DCP Report)
> - Notification bell, Alert reports (Promise Date Risk, Core Shortage, Machine Utilization, Late Order Summary)
> - Mfg Eng Review page, DCP Report parser, Feedback status tracking
> - Planner workflow: scenario simulation, comparison, base schedule selection, publish flow
>
> **Still pending (MVP 1.x backlog):**
> - Rubber grouping optimization (LOW)
> - Resource utilization report (MEDIUM — MVP 1.8 target)
> - Extended simulation: 6-day weeks, skeleton shifts (HIGH)
> - RBAC / user management (MEDIUM)
> - Core Mapping read-only web view (MEDIUM)
> - Days Idle column (MEDIUM)
> - Basic schedule reorder (MEDIUM)
> - Automated tests (MEDIUM)
> - Dual-cylinder mode recommendation (deferred to MVP 3.0+)
> - QN integration (deferred — no data source yet)
>
> **MVP 2.0 scope (redefined Feb 15, 2026):**
> - Rotors product line (second department)
> - Customer-facing reports & quoting system
> - Full schedule manipulation GUI
> - Core Mapping editable database
> - See `MVP_2.0_Planning.md` for details

---

## 1. Executive Summary

### 1.1 Purpose
Develop a production scheduling application for a stator manufacturing facility that ingests SAP data, applies optimization algorithms to generate production schedules, and provides visual simulation of the production process. The application will replace manual scheduling processes and improve turnaround times, particularly for reline stators.

### 1.2 Key Objectives
- Minimize turnaround time for reline stators (80%+ of volume)
- Automate production sequencing based on tooling (core) availability
- Optimize injection machine utilization and rubber type sequencing
- Provide visual simulation of production flow
- Enable scenario analysis (different work schedules, priorities)
- Support multi-user collaboration with role-based permissions

---

## 2. Product Overview

### 2.1 Product Types
- **New Stators:** Part numbers beginning with numerical digits
- **Reline Stators:** Part numbers beginning with "XN" (80%+ of total volume)

### 2.2 Production Process
The production line consists of 22 steps, with variations based on product type:

**Process Steps (from left to right):**
1. RUBBER REMOVAL (Reline only)
2. RECEIVE TUBE
3. COUNTERBORE (New only)
4. INDUCTION COIL
5. STAMPING & INSPECTION
6. TRANSFER TO SUPERMKT
7. SUPERMKT (storage area)
8. BLAST ← **First scheduled operation**
9. TUBE PREP (concurrent with CORE OVEN)
10. CORE OVEN (concurrent with TUBE PREP)
11. ASSEMBLY
12. INJECTION ← **Bottleneck operation**
13. CURE
14. QUENCH
15. DISASSEMBLY
16. BLD END CUTBACK
17. INJ END CUTBACK
18. CUT THREADS (New only)
19. CUT ID BAND (New only)
20. STAMP ID BAND (New only)
21. SHOTPEEN
22. INSPECT RUBBER AND CERTIFY

**Critical Notes:**
- Operations before BLAST are not scheduled (feed the supermarket buffer)
- Scheduling begins at BLAST operation
- INJECTION is the bottleneck (5 machines, single-piece capacity each)

---

## 3. Data Requirements

### 3.1 Input Files

#### 3.1.1 Primary Data Source: Open Sales Order (Excel)
**Purpose:** Master file for production scheduling  
**Key Columns:**
- WO# (Work Order Number)
- BLAST DATE
- CORE (Core number)
- ITEM DESC (Part description)
- CUSTOMER NAME
- PROMISE DATE (Column AC - customer commitment)
- Basic Finish Date (Column AC - SAP planned date)
- Work Order Creation Date (Column AA - for turnaround time calculation)

**Update Frequency:** Daily or as needed when new orders are entered

#### 3.1.2 Supporting Data Sources

**Pegging Report (Excel):**
- Links sales orders to production orders
- Contains order numbers, materials, dates
- Used for context/validation

**Shop Dispatch Report (Excel):**
- Shows work-in-process (WIP) orders
- Contains current operation, elapsed days, priority
- Used to identify orders already past BLAST (exclude from scheduling)

### 3.2 Reference Files

#### 3.2.1 Core Mapping and Process Times (Excel)
**Sheet 1: Core Mapping and Process Times**
- New Part Number
- Reline Part Number
- Core Number (tooling required)
- Stator OD (Column H)
- Lobe Configuration (Column I)
- Stage Count (Column J)
- Rubber Type (Column K) - HR, XE, XR, XD
- Fit (Column L)
- Injection Time (hours) (Column M)
- Cure Time (hours) (Column N)
- Quench Time (hours) (Column O)

**Sheet 2: Core Inventory**
- Core Number
- Suffix (unique identifier within core number, e.g., "A", "B", "C")
- Core PN#
- Power Section Model
- Tooling components (Head, Nut, Bld Cone, Ring, Rod)

**Update Frequency:** 1-2 times per month (new cores added)  
**Access Method:** Auto-detect file updates and reload

#### 3.2.2 Process Map (Excel: Stators_Process_VSM.xlsx)
Contains operation details:
- SAP Operation Number (Row 0)
- SAP Workcenter Name (Row 1)
- New Stator routing flags (Row 2: Yes/No)
- Reline Stator routing flags (Row 3: Yes/No)
- Standard Cycle Time (hours) (Row 4)
- Standard Set-Up Time (hours) (Row 5)
- Operator Touch Time (Row 6)
- Machines Available (Row 7)
- Concurrent Capacity per Machine (Row 8)
- Standard WIP (SWIP) (Row 9)
- Include in Completion Date Calculation (Row 10: Yes/No)
- Include in Visual Simulation (Row 11: Yes/No)
- Concurrent or Sequential Operation (Row 12)

#### 3.2.3 Hot List (Excel - User Uploaded)
**Purpose:** Priority orders to move to front of schedule  
**Format:** List of production order numbers (WO#)  
**Access:** Customer service team uploads

#### 3.2.4 Quality Notifications (Excel - Future)
**Purpose:** Orders with quality holds  
**Action:** Move orders before BLAST back by 1 day  
**Status:** To be provided later in development

### 3.3 Floor Map
**File:** stators_only.pdf  
**Purpose:** Reference for building visual simulation block diagram  
**Key Areas:**
- Blast area
- Tube Prep and Paint
- Core Oven (capacity: 12 cores)
- Assembly benches
- Injection machines (5 units: Autoclave #5, #6, Puma 800L, Coil Tubing, Desma)
- Cure (Autoclaves)
- Quench tanks
- Disassembly benches (2 units)
- Core cleaning station (capacity: 2 cores, located near core oven)
- Shot peen area
- Final inspection

---

## 4. Scheduling Algorithm Requirements

### 4.1 Core Constraints

#### 4.1.1 Core-to-Part Mapping
- Each part number requires a specific core (from Core Mapping file)
- One core can only make one part at a time
- Multiple cores may exist for the same core number (identified by suffix)
- Example: Core 132-A, 132-B, 132-C are three separate cores

#### 4.1.2 Core Lifecycle
1. **CORE OVEN:** Heat core (2.5 hours standard, varies by size)
2. **ASSEMBLY:** Assemble heated core with prepared tube
3. **INJECTION:** Core remains in tube during injection
4. **CURE:** Core remains in tube during cure
5. **QUENCH:** Core remains in tube during quench
6. **DISASSEMBLY:** Remove core from tube
7. **CLEANING:** 45 minutes at dedicated cleaning station (2-core capacity)
8. **Return to CORE OVEN** for next use

#### 4.1.3 Core Oven Management
- Capacity: 12 cores simultaneously
- Cores pulled from oven only when ready for assembly (prevent cooling)
- Scheduler must track which core is heating for which job
- Generate core loading schedule (sequence and timing)

### 4.2 Injection Machine Optimization

#### 4.2.1 Machine Configuration
- 5 injection machines available
- Each machine processes 1 part at a time
- Standard injection time varies by part (from Core Mapping file)
- Injection is the bottleneck operation

#### 4.2.2 Rubber Type Sequencing
**Four rubber types:** HR, XE, XR, XD
- **Primary types:** HR and XE (XE replacing HR in volume)
- **Low volume types:** XR and XD (may not run daily)
- **Priority:** Group XR and XD parts together when possible
- **Minimize:** Rubber changeovers on each machine

#### 4.2.3 Dual-Cylinder Mode
- Each injection machine has 2 cylinders
- **Single-cylinder mode:** Load one rubber type, normal speed
- **Dual-cylinder mode:** Load two rubber types, 2.2X slower for BOTH types
- Operators can switch modes as needed
- **Scheduler action:** Recommend dual-cylinder mode when beneficial
- **Changeover time:** 1 hour when switching rubber types

### 4.3 Capacity Constraints

#### 4.3.1 Machine and Concurrent Capacity
- Respect "Machines Available" for each operation
- Respect "Concurrent Capacity per Machine" (pieces)
- Cannot start job if all machines/capacity occupied

#### 4.3.2 Concurrent Operations
**TUBE PREP and CORE OVEN run simultaneously:**
- Both start at same time for same stator
- TUBE PREP: Paint tubes, roll into tube oven (capacity: 18 pieces)
- CORE OVEN: Heat cores (capacity: 12 cores)
- Both complete before ASSEMBLY can begin

#### 4.3.3 Standard WIP Buffers
- **STAMPING & INSPECTION:** Maintain 8-piece buffer (cooling requirement)
- Other SWIP values are informational (typical queue sizes)

### 4.4 Sequencing Logic

#### 4.4.1 Primary Priority
**Minimize turnaround time for reline stators**
- Turnaround time = Days since Work Order Creation Date
- Reline stators are 80%+ of volume

#### 4.4.2 Default Sequencing
- **FIFO (First-In-First-Out)** based on Work Order Creation Date
- Earlier orders scheduled first

#### 4.4.3 Hot List Override
- Customer service team can upload priority order list
- Hot list orders moved to front of schedule
- **Required output:** Impact analysis showing:
  - Which orders are delayed
  - By how many days each is delayed
  - New completion dates for delayed orders
  - Updated turnaround times

#### 4.4.4 Quality Notification Handling (Future)
- Orders with open QNs before BLAST: delay by 1 day
- Allows time for QN resolution

### 4.5 Work-in-Process Handling
- Only schedule orders that have not yet reached BLAST
- Orders already at/past BLAST continue processing
- Assume ongoing operations continue per standard times

---

## 5. Work Schedule Configuration

### 5.1 Configurable Parameters

Users must be able to set:
1. **Work days per week:** 4, 5, or 6 days
2. **Shift length:** 10 or 12 hours
3. **Shift start times:** Default 5:00 AM and 5:00 PM
4. **Number of shifts:** 1 or 2 per day

### 5.2 Schedule Variations by Operation

**Operations after BLAST (scheduled operations):**
- Run on configured schedule (1-2 shifts, 10-12 hours)

**Operations before BLAST (feeding operations):**
- Typically run 1 shift only
- Scheduler should calculate: Days needed to keep up with scheduled operations

### 5.3 Holidays and Shutdowns

**Federal Holidays:** Assume plant closed (default)
- New Year's Day
- MLK Day
- Presidents' Day
- Memorial Day
- Independence Day
- Labor Day
- Thanksgiving + day after
- Christmas

**Custom Shutdowns:** User can enter specific shutdown dates

**Weekend Handling:** Simulation skips non-working days (accelerated time)

### 5.4 Start Date and Time
- **Default:** Today's date
- **User override:** Specify custom start date
- **Start time for BLAST:** 5:00 AM on first shift

---

## 6. Output Requirements

### 6.1 Production Schedule (Excel Export)

#### 6.1.1 Master Schedule
For each work order:
- WO# (Work Order Number)
- Part Number
- Part Description
- Customer Name
- Quantity
- Core Number and Suffix
- Rubber Type
- BLAST Start Date/Time
- Final Completion Date/Time
- Total Turnaround Time (days)
- Promise Date
- On-Time Status (Yes/No/At Risk)

#### 6.1.2 BLAST Operation Schedule (Printable)
Sequence of production orders to load at blast:
- Sequence number
- WO#
- Part Number
- BLAST Date/Time
- Core required

#### 6.1.3 Core Oven Schedule (Printable)
Sequence of cores to load in oven:
- Sequence number
- Core Number-Suffix (e.g., "132-B")
- Load Date/Time
- Associated WO#
- Part Number

#### 6.1.4 Projected Basic Finish Dates
For SAP update by planning team:
- WO#
- Current Basic Finish Date (from SAP)
- Projected Basic Finish Date (from scheduler)
- Variance (days)

### 6.2 Resource Utilization Reports (Excel Export)

For each operation and machine:
- Operation name
- Machine/resource ID
- Total available hours
- Total utilized hours
- Utilization percentage
- Idle time
- Setup time
- Processing time

### 6.3 Alert Reports (Excel Export)

#### 6.3.1 Promise Date Risk
Orders at risk of missing promise dates:
- WO#
- Part Number
- Customer Name
- Promise Date
- Projected Completion Date
- Days Late
- Turnaround Time

#### 6.3.2 Core Inventory Shortages
Core numbers with insufficient inventory:
- Core Number
- Cores Needed (count)
- Cores Available (count)
- Shortage (count)
- Affected Orders (list of WO#)

#### 6.3.3 Machine Utilization Alerts
- Machines below 20% utilization
- Machines above 85% utilization
- Recommendation for dual-cylinder mode (if applicable)

### 6.4 Schedule Versioning
- Each schedule saved with date and timestamp
- Ability to save multiple scenarios
- Compare scenarios side-by-side:
  - 5-day vs 6-day schedule
  - Different shift configurations
  - Hot list vs no hot list

---

## 7. Visual Simulation Requirements

### 7.1 Simulation Scope

**Include operations:** Only those marked "Yes" in "Include in Visual Simulation"
- SUPERMKT
- BLAST
- TUBE PREP
- CORE OVEN
- ASSEMBLY
- INJECTION
- CURE
- QUENCH
- DISASSEMBLY
- BLD END CUTBACK
- INJ END CUTBACK
- CUT THREADS
- SHOTPEEN
- INSPECT RUBBER AND CERTIFY

**Exclude operations:** Pre-BLAST operations not in visual simulation

### 7.2 Block Diagram Layout

**Based on floor map (stators_only.pdf):**
- Visual representation of shop floor
- Each operation shown as a block/area
- Layout reflects physical arrangement
- Queue/buffer areas visible between operations

### 7.3 Animation Features

#### 7.3.1 Moving Units
- Individual stators represented as moving objects
- Animation shows parts moving from operation to operation
- Parts accumulate in queue areas when waiting

#### 7.3.2 Queue/Buffer Display
- Visual indication of parts waiting at each operation
- Queue length visible (number of parts)
- SWIP levels indicated

#### 7.3.3 Machine Status (Color-Coded)
- **Gray:** Idle (not running)
- **Yellow:** Under 40% utilization
- **Green:** 40-85% utilization (optimal)
- **Orange:** Over 85% utilization (at risk)

### 7.4 Simulation Speed
- **Time scale:** 20 real minutes = 1 second of simulation
- **Weekend handling:** Skip non-working days (accelerated)
- **Controls:** Play, pause, speed adjustment
- **Time display:** Current simulated date/time

### 7.5 Additional Simulation Information
- Current operation for each stator
- Time in current operation
- Next operation scheduled
- Core assignment for each job
- Rubber type for injection jobs

---

## 8. User Interface Requirements

### 8.1 Main Dashboard

Display:
- Schedule status (date generated, version)
- Key metrics:
  - Total orders in schedule
  - Orders on time
  - Orders at risk
  - Average turnaround time
  - Resource utilization summary
- Alert summary (counts by type)
- Quick actions (generate schedule, run simulation, export reports)

### 8.2 Data Input Section

**File Upload:**
- Open Sales Order (Excel)
- Core Mapping and Process Times (Excel - auto-reload if updated)
- Hot List (Excel - optional)
- Quality Notifications (Excel - optional, future)

**Configuration:**
- Work schedule settings (days/week, shift length, start times)
- Start date for scheduling
- Holiday/shutdown dates
- Scenario name (for versioning)

### 8.3 Schedule Generation

**Process:**
1. User uploads data files
2. User configures work schedule
3. User clicks "Generate Schedule"
4. App displays progress/status
5. Results shown in dashboard
6. Export options available

**Scenario Comparison:**
- Save multiple scenarios
- View scenarios side-by-side in table format
- Compare key metrics (completion dates, utilization, etc.)

### 8.4 Simulation Viewer

**Controls:**
- Play/Pause
- Speed slider
- Jump to date/time
- Highlight specific order
- Highlight specific core

**Information Panel:**
- Selected order details
- Selected machine status
- Queue contents
- Current simulated time

### 8.5 Reports Section

**Available Reports:**
- Master Schedule
- BLAST Schedule (printable)
- Core Oven Schedule (printable)
- Resource Utilization
- Promise Date Risk
- Core Inventory Shortages
- Machine Utilization Alerts
- Projected Basic Finish Dates

**Export options:** Excel for all reports

---

## 9. User Access and Permissions

### 9.1 User Roles

#### 9.1.1 Administrator
**Permissions:**
- Full access to all features
- Manage users and permissions
- Configure system settings
- Upload/update all reference files

#### 9.1.2 Production Planner
**Permissions:**
- Generate schedules
- Configure work schedules
- Upload Open Sales Order data
- Run simulations
- Export all reports
- Save scenarios
- Update Basic Finish Dates in SAP (via export)

#### 9.1.3 Customer Service
**Permissions:**
- Upload Hot List
- View schedule impact analysis
- View promise date risk reports
- Generate "what-if" scenarios with hot list changes
- Cannot modify main schedule

#### 9.1.4 Operator (View Only)
**Permissions:**
- View BLAST schedule
- View Core Oven schedule
- View current production status
- Cannot generate schedules or modify data

### 9.2 Collaboration Features

**Multi-user support:**
- Multiple users can access simultaneously
- Role-based access control
- Activity log (who generated which schedule, when)
- Concurrent viewing of simulation (read-only for most users)

---

## 10. Technical Requirements

### 10.1 File Processing

**Excel Reading:**
- Support .xlsx and .XLSX file extensions
- Handle multi-sheet workbooks
- Parse specific columns by name or position
- Validate data format and completeness

**PDF Reading:**
- Extract floor map layout from PDF
- Use for simulation visualization reference

**Auto-Reload:**
- Monitor Core Mapping file for changes
- Detect file timestamp/modification date
- Reload and validate data automatically
- Notify user of reload

### 10.2 Data Validation

**Required checks:**
- All work orders have valid part numbers
- Part numbers exist in Core Mapping file
- Core numbers exist in Core Inventory
- Date fields are valid dates
- Numeric fields are valid numbers
- Required columns present in all input files

**Error handling:**
- Display clear error messages
- Identify specific rows/records with issues
- Allow user to correct and re-upload
- Do not proceed with invalid data

### 10.3 Scheduling Algorithm

**Must handle:**
- 100+ work orders simultaneously
- Complex resource constraints (machines, cores, capacity)
- Multi-objective optimization (minimize turnaround, balance utilization)
- What-if scenario analysis
- Real-time updates when hot list changes

**Performance:**
- Generate schedule in under 2 minutes for 100 orders
- Responsive UI during calculation
- Progress indication for long operations

### 10.4 Simulation Engine

**Requirements:**
- Event-driven simulation
- Accurate time tracking (down to minutes)
- Resource state management
- Queue management
- Visual rendering at 60 FPS minimum

### 10.5 Export Capabilities

**Excel:**
- Generate formatted workbooks
- Multiple sheets per file
- Conditional formatting for alerts
- Print-friendly formatting for BLAST and Core schedules

**Standards:**
- Use standard Excel formats (.xlsx)
- Compatible with Microsoft Excel 2016+
- Compatible with Google Sheets

---

## 11. Data Mapping and Business Rules

### 11.1 Part Number to Core Mapping

**Source:** Core Mapping and Process Times (Sheet 1)
**Rule:** Match order part number to New Part Number or Reline Part Number
**Result:** Obtain Core Number, Rubber Type, Injection Time, Cure Time, Quench Time

**Special cases:**
- Part number starts with "XN" → Reline (use Reline Part Number column)
- Part number starts with digit → New (use New Part Number column)
- If no exact match found → Flag as error

### 11.2 Routing Determination

**Source:** Stators_Process_VSM.xlsx (Rows 2 and 3)
**Rule:** Based on part number prefix:
- New stator → Use "New Stator" row flags
- Reline stator → Use "Reline Stator" row flags

**Operation inclusion:**
- If flag = "Yes" → Include operation in routing
- If flag = "No" → Skip operation

### 11.3 Processing Time Calculation

**Cycle time:** Standard Cycle Time (from Process Map)
**Setup time:** Standard Set-Up Time (from Process Map)
**Variable times:**
- INJECTION: From Core Mapping (Column M)
- CURE: From Core Mapping (Column N)
- QUENCH: From Core Mapping (Column O)

**Concurrent operations:**
- TUBE PREP and CORE OVEN: Start together, both must complete before ASSEMBLY
- Use max(TUBE PREP time, CORE OVEN time) for scheduling

**Dual-cylinder injection:**
- Normal injection time × 2.2 when machine in dual-cylinder mode

### 11.4 Turnaround Time Calculation

**Formula:** (Completion Date - Work Order Creation Date) in days
**Source:** Work Order Creation Date from Open Sales Order (Column AA)
**Use:** Performance metric, optimization objective

### 11.5 Promise Date Compliance

**Source:** Promise Date from Open Sales Order
**Rule:** 
- On-time if Completion Date ≤ Promise Date
- At-risk if (Promise Date - Completion Date) ≤ 2 days
- Late if Completion Date > Promise Date

### 11.6 Core Availability Check

**When scheduling order:**
1. Identify required Core Number from mapping
2. Check Core Inventory for available cores with that number
3. Track core lifecycle state (oven, in-use, cleaning, available)
4. If no cores available → Queue order or flag shortage
5. Assign specific core (with suffix) to order

---

## 12. Assumptions and Constraints

### 12.1 Assumptions

1. **Data accuracy:** Uploaded files contain accurate, current data
2. **Single facility:** Schedule applies to one production facility
3. **Standard times:** Process times from mapping file are accurate averages
4. **Resource availability:** Machines and operators available as configured
5. **No unplanned downtime:** Maintenance and breakdowns not modeled
6. **Order quantities:** Assume quantity = 1 unless specified (most common)
7. **Material availability:** Raw materials (rubber, tubes) are available when needed

### 12.2 Constraints

1. **Core constraint:** Each order requires specific core, only one core per core number can be used at a time (if only one exists)
2. **Injection bottleneck:** 5 machines, single capacity each, limits throughput
3. **Core oven capacity:** 12 cores maximum
4. **Cleaning capacity:** 2 cores maximum at cleaning station
5. **SWIP buffer:** 8-piece buffer required at STAMPING & INSPECTION
6. **Work schedule:** Operations only run during scheduled shifts
7. **Changeover time:** 1 hour lost when changing rubber types
8. **Dual-cylinder penalty:** 2.2X slower injection when using dual cylinders

### 12.3 Out of Scope (Current Version)

1. **Operator scheduling:** Assumes operators available when needed
2. **Preventive maintenance:** Not scheduled in current version
3. **Material resource planning:** Rubber and tube inventory not tracked
4. **Quality control details:** Beyond QN delay, not modeled
5. **Cost optimization:** Focus on time, not cost minimization
6. **Real-time tracking:** Not integrated with shop floor data collection
7. **Automatic SAP updates:** Manual export/import required

---

## 13. Success Criteria

### 13.1 Functional Success

1. **Schedule generation:** Successfully creates feasible schedule for 100+ orders
2. **Core allocation:** Correctly assigns cores based on availability and part requirements
3. **Resource constraints:** Respects all capacity limits (machines, oven, cleaning)
4. **Time accuracy:** Completion dates accurate within ±4 hours
5. **Hot list impact:** Correctly shows delay impact when priorities change
6. **Simulation:** Visual representation matches schedule logic

### 13.2 Performance Success

1. **Schedule generation time:** Under 2 minutes for 100 orders
2. **Simulation frame rate:** 60 FPS minimum
3. **File upload:** Process files under 10 MB in under 30 seconds
4. **Report export:** Generate Excel reports in under 10 seconds

### 13.3 Usability Success

1. **User training:** Production planners can use system after 2-hour training
2. **Error handling:** Clear error messages guide users to resolution
3. **Interface:** Intuitive navigation, minimal clicks to common tasks
4. **Mobile access:** Operators can view schedules on tablets

### 13.4 Business Success

1. **Turnaround time reduction:** 10% improvement in average reline turnaround
2. **On-time delivery:** 5% improvement in orders meeting promise dates
3. **Resource utilization:** Injection machines at 70-85% utilization
4. **Planner time savings:** 50% reduction in manual scheduling time

---

## 14. Future Enhancements (Beyond MVP 1.x)

> **Note:** The project roadmap was replanned on Feb 15, 2026. See `MVP_2.0_Planning.md` for the current plan. This section is kept for historical reference and long-term vision.

### 14.1 MVP 2.0 (Planned)
- **Rotors product line** — second manufacturing department with own staffing, machines, scheduling logic
- **Customer-facing reports & quoting system** — customer reports, quotes with temporary production slot holds
- **Full schedule manipulation GUI** — drag-drop reorder, resource reassignment, manual overrides
- **Core Mapping editable database** — replace Excel upload with web editor

### 14.2 MVP 3.0+ (Deferred)
- Dual-cylinder mode recommendation
- Integration with SAP for automatic data pull
- Real-time shop floor data integration
- Customer self-service portal
- Quality Notification integration (QN report)

### 14.3 Long-term Vision
- Autonomous scheduling (minimal human intervention)
- IoT integration for real-time machine status
- Predictive maintenance scheduling
- Material resource planning (rubber inventory)
- Cost optimization alongside time optimization
- Supply chain integration (vendor coordination)

---

## 15. Appendices

### 15.1 Glossary

- **Core:** Injection molding tool/die used to form stator interior
- **Reline:** Refurbishment process for used stators
- **SWIP:** Standard Work-in-Process (buffer inventory)
- **QN:** Quality Notification (issue requiring resolution)
- **WO#:** Work Order Number
- **FIFO:** First-In-First-Out
- **Turnaround Time:** Days from order creation to completion
- **Hot List:** Priority orders requiring expedited processing
- **DXA:** Document eXchange Architecture (measurement unit)

### 15.2 File Locations

**Production (Google Cloud Storage):**

All files are stored in GCS bucket `gs://estradabot-files/`:
- `uploads/` - All uploaded input files (uploaded via web UI)
- `outputs/` - Generated reports (created during schedule generation)
- `state/current_schedule.json` - Persisted schedule state

**Input Files (uploaded via web UI):**
- `Open Sales Order *.xlsx` - Uploaded by Planner
- `Pegging Report *.xlsx` (optional) - Uploaded by Planner
- `Shop Dispatch *.xlsx` (optional) - Uploaded by Planner
- `HOT LIST *.xlsx` (optional) - Uploaded by Planner or Customer Service

**Reference Files (uploaded by Admin):**
- `Core Mapping.xlsx` - Core mapping and process times
- `Stators Process VSM.xlsx` - Operation routing parameters

**Local Development:**

For local development, files can be placed in `Scheduler Bot Info/` or uploaded via the local web UI.

**Quality Notifications (future):**
- QN Report integration not yet implemented

### 15.3 Contact Information

**Project Stakeholders:**
- Production Planning Team
- Manufacturing Operations
- Customer Service Team
- Quality Control
- IT Support

---

**Document End**

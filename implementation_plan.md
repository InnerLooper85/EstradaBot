# Stator Production Scheduling Application - Implementation Plan

**Document Version:** 1.0  
**Date:** January 31, 2026  
**Estimated Total Timeline:** 8-12 weeks

---

## 1. Implementation Overview

### 1.1 Development Approach

**Strategy:** Phased, incremental development with testing at each phase

**Key Principles:**
1. Build foundation first (data processing, core algorithms)
2. Validate logic before UI development
3. Test with real data throughout
4. Deliver working features incrementally
5. User feedback loops at each phase

### 1.2 Phase Summary

| Phase | Focus | Duration | Deliverable |
|-------|-------|----------|-------------|
| Phase 1 | Data Foundation | 1-2 weeks | Data ingestion and validation |
| Phase 2 | Core Scheduling Algorithm | 2-3 weeks | Basic schedule generation |
| Phase 3 | Optimization Logic | 1-2 weeks | Resource optimization |
| Phase 4 | User Interface | 2-3 weeks | Web application UI |
| Phase 5 | Visual Simulation | 2-3 weeks | Animated simulation |
| Phase 6 | Reporting & Export | 1 week | All reports and exports |
| Phase 7 | Testing & Refinement | 1-2 weeks | User acceptance testing |

**Total:** 10-16 weeks (can be compressed with parallel work)

---

## 2. Phase 1: Data Foundation (Weeks 1-2)

### 2.1 Objectives
- Parse all input Excel files correctly
- Validate data completeness and format
- Build data models for internal processing
- Create file monitoring for Core Mapping updates

### 2.2 Detailed Steps

#### Step 1.1: Set Up Development Environment
**Duration:** 1 day

**Tasks:**
- Set up Node.js/Python development environment
- Install required libraries:
  - Excel processing: `xlsx`, `pandas`, `openpyxl`
  - File monitoring: `chokidar`, `watchdog`
  - Date/time: `date-fns`, `luxon`, `datetime`
- Set up version control (Git)
- Create project directory structure

**Directory Structure:**
```
stator-scheduler/
├── backend/
│   ├── data/           # Input files
│   ├── reference/      # Core mapping, process VSM
│   ├── models/         # Data models
│   ├── parsers/        # File parsers
│   ├── algorithms/     # Scheduling logic
│   └── utils/          # Helper functions
├── frontend/
│   ├── src/
│   │   ├── components/ # React components
│   │   ├── pages/      # Main pages
│   │   └── services/   # API calls
│   └── public/
└── outputs/            # Generated schedules, reports
```

#### Step 1.2: Build Excel File Parsers
**Duration:** 3 days

**Task 1.2.1: Open Sales Order Parser**
- Read Excel file using `xlsx` or `pandas`
- Extract key columns:
  - WO# (Work Order Number)
  - BLAST DATE
  - CORE
  - ITEM DESC
  - CUSTOMER NAME
  - PROMISE DATE (Column AC)
  - Basic Finish Date (Column AC)
  - Work Order Creation Date (Column AA)
- Handle missing/null values
- Validate data types (dates are dates, numbers are numbers)
- Return structured array of orders

**Code Example:**
```python
def parse_open_sales_order(filepath):
    df = pd.read_excel(filepath, sheet_name='OSO')  # Or appropriate sheet
    
    orders = []
    for index, row in df.iterrows():
        order = {
            'wo_number': str(row['WO#']),
            'part_number': extract_part_from_desc(row['ITEM DESC']),
            'description': row['ITEM DESC'],
            'customer': row['CUSTOMER NAME'],
            'promise_date': pd.to_datetime(row['PROMISE DATE']),
            'creation_date': pd.to_datetime(row['Work Order Creation Date']),
            'core_number': row['CORE'],
            'blast_date': row['BLAST DATE'] if pd.notna(row['BLAST DATE']) else None
        }
        orders.append(order)
    
    return orders
```

**Task 1.2.2: Core Mapping Parser**
- Read "Core Mapping and Process Times" sheet
- Create lookup dictionary: part_number → {core_number, rubber_type, injection_time, cure_time, quench_time}
- Handle both new and reline part numbers
- Validate all required columns present

**Code Example:**
```python
def parse_core_mapping(filepath):
    df = pd.read_excel(filepath, sheet_name='Core Mapping and Process Times')
    
    mapping = {}
    for index, row in df.iterrows():
        # Map both new and reline part numbers to same data
        for part_col in ['New Part Number', 'Reline Part Number']:
            if pd.notna(row[part_col]):
                part = str(row[part_col])
                mapping[part] = {
                    'core_number': row['Core Number'],
                    'rubber_type': row['Rubber Type'],
                    'injection_time': row['Injection Time (hours)'],
                    'cure_time': row['Cure Time'],
                    'quench_time': row['Quench Time'],
                    'stator_od': row['Stator OD'],
                    'lobe_config': row['Lobe Configuration'],
                    'stage_count': row['Stage Count']
                }
    
    return mapping
```

**Task 1.2.3: Core Inventory Parser**
- Read "Core Inventory" sheet
- Create list of available cores with suffixes
- Group by core number for availability counting

**Code Example:**
```python
def parse_core_inventory(filepath):
    df = pd.read_excel(filepath, sheet_name='Core Inventory')
    
    inventory = {}
    for index, row in df.iterrows():
        core_num = row['Core Number']
        suffix = row['Suffix']
        
        if core_num not in inventory:
            inventory[core_num] = []
        
        inventory[core_num].append({
            'suffix': suffix,
            'core_pn': row['Core PN#'],
            'model': row['Power Section Model'],
            'state': 'available'  # Will track: available, oven, in_use, cleaning
        })
    
    return inventory
```

**Task 1.2.4: Process Map Parser**
- Read Stators_Process_VSM.xlsx
- Extract operation details (cycle times, setup times, capacities)
- Create routing templates for new vs reline

#### Step 1.3: Data Validation Module
**Duration:** 2 days

**Validations:**
1. **Order validation:**
   - WO# is unique
   - Part number exists in Core Mapping
   - Dates are valid and logical (promise date > creation date)
   - Core number matches expected value

2. **Core validation:**
   - All required cores exist in inventory
   - Sufficient cores available for demand
   - Injection/cure/quench times are numeric and positive

3. **Process validation:**
   - All operations have required parameters
   - Capacities are positive integers
   - Time values are numeric

**Error Reporting:**
- Generate detailed validation report
- List all errors with row numbers
- Categorize as blocking vs warning
- Do not proceed if blocking errors exist

#### Step 1.4: File Monitoring System
**Duration:** 1 day

**Requirements:**
- Watch Core Mapping file for changes (modification timestamp)
- Auto-reload when file updated
- Validate new data before replacing old
- Notify user of successful reload
- Handle file lock issues (file open in Excel)

**Code Example (Node.js):**
```javascript
const chokidar = require('chokidar');

const watcher = chokidar.watch('reference/Core_Mapping.xlsx', {
  persistent: true,
  ignoreInitial: true
});

watcher.on('change', async (path) => {
  console.log(`File ${path} has been changed, reloading...`);
  try {
    const newMapping = await parseCore Mapping(path);
    const validation = validateCoreMapping(newMapping);
    
    if (validation.isValid) {
      globalCoreMapping = newMapping;
      notifyUI('Core mapping updated successfully');
    } else {
      notifyUI('Core mapping update failed: ' + validation.errors);
    }
  } catch (error) {
    console.error('Error reloading core mapping:', error);
  }
});
```

### 2.3 Phase 1 Testing

**Test Cases:**
1. Load each sample Excel file successfully
2. Validate data extraction accuracy (spot-check 10 rows)
3. Handle missing columns gracefully
4. Handle malformed data (text in number fields)
5. File monitoring detects changes within 5 seconds
6. Validation catches all known error types

**Deliverable:** 
- Data parser library with unit tests
- Validation report generator
- File monitoring service

---

## 3. Phase 2: Core Scheduling Algorithm (Weeks 3-5)

### 3.1 Objectives
- Implement basic scheduling logic (FIFO)
- Handle resource constraints (machines, cores, capacity)
- Calculate operation start/end times
- Respect work schedule (shifts, holidays)

### 3.2 Detailed Steps

#### Step 2.1: Define Data Models
**Duration:** 1 day

**Models needed:**
```python
class WorkOrder:
    wo_number: str
    part_number: str
    description: str
    customer: str
    creation_date: datetime
    promise_date: datetime
    quantity: int = 1
    routing: List[Operation]
    assigned_core: str  # e.g., "124-B"
    
class Operation:
    name: str
    sap_number: str
    workcenter: str
    cycle_time: float  # hours
    setup_time: float
    machines_available: int
    concurrent_capacity: int
    scheduled_start: datetime
    scheduled_end: datetime
    
class Resource:
    resource_id: str  # e.g., "Autoclave_5"
    type: str  # e.g., "injection_machine"
    available: bool
    current_rubber: str  # For injection machines
    utilization: float
    schedule: List[Tuple[datetime, datetime, str]]  # (start, end, wo_number)
    
class Core:
    core_number: int
    suffix: str
    state: str  # available, oven, in_use, cleaning
    assigned_to: str  # wo_number
    state_change_time: datetime
```

#### Step 2.2: Work Schedule Calculator
**Duration:** 2 days

**Task 2.2.1: Shift Configuration**
- Accept user inputs: days/week, shift length, start times
- Generate working hours for date range
- Default: 2 shifts (5 AM - 3 PM, 5 PM - 3 AM), 5 days/week

**Task 2.2.2: Holiday Calendar**
- Load federal holidays for current year
- Allow user to add custom shutdown dates
- Function: `is_working_time(datetime) -> bool`

**Task 2.2.3: Time Advancement**
- Given current time and duration, calculate end time
- Skip non-working hours
- Account for shift boundaries
- Handle overnight operations

**Code Example:**
```python
def advance_time(start_time, duration_hours, work_schedule):
    """
    Advance time by duration_hours, skipping non-working periods.
    Returns end_time.
    """
    current = start_time
    remaining = duration_hours
    
    while remaining > 0:
        if not is_working_time(current, work_schedule):
            # Skip to next shift start
            current = next_shift_start(current, work_schedule)
            continue
        
        # How much time until shift ends?
        shift_end = get_shift_end(current, work_schedule)
        time_in_shift = (shift_end - current).total_seconds() / 3600
        
        if time_in_shift >= remaining:
            # Can finish in this shift
            current = current + timedelta(hours=remaining)
            remaining = 0
        else:
            # Use rest of shift, continue in next shift
            remaining -= time_in_shift
            current = next_shift_start(shift_end, work_schedule)
    
    return current
```

#### Step 2.3: Routing Generator
**Duration:** 2 days

**Task 2.3.1: Build Routing for Order**
- Determine if new or reline (based on part number prefix)
- Look up routing flags in Process Map
- Create sequence of operations
- Attach time parameters to each operation

**Task 2.3.2: Variable Time Lookup**
- For INJECTION, CURE, QUENCH: get times from Core Mapping
- Use part number to lookup
- Handle missing data (flag as error)

**Code Example:**
```python
def build_routing(order, process_map, core_mapping):
    """Generate list of operations for this order."""
    is_reline = order.part_number.startswith('XN')
    routing_row = 'Reline Stator' if is_reline else 'New Stator'
    
    operations = []
    for op_name, op_data in process_map.items():
        # Check if this operation applies to this product type
        if op_data['routing_flags'][routing_row] == 'Yes':
            operation = Operation(
                name=op_name,
                sap_number=op_data['sap_number'],
                workcenter=op_data['workcenter'],
                cycle_time=get_cycle_time(op_name, order, op_data, core_mapping),
                setup_time=op_data['setup_time'],
                machines_available=op_data['machines_available'],
                concurrent_capacity=op_data['concurrent_capacity']
            )
            operations.append(operation)
    
    return operations

def get_cycle_time(op_name, order, op_data, core_mapping):
    """Get cycle time, checking for variable times."""
    if op_name == 'INJECTION':
        return core_mapping[order.part_number]['injection_time']
    elif op_name == 'CURE':
        return core_mapping[order.part_number]['cure_time']
    elif op_name == 'QUENCH':
        return core_mapping[order.part_number]['quench_time']
    else:
        return op_data['cycle_time']
```

#### Step 2.4: Core Allocation Logic
**Duration:** 2 days

**Task 2.4.1: Core Assignment**
- When scheduling order, look up required core number
- Find available core with that number (check inventory)
- Assign specific core (with suffix) to order
- Track core state through lifecycle

**Task 2.4.2: Core State Machine**
```
available → oven (2.5 hrs) → ready → in_use (assembly → injection → cure → quench) 
→ disassembly → cleaning (45 min) → available
```

**Task 2.4.3: Core Availability Checker**
- Before scheduling order, check if core will be available
- If not, queue order or delay start
- Flag core shortages

**Code Example:**
```python
def assign_core(order, core_inventory, schedule_time):
    """
    Find and assign available core for this order.
    Returns (core_number, suffix) or None if unavailable.
    """
    required_core = get_required_core(order.part_number, core_mapping)
    
    if required_core not in core_inventory:
        raise CoreShortageError(f"Core {required_core} not in inventory")
    
    # Find available core with this number
    for core in core_inventory[required_core]:
        if core['state'] == 'available':
            # Mark as assigned
            core['state'] = 'oven'
            core['state_change_time'] = schedule_time
            core['assigned_to'] = order.wo_number
            return (required_core, core['suffix'])
    
    # No cores available
    return None
```

#### Step 2.5: Basic FIFO Scheduler
**Duration:** 3 days

**Task 2.5.1: Order Sorting**
- Sort orders by creation date (earliest first)
- This is base FIFO sequence

**Task 2.5.2: Sequential Scheduling**
- Start with first order in sorted list
- Schedule BLAST operation (first scheduled operation)
- For each subsequent operation:
  - Check resource availability
  - Wait for previous operation to complete
  - Wait for resource to become available
  - Schedule operation
  - Update resource schedule

**Task 2.5.3: Resource Tracking**
- Maintain schedule for each machine/resource
- When operation needs resource, find earliest available time
- Book resource for operation duration
- Handle concurrent operations (TUBE PREP + CORE OVEN)

**Code Example:**
```python
def schedule_orders_fifo(orders, resources, work_schedule, start_date):
    """
    Schedule orders in FIFO sequence.
    Returns scheduled_orders with operation times.
    """
    # Sort by creation date
    orders.sort(key=lambda o: o.creation_date)
    
    scheduled = []
    
    for order in orders:
        # Assign core
        core = assign_core(order, core_inventory, start_date)
        if core is None:
            # Log core shortage, skip or queue
            log_shortage(order)
            continue
        
        order.assigned_core = f"{core[0]}-{core[1]}"
        
        # Schedule each operation in routing
        prev_end_time = start_date
        
        for operation in order.routing:
            # Find resource
            resource = find_available_resource(
                operation.workcenter,
                prev_end_time,
                operation.cycle_time + operation.setup_time,
                resources,
                work_schedule
            )
            
            # Schedule operation
            op_start = max(prev_end_time, resource.next_available_time)
            op_end = advance_time(op_start, operation.cycle_time + operation.setup_time, work_schedule)
            
            operation.scheduled_start = op_start
            operation.scheduled_end = op_end
            
            # Book resource
            resource.schedule.append((op_start, op_end, order.wo_number))
            resource.next_available_time = op_end
            
            # Update for next operation
            prev_end_time = op_end
        
        # Final completion time
        order.completion_date = order.routing[-1].scheduled_end
        order.turnaround_time = (order.completion_date - order.creation_date).days
        
        scheduled.append(order)
    
    return scheduled
```

### 3.3 Phase 2 Testing

**Test Cases:**
1. Schedule 10 orders with simple routing (all new or all reline)
2. Verify operation times respect work schedule (no work on weekends)
3. Check resource allocation (no double-booking)
4. Verify concurrent operations (TUBE PREP + CORE OVEN) scheduled correctly
5. Core assignment works (unique cores assigned)
6. Turnaround time calculated correctly

**Deliverable:**
- Basic scheduler engine
- Generates feasible schedule with operation times
- Text-based output showing schedule

---

## 4. Phase 3: Optimization Logic (Weeks 6-7)

### 4.1 Objectives
- Implement rubber type sequencing optimization
- Add hot list priority handling
- Calculate and display schedule impacts
- Optimize for minimal turnaround time

### 4.2 Detailed Steps

#### Step 3.1: Rubber Type Grouping
**Duration:** 2 days

**Task 3.1.1: Rubber Type Analyzer**
- Analyze orders in queue by rubber type
- Count orders per type: HR, XE, XR, XD
- Identify low-volume types (XR, XD)
- Group consecutive orders of same type

**Task 3.1.2: Injection Machine Assignment**
- Assign orders to specific injection machines
- Try to group same rubber types on same machine
- Calculate changeover time penalty (1 hour) when switching
- Recommend dual-cylinder mode if beneficial

**Optimization Goal:**
- Minimize number of rubber changeovers
- Group XR and XD orders together
- Balance load across 5 machines

**Code Example:**
```python
def optimize_injection_sequence(orders):
    """
    Re-sequence orders to minimize rubber changeovers.
    Returns optimized sequence.
    """
    # Group by rubber type
    by_rubber = {}
    for order in orders:
        rubber = get_rubber_type(order.part_number, core_mapping)
        if rubber not in by_rubber:
            by_rubber[rubber] = []
        by_rubber[rubber].append(order)
    
    # Prioritize grouping low-volume types
    optimized_sequence = []
    
    # First, schedule grouped XR and XD
    for rare_rubber in ['XR', 'XD']:
        if rare_rubber in by_rubber:
            optimized_sequence.extend(by_rubber[rare_rubber])
    
    # Then interleave HR and XE to balance machines
    hr_orders = by_rubber.get('HR', [])
    xe_orders = by_rubber.get('XE', [])
    
    # Simple interleaving (can be more sophisticated)
    while hr_orders or xe_orders:
        if hr_orders:
            optimized_sequence.append(hr_orders.pop(0))
        if xe_orders:
            optimized_sequence.append(xe_orders.pop(0))
    
    return optimized_sequence
```

#### Step 3.2: Hot List Integration
**Duration:** 2 days

**Task 3.2.1: Hot List Parser**
- Read Excel file with WO# list
- Validate WO# exist in main order list
- Flag errors for invalid WO#

**Task 3.2.2: Priority Sequencing**
- Move hot list orders to front of queue
- Maintain FIFO within hot list
- Re-schedule all orders
- Calculate delay impact on non-hot orders

**Task 3.2.3: Impact Analysis**
- Compare original schedule vs hot list schedule
- For each delayed order, calculate:
  - Original completion date
  - New completion date
  - Days delayed
  - New turnaround time
  - Promise date impact (now late?)

**Code Example:**
```python
def apply_hot_list(orders, hot_list_wos):
    """
    Move hot list orders to front, calculate impact.
    Returns (new_sequence, impact_report).
    """
    hot_orders = []
    normal_orders = []
    
    for order in orders:
        if order.wo_number in hot_list_wos:
            hot_orders.append(order)
        else:
            normal_orders.append(order)
    
    # Hot list first (FIFO within hot list), then normal orders
    new_sequence = hot_orders + normal_orders
    
    # Re-schedule with new sequence
    original_schedule = {o.wo_number: o.completion_date for o in orders}
    new_schedule = schedule_orders(new_sequence, ...)
    
    # Calculate impact
    impact = []
    for order in new_schedule:
        if order.wo_number not in hot_list_wos:
            original_date = original_schedule[order.wo_number]
            new_date = order.completion_date
            delay_days = (new_date - original_date).days
            
            if delay_days > 0:
                impact.append({
                    'wo_number': order.wo_number,
                    'customer': order.customer,
                    'original_date': original_date,
                    'new_date': new_date,
                    'days_delayed': delay_days,
                    'new_turnaround': order.turnaround_time,
                    'promise_date': order.promise_date,
                    'now_late': new_date > order.promise_date
                })
    
    return new_schedule, impact
```

#### Step 3.3: Dual-Cylinder Mode Recommendation
**Duration:** 1 day

**Logic:**
- If queue has many mixed rubber types (e.g., 40% HR, 40% XE, 20% XR)
- AND changeover time penalty is high
- THEN recommend dual-cylinder for one or more machines

**Calculation:**
- Compare: (changeover_time × num_changeovers) vs (2.2 × injection_time × num_orders)
- If dual-cylinder saves time overall, recommend it

#### Step 3.4: Turnaround Time Minimization
**Duration:** 2 days

**Heuristic Optimization:**
- Prioritize reline orders (80% of volume)
- Within reline, schedule oldest orders first
- Consider "critical ratio": (promise_date - current_date) / remaining_time
- If critical ratio < 1.0, order is at risk → prioritize

**Code Example:**
```python
def optimize_for_turnaround(orders):
    """
    Optimize sequence to minimize average turnaround time.
    """
    # Separate reline vs new
    reline = [o for o in orders if o.part_number.startswith('XN')]
    new = [o for o in orders if not o.part_number.startswith('XN')]
    
    # Sort reline by creation date (FIFO = minimize turnaround for majority)
    reline.sort(key=lambda o: o.creation_date)
    
    # Sort new by creation date
    new.sort(key=lambda o: o.creation_date)
    
    # Reline first (priority), then new
    return reline + new
```

### 4.3 Phase 3 Testing

**Test Cases:**
1. Rubber grouping reduces changeovers by ≥30%
2. Hot list correctly moves orders to front
3. Impact analysis shows accurate delay calculations
4. Dual-cylinder recommendation appears when appropriate
5. Turnaround time optimization reduces average by ≥10%

**Deliverable:**
- Optimized scheduler with rubber sequencing
- Hot list functionality with impact analysis
- Recommendation engine for dual-cylinder mode

---

## 5. Phase 4: User Interface (Weeks 8-10)

### 5.1 Objectives
- Build web-based user interface
- Enable file uploads and configuration
- Display schedules and reports
- Support role-based access

### 5.2 Technology Stack

**Frontend:**
- React.js for UI components
- Material-UI or Ant Design for component library
- Recharts for visualizations
- Axios for API calls

**Backend:**
- Node.js with Express OR Python with Flask/FastAPI
- RESTful API endpoints
- File upload handling
- Session management for user roles

**Database (optional for this phase):**
- SQLite or PostgreSQL for storing schedules, users
- Can use file-based storage initially

### 5.3 Detailed Steps

#### Step 4.1: Backend API Development
**Duration:** 3 days

**Endpoints needed:**
```
POST /api/upload/sales-order      # Upload Open Sales Order file
POST /api/upload/hot-list          # Upload Hot List file
POST /api/upload/qn-report         # Upload QN Report (future)
GET  /api/reference/core-mapping   # Get current core mapping data
POST /api/schedule/generate        # Generate schedule
GET  /api/schedule/:id             # Get specific schedule
GET  /api/schedule/:id/compare/:id2 # Compare two schedules
POST /api/config/work-schedule     # Set work schedule parameters
GET  /api/reports/utilization      # Get resource utilization report
GET  /api/reports/promise-risk     # Get promise date risk report
GET  /api/reports/core-shortage    # Get core shortage report
POST /api/auth/login               # User authentication
GET  /api/auth/user                # Get current user info
```

**Example Endpoint:**
```javascript
app.post('/api/schedule/generate', async (req, res) => {
  try {
    const { salesOrderFile, hotListFile, workConfig } = req.body;
    
    // Parse input files
    const orders = await parseOpenSalesOrder(salesOrderFile);
    const hotList = hotListFile ? await parseHotList(hotListFile) : [];
    
    // Validate data
    const validation = validateOrders(orders);
    if (!validation.isValid) {
      return res.status(400).json({ errors: validation.errors });
    }
    
    // Generate schedule
    const schedule = await generateSchedule(orders, hotList, workConfig);
    
    // Save schedule with timestamp
    const scheduleId = await saveSchedule(schedule, req.user.id);
    
    res.json({
      scheduleId,
      summary: {
        totalOrders: schedule.orders.length,
        avgTurnaround: calculateAvgTurnaround(schedule.orders),
        onTimeCount: countOnTime(schedule.orders),
        utilizationAvg: calculateAvgUtilization(schedule.resources)
      },
      schedule
    });
    
  } catch (error) {
    console.error('Schedule generation error:', error);
    res.status(500).json({ error: error.message });
  }
});
```

#### Step 4.2: Frontend Page Development
**Duration:** 4 days

**Pages needed:**

1. **Login Page**
   - Username/password fields
   - Role selection (Admin, Planner, Customer Service, Operator)
   - Session management

2. **Dashboard Page**
   - Schedule summary metrics
   - Alert counts
   - Quick actions (Generate Schedule, Run Simulation, View Reports)
   - Recent schedules list

3. **Data Upload Page**
   - File upload forms (drag-and-drop or button)
   - Upload Open Sales Order
   - Upload Hot List (optional)
   - Upload QN Report (optional, future)
   - File validation status
   - Error display

4. **Configuration Page**
   - Work schedule settings:
     - Days per week (4, 5, 6)
     - Shift length (10, 12 hours)
     - Shift start times
     - Number of shifts (1, 2)
   - Holiday/shutdown date picker
   - Start date selector
   - Scenario name input
   - Save configuration button

5. **Schedule View Page**
   - Table view of scheduled orders
   - Columns: WO#, Part, Customer, BLAST Date, Completion Date, Turnaround, On-Time Status
   - Filters: by customer, by rubber type, by on-time status
   - Sort by any column
   - Export to Excel button

6. **Schedule Comparison Page**
   - Select two schedules to compare
   - Side-by-side table view
   - Highlight differences
   - Summary metrics comparison

7. **Reports Page**
   - Dropdown to select report type
   - Display report in table
   - Export to Excel button
   - Print-friendly view for BLAST and Core schedules

8. **Simulation Page**
   - (Developed in Phase 5)

**Component Examples:**

```jsx
// Dashboard Summary Component
function DashboardSummary({ schedule }) {
  return (
    <div className="summary-cards">
      <Card>
        <h3>Total Orders</h3>
        <p className="metric">{schedule.orders.length}</p>
      </Card>
      <Card>
        <h3>Avg Turnaround</h3>
        <p className="metric">{schedule.avgTurnaround.toFixed(1)} days</p>
      </Card>
      <Card>
        <h3>On-Time Orders</h3>
        <p className="metric">{schedule.onTimeCount} / {schedule.orders.length}</p>
      </Card>
      <Card>
        <h3>Avg Utilization</h3>
        <p className="metric">{(schedule.avgUtilization * 100).toFixed(1)}%</p>
      </Card>
    </div>
  );
}

// Work Schedule Configuration Component
function WorkScheduleConfig({ config, onChange }) {
  return (
    <div className="config-form">
      <label>
        Days per Week:
        <select value={config.daysPerWeek} onChange={e => onChange('daysPerWeek', e.target.value)}>
          <option value="4">4 days</option>
          <option value="5">5 days</option>
          <option value="6">6 days</option>
        </select>
      </label>
      
      <label>
        Shift Length:
        <select value={config.shiftLength} onChange={e => onChange('shiftLength', e.target.value)}>
          <option value="10">10 hours</option>
          <option value="12">12 hours</option>
        </select>
      </label>
      
      <label>
        Number of Shifts:
        <select value={config.numShifts} onChange={e => onChange('numShifts', e.target.value)}>
          <option value="1">1 shift</option>
          <option value="2">2 shifts</option>
        </select>
      </label>
      
      <label>
        Shift 1 Start Time:
        <input type="time" value={config.shift1Start} onChange={e => onChange('shift1Start', e.target.value)} />
      </label>
      
      {config.numShifts === '2' && (
        <label>
          Shift 2 Start Time:
          <input type="time" value={config.shift2Start} onChange={e => onChange('shift2Start', e.target.value)} />
        </label>
      )}
      
      <label>
        Start Date:
        <input type="date" value={config.startDate} onChange={e => onChange('startDate', e.target.value)} />
      </label>
      
      <button onClick={handleSave}>Save Configuration</button>
    </div>
  );
}
```

#### Step 4.3: User Authentication & Roles
**Duration:** 2 days

**Roles & Permissions Implementation:**

```javascript
const roles = {
  admin: {
    canUploadFiles: true,
    canGenerateSchedule: true,
    canRunSimulation: true,
    canExportReports: true,
    canManageUsers: true,
    canUpdateReference: true
  },
  planner: {
    canUploadFiles: true,
    canGenerateSchedule: true,
    canRunSimulation: true,
    canExportReports: true,
    canManageUsers: false,
    canUpdateReference: false
  },
  customerService: {
    canUploadFiles: true,  // Only hot list
    canGenerateSchedule: false,
    canRunSimulation: false,
    canExportReports: true,  // Only promise risk report
    canManageUsers: false,
    canUpdateReference: false
  },
  operator: {
    canUploadFiles: false,
    canGenerateSchedule: false,
    canRunSimulation: false,
    canExportReports: false,  // Can only view/print BLAST and Core schedules
    canManageUsers: false,
    canUpdateReference: false
  }
};

// Middleware to check permissions
function requirePermission(permission) {
  return (req, res, next) => {
    const userRole = req.user.role;
    if (roles[userRole][permission]) {
      next();
    } else {
      res.status(403).json({ error: 'Permission denied' });
    }
  };
}

// Protected route example
app.post('/api/schedule/generate', 
  requireAuth, 
  requirePermission('canGenerateSchedule'), 
  async (req, res) => {
    // ... schedule generation logic
  }
);
```

### 5.4 Phase 4 Testing

**Test Cases:**
1. All pages load without errors
2. File upload works for all file types
3. Configuration settings save and persist
4. Schedule table displays all orders correctly
5. Filters and sorting work in schedule view
6. Role-based access controls work (customer service can't generate schedule)
7. API endpoints return correct data
8. Error messages display clearly

**Deliverable:**
- Functional web application
- All core pages working
- User authentication and authorization
- File uploads and data validation
- Schedule display and export

---

## 6. Phase 5: Visual Simulation (Weeks 11-13)

### 6.1 Objectives
- Build animated simulation of production floor
- Show parts moving through operations
- Display machine status with color coding
- Control playback speed and navigation

### 6.2 Technology Stack

**Animation Library Options:**
1. **D3.js** - Flexible, powerful, good for custom layouts
2. **Three.js** - 3D graphics if desired
3. **React Spring** - Animation library for React
4. **Canvas API** - Direct 2D drawing for performance

**Recommended:** D3.js for flexibility or Canvas API for performance

### 6.3 Detailed Steps

#### Step 5.1: Floor Layout Design
**Duration:** 2 days

**Task 5.1.1: Parse Floor Map**
- Extract coordinates from PDF floor map
- Identify operation locations
- Define paths between operations

**Task 5.1.2: Create SVG Layout**
- Design visual blocks for each operation
- Size blocks proportional to capacity
- Draw connection lines between operations
- Add labels

**Code Example (SVG layout):**
```jsx
function FloorMap({ operations }) {
  // Define positions based on floor map
  const positions = {
    'SUPERMKT': { x: 100, y: 100 },
    'BLAST': { x: 200, y: 100 },
    'TUBE PREP': { x: 300, y: 80 },
    'CORE OVEN': { x: 300, y: 120 },
    'ASSEMBLY': { x: 400, y: 100 },
    'INJECTION': { x: 500, y: 100 },
    // ... etc
  };
  
  return (
    <svg width="1200" height="600">
      {/* Draw operations */}
      {Object.entries(positions).map(([opName, pos]) => (
        <g key={opName}>
          <rect 
            x={pos.x} 
            y={pos.y} 
            width={80} 
            height={60}
            fill={getOperationColor(opName)}
            stroke="black"
          />
          <text x={pos.x + 40} y={pos.y + 35} textAnchor="middle">
            {opName}
          </text>
        </g>
      ))}
      
      {/* Draw connection lines */}
      <line x1={180} y1={130} x2={200} y2={130} stroke="gray" />
      {/* ... more lines */}
    </svg>
  );
}
```

#### Step 5.2: Machine Status Display
**Duration:** 1 day

**Color Coding:**
- Gray: Idle
- Yellow: < 40% utilization
- Green: 40-85% utilization
- Orange: > 85% utilization

**Utilization Calculation:**
```javascript
function calculateUtilization(resource, currentTime, windowHours = 8) {
  const windowStart = currentTime - (windowHours * 3600 * 1000);
  
  const scheduledTasks = resource.schedule.filter(task => 
    task.start >= windowStart && task.start <= currentTime
  );
  
  const totalScheduledTime = scheduledTasks.reduce((sum, task) => 
    sum + (task.end - task.start), 0
  );
  
  const windowDuration = windowHours * 3600 * 1000;
  const utilization = totalScheduledTime / windowDuration;
  
  return utilization;
}

function getUtilizationColor(utilization) {
  if (utilization === 0) return '#808080'; // Gray
  if (utilization < 0.40) return '#FFD700'; // Yellow
  if (utilization <= 0.85) return '#00AA00'; // Green
  return '#FF8C00'; // Orange
}
```

#### Step 5.3: Stator Animation
**Duration:** 3 days

**Task 5.3.1: Stator Objects**
- Create visual representation of stator (circle or icon)
- Track position and state
- Animate movement between operations

**Task 5.3.2: Movement Logic**
- Calculate path from operation A to operation B
- Animate along path (smooth transition)
- Duration based on simulation speed

**Code Example (React + D3):**
```jsx
function StatorAnimation({ stator, positions, speed }) {
  const [position, setPosition] = useState(positions[stator.currentOp]);
  
  useEffect(() => {
    const targetPos = positions[stator.nextOp];
    
    // D3 transition
    d3.select(`#stator-${stator.id}`)
      .transition()
      .duration(1000 / speed) // Adjust by speed
      .attr('cx', targetPos.x)
      .attr('cy', targetPos.y)
      .on('end', () => {
        setPosition(targetPos);
        stator.currentOp = stator.nextOp;
      });
  }, [stator.nextOp]);
  
  return (
    <circle
      id={`stator-${stator.id}`}
      cx={position.x}
      cy={position.y}
      r={5}
      fill="blue"
    />
  );
}
```

#### Step 5.4: Queue Display
**Duration:** 2 days

**Visualization:**
- Show waiting stators as stacked circles/icons near operation
- Display queue count as number
- Highlight SWIP threshold

**Code Example:**
```jsx
function QueueDisplay({ operation, queue, positions }) {
  const opPos = positions[operation.name];
  
  return (
    <g>
      {/* Queue items */}
      {queue.slice(0, 5).map((stator, i) => (
        <circle
          key={stator.id}
          cx={opPos.x - 20}
          cy={opPos.y + (i * 8)}
          r={3}
          fill="lightblue"
        />
      ))}
      
      {/* Queue count */}
      <text x={opPos.x - 20} y={opPos.y - 10}>
        Queue: {queue.length}
      </text>
      
      {/* SWIP indicator */}
      {operation.swip > 0 && (
        <text x={opPos.x - 20} y={opPos.y - 20} fill="red">
          SWIP: {operation.swip}
        </text>
      )}
    </g>
  );
}
```

#### Step 5.5: Simulation Engine
**Duration:** 3 days

**Event-Driven Simulation:**
- Process events in chronological order
- Events: operation start, operation end, resource available, stator move
- Advance simulation time event by event
- Update UI at each frame (60 FPS)

**Code Example:**
```javascript
class SimulationEngine {
  constructor(schedule, speed = 1) {
    this.events = this.generateEvents(schedule);
    this.currentTime = schedule.startDate;
    this.speed = speed; // 1200x = 20 min/sec
    this.isRunning = false;
    this.stators = [];
    this.resources = [];
  }
  
  generateEvents(schedule) {
    const events = [];
    
    for (const order of schedule.orders) {
      for (const operation of order.routing) {
        events.push({
          time: operation.scheduled_start,
          type: 'operation_start',
          order: order,
          operation: operation
        });
        
        events.push({
          time: operation.scheduled_end,
          type: 'operation_end',
          order: order,
          operation: operation
        });
      }
    }
    
    // Sort events by time
    events.sort((a, b) => a.time - b.time);
    return events;
  }
  
  start() {
    this.isRunning = true;
    this.animationLoop();
  }
  
  pause() {
    this.isRunning = false;
  }
  
  animationLoop() {
    if (!this.isRunning) return;
    
    // Process events up to current time
    while (this.events.length > 0 && this.events[0].time <= this.currentTime) {
      const event = this.events.shift();
      this.processEvent(event);
    }
    
    // Update UI
    this.updateVisualization();
    
    // Advance time (20 real minutes = 1 second)
    const msPerSimSecond = (20 * 60 * 1000) / this.speed;
    this.currentTime = new Date(this.currentTime.getTime() + msPerSimSecond / 60);
    
    // Continue loop
    requestAnimationFrame(() => this.animationLoop());
  }
  
  processEvent(event) {
    switch (event.type) {
      case 'operation_start':
        this.startOperation(event.order, event.operation);
        break;
      case 'operation_end':
        this.endOperation(event.order, event.operation);
        break;
    }
  }
  
  startOperation(order, operation) {
    // Find stator
    const stator = this.stators.find(s => s.orderId === order.wo_number);
    
    // Move to operation
    stator.currentOp = operation.name;
    stator.state = 'processing';
    
    // Mark resource busy
    const resource = this.resources.find(r => r.name === operation.workcenter);
    resource.busy = true;
  }
  
  endOperation(order, operation) {
    // Find stator
    const stator = this.stators.find(s => s.orderId === order.wo_number);
    
    // Move to next operation or complete
    const nextOp = this.getNextOperation(order, operation);
    if (nextOp) {
      stator.nextOp = nextOp.name;
      stator.state = 'moving';
    } else {
      stator.state = 'complete';
    }
    
    // Free resource
    const resource = this.resources.find(r => r.name === operation.workcenter);
    resource.busy = false;
  }
}
```

#### Step 5.6: Simulation Controls
**Duration:** 1 day

**Controls UI:**
- Play / Pause button
- Speed slider (0.5x, 1x, 2x, 5x, 10x)
- Jump to date/time
- Highlight specific order (search by WO#)
- Time display (current simulated date/time)

**Code Example:**
```jsx
function SimulationControls({ simulation, onSpeedChange, onJumpToDate }) {
  return (
    <div className="simulation-controls">
      <button onClick={() => simulation.isRunning ? simulation.pause() : simulation.start()}>
        {simulation.isRunning ? 'Pause' : 'Play'}
      </button>
      
      <label>
        Speed:
        <input 
          type="range" 
          min="0.5" 
          max="10" 
          step="0.5"
          value={simulation.speed}
          onChange={e => onSpeedChange(parseFloat(e.target.value))}
        />
        <span>{simulation.speed}x</span>
      </label>
      
      <label>
        Jump to:
        <input 
          type="datetime-local" 
          onChange={e => onJumpToDate(new Date(e.target.value))}
        />
      </label>
      
      <div className="time-display">
        Current Time: {simulation.currentTime.toLocaleString()}
      </div>
    </div>
  );
}
```

### 6.4 Phase 5 Testing

**Test Cases:**
1. Floor layout matches physical floor map
2. Stators animate smoothly between operations
3. Machine colors update based on utilization
4. Queues display correct counts
5. Simulation speed controls work
6. Can jump to specific date/time
7. Simulation accurately reflects schedule
8. Performance: 60 FPS with 50+ stators

**Deliverable:**
- Animated simulation of production floor
- Interactive controls
- Real-time machine status display
- Queue and buffer visualization

---

## 7. Phase 6: Reporting & Export (Week 14)

### 7.1 Objectives
- Generate all required Excel reports
- Create printable BLAST and Core schedules
- Export functionality from UI
- Format reports professionally

### 7.2 Detailed Steps

#### Step 6.1: Excel Export Library Setup
**Duration:** 0.5 days

**Library:** `exceljs` (Node.js) or `openpyxl` (Python)

**Installation:**
```bash
npm install exceljs
# or
pip install openpyxl
```

#### Step 6.2: Master Schedule Report
**Duration:** 1 day

**Columns:**
- WO#
- Part Number
- Description
- Customer
- Quantity
- Core Number-Suffix
- Rubber Type
- BLAST Date/Time
- Completion Date/Time
- Turnaround (days)
- Promise Date
- On-Time Status

**Formatting:**
- Header row: bold, background color
- On-Time Status: conditional formatting (green = on time, red = late, yellow = at risk)
- Date columns: formatted as dates
- Freeze top row
- Auto-fit column widths

**Code Example:**
```javascript
const ExcelJS = require('exceljs');

async function generateMasterScheduleReport(schedule) {
  const workbook = new ExcelJS.Workbook();
  const worksheet = workbook.addWorksheet('Master Schedule');
  
  // Define columns
  worksheet.columns = [
    { header: 'WO#', key: 'wo_number', width: 12 },
    { header: 'Part Number', key: 'part_number', width: 20 },
    { header: 'Description', key: 'description', width: 40 },
    { header: 'Customer', key: 'customer', width: 30 },
    { header: 'Quantity', key: 'quantity', width: 10 },
    { header: 'Core', key: 'core', width: 10 },
    { header: 'Rubber Type', key: 'rubber_type', width: 12 },
    { header: 'BLAST Date', key: 'blast_date', width: 18 },
    { header: 'Completion Date', key: 'completion_date', width: 18 },
    { header: 'Turnaround (days)', key: 'turnaround', width: 16 },
    { header: 'Promise Date', key: 'promise_date', width: 18 },
    { header: 'On-Time', key: 'on_time', width: 12 }
  ];
  
  // Style header row
  worksheet.getRow(1).font = { bold: true };
  worksheet.getRow(1).fill = {
    type: 'pattern',
    pattern: 'solid',
    fgColor: { argb: 'FFD3D3D3' }
  };
  
  // Add data rows
  schedule.orders.forEach(order => {
    const blastOp = order.routing.find(op => op.name === 'BLAST');
    const finalOp = order.routing[order.routing.length - 1];
    
    const row = worksheet.addRow({
      wo_number: order.wo_number,
      part_number: order.part_number,
      description: order.description,
      customer: order.customer,
      quantity: order.quantity,
      core: order.assigned_core,
      rubber_type: order.rubber_type,
      blast_date: blastOp.scheduled_start,
      completion_date: finalOp.scheduled_end,
      turnaround: order.turnaround_time,
      promise_date: order.promise_date,
      on_time: getOnTimeStatus(finalOp.scheduled_end, order.promise_date)
    });
    
    // Conditional formatting for On-Time column
    const onTimeCell = row.getCell('on_time');
    if (onTimeCell.value === 'On Time') {
      onTimeCell.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FF00FF00' } };
    } else if (onTimeCell.value === 'Late') {
      onTimeCell.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FFFF0000' } };
    } else {
      onTimeCell.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FFFFFF00' } };
    }
  });
  
  // Save file
  await workbook.xlsx.writeFile('Master_Schedule.xlsx');
}
```

#### Step 6.3: BLAST Schedule (Printable)
**Duration:** 0.5 days

**Format:**
- Sequence number
- WO#
- Part Number
- BLAST Date/Time
- Core Required

**Layout:** Print-friendly, large text, clear spacing

#### Step 6.4: Core Oven Schedule (Printable)
**Duration:** 0.5 days

**Format:**
- Sequence number
- Core Number-Suffix
- Load Date/Time
- WO#
- Part Number

**Layout:** Print-friendly, sorted by load time

#### Step 6.5: Resource Utilization Report
**Duration:** 1 day

**Content:**
- For each operation and machine
- Total available hours
- Total utilized hours
- Utilization %
- Idle hours
- Setup hours
- Processing hours

**Charts:** Bar chart showing utilization by resource

#### Step 6.6: Alert Reports
**Duration:** 1 day

**Report 1: Promise Date Risk**
- Orders at risk or late
- Sorted by days late (descending)

**Report 2: Core Inventory Shortages**
- Core numbers with shortages
- Affected orders

**Report 3: Machine Utilization Alerts**
- Machines < 20% or > 85%
- Recommendations

#### Step 6.7: Projected Basic Finish Dates
**Duration:** 0.5 days

**For SAP Update:**
- WO#
- Current Basic Finish Date
- Projected Basic Finish Date
- Variance (days)

### 7.3 Phase 6 Testing

**Test Cases:**
1. All reports generate without errors
2. Data accuracy (spot-check 10 rows)
3. Formatting looks professional
4. Excel files open in Microsoft Excel and Google Sheets
5. Print-friendly layouts fit on standard paper
6. Conditional formatting works correctly

**Deliverable:**
- All Excel reports functional
- Export buttons in UI working
- Professional formatting
- Print-ready BLAST and Core schedules

---

## 8. Phase 7: Testing & Refinement (Weeks 15-16)

### 8.1 Objectives
- Comprehensive testing with real data
- User acceptance testing
- Bug fixes and performance optimization
- Documentation and training

### 8.2 Detailed Steps

#### Step 7.1: Unit Testing
**Duration:** 2 days

**Coverage:**
- Data parsers: test with sample files
- Scheduling algorithm: verify correctness
- Time calculations: check against manual calculations
- Resource allocation: no double-booking
- Core assignment: correct cores assigned

**Tools:** Jest (JavaScript), pytest (Python)

#### Step 7.2: Integration Testing
**Duration:** 2 days

**End-to-End Scenarios:**
1. Upload files → Generate schedule → Export report
2. Upload hot list → Re-generate schedule → View impact
3. Change work schedule → Re-generate → Compare scenarios
4. Run simulation → Verify matches schedule
5. Multi-user access → Verify role permissions

#### Step 7.3: Performance Testing
**Duration:** 1 day

**Benchmarks:**
- Schedule generation: < 2 min for 100 orders
- File upload: < 30 sec for 10 MB
- Report export: < 10 sec
- Simulation: 60 FPS
- UI responsiveness: < 200 ms for user actions

**Load Testing:**
- Multiple users (5+) simultaneously
- Large datasets (200+ orders)
- Concurrent schedule generations

#### Step 7.4: User Acceptance Testing (UAT)
**Duration:** 3 days

**Participants:**
- Production planners (2-3)
- Customer service rep (1)
- Operator (1)
- Admin/IT (1)

**Test Scenarios:**
1. **Planner:** Upload sales order, generate schedule, review for accuracy
2. **Planner:** Adjust work schedule (6-day vs 5-day), compare results
3. **Customer Service:** Upload hot list, view impact on promise dates
4. **Operator:** View BLAST schedule, print for shop floor
5. **Admin:** Add new user, assign role, verify permissions

**Feedback Collection:**
- Usability issues
- Missing features
- Confusing UI elements
- Performance concerns
- Bug reports

#### Step 7.5: Bug Fixes & Refinement
**Duration:** 3 days

**Priority Levels:**
- Critical: Blocks core functionality, fix immediately
- High: Major feature broken, fix in this phase
- Medium: Minor issue, fix if time permits
- Low: Enhancement, defer to future release

**Bug Tracking:**
- Use issue tracker (GitHub Issues, Jira, Trello)
- Categorize by priority and component
- Assign to developers
- Verify fixes with users

#### Step 7.6: Documentation
**Duration:** 2 days

**User Manual:**
- Getting started guide
- File upload instructions
- Configuration settings
- Generating schedules
- Running simulations
- Exporting reports
- Troubleshooting common issues

**Technical Documentation:**
- System architecture
- API documentation
- Database schema (if applicable)
- Deployment instructions
- Maintenance procedures

#### Step 7.7: Training
**Duration:** 1 day

**Sessions:**
1. **Planner Training (2 hours):**
   - Upload files and validate data
   - Configure work schedules
   - Generate and review schedules
   - Use hot list for priorities
   - Export reports
   - Run simulations

2. **Customer Service Training (1 hour):**
   - Upload hot list
   - View impact analysis
   - Export promise date risk report

3. **Operator Training (0.5 hours):**
   - View BLAST and Core schedules
   - Print schedules
   - Understand schedule updates

4. **Admin Training (1 hour):**
   - User management
   - System configuration
   - Update reference files
   - Monitor system health

### 8.3 Phase 7 Deliverables

- Fully tested application
- Bug fixes completed
- User manual and technical documentation
- Trained users
- Deployment-ready system

---

## 9. Deployment & Launch (Week 17)

### 9.1 Deployment Steps

#### Step 9.1: Production Environment Setup
**Duration:** 1 day

**Infrastructure:**
- Web server (AWS, Azure, on-premise)
- Database (if using)
- File storage for uploads and outputs
- Backup system

**Configuration:**
- Environment variables (API keys, database URLs)
- HTTPS/SSL certificate
- Domain name setup
- Firewall rules

#### Step 9.2: Data Migration
**Duration:** 0.5 days

**Tasks:**
- Transfer reference files (Core Mapping, Process VSM)
- Set up file monitoring
- Verify data integrity

#### Step 9.3: User Setup
**Duration:** 0.5 days

**Tasks:**
- Create user accounts for all team members
- Assign roles
- Send login credentials
- Verify access

#### Step 9.4: Go-Live
**Duration:** 1 day

**Activities:**
- Switch from test to production
- Monitor system closely
- Support users during first use
- Collect feedback

**Go-Live Checklist:**
- [ ] All users can log in
- [ ] Reference files loaded correctly
- [ ] First schedule generated successfully
- [ ] Reports export correctly
- [ ] Simulation runs smoothly
- [ ] No critical errors

### 9.2 Post-Launch Support

**First Week:**
- Daily check-ins with users
- Monitor system performance
- Quick bug fixes for any issues
- Gather user feedback

**First Month:**
- Weekly check-ins
- Performance optimization
- Feature refinement based on feedback
- Update documentation as needed

---

## 10. Success Metrics & KPIs

### 10.1 Technical Metrics

- **Schedule generation time:** < 2 minutes for 100 orders
- **System uptime:** > 99%
- **Report generation time:** < 10 seconds
- **Simulation frame rate:** ≥ 60 FPS
- **Data accuracy:** 100% (no scheduling errors)

### 10.2 Business Metrics

- **Turnaround time reduction:** ≥ 10% for reline stators
- **On-time delivery improvement:** ≥ 5%
- **Resource utilization:** 70-85% for injection machines
- **Planner time savings:** ≥ 50% reduction in manual scheduling
- **Core shortages identified:** 100% of shortages flagged proactively

### 10.3 User Satisfaction

- **User adoption:** 100% of planners using system within 2 weeks
- **Training effectiveness:** Users proficient after 2-hour training
- **User satisfaction:** ≥ 4/5 rating on usability survey
- **Support tickets:** < 5 critical issues per month after stabilization

---

## 11. Risk Management

### 11.1 Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Algorithm doesn't produce feasible schedules | Medium | High | Extensive testing with real data, fallback to simpler logic |
| Performance issues with large datasets | Medium | Medium | Optimize algorithms, consider parallel processing |
| Data parsing errors (Excel format changes) | Low | Medium | Robust validation, clear error messages, flexible parsing |
| Simulation too slow | Low | Medium | Use efficient rendering, consider Canvas over SVG |

### 11.2 Business Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Users resist change from manual process | Low | High | Involve users early, show clear benefits, provide training |
| Schedule accuracy issues reduce trust | Medium | High | Validate extensively, allow manual adjustments, build confidence gradually |
| Core Mapping file not kept up-to-date | Medium | Medium | Auto-reload feature, notifications to admin, periodic audits |
| Integration with SAP more complex than expected | Low | Medium | Start with manual export/import, plan API integration for Phase 2 |

### 11.3 Resource Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Development timeline slips | Medium | Medium | Phased approach allows flexibility, prioritize core features |
| Key developer unavailable | Low | High | Documentation, code reviews, knowledge sharing |
| Insufficient testing resources | Medium | Medium | Automate testing, involve users in UAT |

---

## 12. Maintenance & Future Enhancements

### 12.1 Ongoing Maintenance

**Weekly:**
- Monitor system performance
- Review error logs
- Back up schedules and data

**Monthly:**
- Update Core Mapping file if needed
- Review utilization metrics
- Collect user feedback

**Quarterly:**
- Performance optimization
- Security updates
- Feature enhancements

### 12.2 Phase 2 (Months 4-6)

- SAP integration (auto data pull)
- Quality Notification integration
- Real-time shop floor data feed
- Mobile app for operators
- Advanced analytics dashboard

### 12.3 Phase 3 (Months 7-12)

- Predictive maintenance scheduling
- Material resource planning
- Machine learning for time estimation
- Cost optimization
- Customer portal

---

## 13. Conclusion

This implementation plan provides a structured, phased approach to building the Stator Production Scheduling Application. By breaking the project into manageable phases, we can:

1. Deliver working features incrementally
2. Test thoroughly at each stage
3. Gather user feedback early and often
4. Adjust plans based on learnings
5. Minimize risk of large-scale failures

**Estimated Total Timeline:** 12-16 weeks from start to deployment

**Key Success Factors:**
- Strong data foundation (Phase 1)
- Accurate scheduling algorithm (Phases 2-3)
- User-friendly interface (Phase 4)
- Engaging simulation (Phase 5)
- Comprehensive reporting (Phase 6)
- Thorough testing (Phase 7)

With careful execution of this plan and collaboration with users throughout, we will deliver a powerful tool that transforms the production scheduling process and drives significant business value.

---

**Next Steps:**
1. Review and approve this implementation plan
2. Assemble development team
3. Set up development environment
4. Begin Phase 1: Data Foundation

**Questions or Clarifications:**
Please review both the Requirements Document and this Implementation Plan. Let me know if you have any questions, need clarification on any section, or want to adjust priorities or timelines. Once approved, we can proceed with development!

---

**Document End**

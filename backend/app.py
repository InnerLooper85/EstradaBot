"""
EstradaBot - Flask Web Application
With authentication and production deployment support
"""

import os
import sys
from datetime import datetime
from functools import wraps

from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, flash, session
from flask_cors import CORS
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env'))

# Add backend to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_loader import DataLoader
from algorithms.des_scheduler import DESScheduler
from exporters.excel_exporter import (
    export_master_schedule,
    export_blast_schedule,
    export_core_schedule,
    export_pending_core_report
)
from exporters.impact_analysis_exporter import generate_impact_analysis
import gcs_storage


# ============== App Configuration ==============

def create_app():
    """Application factory for Flask app."""
    app = Flask(__name__)

    # Load configuration from environment
    app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['ENV'] = os.environ.get('FLASK_ENV', 'development')
    app.config['DEBUG'] = os.environ.get('FLASK_DEBUG', 'true').lower() == 'true'

    # Session configuration for security
    app.config['SESSION_COOKIE_SECURE'] = os.environ.get('BEHIND_PROXY', 'false').lower() == 'true'
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

    # File upload configuration
    base_dir = os.path.dirname(os.path.abspath(__file__))
    app.config['UPLOAD_FOLDER'] = os.path.join(base_dir, '..', 'Scheduler Bot Info')
    app.config['OUTPUT_FOLDER'] = os.path.join(base_dir, '..', 'outputs')
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
    app.config['ALLOWED_EXTENSIONS'] = {'xlsx', 'xls'}

    # Ensure directories exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

    # CORS for API access
    CORS(app)

    return app


app = create_app()

# ============== User Management ==============

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'warning'


class User(UserMixin):
    """Simple user class for authentication."""

    def __init__(self, username, password_hash, role='user'):
        self.id = username
        self.username = username
        self.password_hash = password_hash
        self.role = role

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


def load_users():
    """Load users from environment variables."""
    users = {}

    # Load admin user
    admin_username = os.environ.get('ADMIN_USERNAME', 'admin')
    admin_password = os.environ.get('ADMIN_PASSWORD', 'admin')  # Default for development only
    users[admin_username] = User(
        admin_username,
        generate_password_hash(admin_password),
        role='admin'
    )

    # Load additional users from USERS env var
    # Format: username1:password1:role1,username2:password2:role2
    # Role is optional, defaults to 'user'. Valid roles: planner, mfgeng, customerservice, guest
    users_env = os.environ.get('USERS', '')
    if users_env:
        for user_pair in users_env.split(','):
            parts = user_pair.strip().split(':')
            if len(parts) >= 2:
                username = parts[0]
                password = parts[1]
                role = parts[2] if len(parts) > 2 else 'user'
                users[username] = User(
                    username,
                    generate_password_hash(password),
                    role=role
                )

    return users


# Load users on startup
USERS = load_users()


@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login."""
    return USERS.get(user_id)


# ============== Global State ==============

current_schedule = {
    'orders': [],
    'baseline_orders': [],
    'generated_at': None,
    'reports': {},
    'stats': {}
}


def load_persisted_schedule():
    """Load schedule state from GCS on startup."""
    global current_schedule
    try:
        state = gcs_storage.load_schedule_state()
        if state:
            # Restore the serialized state (orders stay as dicts for JSON API)
            current_schedule['stats'] = state.get('stats', {})
            current_schedule['reports'] = state.get('reports', {})
            current_schedule['generated_at'] = datetime.fromisoformat(state['generated_at']) if state.get('generated_at') else None
            current_schedule['published_by'] = state.get('published_by', '')
            # Store serialized orders for the API
            current_schedule['serialized_orders'] = state.get('orders', [])
            print(f"[Startup] Loaded persisted schedule with {len(current_schedule.get('serialized_orders', []))} orders")
    except Exception as e:
        print(f"[Startup] Failed to load persisted schedule: {e}")


# Load persisted schedule on module import
load_persisted_schedule()


# ============== Helper Functions ==============

def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def get_uploaded_files():
    """Get list of uploaded files from GCS bucket."""
    try:
        return gcs_storage.get_uploaded_files_info()
    except Exception as e:
        print(f"[WARN] Failed to get files from GCS: {e}")
        # Return empty structure on error
        return {
            'sales_order': None,
            'shop_dispatch': None,
            'hot_list': None,
            'core_mapping': None,
            'process_map': None
        }


def get_available_reports():
    """Get list of generated report files from GCS."""
    try:
        files = gcs_storage.list_files(gcs_storage.OUTPUTS_FOLDER)
    except Exception as e:
        print(f"[WARN] Failed to list reports from GCS: {e}")
        return []

    reports = []
    for file_info in files:
        filename = file_info['name']
        if not filename.endswith('.xlsx') or filename.startswith('~$'):
            continue

        # Determine report type
        report_type = 'Unknown'
        if 'Master_Schedule' in filename:
            report_type = 'Master Schedule'
        elif 'BLAST_Schedule' in filename:
            report_type = 'BLAST Schedule'
        elif 'Core_Oven' in filename or 'Core_Schedule' in filename:
            report_type = 'Core Oven Schedule'
        elif 'Pending_Core' in filename:
            report_type = 'Pending Core Report'
        elif 'Impact_Analysis' in filename:
            report_type = 'Impact Analysis'

        reports.append({
            'filename': filename,
            'type': report_type,
            'modified': file_info['modified'],
            'size': file_info['size']
        })

    # Already sorted by modified (newest first) from GCS
    return reports[:50]  # Return most recent 50


# ============== Authentication Routes ==============

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page and handler."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)

        user = USERS.get(username)
        if user and user.check_password(password):
            login_user(user, remember=remember)
            flash(f'Welcome back, {username}!', 'success')

            # Redirect to requested page or dashboard
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(url_for('index'))

        flash('Invalid username or password.', 'danger')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    """Log out the current user."""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


# ============== Page Routes ==============

@app.route('/')
@login_required
def index():
    """Dashboard home page."""
    files = get_uploaded_files()
    reports = get_available_reports()

    can_generate = current_user.role in ('admin', 'planner')
    return render_template('index.html',
                           files=files,
                           reports=reports[:5],
                           schedule=current_schedule,
                           can_generate=can_generate)


@app.route('/upload')
@login_required
def upload_page():
    """File upload page."""
    files = get_uploaded_files()
    return render_template('upload.html', files=files)


@app.route('/schedule')
@login_required
def schedule_page():
    """Schedule viewer page."""
    can_generate = current_user.role in ('admin', 'planner')
    return render_template('schedule.html', schedule=current_schedule, can_generate=can_generate)


@app.route('/reports')
@login_required
def reports_page():
    """Reports page."""
    reports = get_available_reports()
    return render_template('reports.html', reports=reports)


@app.route('/simulation')
@login_required
def simulation_page():
    """Visual simulation page."""
    return render_template('simulation.html')


@app.route('/updates')
@login_required
def update_log_page():
    """Update log and feedback page."""
    return render_template('update_log.html')


# ============== API Routes ==============

@app.route('/api/upload', methods=['POST'])
@login_required
def upload_file():
    """Handle file upload to GCS."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    file_type = request.form.get('type', 'unknown')

    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Only .xlsx and .xls files allowed.'}), 400

    # Upload to GCS
    filename = secure_filename(file.filename)
    try:
        # Scrub sensitive columns from sales order files before uploading
        if file_type == 'sales_order' or 'open sales order' in filename.lower().replace('_', ' '):
            import tempfile
            import openpyxl

            # Save to temp file for processing
            fd, temp_path = tempfile.mkstemp(suffix='.xlsx')
            os.close(fd)
            file.save(temp_path)

            # Open and scrub sensitive columns
            wb = openpyxl.load_workbook(temp_path)
            scrubbed_columns = []
            sensitive_headers = ['unit price', 'net price', 'customer address', 'address']

            for ws in wb.worksheets:
                cols_to_delete = []
                for col_idx in range(1, ws.max_column + 1):
                    header = ws.cell(row=1, column=col_idx).value
                    if header and str(header).strip().lower() in sensitive_headers:
                        cols_to_delete.append(col_idx)
                        scrubbed_columns.append(str(header).strip())

                # Delete columns in reverse order to preserve indices
                for col_idx in sorted(cols_to_delete, reverse=True):
                    ws.delete_cols(col_idx)

            wb.save(temp_path)
            wb.close()

            if scrubbed_columns:
                print(f"[Scrub] Removed sensitive columns from {filename}: {scrubbed_columns}")

            # Upload scrubbed file to GCS
            gcs_storage.upload_file(temp_path, filename)
            os.unlink(temp_path)
        else:
            gcs_storage.upload_file_object(file, filename)

        flash(f'File "{filename}" uploaded successfully!', 'success')
        return jsonify({
            'success': True,
            'filename': filename,
            'type': file_type
        })
    except Exception as e:
        print(f"[ERROR] Failed to upload to GCS: {e}")
        return jsonify({'error': f'Failed to upload file: {str(e)}'}), 500


@app.route('/api/generate', methods=['POST'])
@login_required
def generate_schedule():
    """Generate schedule from uploaded files in GCS. Only admin/planner roles."""
    global current_schedule

    # Role check: only admin and planner can generate schedules
    if current_user.role not in ('admin', 'planner'):
        return jsonify({'error': 'Only Planner and Admin users can generate schedules.'}), 403

    try:
        # Download files from GCS to local temp directory
        import tempfile
        temp_dir = tempfile.mkdtemp(prefix='estradabot_')
        print(f"[Generate] Downloading files from GCS to {temp_dir}")

        local_paths = gcs_storage.download_files_for_processing(temp_dir)
        print(f"[Generate] Downloaded files: {local_paths}")

        # Load data from temp directory
        loader = DataLoader(data_dir=temp_dir)
        loader.load_all()

        if not loader.orders:
            return jsonify({'error': 'No orders loaded. Please upload a Sales Order file.'}), 400

        # Create scheduler
        scheduler = DESScheduler(
            orders=loader.orders,
            core_mapping=loader.core_mapping,
            core_inventory=loader.core_inventory
        )

        # Run baseline schedule (without hot list)
        baseline_orders = scheduler.schedule_orders()
        active_scheduler = scheduler  # Track which scheduler to get pending orders from

        # If hot list exists, run with hot list
        scheduled_orders = baseline_orders
        if loader.hot_list_entries:
            # Create new scheduler for hot list run
            scheduler_with_hot = DESScheduler(
                orders=loader.orders,
                core_mapping=loader.core_mapping,
                core_inventory=loader.core_inventory
            )
            scheduled_orders = scheduler_with_hot.schedule_orders(
                hot_list_entries=loader.hot_list_entries
            )
            active_scheduler = scheduler_with_hot

        # Generate timestamp for reports
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Export reports to temp directory, then upload to GCS
        reports = {}

        master_filename = f'Master_Schedule_{timestamp}.xlsx'
        master_path = os.path.join(temp_dir, master_filename)
        export_master_schedule(scheduled_orders, master_path)
        gcs_storage.upload_file(master_path, master_filename, gcs_storage.OUTPUTS_FOLDER)
        reports['master'] = master_filename

        blast_filename = f'BLAST_Schedule_{timestamp}.xlsx'
        blast_path = os.path.join(temp_dir, blast_filename)
        export_blast_schedule(scheduled_orders, blast_path)
        gcs_storage.upload_file(blast_path, blast_filename, gcs_storage.OUTPUTS_FOLDER)
        reports['blast'] = blast_filename

        core_filename = f'Core_Oven_Schedule_{timestamp}.xlsx'
        core_path = os.path.join(temp_dir, core_filename)
        export_core_schedule(scheduled_orders, core_path)
        gcs_storage.upload_file(core_path, core_filename, gcs_storage.OUTPUTS_FOLDER)
        reports['core'] = core_filename

        # Pending core report uses orders that couldn't be scheduled (no core available)
        pending_filename = f'Pending_Core_{timestamp}.xlsx'
        pending_path = os.path.join(temp_dir, pending_filename)
        pending_orders = getattr(active_scheduler, 'pending_core_orders', [])
        export_pending_core_report(pending_orders, pending_path)
        gcs_storage.upload_file(pending_path, pending_filename, gcs_storage.OUTPUTS_FOLDER)
        reports['pending'] = pending_filename

        # Impact analysis if hot list was used
        if loader.hot_list_entries:
            hot_list_core_shortages = getattr(active_scheduler, 'hot_list_core_shortages', [])
            impact_path = generate_impact_analysis(
                scheduled_orders,
                baseline_orders,
                loader.hot_list_entries,
                hot_list_core_shortages,
                temp_dir
            )
            impact_filename = os.path.basename(impact_path)
            gcs_storage.upload_file(impact_path, impact_filename, gcs_storage.OUTPUTS_FOLDER)
            reports['impact'] = impact_filename

        # Clean up temp directory
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
        print(f"[Generate] Cleaned up temp directory {temp_dir}")

        # Calculate stats (ScheduledOrder is a dataclass, use attribute access)
        # At Risk = on_time but completion within 2 days of deadline
        from datetime import timedelta
        AT_RISK_BUFFER_DAYS = 2

        on_time_count = 0
        late_count = 0
        at_risk_count = 0

        for o in scheduled_orders:
            if not getattr(o, 'on_time', True):
                late_count += 1
            else:
                # Check if "at risk" - on time but close to deadline
                deadline = getattr(o, 'basic_finish_date', None) or getattr(o, 'promise_date', None)
                completion = getattr(o, 'completion_date', None)
                if deadline and completion:
                    days_buffer = (deadline - completion).days
                    if days_buffer <= AT_RISK_BUFFER_DAYS:
                        at_risk_count += 1
                    else:
                        on_time_count += 1
                else:
                    on_time_count += 1

        turnaround_times = [o.turnaround_days for o in scheduled_orders if o.turnaround_days]
        avg_turnaround = sum(turnaround_times) / len(turnaround_times) if turnaround_times else 0

        # Serialize orders for persistence and API
        serialized_orders = []
        for order in scheduled_orders:
            deadline = order.basic_finish_date or order.promise_date
            if not order.on_time:
                status = 'Late'
            elif deadline and order.completion_date:
                days_buffer = (deadline - order.completion_date).days
                status = 'At Risk' if days_buffer <= AT_RISK_BUFFER_DAYS else 'On Time'
            else:
                status = 'On Time'

            serialized_orders.append({
                'wo_number': order.wo_number or '',
                'serial_number': order.serial_number or '',
                'part_number': order.part_number or '',
                'description': order.description or '',
                'customer': order.customer or '',
                'assigned_core': order.assigned_core or '',
                'rubber_type': order.rubber_type or '',
                'priority': order.priority,
                'blast_date': order.blast_date.isoformat() if order.blast_date else None,
                'completion_date': order.completion_date.isoformat() if order.completion_date else None,
                'promise_date': order.promise_date.isoformat() if order.promise_date else None,
                'basic_finish_date': order.basic_finish_date.isoformat() if order.basic_finish_date else None,
                'turnaround_days': order.turnaround_days,
                'on_time': order.on_time,
                'on_time_status': status,
                'is_reline': order.is_reline
            })

        generated_at = datetime.now()

        # Update global state
        current_schedule = {
            'orders': scheduled_orders,
            'baseline_orders': baseline_orders,
            'generated_at': generated_at,
            'published_by': current_user.username,
            'reports': reports,
            'stats': {
                'total_orders': len(scheduled_orders),
                'on_time': on_time_count,
                'late': late_count,
                'at_risk': at_risk_count,
                'avg_turnaround': round(avg_turnaround, 1),
                'hot_list_count': len(loader.hot_list_entries) if loader.hot_list_entries else 0
            },
            'serialized_orders': serialized_orders
        }

        # Persist to GCS for other users / restarts
        gcs_storage.save_schedule_state({
            'orders': serialized_orders,
            'stats': current_schedule['stats'],
            'reports': reports,
            'generated_at': generated_at.isoformat(),
            'published_by': current_user.username
        })

        flash(f'Schedule generated successfully! {len(scheduled_orders)} orders scheduled.', 'success')
        return jsonify({
            'success': True,
            'stats': current_schedule['stats'],
            'reports': reports  # Already just filenames now
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/schedule')
@login_required
def get_schedule():
    """Get current schedule data as JSON."""
    # Check if we have in-memory orders (just generated) or serialized orders (loaded from GCS)
    if current_schedule.get('orders'):
        # We have in-memory ScheduledOrder objects - serialize them
        AT_RISK_BUFFER_DAYS = 2
        orders_data = []
        on_time_count = 0
        late_count = 0
        at_risk_count = 0

        for order in current_schedule['orders']:
            if not order.on_time:
                status = 'Late'
                late_count += 1
            else:
                deadline = order.basic_finish_date or order.promise_date
                if deadline and order.completion_date:
                    days_buffer = (deadline - order.completion_date).days
                    if days_buffer <= AT_RISK_BUFFER_DAYS:
                        status = 'At Risk'
                        at_risk_count += 1
                    else:
                        status = 'On Time'
                        on_time_count += 1
                else:
                    status = 'On Time'
                    on_time_count += 1

            order_dict = {
                'wo_number': order.wo_number or '',
                'serial_number': order.serial_number or '',
                'part_number': order.part_number or '',
                'description': order.description or '',
                'customer': order.customer or '',
                'core': order.assigned_core or '',
                'rubber_type': order.rubber_type or '',
                'priority': order.priority,
                'blast_date': order.blast_date.isoformat() if order.blast_date else '',
                'completion_date': order.completion_date.isoformat() if order.completion_date else '',
                'promise_date': order.promise_date.isoformat() if order.promise_date else '',
                'turnaround_days': order.turnaround_days or '',
                'on_time_status': status,
                'is_rework': order.is_reline
            }
            orders_data.append(order_dict)

        turnaround_times = [o.turnaround_days for o in current_schedule['orders'] if o.turnaround_days]
        avg_turnaround = sum(turnaround_times) / len(turnaround_times) if turnaround_times else 0

        fresh_stats = {
            'total_orders': len(orders_data),
            'on_time': on_time_count,
            'late': late_count,
            'at_risk': at_risk_count,
            'avg_turnaround': round(avg_turnaround, 1),
            'hot_list_count': current_schedule['stats'].get('hot_list_count', 0)
        }

        return jsonify({
            'orders': orders_data,
            'stats': fresh_stats,
            'generated_at': current_schedule['generated_at'].isoformat() if current_schedule['generated_at'] else None,
            'published_by': current_schedule.get('published_by', '')
        })

    elif current_schedule.get('serialized_orders'):
        # We have serialized orders loaded from GCS - use them directly
        orders_data = []
        for order in current_schedule['serialized_orders']:
            orders_data.append({
                'wo_number': order.get('wo_number', ''),
                'serial_number': order.get('serial_number', ''),
                'part_number': order.get('part_number', ''),
                'description': order.get('description', ''),
                'customer': order.get('customer', ''),
                'core': order.get('assigned_core', ''),
                'rubber_type': order.get('rubber_type', ''),
                'priority': order.get('priority', ''),
                'blast_date': order.get('blast_date', ''),
                'completion_date': order.get('completion_date', ''),
                'promise_date': order.get('promise_date', ''),
                'turnaround_days': order.get('turnaround_days', ''),
                'on_time_status': order.get('on_time_status', 'On Time'),
                'is_rework': order.get('is_reline', False)
            })

        return jsonify({
            'orders': orders_data,
            'stats': current_schedule.get('stats', {}),
            'generated_at': current_schedule['generated_at'].isoformat() if current_schedule.get('generated_at') else None,
            'published_by': current_schedule.get('published_by', '')
        })

    else:
        # No schedule data at all
        return jsonify({'orders': [], 'stats': {}})


@app.route('/api/download/<filename>')
@login_required
def download_report(filename):
    """Download a report file from GCS."""
    safe_filename = secure_filename(filename)

    # Download from GCS to temp file
    temp_path = gcs_storage.download_to_temp(safe_filename, gcs_storage.OUTPUTS_FOLDER)
    if temp_path:
        return send_file(temp_path, as_attachment=True, download_name=safe_filename)
    return jsonify({'error': 'File not found'}), 404


@app.route('/api/files')
@login_required
def get_files():
    """Get list of uploaded files."""
    files = get_uploaded_files()
    # Convert datetime to string for JSON
    for key, value in files.items():
        if value and 'modified' in value:
            value['modified'] = value['modified'].isoformat()
    return jsonify(files)


@app.route('/api/reports')
@login_required
def get_reports():
    """Get list of available reports."""
    reports = get_available_reports()
    # Convert datetime to string for JSON
    for r in reports:
        r['modified'] = r['modified'].isoformat()
    return jsonify(reports)


@app.route('/api/feedback', methods=['POST'])
@login_required
def submit_feedback():
    """Submit user feedback."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    message = data.get('message', '').strip()
    category = data.get('category', '').strip()

    if not message:
        return jsonify({'error': 'Message is required'}), 400
    if not category:
        return jsonify({'error': 'Category is required'}), 400

    feedback_entry = {
        'username': current_user.username,
        'category': category,
        'priority': data.get('priority', 'Medium'),
        'page': data.get('page', ''),
        'message': message,
        'submitted_at': datetime.now().isoformat()
    }

    try:
        gcs_storage.save_feedback(feedback_entry)
        return jsonify({'success': True})
    except Exception as e:
        print(f"[ERROR] Failed to save feedback: {e}")
        return jsonify({'error': 'Failed to save feedback'}), 500


@app.route('/api/feedback')
@login_required
def get_feedback():
    """Get all feedback (admin only)."""
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    try:
        feedback = gcs_storage.load_feedback()
        # Return newest first
        feedback.reverse()
        return jsonify({'feedback': feedback})
    except Exception as e:
        print(f"[ERROR] Failed to load feedback: {e}")
        return jsonify({'feedback': []})


@app.route('/api/simulation-data')
@login_required
def get_simulation_data():
    """Get simulation data for visual factory floor animation."""
    if not current_schedule['orders']:
        return jsonify({'error': 'No schedule generated. Please generate a schedule first.'}), 400

    # Station layout configuration (x, y positions for rendering)
    stations = [
        {'id': 'BLAST', 'name': 'BLAST', 'x': 50, 'y': 180, 'width': 80, 'height': 50},
        {'id': 'TUBE PREP', 'name': 'TUBE PREP', 'x': 180, 'y': 100, 'width': 100, 'height': 50, 'capacity': 18},
        {'id': 'CORE OVEN', 'name': 'CORE OVEN', 'x': 180, 'y': 260, 'width': 100, 'height': 50, 'capacity': 12},
        {'id': 'ASSEMBLY', 'name': 'ASSEMBLY', 'x': 340, 'y': 180, 'width': 80, 'height': 50},
        {'id': 'INJECTION', 'name': 'INJECTION', 'x': 470, 'y': 180, 'width': 100, 'height': 80, 'machines': ['D1', 'D2', 'D3', 'D4', 'D5']},
        {'id': 'CURE', 'name': 'CURE', 'x': 620, 'y': 180, 'width': 80, 'height': 50, 'capacity': 16},
        {'id': 'QUENCH', 'name': 'QUENCH', 'x': 620, 'y': 280, 'width': 80, 'height': 50, 'capacity': 16},
        {'id': 'DISASSEMBLY', 'name': 'DISASSEMBLY', 'x': 470, 'y': 330, 'width': 100, 'height': 50},
        {'id': 'BLD END CUTBACK', 'name': 'CUTBACK', 'x': 340, 'y': 330, 'width': 80, 'height': 50},
        {'id': 'INJ END CUTBACK', 'name': 'CUTBACK', 'x': 340, 'y': 330, 'width': 80, 'height': 50},
        {'id': 'CUT THREADS', 'name': 'CUT THREADS', 'x': 210, 'y': 330, 'width': 80, 'height': 50},
        {'id': 'INSPECT', 'name': 'INSPECT', 'x': 80, 'y': 330, 'width': 80, 'height': 50},
    ]

    # Get date range from scheduled orders
    all_starts = []
    all_ends = []
    for order in current_schedule['orders']:
        if order.blast_date:
            all_starts.append(order.blast_date)
        if order.completion_date:
            all_ends.append(order.completion_date)
        for op in order.operations:
            all_starts.append(op.start_time)
            all_ends.append(op.end_time)

    start_date = min(all_starts) if all_starts else datetime.now()
    end_date = max(all_ends) if all_ends else datetime.now()

    # Convert orders to simulation format
    parts = []
    orders_with_ops = 0
    for order in current_schedule['orders']:
        operations = []
        for op in order.operations:
            operations.append({
                'station': op.operation_name,
                'start': op.start_time.isoformat(),
                'end': op.end_time.isoformat(),
                'resource': op.resource_id
            })

        if operations:
            orders_with_ops += 1

        parts.append({
            'wo_number': order.wo_number or '',
            'part_number': order.part_number or '',
            'customer': order.customer or '',
            'priority': order.priority or 'Normal',
            'rubber_type': order.rubber_type or '',
            'assigned_core': order.assigned_core or '',
            'is_rework': order.is_reline,
            'operations': operations
        })

    print(f"[Simulation API] {len(parts)} parts, {orders_with_ops} with operations")

    return jsonify({
        'schedule_info': {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'total_orders': len(parts),
            'generated_at': current_schedule['generated_at'].isoformat() if current_schedule['generated_at'] else None
        },
        'stations': stations,
        'parts': parts
    })


# ============== Error Handlers ==============

@app.errorhandler(401)
def unauthorized(e):
    """Handle unauthorized access."""
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Unauthorized'}), 401
    return redirect(url_for('login'))


@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors."""
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Not found'}), 404
    return render_template('404.html'), 404


@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors."""
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Internal server error'}), 500
    return render_template('500.html'), 500


# ============== Main ==============

def run_development():
    """Run the development server."""
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))

    print("=" * 60)
    print("EstradaBot - Web Interface (Development)")
    print("=" * 60)
    print(f"Upload folder: {app.config['UPLOAD_FOLDER']}")
    print(f"Output folder: {app.config['OUTPUT_FOLDER']}")
    print(f"Starting server at http://{host}:{port}")
    print("=" * 60)
    print("WARNING: Using development server. For production, use:")
    print("  waitress-serve --port=5000 app:app")
    print("=" * 60)

    app.run(debug=True, host=host, port=port)


def run_production():
    """Run the production server with Waitress."""
    from waitress import serve

    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))

    print("=" * 60)
    print("EstradaBot - Web Interface (Production)")
    print("=" * 60)
    print(f"Upload folder: {app.config['UPLOAD_FOLDER']}")
    print(f"Output folder: {app.config['OUTPUT_FOLDER']}")
    print(f"Starting Waitress server at http://{host}:{port}")
    print("=" * 60)

    serve(app, host=host, port=port, threads=4)


if __name__ == '__main__':
    env = os.environ.get('FLASK_ENV', 'development')

    if env == 'production':
        run_production()
    else:
        run_development()

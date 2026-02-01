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
    # Format: username1:password1,username2:password2
    users_env = os.environ.get('USERS', '')
    if users_env:
        for user_pair in users_env.split(','):
            if ':' in user_pair:
                username, password = user_pair.strip().split(':', 1)
                users[username] = User(
                    username,
                    generate_password_hash(password),
                    role='user'
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


# ============== Helper Functions ==============

def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def get_uploaded_files():
    """Get list of uploaded files in the upload folder."""
    files = {
        'sales_order': None,
        'shop_dispatch': None,
        'pegging_report': None,
        'hot_list': None,
        'core_mapping': None
    }

    upload_folder = app.config['UPLOAD_FOLDER']
    if not os.path.exists(upload_folder):
        return files

    for filename in os.listdir(upload_folder):
        filepath = os.path.join(upload_folder, filename)
        if not os.path.isfile(filepath):
            continue

        fname_lower = filename.lower()
        mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
        file_info = {'name': filename, 'modified': mtime}

        if 'open sales order' in fname_lower:
            if files['sales_order'] is None or mtime > files['sales_order']['modified']:
                files['sales_order'] = file_info
        elif 'shop dispatch' in fname_lower:
            if files['shop_dispatch'] is None or mtime > files['shop_dispatch']['modified']:
                files['shop_dispatch'] = file_info
        elif 'pegging' in fname_lower:
            if files['pegging_report'] is None or mtime > files['pegging_report']['modified']:
                files['pegging_report'] = file_info
        elif 'hot list' in fname_lower:
            if files['hot_list'] is None or mtime > files['hot_list']['modified']:
                files['hot_list'] = file_info
        elif 'core mapping' in fname_lower:
            if files['core_mapping'] is None or mtime > files['core_mapping']['modified']:
                files['core_mapping'] = file_info

    return files


def get_available_reports():
    """Get list of generated report files."""
    reports = []
    output_folder = app.config['OUTPUT_FOLDER']

    if not os.path.exists(output_folder):
        return reports

    for filename in sorted(os.listdir(output_folder), reverse=True):
        if filename.endswith('.xlsx'):
            filepath = os.path.join(output_folder, filename)
            mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
            size = os.path.getsize(filepath)

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
                'modified': mtime,
                'size': size
            })

    return reports[:20]  # Return only most recent 20


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

    return render_template('index.html',
                           files=files,
                           reports=reports[:5],
                           schedule=current_schedule)


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
    return render_template('schedule.html', schedule=current_schedule)


@app.route('/reports')
@login_required
def reports_page():
    """Reports page."""
    reports = get_available_reports()
    return render_template('reports.html', reports=reports)


# ============== API Routes ==============

@app.route('/api/upload', methods=['POST'])
@login_required
def upload_file():
    """Handle file upload."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    file_type = request.form.get('type', 'unknown')

    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Only .xlsx and .xls files allowed.'}), 400

    # Save file
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    flash(f'File "{filename}" uploaded successfully!', 'success')
    return jsonify({
        'success': True,
        'filename': filename,
        'type': file_type
    })


@app.route('/api/generate', methods=['POST'])
@login_required
def generate_schedule():
    """Generate schedule from uploaded files."""
    global current_schedule

    try:
        # Load data
        loader = DataLoader(data_dir=app.config['UPLOAD_FOLDER'])
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

        # Generate timestamp for reports
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_folder = app.config['OUTPUT_FOLDER']

        # Export reports
        reports = {}

        master_path = os.path.join(output_folder, f'Master_Schedule_{timestamp}.xlsx')
        export_master_schedule(scheduled_orders, master_path)
        reports['master'] = master_path

        blast_path = os.path.join(output_folder, f'BLAST_Schedule_{timestamp}.xlsx')
        export_blast_schedule(scheduled_orders, blast_path)
        reports['blast'] = blast_path

        core_path = os.path.join(output_folder, f'Core_Oven_Schedule_{timestamp}.xlsx')
        export_core_schedule(scheduled_orders, core_path)
        reports['core'] = core_path

        pending_path = os.path.join(output_folder, f'Pending_Core_{timestamp}.xlsx')
        export_pending_core_report(scheduled_orders, pending_path)
        reports['pending'] = pending_path

        # Impact analysis if hot list was used
        if loader.hot_list_entries:
            impact_path = os.path.join(output_folder, f'Impact_Analysis_{timestamp}.xlsx')
            generate_impact_analysis(baseline_orders, scheduled_orders, loader.hot_list_entries, impact_path)
            reports['impact'] = impact_path

        # Calculate stats (ScheduledOrder is a dataclass, use attribute access)
        on_time_count = sum(1 for o in scheduled_orders if getattr(o, 'on_time', False))
        late_count = sum(1 for o in scheduled_orders if not getattr(o, 'on_time', True))
        at_risk_count = 0  # Not tracked separately in current model

        turnaround_times = [o.turnaround_days for o in scheduled_orders if o.turnaround_days]
        avg_turnaround = sum(turnaround_times) / len(turnaround_times) if turnaround_times else 0

        # Update global state
        current_schedule = {
            'orders': scheduled_orders,
            'baseline_orders': baseline_orders,
            'generated_at': datetime.now(),
            'reports': reports,
            'stats': {
                'total_orders': len(scheduled_orders),
                'on_time': on_time_count,
                'late': late_count,
                'at_risk': at_risk_count,
                'avg_turnaround': round(avg_turnaround, 1),
                'hot_list_count': len(loader.hot_list_entries) if loader.hot_list_entries else 0
            }
        }

        flash(f'Schedule generated successfully! {len(scheduled_orders)} orders scheduled.', 'success')
        return jsonify({
            'success': True,
            'stats': current_schedule['stats'],
            'reports': {k: os.path.basename(v) for k, v in reports.items()}
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/schedule')
@login_required
def get_schedule():
    """Get current schedule data as JSON."""
    if not current_schedule['orders']:
        return jsonify({'orders': [], 'stats': {}})

    # Convert ScheduledOrder dataclass objects to JSON-serializable format
    orders_data = []
    for order in current_schedule['orders']:
        order_dict = {
            'wo_number': order.wo_number or '',
            'part_number': order.part_number or '',
            'description': order.description or '',
            'customer': order.customer or '',
            'core': order.assigned_core or '',
            'rubber_type': order.rubber_type or '',
            'priority': getattr(order, 'priority', 'Normal'),
            'blast_date': order.blast_date.isoformat() if order.blast_date else '',
            'completion_date': order.completion_date.isoformat() if order.completion_date else '',
            'promise_date': order.promise_date.isoformat() if order.promise_date else '',
            'turnaround_days': order.turnaround_days or '',
            'on_time_status': 'On Time' if order.on_time else 'Late',
            'is_rework': order.is_reline  # Using is_reline as proxy for rework
        }
        orders_data.append(order_dict)

    return jsonify({
        'orders': orders_data,
        'stats': current_schedule['stats'],
        'generated_at': current_schedule['generated_at'].isoformat() if current_schedule['generated_at'] else None
    })


@app.route('/api/download/<filename>')
@login_required
def download_report(filename):
    """Download a report file."""
    filepath = os.path.join(app.config['OUTPUT_FOLDER'], secure_filename(filename))
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True)
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

# DD Scheduler Bot

A scheduling application with a Python backend and web frontend.

## Project Structure

```
DD Scheduler Bot/
├── backend/
│   ├── data/           # Data storage
│   ├── reference/      # Reference files
│   ├── models/         # Data models
│   ├── parsers/        # File parsing utilities
│   ├── algorithms/     # Scheduling algorithms
│   └── utils/          # Utility functions
├── frontend/
│   ├── src/
│   │   ├── components/ # Reusable UI components
│   │   ├── pages/      # Page components
│   │   └── services/   # API services
│   └── public/         # Static assets
├── outputs/            # Generated output files
├── tests/              # Test files
├── venv/               # Python virtual environment
└── requirements.txt    # Python dependencies
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

### Frontend

Coming soon.

## Usage

Coming soon.

## Dependencies

- pandas
- openpyxl
- python-dateutil
- watchdog
- flask
- flask-cors

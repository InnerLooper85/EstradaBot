Create a new input file parser in `backend/parsers/`.

Follow the established parser pattern from existing parsers (e.g., `dcp_report_parser.py`, `hot_list_parser.py`).

## Pattern to follow

1. **Module docstring** at the top explaining what the parser does, what file it expects, and the expected columns
2. **Imports**: `typing`, `pathlib`, `pandas` (imported inside the parse function)
3. **Main parse function**: `parse_<name>(file_path: str) -> <return_type>`
   - Accept a file path string
   - Convert to `Path`, check existence
   - Read with `pd.read_excel(file_path, engine='openpyxl')`
   - Normalize column names (strip whitespace)
   - Use `_find_column()` helper for flexible column matching
   - Print status messages with `[<Parser Name>]` prefix
   - Return a dict or list of parsed data
4. **Helper functions** as needed (prefixed with `_`)

## After creating the parser

- Add it to `backend/parsers/__init__.py` if the project uses one
- Tell the developer which files need to be updated to integrate the parser:
  - `backend/data_loader.py` — to call the parser during data loading
  - `backend/app.py` — to accept the new file type in uploads
  - `backend/templates/upload.html` — to show the new file type on the upload page

## Ask the developer

Before creating the parser, confirm:
1. What is the file/report name?
2. What columns does it contain?
3. What data should be extracted and in what format?

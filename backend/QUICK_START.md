# Quick Start: Google Sheets Integration

## Overview
The `/api/parse-spreadsheet` endpoint **directly connects to your Google Sheet** using the Google Sheets API and returns parsed student/batch data.

## How It Works

```
Your Google Sheet
       ↓
   [API Call]
       ↓
Google Sheets API (reads data)
       ↓
Parse & Validate Data
       ↓
Return JSON: {students, batches}
       ↓
Use CRUD endpoints to save to database
```

## Quick Setup (5 minutes)

### 1. Install Packages
```bash
pip install -r requirements.txt
```

### 2. Set Up Google Cloud Credentials
Follow [SETUP_GOOGLE_SHEETS.md](SETUP_GOOGLE_SHEETS.md) to:
- Create a Google Cloud project
- Enable Sheets API
- Create service account
- Download `credentials.json`
- Share your sheet with service account email

### 3. Place credentials.json
```
backend/
├── credentials.json    ← Place it here
├── app.py
└── ...
```

### 4. Test the Endpoint

**Get your Sheet ID from the URL:**
```
https://docs.google.com/spreadsheets/d/SHEET_ID_HERE/edit#gid=0
                                        ^^^^^^^^^^^^^^^^
                                        Copy this part
```

**Call the endpoint:**
```bash
curl -X POST http://localhost:5001/api/parse-spreadsheet \
  -H "Content-Type: application/json" \
  -d '{
    "spreadsheet_id": "YOUR_SHEET_ID"
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Parsed 5 students and 2 batches",
  "errors": null,
  "students": [
    {
      "name": "Aditya Rao",
      "email": "a.rao@gmail.com",
      "birthdate": "2010-07-13",
      "mother_name": "Sunita Rao",
      "mother_email": "s.rao@email.com",
      "father_name": "Ajay Rao",
      "father_email": "a.rao@gmail.com",
      "batch": "Wednesday 7:00 PM"
    }
  ],
  "batches": [
    {
      "day_of_week": "Wednesday",
      "start_time": "19:00:00",
      "end_time": "20:00:00",
      "is_active": true
    }
  ]
}
```

## API Reference

### POST /api/parse-spreadsheet

**Required:**
- `spreadsheet_id` (string): The ID from your Google Sheet URL

**Optional:**
- `range` (string, default: "Sheet1!A:H"): The range to fetch
  - Examples: "Sheet1!A:H", "Class Data!A:H"

**Success Response (200):**
```json
{
  "success": true,
  "message": "Parsed X students and Y batches",
  "errors": null,
  "students": [...],
  "batches": [...]
}
```

**Error Response (400):**
```json
{
  "success": false,
  "message": "Error description",
  "errors": ["Detailed error 1", "Detailed error 2"],
  "students": [],
  "batches": []
}
```

## Common Errors & Solutions

### "Credentials file not found: credentials.json"
**Solution:** Download credentials.json from Google Cloud and place it in the backend directory

### "Permission denied. Make sure the sheet is shared with the service account email"
**Solution:** 
1. Find the service account email in `credentials.json` (client_email field)
2. Open your Google Sheet
3. Click Share → paste the service account email → Give Editor access

### "Spreadsheet not found"
**Solution:** Check that you copied the correct spreadsheet ID from the URL

### "No data found in sheet"
**Solution:** Make sure your sheet has data and the range is correct (default is Sheet1!A:H)

## Complete Workflow Example

See `example_import.py` for a complete working example that:
1. Fetches data from Google Sheets
2. Creates batches
3. Creates students
4. Enrolls students in batches

Run it:
```bash
# First, edit example_import.py and set your GOOGLE_SHEET_ID
python example_import.py
```

## Environment Variables (Optional)

You can set these to avoid passing them in each request:

```bash
# Windows PowerShell
$env:GOOGLE_SHEETS_ID = "YOUR_SHEET_ID"
$env:GOOGLE_SHEETS_CREDENTIALS_PATH = "path/to/credentials.json"
$env:GOOGLE_SHEETS_RANGE = "Sheet1!A:H"
```

Then you can call the endpoint with just:
```bash
curl -X POST http://localhost:5001/api/parse-spreadsheet -H "Content-Type: application/json" -d '{}'
```

## Google Sheet Format

Your sheet must have this structure:

| Column | Header | Format | Required |
|--------|--------|--------|----------|
| A | Student Name | Text | Yes |
| B | Birthdate | MM-DD-YYYY or MM/DD/YYYY | Yes |
| C | Email | Email | Yes |
| D | Mother Name | Text | No* |
| E | Mother Email | Email | No* |
| F | Father Name | Text | No* |
| G | Father Email | Email | No* |
| H | Batch | "Day HH:MM AM/PM" | Yes |

*At least one parent name or email must be provided

## Batch Time Formats (All Case-Insensitive)

All of these are valid:
- `Monday 7:00 PM`
- `monday 7:00 pm`
- `Monday, 7:00 PM`
- `FRIDAY 2:30 AM`
- `wednesday 3:45 pm`

## Date Formats

Both are valid:
- `07-13-2010` (MM-DD-YYYY)
- `07/13/2010` (MM/DD/YYYY)

## What Happens Next

After parsing, use the existing CRUD endpoints:

```bash
# 1. Create batches
POST /api/batches (for each batch in response)

# 2. Create students  
POST /api/students (for each student in response)

# 3. Enroll students
POST /api/student-batches (link students to batches)
```

See `example_import.py` for complete implementation.

## Troubleshooting

### Testing without Google Sheets API
For development, you can use the included test functions:
```bash
python test_api.py
```

### Checking Sheet Structure
Make sure your Google Sheet:
1. Has headers in row 1
2. Has data starting from row 2
3. All required columns (A-H) have data
4. Is shared with service account email

### Debugging API Errors
The response includes detailed errors for each invalid row:
```json
{
  "success": false,
  "errors": [
    "Row 2: Student name is required",
    "Row 3: Invalid birthdate format '13-7-2010'. Use MM-DD-YYYY or MM/DD/YYYY",
    "Row 4: Batch parsing failed for 'MondayInvalid'"
  ]
}
```

This helps identify exactly what's wrong with your data.

## Next Steps

1. ✅ Install dependencies
2. ✅ Set up Google Cloud credentials
3. ✅ Share sheet with service account
4. ✅ Call /api/parse-spreadsheet with your sheet ID
5. ✅ Use CRUD endpoints to save data to database
6. ✅ Verify data in database

See SETUP_GOOGLE_SHEETS.md for detailed setup instructions.

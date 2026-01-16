# Quick Reference - Google Sheets Integration

## New Endpoint

### POST /api/parse-spreadsheet
Parse spreadsheet rows and get student/batch data as JSON

```bash
curl -X POST http://localhost:5001/api/parse-spreadsheet \
  -H "Content-Type: application/json" \
  -d '{
    "rows": [
      ["Student Name", "Birthdate", "Email", "Mother Name", "Mother Email", "Father Name", "Father Email", "Batch"],
      ["John Doe", "07-13-2010", "john@example.com", "Jane", "jane@ex.com", "", "", "Monday 7:00 PM"]
    ]
  }'
```

## New Test Functions

Added to `test_api.py`:
- `test_spreadsheet_parsing_and_integration()` - Full workflow test
- `test_spreadsheet_error_handling()` - Validation test

Run with: `python test_api.py`

## Updated Student Endpoint

### POST /api/students (UPDATED)
Now requires:
- ✅ `name` (required)
- ✅ `email` (required) ← NEW
- ✅ `birthdate` (required) ← NEW, format: YYYY-MM-DD
- ✅ At least one parent field ← NEW VALIDATION

```bash
curl -X POST http://localhost:5001/api/students \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "birthdate": "2010-07-13",
    "mother_name": "Jane Doe",
    "mother_email": "jane@example.com"
  }'
```

## Supported Data Formats

### Birthdate
- ✅ `07-13-2010` (MM-DD-YYYY)
- ✅ `07/13/2010` (MM/DD/YYYY)
- ❌ `2010-07-13` (not accepted as input)

### Batch Time (Case Insensitive)
- ✅ `Monday 7:00 PM`
- ✅ `monday 7:00 pm`
- ✅ `Monday, 7:00 PM`
- ✅ `FRIDAY, 2:30 AM`
- ✅ `wednesday 9:00 am`
- ❌ `Monday7:00PM` (no space/comma)
- ❌ `Monday 19:00` (24-hour format not accepted)

### Valid Days
Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday

## Batch Deduplication

Multiple students with same day/time = **One batch**

```
Input:
Row 2: Student A → Monday 7:00 PM
Row 3: Student B → Monday 7:00 PM
Row 4: Student C → Monday, 7:00 PM

Output: 1 batch (Monday, 7:00 PM)
```

## File Changes Summary

| File | Change |
|------|--------|
| `requirements.txt` | Added Google Sheets packages |
| `models.py` | Added `birthdate` field to Student |
| `app.py` | Updated student endpoint, added parse-spreadsheet endpoint |
| `test_api.py` | Added spreadsheet parsing tests |
| `utils/google_sheets.py` | NEW - Parser utility |
| `SETUP_GOOGLE_SHEETS.md` | NEW - Detailed setup guide |
| `IMPLEMENTATION_SUMMARY.md` | NEW - Complete summary |

## Installation & Setup

```bash
# 1. Install packages
pip install -r requirements.txt

# 2. Delete old database (model changed)
rm mridangam_students.db

# 3. Run tests
python test_api.py
```

## Common Errors & Solutions

| Error | Solution |
|-------|----------|
| `Invalid date format` | Use MM-DD-YYYY or MM/DD/YYYY |
| `Invalid batch format` | Use `Day HH:MM AM/PM` format |
| `At least one parent` | Add mother_name/email or father_name/email |
| `Email is required` | Add email field to student |
| `Birthdate is required` | Add birthdate in YYYY-MM-DD format |

## Example Workflow

```python
import requests

# 1. Parse spreadsheet
rows = [
    ["Student Name", "Birthdate", "Email", "Mother Name", "Mother Email", "Father Name", "Father Email", "Batch"],
    ["John Doe", "07-13-2010", "john@example.com", "Jane", "jane@ex.com", "", "", "Monday 7:00 PM"]
]

response = requests.post('http://localhost:5001/api/parse-spreadsheet', 
                        json={"rows": rows})
parsed = response.json()

# 2. Create batch
batch = parsed['batches'][0]
response = requests.post('http://localhost:5001/api/batches', json=batch)
batch_id = response.json()['batch_id']

# 3. Create student
student = parsed['students'][0]
response = requests.post('http://localhost:5001/api/students', json=student)
student_id = response.json()['student_id']

# 4. Enroll student
response = requests.post('http://localhost:5001/api/student-batches',
                        json={"student_id": student_id, "batch_id": batch_id})
```

## API Response Examples

### Parse Success
```json
{
  "success": true,
  "message": "Parsed 2 students and 1 batches",
  "errors": null,
  "students": [
    {
      "name": "John Doe",
      "email": "john@example.com",
      "birthdate": "2010-07-13",
      "mother_name": "Jane Doe",
      "mother_email": "jane@example.com",
      "father_name": null,
      "father_email": null,
      "batch": "Monday 7:00 PM"
    }
  ],
  "batches": [
    {
      "day_of_week": "Monday",
      "start_time": "19:00:00",
      "end_time": "20:00:00",
      "is_active": true
    }
  ]
}
```

### Parse Error
```json
{
  "success": false,
  "message": "Parsed 0 students and 0 batches",
  "errors": [
    "Row 2: Email is required",
    "Row 3: Invalid batch format 'InvalidFormat'"
  ],
  "students": [],
  "batches": []
}
```

## Key Features

✅ Parse multiple date/time formats
✅ Automatic batch deduplication  
✅ 1-hour auto class duration
✅ Comprehensive validation
✅ Detailed error messages
✅ Full test coverage
✅ Case-insensitive batch parsing
✅ Multiple comma/space format support

## Database Changes

⚠️ Student model now has `birthdate` field

**Existing data:** Delete `mridangam_students.db` and restart (will recreate with new schema)

**For production:** Use database migration tools

## Next: Google Sheets Live Integration

To connect directly to Google Sheets (future enhancement):

1. Set up Google Cloud project (see SETUP_GOOGLE_SHEETS.md)
2. Create endpoint to fetch rows from Google Sheets API
3. Call existing `/api/parse-spreadsheet` with fetched rows
4. Process normally

For now, manually pass spreadsheet rows as JSON.

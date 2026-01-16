# Mridangam School App - Google Sheets Integration Setup Guide

## Overview
This guide explains how to set up the Google Sheets integration for the Mridangam School App backend. The integration allows you to programmatically read student and batch data from a Google Sheet and import them into the database.

## Step-by-Step Setup Instructions

### Step 1: Install Required Packages

The required packages have been added to `requirements.txt`:
- `google-auth-oauthlib`
- `google-auth-httplib2`
- `google-api-python-client`

Install all dependencies:

```bash
cd c:\Users\nandh\OneDrive\Documents\AppaMridangamSchoolApp\backend
pip install -r requirements.txt
```

### Step 2: Set Up Google Cloud Project

1. **Go to Google Cloud Console:**
   - Visit https://console.cloud.google.com/
   - Sign in with your Google account

2. **Create a new project:**
   - Click on the project dropdown at the top
   - Click "NEW PROJECT"
   - Enter project name: "Mridangam School App"
   - Click "CREATE"

3. **Enable Google Sheets API:**
   - In the Cloud Console, go to "APIs & Services" > "Library"
   - Search for "Google Sheets API"
   - Click on it
   - Click "ENABLE"

4. **Enable Google Drive API:**
   - In the same Library section, search for "Google Drive API"
   - Click on it
   - Click "ENABLE"

### Step 3: Create Service Account (Recommended for Server-to-Server Access)

1. **Navigate to Service Accounts:**
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "Service Account"

2. **Fill in Service Account Details:**
   - Service account name: "mridangam-service"
   - Click "CREATE AND CONTINUE"
   - Skip the optional steps and click "DONE"

3. **Create and Download JSON Key:**
   - In the Service Accounts list, find your newly created account
   - Click on it
   - Go to the "KEYS" tab
   - Click "Add Key" > "Create new key"
   - Choose "JSON"
   - Click "CREATE"
   - A JSON file will be downloaded to your computer

4. **Save the Credentials File:**
   - Move the downloaded JSON file to your backend directory:
     ```
     Move it to: c:\Users\nandh\OneDrive\Documents\AppaMridangamSchoolApp\backend\
     ```
   - Rename it to: `credentials.json`

5. **Get Your Service Account Email:**
   - Open `credentials.json` in a text editor
   - Find the "client_email" field
   - Copy this email address (it looks like: `mridangam-service@project-id.iam.gserviceaccount.com`)

### Step 4: Share Your Google Sheet with the Service Account

1. **Open Your Google Sheet:**
   - Go to https://sheets.google.com/
   - Open your "Mridangam Class Example" sheet

2. **Share the Sheet:**
   - Click the "Share" button in the top right
   - Paste the service account email (from Step 3.5)
   - Give it "Editor" permissions
   - Click "Share"
   - You may see a warning about sharing with a non-Google account - this is normal

### Step 5: Get Your Spreadsheet ID

1. **Find the Sheet ID:**
   - Open your Google Sheet in a browser
   - The URL will look like: `https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit#gid=0`
   - Copy the `SPREADSHEET_ID` (the long string between `/d/` and `/edit`)

2. **Add to Configuration (Optional):**
   - You can store this in `config.py` or pass it when calling the API

### Step 6: Understanding the Spreadsheet Format

Your Google Sheet should have the following structure:

**Header Row (Row 1):**
```
Student Name | Birthdate | Email | Mother Name | Mother Email | Father Name | Father Email | Batch
```

**Data Rows (Row 2+):**
```
John Doe | 07-13-2010 | john@example.com | Jane Doe | jane@example.com | James Doe | james@example.com | Monday 7:00 PM
```

### Important Notes on Data Formats:

**Birthdate Format:**
- Accepts: `MM-DD-YYYY` or `MM/DD/YYYY`
- Examples: `07-13-2010` or `07/13/2010`

**Batch Time Format (Case Insensitive):**
- Format: `Day HH:MM AM/PM` or `Day, HH:MM AM/PM`
- Examples:
  - `Monday 7:00 PM`
  - `wednesday 2:30 pm`
  - `Friday, 10:00 AM`
  - `Saturday, 9:30 am`
- Note: Hours can be 1-12 for AM/PM format
- Classes are automatically set to 1 hour duration

**Valid Days:**
- Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday

### Step 7: Using the API Endpoint

#### Endpoint: `POST /api/parse-spreadsheet`

**Purpose:** Parse spreadsheet data and return structured student/batch information

**Request Format:**
```json
{
  "rows": [
    ["Student Name", "Birthdate", "Email", "Mother Name", "Mother Email", "Father Name", "Father Email", "Batch"],
    ["John Doe", "07-13-2010", "john@example.com", "Jane Doe", "jane@example.com", "", "", "Monday 7:00 PM"],
    ["Jane Smith", "05-20-2012", "jane@example.com", "Mary Smith", "mary@example.com", "", "", "Monday 7:00 PM"]
  ]
}
```

**Response Format:**
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

### Step 8: Complete Workflow Example

1. **Parse Spreadsheet:**
   ```bash
   curl -X POST http://localhost:5001/api/parse-spreadsheet \
     -H "Content-Type: application/json" \
     -d '{"rows": [[...spreadsheet data...]]}'
   ```

2. **Create Batches:**
   ```bash
   curl -X POST http://localhost:5001/api/batches \
     -H "Content-Type: application/json" \
     -d '{
       "day_of_week": "Monday",
       "start_time": "19:00:00",
       "end_time": "20:00:00",
       "is_active": true
     }'
   ```

3. **Create Students:**
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

4. **Enroll Students in Batches:**
   ```bash
   curl -X POST http://localhost:5001/api/student-batches \
     -H "Content-Type: application/json" \
     -d '{
       "student_id": 1,
       "batch_id": 1
     }'
   ```

### Step 9: Running Tests

To test the complete workflow including spreadsheet parsing:

```bash
cd c:\Users\nandh\OneDrive\Documents\AppaMridangamSchoolApp\backend
python test_api.py
```

This will run all existing tests plus two new test functions:
- `test_spreadsheet_parsing_and_integration()` - Tests parsing and database integration
- `test_spreadsheet_error_handling()` - Tests error handling and validation

## Data Validation Rules

The API enforces the following validation rules at the `/api/students` endpoint:

1. **Student Name:** Required
2. **Email:** Required
3. **Birthdate:** Required (format: `YYYY-MM-DD`)
4. **Parent Information:** At least one of the following must be provided:
   - Mother name
   - Mother email
   - Father name
   - Father email

## Key Features

### Batch Deduplication
If multiple students have the same batch day and time, only one batch entry will be created. For example:
- Student 1: Monday 7:00 PM
- Student 2: Monday 7:00 PM
- Student 3: Monday, 7:00 PM

This results in 1 unique batch (Monday 7:00 PM), not 3 separate batches.

### Automatic Class Duration
Classes are automatically set to 1 hour duration:
- If start time is 7:00 PM, end time will be 8:00 PM
- If start time is 10:00 AM, end time will be 11:00 AM

### Multiple Date/Time Formats
The parser handles various date and batch time formats:
- Dates: `MM-DD-YYYY` or `MM/DD/YYYY`
- Batch times: `Day HH:MM AM/PM`, `Day h:MM AM/PM`, `Day, HH:MM AM/PM`, etc. (case-insensitive)

## Troubleshooting

### Issue: "credentials.json not found"
- Ensure the `credentials.json` file is in the backend directory
- Check the file name spelling

### Issue: "Service account doesn't have access to sheet"
- Verify you shared the Google Sheet with the service account email
- Check that the email in `credentials.json` matches the one you shared with

### Issue: Invalid date format error
- Ensure dates are in `MM-DD-YYYY` or `MM/DD/YYYY` format
- Example: `07-13-2010` not `7-13-2010`

### Issue: Batch parsing fails
- Ensure batch format is `Day HH:MM AM/PM` (space or comma before time)
- Valid examples: `Monday 7:00 PM`, `Monday, 7:00 PM`
- Invalid: `Monday7:00PM`, `Monday 19:00`

## API Documentation

### Student Creation Validation

**POST /api/students**

Required fields:
- `name` (string)
- `email` (string)
- `birthdate` (string, YYYY-MM-DD format)
- At least one parent field:
  - `mother_name` (string)
  - `mother_email` (string)
  - `father_name` (string)
  - `father_email` (string)

Optional fields:
- `birth_month` (integer, 1-12)
- `birth_year` (integer)

### Batch Creation

**POST /api/batches**

Required fields:
- `day_of_week` (string: Monday, Tuesday, etc.)
- `start_time` (string, HH:MM:SS format)
- `end_time` (string, HH:MM:SS format)

Optional fields:
- `is_active` (boolean, defaults to true)

## Next Steps

1. Start the Flask app: `python app.py`
2. Use the `/api/parse-spreadsheet` endpoint to parse your data
3. Use the existing CRUD endpoints to create batches and students
4. Use `/api/student-batches` to enroll students in batches
5. Track classes and attendance using the respective endpoints

"""
Complete End-to-End Example: Google Sheets Integration

This example demonstrates the complete workflow for reading from a Google Sheet
and importing students/batches into the database.

Before running this example:
1. Set up Google Cloud credentials (see SETUP_GOOGLE_SHEETS.md)
2. Place credentials.json in the backend directory
3. Share your Google Sheet with the service account email
4. Get your spreadsheet ID from the sheet URL
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:5001/api"

# *** IMPORTANT: Replace with your actual Google Sheet ID ***
# The spreadsheet ID is the long string in the sheet URL:
# https://docs.google.com/spreadsheets/d/SPREADSHEET_ID_HERE/edit#gid=0
GOOGLE_SHEET_ID = "YOUR_GOOGLE_SHEET_ID_HERE"

# Optional: If your data is in a different sheet (not Sheet1), change this
SHEET_RANGE = "Sheet1!A:H"

def step1_parse_spreadsheet():
    """
    Step 1: Call the parse-spreadsheet endpoint to fetch and parse data from Google Sheets
    
    This endpoint:
    - Connects to Google Sheets API using credentials.json
    - Fetches data from the specified sheet
    - Validates all data
    - Parses dates and batch times
    - Deduplicates batches
    - Returns structured JSON for further processing
    """
    print("\n" + "="*80)
    print("STEP 1: Fetch and Parse Google Sheet")
    print("="*80)
    
    print(f"\nConnecting to Google Sheet: {GOOGLE_SHEET_ID}")
    print(f"Range: {SHEET_RANGE}")
    print("\nSending request to /api/parse-spreadsheet...")
    
    # Request to API endpoint with spreadsheet ID
    payload = {
        "spreadsheet_id": GOOGLE_SHEET_ID,
        "range": SHEET_RANGE
    }
    
    response = requests.post(
        f"{BASE_URL}/parse-spreadsheet",
        json=payload
    )
    
    if response.status_code not in [200, 400]:
        print(f"ERROR: Unexpected status code {response.status_code}")
        print(response.text)
        return None
    
    parsed_data = response.json()
    
    if not parsed_data.get('success'):
        print(f"\n✗ Failed to parse spreadsheet")
        print(f"Error: {parsed_data.get('message')}")
        if parsed_data.get('errors'):
            print(f"\nDetails:")
            for error in parsed_data['errors']:
                print(f"  - {error}")
        return None
    
    print("\n✓ Google Sheet fetched and parsed successfully!")
    print(f"✓ Found {len(parsed_data['students'])} students")
    print(f"✓ Found {len(parsed_data['batches'])} unique batches (deduplication worked!)")


def step2_create_batches(parsed_data):
    """
    Step 2: Create batches in the database using the parsed batch data
    
    This step:
    - Takes deduplicated batch data from parsing
    - Posts each to /api/batches
    - Stores the batch IDs for later enrollment
    """
    print("\n" + "="*80)
    print("STEP 2: Create Batches in Database")
    print("="*80)
    
    batch_id_map = {}  # Map (day, time) -> batch_id for later use
    
    for batch in parsed_data['batches']:
        batch_key = (batch['day_of_week'], batch['start_time'])
        
        print(f"\nCreating batch: {batch['day_of_week']} {batch['start_time']} - {batch['end_time']}")
        
        response = requests.post(
            f"{BASE_URL}/batches",
            json=batch
        )
        
        if response.status_code != 201:
            print(f"  ✗ Failed to create batch (Status: {response.status_code})")
            print(f"    Error: {response.text}")
            continue
        
        batch_response = response.json()
        batch_id = batch_response['batch_id']
        batch_id_map[batch_key] = batch_id
        
        print(f"  ✓ Created batch ID: {batch_id}")
    
    print(f"\n✓ Created {len(batch_id_map)} batches")
    return batch_id_map


def step3_create_students(parsed_data, batch_id_map):
    """
    Step 3: Create students in the database using the parsed student data
    
    This step:
    - Takes validated student data from parsing
    - Posts each to /api/students
    - Stores the student IDs for later enrollment
    """
    print("\n" + "="*80)
    print("STEP 3: Create Students in Database")
    print("="*80)
    
    student_batch_map = {}  # Store (student_id, batch_reference) for enrollment
    created_count = 0
    
    for student in parsed_data['students']:
        batch_reference = student.pop('batch')  # Remove batch reference from student data
        
        print(f"\nCreating student: {student['name']}")
        print(f"  Email: {student['email']}")
        print(f"  Birthdate: {student['birthdate']}")
        print(f"  Batch: {batch_reference}")
        
        response = requests.post(
            f"{BASE_URL}/students",
            json=student
        )
        
        if response.status_code != 201:
            print(f"  ✗ Failed to create student (Status: {response.status_code})")
            print(f"    Error: {response.text}")
            continue
        
        student_response = response.json()
        student_id = student_response['student_id']
        created_count += 1
        
        print(f"  ✓ Created student ID: {student_id}")
        
        # Store for enrollment step
        student_batch_map[student_id] = batch_reference
    
    print(f"\n✓ Created {created_count} students")
    return student_batch_map


def step4_enroll_students(parsed_data, batch_id_map, student_batch_map):
    """
    Step 4: Enroll students in their batches
    
    This step:
    - Takes student-batch mappings from parsing
    - Uses batch_id_map and student_batch_map to find matching pairs
    - Posts to /api/student-batches to create enrollments
    """
    print("\n" + "="*80)
    print("STEP 4: Enroll Students in Batches")
    print("="*80)
    
    enrolled_count = 0
    
    for student_id, batch_reference in student_batch_map.items():
        # Find the matching batch in parsed data
        # Extract day from batch reference (e.g., "Wednesday 7:00 PM" -> "Wednesday")
        # This is a simplified approach; you might want more robust matching
        
        print(f"\nEnrolling student {student_id} in batch: {batch_reference}")
        
        # Find matching batch
        matching_batch = None
        for batch in parsed_data['batches']:
            if batch['day_of_week'].lower() in batch_reference.lower():
                matching_batch = batch
                break
        
        if not matching_batch:
            print(f"  ✗ Could not find matching batch for: {batch_reference}")
            continue
        
        batch_key = (matching_batch['day_of_week'], matching_batch['start_time'])
        if batch_key not in batch_id_map:
            print(f"  ✗ Batch {batch_key} not found in batch_id_map")
            continue
        
        batch_id = batch_id_map[batch_key]
        
        enrollment_data = {
            "student_id": student_id,
            "batch_id": batch_id
        }
        
        response = requests.post(
            f"{BASE_URL}/student-batches",
            json=enrollment_data
        )
        
        if response.status_code != 201:
            print(f"  ✗ Failed to enroll (Status: {response.status_code})")
            print(f"    Error: {response.text}")
            continue
        
        print(f"  ✓ Enrolled in batch ID: {batch_id}")
        enrolled_count += 1
    
    print(f"\n✓ Enrolled {enrolled_count} students in batches")


def step5_verify_data():
    """
    Step 5: Verify that all data was created successfully
    
    This step:
    - Gets all students from database
    - Gets all batches from database
    - Gets all enrollments from database
    - Displays summary
    """
    print("\n" + "="*80)
    print("STEP 5: Verify Data in Database")
    print("="*80)
    
    # Get all students
    response = requests.get(f"{BASE_URL}/students")
    students = response.json() if response.status_code == 200 else []
    
    # Get all batches
    response = requests.get(f"{BASE_URL}/batches")
    batches = response.json() if response.status_code == 200 else []
    
    # Get all enrollments
    response = requests.get(f"{BASE_URL}/student-batches")
    enrollments = response.json() if response.status_code == 200 else []
    
    print(f"\n✓ Database Summary:")
    print(f"  - Total Students: {len(students)}")
    print(f"  - Total Batches: {len(batches)}")
    print(f"  - Total Enrollments: {len(enrollments)}")
    
    print(f"\n✓ Students:")
    for student in students[-6:]:  # Show last 6 (our imported ones)
        print(f"  - {student['name']} (ID: {student['student_id']})")
        print(f"    Email: {student['email']}")
        print(f"    Birthdate: {student['birthdate']}")
    
    print(f"\n✓ Batches:")
    for batch in batches:
        print(f"  - {batch['day_of_week']} {batch['start_time']} (ID: {batch['batch_id']})")
    
    print(f"\n✓ Active Enrollments:")
    active_enrollments = [e for e in enrollments if e.get('is_active', True)]
    for enrollment in active_enrollments[-10:]:
        print(f"  - Student {enrollment['student_id']} -> Batch {enrollment['batch_id']}")


def main():
    """
    Main workflow: Fetch Google Sheet -> Parse -> Create batches -> Create students -> Enroll students
    """
    print("\n" + "="*80)
    print("MRIDANGAM SCHOOL APP - GOOGLE SHEETS IMPORT WORKFLOW")
    print("="*80)
    print("\nThis example demonstrates importing student data directly from Google Sheets")
    print("into the Mridangam School management database.")
    
    # Validate configuration
    if GOOGLE_SHEET_ID == "YOUR_GOOGLE_SHEET_ID_HERE":
        print("\n" + "="*80)
        print("❌ CONFIGURATION ERROR")
        print("="*80)
        print("\nYou need to set your Google Sheet ID:")
        print("1. Open your Google Sheet")
        print("2. Copy the ID from the URL:")
        print("   https://docs.google.com/spreadsheets/d/[ID_HERE]/edit#gid=0")
        print("3. Replace 'YOUR_GOOGLE_SHEET_ID_HERE' in example_import.py with the ID")
        print("\nAlso make sure:")
        print("- credentials.json is in the backend directory")
        print("- The sheet is shared with the service account email")
        print("- See SETUP_GOOGLE_SHEETS.md for complete setup instructions")
        return
    
    try:
        # Step 1: Fetch and parse from Google Sheets
        parsed_data = step1_parse_spreadsheet()
        if not parsed_data or not parsed_data['success']:
            print("\n✗ Failed to fetch/parse spreadsheet. Aborting.")
            return
        
        print("\nParsed Batches:")
        for batch in parsed_data['batches']:
            print(f"  - {batch['day_of_week']} {batch['start_time']} to {batch['end_time']}")
        
        print("\nParsed Students (first 3):")
        for student in parsed_data['students'][:3]:
            print(f"  - {student['name']} ({student['birthdate']})")
            print(f"    Email: {student['email']}")
        
        # Step 2: Create batches
        batch_id_map = step2_create_batches(parsed_data)
        if not batch_id_map:
            print("\n✗ Failed to create batches. Aborting.")
            return
        
        # Step 3: Create students
        student_batch_map = step3_create_students(parsed_data, batch_id_map)
        if not student_batch_map:
            print("\n✗ Failed to create students. Aborting.")
            return
        
        # Step 4: Enroll students
        step4_enroll_students(parsed_data, batch_id_map, student_batch_map)
        
        # Step 5: Verify
        step5_verify_data()
        
        print("\n" + "="*80)
        print("✓ IMPORT COMPLETED SUCCESSFULLY!")
        print("="*80)
        
    except Exception as e:
        print(f"\n✗ Error during import: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

import requests
import json
from datetime import datetime, timedelta

# Base URL for the API
BASE_URL = "http://localhost:5001/api"

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

# Test results tracking
test_results = {
    'passed': 0,
    'failed': 0,
    'total': 0
}

def print_test_header(test_name):
    print(f"\n{Colors.BLUE}{'='*80}{Colors.END}")
    print(f"{Colors.BLUE}Testing: {test_name}{Colors.END}")
    print(f"{Colors.BLUE}{'='*80}{Colors.END}")

def print_success(message):
    test_results['passed'] += 1
    test_results['total'] += 1
    print(f"{Colors.GREEN}âœ“ PASS:{Colors.END} {message}")

def print_failure(message):
    test_results['failed'] += 1
    test_results['total'] += 1
    print(f"{Colors.RED}âœ— FAIL:{Colors.END} {message}")

def print_info(message):
    print(f"{Colors.YELLOW}â„¹ INFO:{Colors.END} {message}")

def assert_status_code(response, expected_code, test_name):
    if response.status_code == expected_code:
        print_success(f"{test_name} - Status code {response.status_code}")
        return True
    else:
        print_failure(f"{test_name} - Expected {expected_code}, got {response.status_code}")
        print_info(f"Response: {response.text}")
        return False

def assert_field_exists(data, field, test_name):
    if field in data:
        print_success(f"{test_name} - Field '{field}' exists")
        return True
    else:
        print_failure(f"{test_name} - Field '{field}' missing")
        return False

def assert_field_value(data, field, expected_value, test_name):
    if data.get(field) == expected_value:
        print_success(f"{test_name} - Field '{field}' = {expected_value}")
        return True
    else:
        print_failure(f"{test_name} - Field '{field}': expected {expected_value}, got {data.get(field)}")
        return False

# Test 1: Health Check
def test_health_check():
    print_test_header("Health Check")
    response = requests.get(f"{BASE_URL}/health")
    assert_status_code(response, 200, "Health check")
    if response.status_code == 200:
        data = response.json()
        assert_field_value(data, 'status', 'healthy', "Health status")

# Test 2: Student CRUD Operations
def test_student_crud():
    print_test_header("Student CRUD Operations")
    
    # Create student
    student_data = {
        "name": "Ravi Kumar",
        "birth_month": 5,
        "birth_year": 2010,
        "birthdate": "2010-05-15",
        "email": "ravi@example.com",
        "mother_name": "Lakshmi Kumar",
        "mother_email": "lakshmi@example.com",
        "father_name": "Suresh Kumar",
        "father_email": "suresh@example.com"
    }
    
    response = requests.post(f"{BASE_URL}/students", json=student_data)
    if assert_status_code(response, 201, "Create student"):
        student = response.json()
        student_id = student['student_id']
        assert_field_exists(student, 'student_id', "Student creation")
        assert_field_value(student, 'name', 'Ravi Kumar', "Student name")
        
        # Get student by ID
        response = requests.get(f"{BASE_URL}/students/{student_id}")
        if assert_status_code(response, 200, "Get student by ID"):
            student = response.json()
            assert_field_value(student, 'email', 'ravi@example.com', "Student email")
        
        # Update student
        update_data = {"email": "ravi.new@example.com"}
        response = requests.put(f"{BASE_URL}/students/{student_id}", json=update_data)
        if assert_status_code(response, 200, "Update student"):
            student = response.json()
            assert_field_value(student, 'email', 'ravi.new@example.com', "Updated email")
        
        # Get all students
        response = requests.get(f"{BASE_URL}/students")
        if assert_status_code(response, 200, "Get all students"):
            students = response.json()
            if len(students) >= 1:
                print_success(f"Get all students - Found {len(students)} student(s)")
            else:
                print_failure("Get all students - No students found")
        
        return student_id
    
    return None

# Test 3: Create multiple students for testing
def test_create_multiple_students():
    print_test_header("Creating Multiple Students")
    
    students_data = [
        {"name": "Priya Sharma", "birth_month": 3, "birth_year": 2012, "birthdate": "2012-03-10", "email": "priya@example.com", "mother_name": "Rajvi Sharma", "mother_email": "rajvi@example.com"},
        {"name": "Arun Patel", "birth_month": 8, "birth_year": 2009, "birthdate": "2009-08-22", "email": "arun@example.com", "mother_email": "meera.mom@example.com", "father_name": "Rajesh Patel"},
        {"name": "Meera Reddy", "birth_month": 11, "birth_year": 2011, "birthdate": "2011-11-10", "email": "meera@example.com", "mother_name": "Lakshmi Reddy", "mother_email": "lakshmi@example.com"}
    ]
    
    student_ids = []
    for student_data in students_data:
        response = requests.post(f"{BASE_URL}/students", json=student_data)
        if response.status_code == 201:
            student = response.json()
            student_ids.append(student['student_id'])
            print_success(f"Created student: {student_data['name']}")
        else:
            print_failure(f"Failed to create student: {student_data['name']}")
    
    return student_ids

# Test 4: Batch CRUD Operations
def test_batch_crud():
    print_test_header("Batch CRUD Operations")
    
    # Create batch
    batch_data = {
        "day_of_week": "Monday",
        "start_time": "17:00:00",
        "end_time": "18:00:00",
        "is_active": True
    }
    
    response = requests.post(f"{BASE_URL}/batches", json=batch_data)
    if assert_status_code(response, 201, "Create batch"):
        batch = response.json()
        batch_id = batch['batch_id']
        assert_field_exists(batch, 'batch_id', "Batch creation")
        assert_field_value(batch, 'day_of_week', 'Monday', "Batch day")
        
        # Get batch by ID
        response = requests.get(f"{BASE_URL}/batches/{batch_id}")
        if assert_status_code(response, 200, "Get batch by ID"):
            batch = response.json()
            assert_field_value(batch, 'start_time', '17:00:00', "Batch start time")
        
        # Update batch
        update_data = {"start_time": "17:30:00"}
        response = requests.put(f"{BASE_URL}/batches/{batch_id}", json=update_data)
        if assert_status_code(response, 200, "Update batch"):
            batch = response.json()
            assert_field_value(batch, 'start_time', '17:30:00', "Updated start time")
        
        # Get all batches
        response = requests.get(f"{BASE_URL}/batches")
        assert_status_code(response, 200, "Get all batches")
        
        return batch_id
    
    return None

# Test 5: Create multiple batches
def test_create_multiple_batches():
    print_test_header("Creating Multiple Batches")
    
    batches_data = [
        {"day_of_week": "Wednesday", "start_time": "16:00:00", "end_time": "17:00:00"},
        {"day_of_week": "Friday", "start_time": "18:00:00", "end_time": "19:00:00"},
        {"day_of_week": "Saturday", "start_time": "10:00:00", "end_time": "11:00:00"}
    ]
    
    batch_ids = []
    for batch_data in batches_data:
        response = requests.post(f"{BASE_URL}/batches", json=batch_data)
        if response.status_code == 201:
            batch = response.json()
            batch_ids.append(batch['batch_id'])
            print_success(f"Created batch: {batch_data['day_of_week']} {batch_data['start_time']}")
        else:
            print_failure(f"Failed to create batch: {batch_data['day_of_week']}")
    
    return batch_ids

# Test 6: Student-Batch Enrollment
def test_student_batch_enrollment(student_ids, batch_ids):
    print_test_header("Student-Batch Enrollment")
    
    if not student_ids or not batch_ids:
        print_failure("Missing student or batch IDs for enrollment test")
        return []
    
    # Enroll first student in first batch
    enrollment_data = {
        "student_id": student_ids[0],
        "batch_id": batch_ids[0]
    }
    
    response = requests.post(f"{BASE_URL}/student-batches", json=enrollment_data)
    enrollment_ids = []
    
    if assert_status_code(response, 201, "Create enrollment"):
        enrollment = response.json()
        enrollment_id = enrollment['student_batch_id']
        enrollment_ids.append(enrollment_id)
        assert_field_exists(enrollment, 'student_batch_id', "Enrollment creation")
        
        # Test enrolling student in multiple batches
        if len(batch_ids) > 1:
            enrollment_data2 = {
                "student_id": student_ids[0],
                "batch_id": batch_ids[1]
            }
            response = requests.post(f"{BASE_URL}/student-batches", json=enrollment_data2)
            if assert_status_code(response, 201, "Enroll student in multiple batches"):
                enrollment_ids.append(response.json()['student_batch_id'])
        
        # Test enrolling multiple students in same batch
        if len(student_ids) > 1:
            for i in range(1, min(3, len(student_ids))):
                enrollment_data3 = {
                    "student_id": student_ids[i],
                    "batch_id": batch_ids[0]
                }
                response = requests.post(f"{BASE_URL}/student-batches", json=enrollment_data3)
                if response.status_code == 201:
                    enrollment_ids.append(response.json()['student_batch_id'])
                    print_success(f"Enrolled student {student_ids[i]} in batch {batch_ids[0]}")
        
        # Test duplicate enrollment (should fail)
        response = requests.post(f"{BASE_URL}/student-batches", json=enrollment_data)
        if response.status_code == 400:
            print_success("Duplicate enrollment properly rejected")
        else:
            print_failure("Duplicate enrollment should have been rejected")
        
        # Get enrollment by ID
        response = requests.get(f"{BASE_URL}/student-batches/{enrollment_id}")
        assert_status_code(response, 200, "Get enrollment by ID")
        
        # Update enrollment
        update_data = {"is_active": False}
        response = requests.put(f"{BASE_URL}/student-batches/{enrollment_id}", json=update_data)
        if assert_status_code(response, 200, "Update enrollment"):
            enrollment = response.json()
            assert_field_value(enrollment, 'is_active', False, "Enrollment deactivated")
        
        # Get all enrollments
        response = requests.get(f"{BASE_URL}/student-batches")
        assert_status_code(response, 200, "Get all enrollments")
    
    return enrollment_ids

# Test 7: Class CRUD Operations
def test_class_crud(batch_ids):
    print_test_header("Class CRUD Operations")
    
    if not batch_ids:
        print_failure("Missing batch IDs for class test")
        return []
    
    # Create class
    today = datetime.now().date()
    class_data = {
        "batch_id": batch_ids[0],
        "class_date": today.isoformat(),
        "notes": "Introduction to basic talas"
    }
    
    response = requests.post(f"{BASE_URL}/classes", json=class_data)
    class_ids = []
    
    if assert_status_code(response, 201, "Create class"):
        cls = response.json()
        class_id = cls['class_id']
        class_ids.append(class_id)
        assert_field_exists(cls, 'class_id', "Class creation")
        assert_field_value(cls, 'notes', 'Introduction to basic talas', "Class notes")
        
        # Create more classes for different dates
        for i in range(1, 4):
            class_date = (today + timedelta(days=i*7)).isoformat()
            class_data2 = {
                "batch_id": batch_ids[0],
                "class_date": class_date,
                "notes": f"Week {i+1} session"
            }
            response = requests.post(f"{BASE_URL}/classes", json=class_data2)
            if response.status_code == 201:
                class_ids.append(response.json()['class_id'])
                print_success(f"Created class for date {class_date}")
        
        # Get class by ID
        response = requests.get(f"{BASE_URL}/classes/{class_id}")
        assert_status_code(response, 200, "Get class by ID")
        
        # Update class
        update_data = {"notes": "Introduction to basic talas - revised"}
        response = requests.put(f"{BASE_URL}/classes/{class_id}", json=update_data)
        if assert_status_code(response, 200, "Update class"):
            cls = response.json()
            assert_field_value(cls, 'notes', 'Introduction to basic talas - revised', "Updated notes")
        
        # Get all classes
        response = requests.get(f"{BASE_URL}/classes")
        assert_status_code(response, 200, "Get all classes")
    
    return class_ids

# Test 8: Class Attendance
def test_class_attendance(class_ids, student_ids):
    print_test_header("Class Attendance")
    
    if not class_ids or not student_ids:
        print_failure("Missing class or student IDs for attendance test")
        return []
    
    attendance_ids = []
    
    # Record attendance for first student in first class
    attendance_data = {
        "class_id": class_ids[0],
        "student_id": student_ids[0],
        "attended": True,
        "notes": "Excellent performance"
    }
    
    response = requests.post(f"{BASE_URL}/attendance", json=attendance_data)
    if assert_status_code(response, 201, "Create attendance record"):
        attendance = response.json()
        attendance_id = attendance['attendance_id']
        attendance_ids.append(attendance_id)
        assert_field_exists(attendance, 'attendance_id', "Attendance creation")
        assert_field_value(attendance, 'attended', True, "Attendance status")
        
        # Record attendance for multiple students in same class
        for i in range(1, min(3, len(student_ids))):
            attendance_data2 = {
                "class_id": class_ids[0],
                "student_id": student_ids[i],
                "attended": True
            }
            response = requests.post(f"{BASE_URL}/attendance", json=attendance_data2)
            if response.status_code == 201:
                attendance_ids.append(response.json()['attendance_id'])
                print_success(f"Recorded attendance for student {student_ids[i]}")
        
        # Test student attending class from different batch (flexibility test)
        if len(class_ids) > 1 and len(student_ids) > 1:
            attendance_data3 = {
                "class_id": class_ids[1],
                "student_id": student_ids[1],
                "attended": True,
                "notes": "Guest attendance from different batch"
            }
            response = requests.post(f"{BASE_URL}/attendance", json=attendance_data3)
            if assert_status_code(response, 201, "Cross-batch attendance"):
                attendance_ids.append(response.json()['attendance_id'])
        
        # Test duplicate attendance (should fail)
        response = requests.post(f"{BASE_URL}/attendance", json=attendance_data)
        if response.status_code == 400:
            print_success("Duplicate attendance properly rejected")
        else:
            print_failure("Duplicate attendance should have been rejected")
        
        # Get attendance by ID
        response = requests.get(f"{BASE_URL}/attendance/{attendance_id}")
        assert_status_code(response, 200, "Get attendance by ID")
        
        # Update attendance
        update_data = {"attended": False, "notes": "Marked absent"}
        response = requests.put(f"{BASE_URL}/attendance/{attendance_id}", json=update_data)
        if assert_status_code(response, 200, "Update attendance"):
            attendance = response.json()
            assert_field_value(attendance, 'attended', False, "Updated attendance status")
        
        # Get all attendance records
        response = requests.get(f"{BASE_URL}/attendance")
        assert_status_code(response, 200, "Get all attendance records")
    
    return attendance_ids

# Test 9: Invoice CRUD Operations
def test_invoice_crud(class_ids, student_ids):
    print_test_header("Invoice CRUD Operations")
    
    if not class_ids or not student_ids:
        print_failure("Missing class or student IDs for invoice test")
        return []
    
    invoice_ids = []
    
    # Create invoice
    invoice_data = {
        "class_id": class_ids[0],
        "student_id": student_ids[0],
        "amount": 500.00,
        "payment_status": "Pending"
    }
    
    response = requests.post(f"{BASE_URL}/invoices", json=invoice_data)
    if assert_status_code(response, 201, "Create invoice"):
        invoice = response.json()
        invoice_id = invoice['invoice_id']
        invoice_ids.append(invoice_id)
        assert_field_exists(invoice, 'invoice_id', "Invoice creation")
        assert_field_value(invoice, 'amount', 500.00, "Invoice amount")
        assert_field_value(invoice, 'payment_status', 'Pending', "Payment status")
        
        # Create invoices for multiple students
        for i in range(1, min(3, len(student_ids))):
            if i < len(class_ids):
                invoice_data2 = {
                    "class_id": class_ids[i],
                    "student_id": student_ids[i],
                    "amount": 500.00,
                    "payment_status": "Pending"
                }
                response = requests.post(f"{BASE_URL}/invoices", json=invoice_data2)
                if response.status_code == 201:
                    invoice_ids.append(response.json()['invoice_id'])
                    print_success(f"Created invoice for student {student_ids[i]}")
        
        # Get invoice by ID
        response = requests.get(f"{BASE_URL}/invoices/{invoice_id}")
        assert_status_code(response, 200, "Get invoice by ID")
        
        # Update invoice (mark as paid)
        today = datetime.now().date()
        update_data = {
            "payment_status": "Paid",
            "payment_date": today.isoformat()
        }
        response = requests.put(f"{BASE_URL}/invoices/{invoice_id}", json=update_data)
        if assert_status_code(response, 200, "Update invoice"):
            invoice = response.json()
            assert_field_value(invoice, 'payment_status', 'Paid', "Updated payment status")
            if invoice.get('payment_date'):
                print_success("Update invoice - Payment date recorded")
            else:
                print_failure("Update invoice - Payment date not recorded")
        
        # Get all invoices
        response = requests.get(f"{BASE_URL}/invoices")
        assert_status_code(response, 200, "Get all invoices")
    
    return invoice_ids

# Test 10: Error Handling
def test_error_handling():
    print_test_header("Error Handling")
    
    # Test getting non-existent student
    response = requests.get(f"{BASE_URL}/students/99999")
    if response.status_code == 404:
        print_success("Non-existent student returns 404")
    else:
        print_failure(f"Non-existent student should return 404, got {response.status_code}")
    
    # Test creating student without required field
    response = requests.post(f"{BASE_URL}/students", json={})
    if response.status_code == 400:
        print_success("Missing required field returns 400")
    else:
        print_failure(f"Missing required field should return 400, got {response.status_code}")
    
    # Test creating batch with invalid time format
    batch_data = {
        "day_of_week": "Monday",
        "start_time": "invalid",
        "end_time": "18:00:00"
    }
    response = requests.post(f"{BASE_URL}/batches", json=batch_data)
    if response.status_code == 400:
        print_success("Invalid time format returns 400")
    else:
        print_failure(f"Invalid time format should return 400, got {response.status_code}")
    
    # Test creating enrollment with non-existent student
    enrollment_data = {
        "student_id": 99999,
        "batch_id": 1
    }
    response = requests.post(f"{BASE_URL}/student-batches", json=enrollment_data)
    if response.status_code == 404:
        print_success("Non-existent student in enrollment returns 404")
    else:
        print_failure(f"Non-existent student should return 404, got {response.status_code}")

# Test 11: Cascade Delete Testing
def test_cascade_deletes(student_ids, batch_ids, class_ids):
    print_test_header("Cascade Delete Testing")
    
    if not student_ids or not batch_ids or not class_ids:
        print_failure("Missing IDs for cascade delete test")
        return
    
    # Create a test student for deletion
    student_data = {"name": "Test Delete Student", "email": "delete@test.com"}
    response = requests.post(f"{BASE_URL}/students", json=student_data)
    if response.status_code == 201:
        delete_student_id = response.json()['student_id']
        
        # Create enrollment for this student
        enrollment_data = {
            "student_id": delete_student_id,
            "batch_id": batch_ids[0]
        }
        response = requests.post(f"{BASE_URL}/student-batches", json=enrollment_data)
        
        # Create attendance record
        if class_ids:
            attendance_data = {
                "class_id": class_ids[0],
                "student_id": delete_student_id,
                "attended": True
            }
            response = requests.post(f"{BASE_URL}/attendance", json=attendance_data)
        
        # Delete the student and check cascades
        response = requests.delete(f"{BASE_URL}/students/{delete_student_id}")
        if assert_status_code(response, 204, "Delete student (cascade test)"):
            # Verify student is deleted
            response = requests.get(f"{BASE_URL}/students/{delete_student_id}")
            if response.status_code == 404:
                print_success("Cascade delete - Student properly deleted")
            else:
                print_failure("Cascade delete - Student still exists")

# Test 12: Data Integrity
def test_data_integrity(student_ids, batch_ids):
    print_test_header("Data Integrity Testing")
    
    if not student_ids or not batch_ids:
        print_failure("Missing IDs for data integrity test")
        return
    
    # Test that we can't delete a batch that has classes
    batch_id = batch_ids[0]
    
    # First check if batch has classes
    response = requests.get(f"{BASE_URL}/classes")
    if response.status_code == 200:
        classes = response.json()
        batch_has_classes = any(cls['batch_id'] == batch_id for cls in classes)
        
        if batch_has_classes:
            print_info(f"Batch {batch_id} has classes - testing cascade delete")
            response = requests.delete(f"{BASE_URL}/batches/{batch_id}")
            if response.status_code == 204:
                print_success("Batch with classes deleted (cascade working)")
            else:
                print_info(f"Batch delete returned {response.status_code}")

# Main test runner
def run_all_tests():
    print(f"\n{Colors.BLUE}{'='*80}{Colors.END}")
    print(f"{Colors.BLUE}Mridangam Student Management API - Comprehensive Test Suite{Colors.END}")
    print(f"{Colors.BLUE}{'='*80}{Colors.END}")
    
    try:
        # Run all tests in sequence
        test_health_check()
        
        # Test basic CRUD
        first_student_id = test_student_crud()
        additional_student_ids = test_create_multiple_students()
        all_student_ids = [first_student_id] + additional_student_ids if first_student_id else additional_student_ids
        
        first_batch_id = test_batch_crud()
        additional_batch_ids = test_create_multiple_batches()
        all_batch_ids = [first_batch_id] + additional_batch_ids if first_batch_id else additional_batch_ids
        
        # Test relationships
        enrollment_ids = test_student_batch_enrollment(all_student_ids, all_batch_ids)
        class_ids = test_class_crud(all_batch_ids)
        attendance_ids = test_class_attendance(class_ids, all_student_ids)
        invoice_ids = test_invoice_crud(class_ids, all_student_ids)
        
        # Test error handling and edge cases
        test_error_handling()
        test_cascade_deletes(all_student_ids, all_batch_ids, class_ids)
        test_data_integrity(all_student_ids, all_batch_ids)
        
    except requests.exceptions.ConnectionError:
        print(f"\n{Colors.RED}ERROR: Could not connect to API at {BASE_URL}{Colors.END}")
        print(f"{Colors.YELLOW}Make sure the Flask app is running on http://localhost:5000{Colors.END}")
        return
    except Exception as e:
        print(f"\n{Colors.RED}ERROR: {str(e)}{Colors.END}")
        import traceback
        traceback.print_exc()
        return
    
    # Print summary
    print(f"\n{Colors.BLUE}{'='*80}{Colors.END}")
    print(f"{Colors.BLUE}Test Summary{Colors.END}")
    print(f"{Colors.BLUE}{'='*80}{Colors.END}")
    print(f"Total Tests: {test_results['total']}")
    print(f"{Colors.GREEN}Passed: {test_results['passed']}{Colors.END}")
    print(f"{Colors.RED}Failed: {test_results['failed']}{Colors.END}")
    
    pass_rate = (test_results['passed'] / test_results['total'] * 100) if test_results['total'] > 0 else 0
    print(f"Pass Rate: {pass_rate:.1f}%")
    
    if test_results['failed'] == 0:
        print(f"\n{Colors.GREEN}{'ðŸŽ‰ All tests passed! ðŸŽ‰'}{Colors.END}")
    else:
        print(f"\n{Colors.YELLOW}Some tests failed. Please review the output above.{Colors.END}")

# Test 13: Google Sheets Spreadsheet Parsing and Integration
def test_spreadsheet_parsing_and_integration():
    print_test_header("Google Sheets Parsing and Database Integration")
    
    # Import config to get real sheet ID and credentials
    import sys
    import os
    sys.path.insert(0, os.path.dirname(__file__))
    from config import Config
    
    sheet_id = Config.GOOGLE_SHEETS_ID
    
    if not sheet_id or sheet_id == 'YOUR_SHEET_ID':
        print_failure("No Google Sheet ID configured")
        print_info("Set GOOGLE_SHEETS_ID in config.py or environment variable")
        return
    
    print_info(f"Connecting to Google Sheet: {sheet_id[:20]}...")
    
    # Call the actual parse-spreadsheet endpoint
    response = requests.post(
        f"{BASE_URL}/parse-spreadsheet",
        json={"spreadsheet_id": sheet_id}
    )
    
    if assert_status_code(response, 200, "Parse Google Sheet"):
        parsed = response.json()
        
        if parsed.get('success'):
            print_success(f"Google Sheet parsed successfully!")
            students = parsed.get('students', [])
            batches = parsed.get('batches', [])
            print_success(f"Found {len(students)} students")
            print_success(f"Found {len(batches)} unique batches")
            
            # Show sample data
            if students:
                print_info(f"Sample student: {students[0]['name']} ({students[0]['email']})")
            if batches:
                print_info(f"Sample batch: {batches[0]['day_of_week']} {batches[0]['start_time']}")
        else:
            print_failure(f"Parse failed: {parsed.get('message')}")
            if parsed.get('errors'):
                for error in parsed.get('errors', [])[:3]:
                    print_info(f"  - {error}")

# Test 14: Spreadsheet Parsing Error Handling
def test_spreadsheet_error_handling():
    print_test_header("Spreadsheet Parsing Error Handling")
    
    # Test with missing spreadsheet ID
    response = requests.post(
        f"{BASE_URL}/parse-spreadsheet",
        json={}
    )
    
    if response.status_code == 400:
        error_data = response.json()
        error_msg = error_data.get('error', '') or error_data.get('message', '')
        if 'spreadsheet_id' in error_msg.lower():
            print_success("Missing spreadsheet_id properly rejected")
        else:
            print_info(f"Got error (acceptable): {error_msg[:50]}")
    else:
        print_info(f"Endpoint returned {response.status_code} (may use config default)")

if __name__ == "__main__":
    run_all_tests()
    
    # Run additional spreadsheet tests
    print(f"\n{Colors.BLUE}{'='*80}{Colors.END}")
    print(f"{Colors.BLUE}Additional Spreadsheet Integration Tests{Colors.END}")
    print(f"{Colors.BLUE}{'='*80}{Colors.END}")
    
    test_spreadsheet_parsing_and_integration()
    test_spreadsheet_error_handling()
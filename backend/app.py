from flask import Flask, request, jsonify
from config import Config
from models import db, Student, Batch, StudentBatch, Class, ClassAttendance, Invoice
from utils.google_sheets import fetch_and_parse_spreadsheet
from datetime import datetime, date

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

# Create tables
with app.app_context():
    db.create_all()

# Helper function for error responses
def error_response(message, status_code=400):
    return jsonify({'error': message}), status_code

# STUDENT ROUTES
@app.route('/api/students', methods=['GET'])
def get_students():
    students = Student.query.all()
    return jsonify([student.to_dict() for student in students])

@app.route('/api/students/<int:student_id>', methods=['GET'])
def get_student(student_id):
    student = Student.query.get_or_404(student_id)
    return jsonify(student.to_dict())

@app.route('/api/students', methods=['POST'])
def create_student():
    data = request.get_json()
    
    # Validate required fields: name, email, birthdate
    if not data or not data.get('name'):
        return error_response('Name is required')
    
    if not data.get('email'):
        return error_response('Email is required')
    
    if not data.get('birthdate'):
        return error_response('Birthdate is required')
    
    # Validate that at least one parent name/email is present
    has_mother = data.get('mother_name') or data.get('mother_email')
    has_father = data.get('father_name') or data.get('father_email')
    
    if not (has_mother or has_father):
        return error_response('At least one parent name or email must be provided')
    
    # Parse birthdate
    try:
        birthdate = datetime.strptime(data['birthdate'], '%Y-%m-%d').date()
    except ValueError:
        return error_response('Invalid birthdate format. Use YYYY-MM-DD')
    
    student = Student(
        name=data['name'],
        birth_month=data.get('birth_month'),
        birth_year=data.get('birth_year'),
        birthdate=birthdate,
        email=data['email'],
        mother_name=data.get('mother_name'),
        mother_email=data.get('mother_email'),
        father_name=data.get('father_name'),
        father_email=data.get('father_email')
    )
    
    db.session.add(student)
    db.session.commit()
    
    return jsonify(student.to_dict()), 201

@app.route('/api/students/<int:student_id>', methods=['PUT'])
def update_student(student_id):
    student = Student.query.get_or_404(student_id)
    data = request.get_json()
    
    if 'name' in data:
        student.name = data['name']
    if 'birth_month' in data:
        student.birth_month = data['birth_month']
    if 'birth_year' in data:
        student.birth_year = data['birth_year']
    if 'email' in data:
        student.email = data['email']
    if 'mother_name' in data:
        student.mother_name = data['mother_name']
    if 'mother_email' in data:
        student.mother_email = data['mother_email']
    if 'father_name' in data:
        student.father_name = data['father_name']
    if 'father_email' in data:
        student.father_email = data['father_email']
    
    db.session.commit()
    return jsonify(student.to_dict())

@app.route('/api/students/<int:student_id>', methods=['DELETE'])
def delete_student(student_id):
    student = Student.query.get_or_404(student_id)
    db.session.delete(student)
    db.session.commit()
    return '', 204

# BATCH ROUTES
@app.route('/api/batches', methods=['GET'])
def get_batches():
    batches = Batch.query.all()
    return jsonify([batch.to_dict() for batch in batches])

@app.route('/api/batches/<int:batch_id>', methods=['GET'])
def get_batch(batch_id):
    batch = Batch.query.get_or_404(batch_id)
    return jsonify(batch.to_dict())

@app.route('/api/batches', methods=['POST'])
def create_batch():
    data = request.get_json()
    
    if not all(k in data for k in ['day_of_week', 'start_time', 'end_time']):
        return error_response('day_of_week, start_time, and end_time are required')
    
    try:
        start_time = datetime.strptime(data['start_time'], '%H:%M:%S').time()
        end_time = datetime.strptime(data['end_time'], '%H:%M:%S').time()
    except ValueError:
        return error_response('Invalid time format. Use HH:MM:SS')
    
    batch = Batch(
        day_of_week=data['day_of_week'],
        start_time=start_time,
        end_time=end_time,
        is_active=data.get('is_active', True)
    )
    
    db.session.add(batch)
    db.session.commit()
    
    return jsonify(batch.to_dict()), 201

@app.route('/api/batches/<int:batch_id>', methods=['PUT'])
def update_batch(batch_id):
    batch = Batch.query.get_or_404(batch_id)
    data = request.get_json()
    
    if 'day_of_week' in data:
        batch.day_of_week = data['day_of_week']
    if 'start_time' in data:
        try:
            batch.start_time = datetime.strptime(data['start_time'], '%H:%M:%S').time()
        except ValueError:
            return error_response('Invalid start_time format. Use HH:MM:SS')
    if 'end_time' in data:
        try:
            batch.end_time = datetime.strptime(data['end_time'], '%H:%M:%S').time()
        except ValueError:
            return error_response('Invalid end_time format. Use HH:MM:SS')
    if 'is_active' in data:
        batch.is_active = data['is_active']
    
    db.session.commit()
    return jsonify(batch.to_dict())

@app.route('/api/batches/<int:batch_id>', methods=['DELETE'])
def delete_batch(batch_id):
    batch = Batch.query.get_or_404(batch_id)
    db.session.delete(batch)
    db.session.commit()
    return '', 204

# STUDENT-BATCH ENROLLMENT ROUTES
@app.route('/api/student-batches', methods=['GET'])
def get_student_batches():
    enrollments = StudentBatch.query.all()
    return jsonify([enrollment.to_dict() for enrollment in enrollments])

@app.route('/api/student-batches/<int:student_batch_id>', methods=['GET'])
def get_student_batch(student_batch_id):
    enrollment = StudentBatch.query.get_or_404(student_batch_id)
    return jsonify(enrollment.to_dict())

@app.route('/api/student-batches', methods=['POST'])
def create_student_batch():
    data = request.get_json()
    
    if not all(k in data for k in ['student_id', 'batch_id']):
        return error_response('student_id and batch_id are required')
    
    # Check if student and batch exist
    student = Student.query.get(data['student_id'])
    batch = Batch.query.get(data['batch_id'])
    
    if not student:
        return error_response('Student not found', 404)
    if not batch:
        return error_response('Batch not found', 404)
    
    enrollment = StudentBatch(
        student_id=data['student_id'],
        batch_id=data['batch_id'],
        enrollment_date=datetime.strptime(data['enrollment_date'], '%Y-%m-%d').date() if 'enrollment_date' in data else date.today(),
        is_active=data.get('is_active', True)
    )
    
    try:
        db.session.add(enrollment)
        db.session.commit()
    except:
        db.session.rollback()
        return error_response('Student is already enrolled in this batch')
    
    return jsonify(enrollment.to_dict()), 201

@app.route('/api/student-batches/<int:student_batch_id>', methods=['PUT'])
def update_student_batch(student_batch_id):
    enrollment = StudentBatch.query.get_or_404(student_batch_id)
    data = request.get_json()
    
    if 'is_active' in data:
        enrollment.is_active = data['is_active']
    if 'enrollment_date' in data:
        try:
            enrollment.enrollment_date = datetime.strptime(data['enrollment_date'], '%Y-%m-%d').date()
        except ValueError:
            return error_response('Invalid date format. Use YYYY-MM-DD')
    
    db.session.commit()
    return jsonify(enrollment.to_dict())

@app.route('/api/student-batches/<int:student_batch_id>', methods=['DELETE'])
def delete_student_batch(student_batch_id):
    enrollment = StudentBatch.query.get_or_404(student_batch_id)
    db.session.delete(enrollment)
    db.session.commit()
    return '', 204

# CLASS ROUTES
@app.route('/api/classes', methods=['GET'])
def get_classes():
    classes = Class.query.all()
    return jsonify([cls.to_dict() for cls in classes])

@app.route('/api/classes/<int:class_id>', methods=['GET'])
def get_class(class_id):
    cls = Class.query.get_or_404(class_id)
    return jsonify(cls.to_dict())

@app.route('/api/classes', methods=['POST'])
def create_class():
    data = request.get_json()
    
    if not all(k in data for k in ['batch_id', 'class_date']):
        return error_response('batch_id and class_date are required')
    
    batch = Batch.query.get(data['batch_id'])
    if not batch:
        return error_response('Batch not found', 404)
    
    try:
        class_date = datetime.strptime(data['class_date'], '%Y-%m-%d').date()
    except ValueError:
        return error_response('Invalid date format. Use YYYY-MM-DD')
    
    cls = Class(
        batch_id=data['batch_id'],
        class_date=class_date,
        notes=data.get('notes')
    )
    
    db.session.add(cls)
    db.session.commit()
    
    return jsonify(cls.to_dict()), 201

@app.route('/api/classes/<int:class_id>', methods=['PUT'])
def update_class(class_id):
    cls = Class.query.get_or_404(class_id)
    data = request.get_json()
    
    if 'class_date' in data:
        try:
            cls.class_date = datetime.strptime(data['class_date'], '%Y-%m-%d').date()
        except ValueError:
            return error_response('Invalid date format. Use YYYY-MM-DD')
    if 'notes' in data:
        cls.notes = data['notes']
    if 'batch_id' in data:
        batch = Batch.query.get(data['batch_id'])
        if not batch:
            return error_response('Batch not found', 404)
        cls.batch_id = data['batch_id']
    
    db.session.commit()
    return jsonify(cls.to_dict())

@app.route('/api/classes/<int:class_id>', methods=['DELETE'])
def delete_class(class_id):
    cls = Class.query.get_or_404(class_id)
    db.session.delete(cls)
    db.session.commit()
    return '', 204

# CLASS ATTENDANCE ROUTES
@app.route('/api/attendance', methods=['GET'])
def get_attendances():
    attendances = ClassAttendance.query.all()
    return jsonify([attendance.to_dict() for attendance in attendances])

@app.route('/api/attendance/<int:attendance_id>', methods=['GET'])
def get_attendance(attendance_id):
    attendance = ClassAttendance.query.get_or_404(attendance_id)
    return jsonify(attendance.to_dict())

@app.route('/api/attendance', methods=['POST'])
def create_attendance():
    data = request.get_json()
    
    if not all(k in data for k in ['class_id', 'student_id']):
        return error_response('class_id and student_id are required')
    
    cls = Class.query.get(data['class_id'])
    student = Student.query.get(data['student_id'])
    
    if not cls:
        return error_response('Class not found', 404)
    if not student:
        return error_response('Student not found', 404)
    
    attendance = ClassAttendance(
        class_id=data['class_id'],
        student_id=data['student_id'],
        attended=data.get('attended', True),
        notes=data.get('notes')
    )
    
    try:
        db.session.add(attendance)
        db.session.commit()
    except:
        db.session.rollback()
        return error_response('Attendance record already exists for this student and class')
    
    return jsonify(attendance.to_dict()), 201

@app.route('/api/attendance/<int:attendance_id>', methods=['PUT'])
def update_attendance(attendance_id):
    attendance = ClassAttendance.query.get_or_404(attendance_id)
    data = request.get_json()
    
    if 'attended' in data:
        attendance.attended = data['attended']
    if 'notes' in data:
        attendance.notes = data['notes']
    
    db.session.commit()
    return jsonify(attendance.to_dict())

@app.route('/api/attendance/<int:attendance_id>', methods=['DELETE'])
def delete_attendance(attendance_id):
    attendance = ClassAttendance.query.get_or_404(attendance_id)
    db.session.delete(attendance)
    db.session.commit()
    return '', 204

# INVOICE ROUTES
@app.route('/api/invoices', methods=['GET'])
def get_invoices():
    invoices = Invoice.query.all()
    return jsonify([invoice.to_dict() for invoice in invoices])

@app.route('/api/invoices/<int:invoice_id>', methods=['GET'])
def get_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    return jsonify(invoice.to_dict())

@app.route('/api/invoices', methods=['POST'])
def create_invoice():
    data = request.get_json()
    
    if not all(k in data for k in ['class_id', 'student_id']):
        return error_response('class_id and student_id are required')
    
    cls = Class.query.get(data['class_id'])
    student = Student.query.get(data['student_id'])
    
    if not cls:
        return error_response('Class not found', 404)
    if not student:
        return error_response('Student not found', 404)
    
    invoice_date = date.today()
    if 'invoice_date' in data:
        try:
            invoice_date = datetime.strptime(data['invoice_date'], '%Y-%m-%d').date()
        except ValueError:
            return error_response('Invalid date format. Use YYYY-MM-DD')
    
    payment_date = None
    if 'payment_date' in data:
        try:
            payment_date = datetime.strptime(data['payment_date'], '%Y-%m-%d').date()
        except ValueError:
            return error_response('Invalid payment_date format. Use YYYY-MM-DD')
    
    invoice = Invoice(
        class_id=data['class_id'],
        student_id=data['student_id'],
        invoice_date=invoice_date,
        payment_status=data.get('payment_status', 'Pending'),
        amount=data.get('amount'),
        payment_date=payment_date,
        notes=data.get('notes')
    )
    
    db.session.add(invoice)
    db.session.commit()
    
    return jsonify(invoice.to_dict()), 201

@app.route('/api/invoices/<int:invoice_id>', methods=['PUT'])
def update_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    data = request.get_json()
    
    if 'payment_status' in data:
        invoice.payment_status = data['payment_status']
    if 'amount' in data:
        invoice.amount = data['amount']
    if 'invoice_date' in data:
        try:
            invoice.invoice_date = datetime.strptime(data['invoice_date'], '%Y-%m-%d').date()
        except ValueError:
            return error_response('Invalid invoice_date format. Use YYYY-MM-DD')
    if 'payment_date' in data:
        try:
            invoice.payment_date = datetime.strptime(data['payment_date'], '%Y-%m-%d').date()
        except ValueError:
            return error_response('Invalid payment_date format. Use YYYY-MM-DD')
    if 'notes' in data:
        invoice.notes = data['notes']
    
    db.session.commit()
    return jsonify(invoice.to_dict())

@app.route('/api/invoices/<int:invoice_id>', methods=['DELETE'])
def delete_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    db.session.delete(invoice)
    db.session.commit()
    return '', 204

# GOOGLE SHEETS PARSING ROUTE
@app.route('/api/parse-spreadsheet', methods=['POST'])
def parse_spreadsheet():
    """
    Parse student and batch data directly from Google Sheets.
    
    Expected request JSON format:
    {
        "spreadsheet_id": "YOUR_GOOGLE_SHEET_ID",
        "range": "Sheet1!A:H"  (optional, defaults to Sheet1!A:H)
    }
    
    If spreadsheet_id is not provided, uses GOOGLE_SHEETS_ID from config.
    
    Returns:
    {
        "success": bool,
        "message": str,
        "errors": [str] or null,
        "students": [...],
        "batches": [...]
    }
    """
    data = request.get_json() or {}
    
    # Get spreadsheet ID from request or config
    spreadsheet_id = data.get('spreadsheet_id') or app.config.get('GOOGLE_SHEETS_ID')
    
    if not spreadsheet_id:
        return error_response(
            'spreadsheet_id is required in request body or GOOGLE_SHEETS_ID must be set in config'
        )
    
    # Get range (optional)
    range_name = data.get('range', app.config.get('GOOGLE_SHEETS_RANGE', 'Sheet1!A:H'))
    
    # Fetch and parse the spreadsheet
    result = fetch_and_parse_spreadsheet(
        spreadsheet_id=spreadsheet_id,
        range_name=range_name,
        credentials_path=app.config.get('GOOGLE_SHEETS_CREDENTIALS_PATH', 'credentials.json')
    )
    
    # Return appropriate status code based on success
    status_code = 200 if result['success'] else 400
    return jsonify(result), status_code

# Health check route
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'message': 'Mridangam Student Management API is running'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
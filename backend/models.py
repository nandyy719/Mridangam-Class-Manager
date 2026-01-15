from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Student(db.Model):
    __tablename__ = 'students'
    
    student_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    birth_month = db.Column(db.Integer)
    birth_year = db.Column(db.Integer)
    email = db.Column(db.String(200))
    mother_name = db.Column(db.String(200))
    mother_email = db.Column(db.String(200))
    father_name = db.Column(db.String(200))
    father_email = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    batches = db.relationship('StudentBatch', back_populates='student', cascade='all, delete-orphan')
    attendances = db.relationship('ClassAttendance', back_populates='student', cascade='all, delete-orphan')
    invoices = db.relationship('Invoice', back_populates='student', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'student_id': self.student_id,
            'name': self.name,
            'birth_month': self.birth_month,
            'birth_year': self.birth_year,
            'email': self.email,
            'mother_name': self.mother_name,
            'mother_email': self.mother_email,
            'father_name': self.father_name,
            'father_email': self.father_email,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Batch(db.Model):
    __tablename__ = 'batches'
    
    batch_id = db.Column(db.Integer, primary_key=True)
    day_of_week = db.Column(db.String(20), nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    students = db.relationship('StudentBatch', back_populates='batch', cascade='all, delete-orphan')
    classes = db.relationship('Class', back_populates='batch', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'batch_id': self.batch_id,
            'day_of_week': self.day_of_week,
            'start_time': self.start_time.strftime('%H:%M:%S') if self.start_time else None,
            'end_time': self.end_time.strftime('%H:%M:%S') if self.end_time else None,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class StudentBatch(db.Model):
    __tablename__ = 'student_batches'
    
    student_batch_id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.student_id'), nullable=False)
    batch_id = db.Column(db.Integer, db.ForeignKey('batches.batch_id'), nullable=False)
    enrollment_date = db.Column(db.Date, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    student = db.relationship('Student', back_populates='batches')
    batch = db.relationship('Batch', back_populates='students')
    
    __table_args__ = (db.UniqueConstraint('student_id', 'batch_id', name='_student_batch_uc'),)
    
    def to_dict(self):
        return {
            'student_batch_id': self.student_batch_id,
            'student_id': self.student_id,
            'batch_id': self.batch_id,
            'enrollment_date': self.enrollment_date.isoformat() if self.enrollment_date else None,
            'is_active': self.is_active
        }

class Class(db.Model):
    __tablename__ = 'classes'
    
    class_id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.Integer, db.ForeignKey('batches.batch_id'), nullable=False)
    class_date = db.Column(db.Date, nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    batch = db.relationship('Batch', back_populates='classes')
    attendances = db.relationship('ClassAttendance', back_populates='class_obj', cascade='all, delete-orphan')
    invoices = db.relationship('Invoice', back_populates='class_obj', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'class_id': self.class_id,
            'batch_id': self.batch_id,
            'class_date': self.class_date.isoformat() if self.class_date else None,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class ClassAttendance(db.Model):
    __tablename__ = 'class_attendance'
    
    attendance_id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.class_id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.student_id'), nullable=False)
    attended = db.Column(db.Boolean, default=True)
    notes = db.Column(db.Text)
    
    # Relationships
    class_obj = db.relationship('Class', back_populates='attendances')
    student = db.relationship('Student', back_populates='attendances')
    
    __table_args__ = (db.UniqueConstraint('class_id', 'student_id', name='_class_student_uc'),)
    
    def to_dict(self):
        return {
            'attendance_id': self.attendance_id,
            'class_id': self.class_id,
            'student_id': self.student_id,
            'attended': self.attended,
            'notes': self.notes
        }

class Invoice(db.Model):
    __tablename__ = 'invoices'
    
    invoice_id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.class_id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.student_id'), nullable=False)
    invoice_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    payment_status = db.Column(db.String(20), nullable=False, default='Pending')
    amount = db.Column(db.Numeric(10, 2))
    payment_date = db.Column(db.Date)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    class_obj = db.relationship('Class', back_populates='invoices')
    student = db.relationship('Student', back_populates='invoices')
    
    def to_dict(self):
        return {
            'invoice_id': self.invoice_id,
            'class_id': self.class_id,
            'student_id': self.student_id,
            'invoice_date': self.invoice_date.isoformat() if self.invoice_date else None,
            'payment_status': self.payment_status,
            'amount': float(self.amount) if self.amount else None,
            'payment_date': self.payment_date.isoformat() if self.payment_date else None,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
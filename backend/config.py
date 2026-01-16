import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///mridangam_students.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Google Sheets configuration
    GOOGLE_SHEETS_CREDENTIALS_PATH = os.environ.get('GOOGLE_SHEETS_CREDENTIALS_PATH') or 'credentials.json'
    GOOGLE_SHEETS_ID = os.environ.get('GOOGLE_SHEETS_ID') or '1yPbSVkdjSD4XAPHJ9XU9dmCQ0-QfUm9fASdoXktf1Lc'  # Set via environment variable or pass to API
    GOOGLE_SHEETS_RANGE = os.environ.get('GOOGLE_SHEETS_RANGE') or 'Sheet1!A:H'
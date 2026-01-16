"""
Google Sheets integration utility for parsing Mridangam class spreadsheets.
Directly connects to Google Sheets API to read data.
"""
import re
import os
from datetime import datetime, time
from typing import Dict, List, Tuple, Optional
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class SpreadsheetParser:
    """Parses student and batch data from Google Sheets spreadsheet."""
    
    # Days of week for batch validation
    VALID_DAYS = {
        'monday', 'tuesday', 'wednesday', 'thursday', 
        'friday', 'saturday', 'sunday'
    }
    
    @staticmethod
    def parse_birthdate(birthdate_str: str) -> Optional[str]:
        """
        Parse birthdate string in either MM-DD-YYYY or MM/DD/YYYY format.
        Returns ISO format string (YYYY-MM-DD) or None if parsing fails.
        """
        if not birthdate_str or not isinstance(birthdate_str, str):
            return None
        
        birthdate_str = birthdate_str.strip()
        
        # Try MM-DD-YYYY format
        try:
            dt = datetime.strptime(birthdate_str, '%m-%d-%Y')
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            pass
        
        # Try MM/DD/YYYY format
        try:
            dt = datetime.strptime(birthdate_str, '%m/%d/%Y')
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            pass
        
        return None
    
    @staticmethod
    def parse_batch_time(batch_str: str) -> Optional[Tuple[str, str, str]]:
        """
        Parse batch string in formats like "Monday 7:00 PM" or "Monday, 7:00 PM".
        Handles: "Day HH:MM AM/PM", "Day h:MM AM/PM", "Day, HH:MM AM/PM", "Day, h:MM AM/PM"
        
        Returns: (day_of_week, start_time_HH:MM:SS, end_time_HH:MM:SS) or None if parsing fails
        """
        if not batch_str or not isinstance(batch_str, str):
            return None
        
        batch_str = batch_str.strip()
        
        # Pattern to match: Day [,] h[h]:MM AM/PM
        # Examples: "Monday 7:00 PM", "Monday, 07:00 AM", "Wednesday 2:30 PM"
        pattern = r'^(\w+),?\s+(\d{1,2}):(\d{2})\s+(AM|PM)$'
        match = re.match(pattern, batch_str, re.IGNORECASE)
        
        if not match:
            return None
        
        day_str = match.group(1).lower()
        hour = int(match.group(2))
        minute = int(match.group(3))
        ampm = match.group(4).upper()
        
        # Validate day
        if day_str not in SpreadsheetParser.VALID_DAYS:
            return None
        
        # Validate time
        if hour < 1 or hour > 12 or minute < 0 or minute >= 60:
            return None
        
        # Convert to 24-hour format
        if ampm == 'AM':
            if hour == 12:
                hour24 = 0
            else:
                hour24 = hour
        else:  # PM
            if hour == 12:
                hour24 = 12
            else:
                hour24 = hour + 12
        
        # Format times
        start_time = f"{hour24:02d}:{minute:02d}:00"
        # End time is 1 hour later
        end_hour = (hour24 + 1) % 24
        end_time = f"{end_hour:02d}:{minute:02d}:00"
        
        # Capitalize day for consistency
        day_formatted = day_str.capitalize()
        
        return (day_formatted, start_time, end_time)
    
    @staticmethod
    def parse_spreadsheet_rows(rows: List[List[str]]) -> Tuple[Dict, List[Dict], List[Dict]]:
        """
        Parse spreadsheet rows and extract students and batches.
        
        Expected row format:
        [Student Name, Birthdate, Email, Mother Name, Mother Email, Father Name, Father Email, Batch]
        
        Returns: (status_dict, students_list, batches_list)
        """
        students = []
        batches = []
        batch_map = {}  # Map of (day, start_time) -> batch for deduplication
        errors = []
        
        if not rows or len(rows) == 0:
            return {'success': False, 'message': 'No rows to parse'}, [], []
        
        # Skip header row (first row)
        data_rows = rows[1:] if len(rows) > 1 else []
        
        if not data_rows:
            return {'success': False, 'message': 'No data rows found (only header)'}, [], []
        
        for row_idx, row in enumerate(data_rows, start=2):  # row_idx starts at 2 (row 1 is header)
            # Skip empty rows
            if not row or all(not cell or not str(cell).strip() for cell in row):
                continue
            
            # Extract fields
            student_name = row[0].strip() if len(row) > 0 and row[0] else None
            birthdate_str = row[1].strip() if len(row) > 1 and row[1] else None
            email = row[2].strip() if len(row) > 2 and row[2] else None
            mother_name = row[3].strip() if len(row) > 3 and row[3] else None
            mother_email = row[4].strip() if len(row) > 4 and row[4] else None
            father_name = row[5].strip() if len(row) > 5 and row[5] else None
            father_email = row[6].strip() if len(row) > 6 and row[6] else None
            batch_str = row[7].strip() if len(row) > 7 and row[7] else None
            
            # Validate required fields
            if not student_name:
                errors.append(f"Row {row_idx}: Student name is required")
                continue
            
            if not email:
                errors.append(f"Row {row_idx}: Email is required")
                continue
            
            if not birthdate_str:
                errors.append(f"Row {row_idx}: Birthdate is required")
                continue
            
            # Validate at least one parent
            if not (mother_name or mother_email or father_name or father_email):
                errors.append(f"Row {row_idx}: At least one parent name or email must be provided")
                continue
            
            # Parse birthdate
            birthdate = SpreadsheetParser.parse_birthdate(birthdate_str)
            if not birthdate:
                errors.append(f"Row {row_idx}: Invalid birthdate format '{birthdate_str}'. Use MM-DD-YYYY or MM/DD/YYYY")
                continue
            
            # Parse batch
            if not batch_str:
                errors.append(f"Row {row_idx}: Batch is required")
                continue
            
            batch_info = SpreadsheetParser.parse_batch_time(batch_str)
            if not batch_info:
                errors.append(f"Row {row_idx}: Invalid batch format '{batch_str}'. Use formats like 'Monday 7:00 PM' or 'Wednesday, 2:30 PM'")
                continue
            
            day_of_week, start_time, end_time = batch_info
            
            # Deduplicate batches: use (day, start_time) as key
            batch_key = (day_of_week, start_time)
            if batch_key not in batch_map:
                batch_map[batch_key] = {
                    'day_of_week': day_of_week,
                    'start_time': start_time,
                    'end_time': end_time,
                    'is_active': True
                }
                batches.append(batch_map[batch_key])
            
            # Add student
            student = {
                'name': student_name,
                'email': email,
                'birthdate': birthdate,
                'mother_name': mother_name or None,
                'mother_email': mother_email or None,
                'father_name': father_name or None,
                'father_email': father_email or None,
                'batch': batch_str  # Store original batch string for reference
            }
            students.append(student)
        
        status = {
            'success': len(errors) == 0,
            'message': f"Parsed {len(students)} students and {len(batches)} batches",
            'errors': errors if errors else None
        }
        
        return status, students, batches


def parse_spreadsheet_data(rows: List[List[str]]) -> Dict:
    """
    Main function to parse spreadsheet data.
    
    Args:
        rows: List of rows from Google Sheets (each row is a list of cell values)
    
    Returns:
        Dictionary containing:
        {
            'success': bool,
            'message': str,
            'errors': List[str] or None,
            'students': List[Dict],
            'batches': List[Dict]
        }
    """
    status, students, batches = SpreadsheetParser.parse_spreadsheet_rows(rows)
    
    return {
        'success': status['success'],
        'message': status['message'],
        'errors': status.get('errors'),
        'students': students,
        'batches': batches
    }


class GoogleSheetsConnector:
    """Handles authentication and connection to Google Sheets API."""
    
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
    
    @staticmethod
    def get_credentials(credentials_path: str = 'credentials.json') -> Optional[Credentials]:
        """
        Get credentials from service account JSON file.
        
        Args:
            credentials_path: Path to credentials.json file
            
        Returns:
            Credentials object or None if file not found
        """
        if not os.path.exists(credentials_path):
            raise FileNotFoundError(
                f"Credentials file not found: {credentials_path}. "
                f"Please set up Google Sheets API credentials. "
                f"See SETUP_GOOGLE_SHEETS.md for instructions."
            )
        
        try:
            credentials = Credentials.from_service_account_file(
                credentials_path,
                scopes=GoogleSheetsConnector.SCOPES
            )
            return credentials
        except Exception as e:
            raise ValueError(f"Failed to load credentials: {str(e)}")
    
    @staticmethod
    def fetch_sheet_data(
        spreadsheet_id: str,
        range_name: str = 'Sheet1!A:H',
        credentials_path: str = 'credentials.json'
    ) -> List[List[str]]:
        """
        Fetch data from Google Sheet.
        
        Args:
            spreadsheet_id: The ID of the Google Sheet
            range_name: The range to fetch (default: Sheet1!A:H for columns A-H)
            credentials_path: Path to credentials.json
            
        Returns:
            List of rows (each row is a list of cell values)
            
        Raises:
            FileNotFoundError: If credentials file not found
            HttpError: If API call fails
            ValueError: If spreadsheet not found or not accessible
        """
        try:
            credentials = GoogleSheetsConnector.get_credentials(credentials_path)
            service = build('sheets', 'v4', credentials=credentials)
            
            # Call the Sheets API
            sheet = service.spreadsheets()
            result = sheet.values().get(
                spreadsheetId=spreadsheet_id,
                range=range_name
            ).execute()
            
            rows = result.get('values', [])
            
            if not rows:
                raise ValueError(f"No data found in sheet: {spreadsheet_id} (range: {range_name})")
            
            return rows
            
        except HttpError as error:
            if error.resp.status == 404:
                raise ValueError(f"Spreadsheet not found: {spreadsheet_id}")
            elif error.resp.status == 403:
                raise PermissionError(
                    f"Permission denied. Make sure the sheet is shared with the service account email. "
                    f"See SETUP_GOOGLE_SHEETS.md for instructions."
                )
            else:
                raise ValueError(f"Google Sheets API error: {str(error)}")


def fetch_and_parse_spreadsheet(
    spreadsheet_id: str,
    range_name: str = 'Sheet1!A:H',
    credentials_path: str = 'credentials.json'
) -> Dict:
    """
    Main function to fetch data directly from Google Sheets and parse it.
    
    Args:
        spreadsheet_id: The ID of the Google Sheet (from the sheet URL)
        range_name: The range to fetch (default: Sheet1!A:H)
        credentials_path: Path to credentials.json
        
    Returns:
        Dictionary containing:
        {
            'success': bool,
            'message': str,
            'errors': List[str] or None,
            'students': List[Dict],
            'batches': List[Dict]
        }
    """
    try:
        # Fetch data from Google Sheets
        rows = GoogleSheetsConnector.fetch_sheet_data(
            spreadsheet_id,
            range_name,
            credentials_path
        )
        
        # Parse the fetched data
        result = parse_spreadsheet_data(rows)
        return result
        
    except FileNotFoundError as e:
        return {
            'success': False,
            'message': f'Configuration error: {str(e)}',
            'errors': [str(e)],
            'students': [],
            'batches': []
        }
    except PermissionError as e:
        return {
            'success': False,
            'message': f'Access error: {str(e)}',
            'errors': [str(e)],
            'students': [],
            'batches': []
        }
    except ValueError as e:
        return {
            'success': False,
            'message': f'Error: {str(e)}',
            'errors': [str(e)],
            'students': [],
            'batches': []
        }
    except Exception as e:
        return {
            'success': False,
            'message': f'Unexpected error: {str(e)}',
            'errors': [str(e)],
            'students': [],
            'batches': []
        }

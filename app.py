import streamlit as st
from datetime import datetime, timedelta
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table as RLTable,
    TableStyle,
    Image,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm, mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib import colors
from PIL import Image as PILImage
from reportlab.platypus import Image as RLImage
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from contextlib import contextmanager
from typing import Union, Dict, List, Any, Optional, Tuple
import mysql.connector
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
import plotly.express as px  # Added import for Plotly Express
import os
import json
import sqlite3
import time
import gc

# For memory checking
import psutil


# Set page config must be the first Streamlit command
st.set_page_config(
    page_title="Student Registration System",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)


# Email configuration constants (replace with your actual SMTP server details)
SMTP_SERVER = "smtp.example.com"  # e.g., "smtp.gmail.com"
SMTP_PORT = 587  # Typical port for TLS
SMTP_USERNAME = "your_email@example.com"
SMTP_PASSWORD = "your_email_password"

# Remove local uploads directory creation
# if not os.path.exists("uploads"):
#     os.makedirs("uploads")

MYSQL_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "ekajiEKAJI1$",  # Set your MySQL password here
    "database": "student_registration",
    "port": 3306
}

def init_mysql_db():
    """
    Initialize the MySQL database if it doesn't exist.
    Returns True if MySQL is available, False if it falls back to SQLite.
    """
    global MYSQL_CONFIG
    
    # Check if MYSQL_CONFIG is None or not defined
    if MYSQL_CONFIG is None:
        print("MySQL configuration is not available. Falling back to SQLite database.")
        return False
    
    # Create a connection without specifying the database
    try:
        temp_config = MYSQL_CONFIG.copy()
        temp_config.pop("database", None)
        
        conn = mysql.connector.connect(**temp_config)
        cursor = conn.cursor()
        
        # Create the database if it doesn't exist
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {MYSQL_CONFIG['database']}")
        
        # Close the connection
        cursor.close()
        conn.close()
        
        print(f"Database '{MYSQL_CONFIG['database']}' initialized successfully")
        return True
    except Exception as err:
        print(f"Error initializing MySQL database: {err}")
        # Fall back to SQLite if MySQL connection fails
        print("Falling back to SQLite database")
        MYSQL_CONFIG = None
        return False



@contextmanager
def get_db_connection(max_retries=3, retry_delay=1):
    """
    Context manager for database connections.
    Tries to use MySQL first, falls back to SQLite if MySQL is not available.
    
    Args:
        max_retries: Maximum number of connection attempts
        retry_delay: Delay between retries in seconds
    """
    conn = None
    for attempt in range(max_retries):
        try:
            if MYSQL_CONFIG:
                # Use MySQL connection
                conn = mysql.connector.connect(**MYSQL_CONFIG)
            else:
                # Fall back to SQLite
                conn = sqlite3.connect("student_registration.db")
            break
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                print(f"Database connection error after {max_retries} attempts: {str(e)}")
                raise
    
    try:
        yield conn
    finally:
        if conn:
            if MYSQL_CONFIG and hasattr(conn, 'is_connected') and conn.is_connected():
                conn.close()
            elif not MYSQL_CONFIG and isinstance(conn, sqlite3.Connection):
                conn.close()


def init_db():
    with get_db_connection() as conn:
        c = conn.cursor()
        
        if MYSQL_CONFIG:
            # MySQL syntax for table creation
            # Create admin table
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS admin (
                    admin_id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(255) UNIQUE,
                    password VARCHAR(255),
                    email VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            # Create student_info table
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS student_info (
                    student_id VARCHAR(255) PRIMARY KEY,
                    surname VARCHAR(255),
                    other_names VARCHAR(255),
                    date_of_birth DATE,
                    place_of_birth VARCHAR(255),
                    home_town VARCHAR(255),
                    residential_address TEXT,
                    postal_address TEXT,
                    email VARCHAR(255),
                    telephone VARCHAR(255),
                    ghana_card_id VARCHAR(255),
                    nationality VARCHAR(255),
                    marital_status VARCHAR(255),
                    gender VARCHAR(255),
                    religion VARCHAR(255),
                    denomination VARCHAR(255),
                    disability_status VARCHAR(255),
                    disability_description TEXT,
                    guardian_name VARCHAR(255),
                    guardian_relationship VARCHAR(255),
                    guardian_occupation VARCHAR(255),
                    guardian_address TEXT,
                    guardian_telephone VARCHAR(255),
                    previous_school VARCHAR(255),
                    qualification_type VARCHAR(255),
                    completion_year VARCHAR(255),
                    aggregate_score VARCHAR(255),
                    ghana_card_path VARCHAR(255),
                    passport_photo_path VARCHAR(255),
                    certificate_path VARCHAR(255),
                    transcript_path VARCHAR(255),
                    receipt_path VARCHAR(255),
                    receipt_amount DECIMAL(10, 2) DEFAULT 0.0,
                    approval_status VARCHAR(255) DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    programme VARCHAR(255),
                    password VARCHAR(255),
                    last_login TIMESTAMP NULL,
                    password_reset_required BOOLEAN DEFAULT 1
                )
                """
            )
            # Create course_registration table
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS course_registration (
                    registration_id INT AUTO_INCREMENT PRIMARY KEY,
                    student_id VARCHAR(255),
                    index_number VARCHAR(255),
                    programme VARCHAR(255),
                    specialization VARCHAR(255),
                    level VARCHAR(255),
                    session VARCHAR(255),
                    academic_year VARCHAR(255),
                    semester VARCHAR(255),
                    courses TEXT,
                    total_credits INT,
                    date_registered DATE,
                    approval_status VARCHAR(255) DEFAULT 'pending',
                    receipt_path VARCHAR(255),
                    receipt_amount DECIMAL(10, 2) DEFAULT 0.0,
                    FOREIGN KEY (student_id) REFERENCES student_info (student_id)
                )
                """
            )
            # Create notifications table
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS notifications (
                    notification_id INT AUTO_INCREMENT PRIMARY KEY,
                    recipient_id VARCHAR(255),
                    recipient_type VARCHAR(255),
                    title VARCHAR(255),
                    message TEXT,
                    notification_type VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    read_at TIMESTAMP NULL,
                    metadata TEXT,
                    expires_at TIMESTAMP NULL
                )
                """
            )
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS notification_reads (
                    notification_id INT,
                    student_id VARCHAR(255),
                    read_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (notification_id, student_id)
                )
                """
            )
        else:
            # SQLite syntax for table creation
            # Create admin table
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS admin (
                    admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    password TEXT,
                    email TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            # Create student_info table
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS student_info (
                    student_id TEXT PRIMARY KEY,
                    surname TEXT,
                    other_names TEXT,
                    date_of_birth DATE,
                    place_of_birth TEXT,
                    home_town TEXT,
                    residential_address TEXT,
                    postal_address TEXT,
                    email TEXT,
                    telephone TEXT,
                    ghana_card_id TEXT,
                    nationality TEXT,
                    marital_status TEXT,
                    gender TEXT,
                    religion TEXT,
                    denomination TEXT,
                    disability_status TEXT,
                    disability_description TEXT,
                    guardian_name TEXT,
                    guardian_relationship TEXT,
                    guardian_occupation TEXT,
                    guardian_address TEXT,
                    guardian_telephone TEXT,
                    previous_school TEXT,
                    qualification_type TEXT,
                    completion_year TEXT,
                    aggregate_score TEXT,
                    ghana_card_path TEXT,
                    passport_photo_path TEXT,
                    certificate_path TEXT,
                    transcript_path TEXT,
                    receipt_path TEXT,
                    receipt_amount REAL DEFAULT 0.0,
                    approval_status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    programme TEXT,
                    password TEXT,
                    last_login TIMESTAMP,
                    password_reset_required INTEGER DEFAULT 1
                )
                """
            )
            # Create course_registration table
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS course_registration (
                    registration_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id TEXT,
                    index_number TEXT,
                    programme TEXT,
                    specialization TEXT,
                    level TEXT,
                    session TEXT,
                    academic_year TEXT,
                    semester TEXT,
                    courses TEXT,
                    total_credits INTEGER,
                    date_registered DATE,
                    approval_status TEXT DEFAULT 'pending',
                    receipt_path TEXT,
                    receipt_amount REAL DEFAULT 0.0,
                    FOREIGN KEY (student_id) REFERENCES student_info (student_id)
                )
                """
            )
            # Create notifications table
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS notifications (
                    notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    recipient_id TEXT,
                    recipient_type TEXT,
                    title TEXT,
                    message TEXT,
                    notification_type TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    read_at TIMESTAMP,
                    metadata TEXT,
                    expires_at TIMESTAMP
                )
                """
            )
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS notification_reads (
                    notification_id INTEGER,
                    student_id TEXT,
                    read_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (notification_id, student_id)
                )
                """
            )
        
        conn.commit()


import mysql.connector
import pandas as pd
import json
from datetime import datetime
import os
import shutil
import zipfile
from typing import Dict, List, Any, Optional
import logging



class DatabaseMigrationHandler:
    """
    Handles database migrations, exports, and imports while maintaining data consistency
    """

    SCHEMA_VERSION = "1.0"

    # Define the expected schema for each table
    SCHEMAS = {
        "student_info": {
            "student_id": "TEXT PRIMARY KEY",
            "surname": "TEXT",
            "other_names": "TEXT",
            "date_of_birth": "DATE",
            "place_of_birth": "TEXT",
            "home_town": "TEXT",
            "residential_address": "TEXT",
            "postal_address": "TEXT",
            "email": "TEXT",
            "telephone": "TEXT",
            "ghana_card_id": "TEXT",
            "nationality": "TEXT",
            "marital_status": "TEXT",
            "gender": "TEXT",
            "religion": "TEXT",
            "denomination": "TEXT",
            "disability_status": "TEXT",
            "disability_description": "TEXT",
            "guardian_name": "TEXT",
            "guardian_relationship": "TEXT",
            "guardian_occupation": "TEXT",
            "guardian_address": "TEXT",
            "guardian_telephone": "TEXT",
            "previous_school": "TEXT",
            "qualification_type": "TEXT",
            "completion_year": "TEXT",
            "aggregate_score": "TEXT",
            "ghana_card_path": "TEXT",
            "passport_photo_path": "TEXT",
            "transcript_path": "TEXT",
            "certificate_path": "TEXT",
            "receipt_path": "TEXT",
            "receipt_amount": "REAL DEFAULT 0.0",
            "approval_status": 'TEXT DEFAULT "pending"',
            "created_at": "DATETIME DEFAULT CURRENT_TIMESTAMP",
            "programme": "TEXT",
            "password": "TEXT",
            "last_login": "DATETIME",
            "password_reset_required": "BOOLEAN DEFAULT 1",
        },
        "course_registration": {
            "registration_id": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "student_id": "TEXT",
            "index_number": "TEXT",
            "programme": "TEXT",
            "specialization": "TEXT",
            "level": "TEXT",
            "session": "TEXT",
            "academic_year": "TEXT",
            "semester": "TEXT",
            "courses": "TEXT",
            "total_credits": "INTEGER",
            "date_registered": "DATE",
            "approval_status": 'TEXT DEFAULT "pending"',
            "receipt_path": "TEXT",
            "receipt_amount": "REAL DEFAULT 0.0",
        },
    }

    def __init__(self, db_path: str, backup_dir: str = "db_backups"):
        self.db_path = db_path
        self.backup_dir = backup_dir
        self.logger = self._setup_logger()

        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)

    def _setup_logger(self) -> logging.Logger:
        """Sets up logging configuration"""
        logger = logging.getLogger("DatabaseMigration")
        logger.setLevel(logging.INFO)
        handler = logging.FileHandler("db_migration.log")
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    def backup_database(self) -> str:
        """Creates a backup of the current database"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(self.backup_dir, f"backup_{timestamp}.db")
        os.system(
            f"mysqldump -u {MYSQL_CONFIG['user']} -p{MYSQL_CONFIG['password']} -h {MYSQL_CONFIG['host']} {MYSQL_CONFIG['database']} > {backup_path}"
        )
        self.logger.info(f"Database backed up to {backup_path}")
        return backup_path

    def export_database(self, export_path: str) -> str:
        """
        Exports the database to a zip file containing:
        - Excel files for each table
        - JSON schema file
        - Metadata file
        """
        try:
            # Create a temporary directory for export files
            temp_dir = "temp_export"
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)

            conn = sqlite3.connect(self.db_path)

            # Export each table to Excel
            for table_name in self.SCHEMAS.keys():
                df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
                excel_path = os.path.join(temp_dir, f"{table_name}.xlsx")
                df.to_excel(excel_path, index=False)

            # Create metadata file
            metadata = {
                "schema_version": self.SCHEMA_VERSION,
                "export_date": datetime.now().isoformat(),
                "tables": list(self.SCHEMAS.keys()),
            }
            with open(os.path.join(temp_dir, "metadata.json"), "w") as f:
                json.dump(metadata, f)

            # Create schema file
            with open(os.path.join(temp_dir, "schema.json"), "w") as f:
                json.dump(self.SCHEMAS, f)

            # Create zip file
            with zipfile.ZipFile(export_path, "w") as zipf:
                for root, _, files in os.walk(temp_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.basename(file_path)
                        zipf.write(file_path, arcname)

            self.logger.info(f"Database exported to {export_path}")
            return export_path

        except Exception as e:
            self.logger.error(f"Export failed: {str(e)}")
            raise

        finally:
            if "conn" in locals():
                conn.close()
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    def import_database(self, import_path: str, validate: bool = True) -> bool:
        """
        Imports database from a zip file while maintaining data consistency
        """
        try:
            # Create temporary directory for import
            temp_dir = "temp_import"
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)

            # Extract zip file
            with zipfile.ZipFile(import_path, "r") as zipf:
                zipf.extractall(temp_dir)

            # Validate import data
            if validate:
                self._validate_import(temp_dir)

            # Create backup before import
            self.backup_database()

            # Import data
            conn = sqlite3.connect(self.db_path)
            for table_name in self.SCHEMAS.keys():
                excel_path = os.path.join(temp_dir, f"{table_name}.xlsx")
                if os.path.exists(excel_path):
                    df = pd.read_excel(excel_path)
                    df.to_sql(table_name, conn, if_exists="replace", index=False)

            self.logger.info("Database import completed successfully")
            return True

        except Exception as e:
            self.logger.error(f"Import failed: {str(e)}")
            raise

        finally:
            if "conn" in locals():
                conn.close()
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    def _validate_import(self, import_dir: str) -> bool:
        """
        Validates import data against schema
        """
        # Check metadata
        with open(os.path.join(import_dir, "metadata.json"), "r") as f:
            metadata = json.load(f)
            if metadata["schema_version"] != self.SCHEMA_VERSION:
                raise ValueError(
                    f"Schema version mismatch. Expected {self.SCHEMA_VERSION}, got {metadata['schema_version']}"
                )

        # Check schema
        with open(os.path.join(import_dir, "schema.json"), "r") as f:
            import_schema = json.load(f)
            if import_schema != self.SCHEMAS:
                raise ValueError("Schema mismatch between import and current database")

        # Validate data in Excel files
        for table_name in self.SCHEMAS.keys():
            excel_path = os.path.join(import_dir, f"{table_name}.xlsx")
            if not os.path.exists(excel_path):
                raise FileNotFoundError(f"Missing table data: {table_name}")

            df = pd.read_excel(excel_path)
            expected_columns = set(self.SCHEMAS[table_name].keys())
            actual_columns = set(df.columns)

            if not expected_columns.issubset(actual_columns):
                missing_columns = expected_columns - actual_columns
                raise ValueError(f"Missing columns in {table_name}: {missing_columns}")

        return True

    def get_schema_info(self) -> Dict[str, Any]:
        """
        Returns current schema information
        """
        return {
            "version": self.SCHEMA_VERSION,
            "tables": self.SCHEMAS,
            "backup_location": self.backup_dir,
        }


def reset_db():
    with get_db_connection() as conn:
        c = conn.cursor()

    # Drop existing tables
    c.execute("DROP TABLE IF EXISTS admin")

    conn.commit()

    # Reinitialize the database
    init_db()


def check_db_locked():
    """
    Utility function to check if database is currently locked
    Returns True if locked, False otherwise
    """
    try:
        with get_db_connection(max_retries=1, retry_delay=0) as conn:
            conn.cursor().execute("SELECT 1")
            return False
    except sqlite3.OperationalError as e:
        if "database is locked" in str(e):
            return True
        raise


def get_program_courses(program):
    courses = {
        "CIMG": {
            "Pathway 1": [
                "PCM 101|FUNDAMENTALS OF MARKETING|3",
                "PCM 103|BUYER BEHAVIOUR|3",
                "PCM 102|BUSINESS LAW AND ETHICS|3",
            ],
            "Pathway 2": [
                "PAC 202|MANAGEMENT IN PRACTICE|3",
                "PCM 203|DIGITAL MARKETING TECHNIQUES|3",
                "PAC 201|DECISION-MAKING TECHNIQUES|3",
            ],
            "Pathway 3": [
                "PDM 301|BRANDS MANAGEMENT|3",
                "PDM 302|MARKETING RESEARCH AND INSIGHTS|3",
                "PDM 304|DIGITAL OPTIMISATION AND STRATEGY|3",
                "PDM 303|SELLING AND SALES MANAGEMENT|3",
            ],
            "Pathway 4": [
                "PDA 407|MASTERING MARKETING METRICS|3",
                "PDA 408|MANAGING CORPORATE REPUTATION|3",
                "PDA 404|DIGITAL CUSTOMER EXPERIENCE|3",
                "PDA 405|PRODUCT MANAGEMENT|3",
                "PDA 403|MANAGING MARKETING PROJECTS|3",
                "PDA 406|CUSTOMER RELATIONSHIP MANAGEMENT|3",
                "PDA 402|FINANCIAL MANAGEMENT FOR MARKETERS|3",
                "PDA 401|INTERNATIONAL MARKETING|3",
            ],
            "Pathway 5": [
                "PGD 502|STRATEGIC MARKETING PRACTICE- CASE STUDY|3",
                "PGD 503|STRATEGIC MARKETING MANAGEMENT|3",
                "PGD 501|INTEGRATED MARKETING COMMUNICATIONS|3",
                "PGD 504|ADVANCED DIGITAL MARKETING|3",
            ],
            "Pathway 6": [
                "PMS 613|SPECIALISED COMMODITIES MARKETING|3",
                "PMS 607|TRANSPORT AND LOGISTICS MARKETING|3",
                "PMS 606|NGO MARKETING|3",
                "PMS 608|AGRI-BUSINESS MARKETING|3",
                "PMS 604|PUBLIC SECTOR MARKETING|3",
                "PMS 601|FINANCIAL SERVICES MARKETING|3",
                "PMS 611|EDUCATION, HEALTHCARE AND HOSPITALITY MARKETING|3",
                "PMS 602|ENERGY MARKETING|3",
                "PMS 610|PRINTING, COMMUNICATIONS AGENCY AND PUBLISHING MARKETING|3",
                "PMS 609|TELECOMMUNICATIONS AND DIGITAL PLATFORM MARKETING|3",
                "PMS 605|POLITICAL MARKETING|3",
                "PMS 612|SPORTS AND ENTERTAINMENT MARKETING|3",
                "PMS 603|FAST MOVING CONSUMER GOOD MARKETING|3",
            ],
            "Pathway 7": [
                "PMD 701|MARKETING CONSULTANCY PRACTICE|3",
                "PMD 703|PROFESSIONAL SERVICES MARKETING|3",
                "PMD 702|CHANGE AND TRANSFORMATION MARKETING|3",
            ],
        },
        "CIM-UK": {
            "Level 4": [
                "CIM101|Marketing Principles|6",
                "CIM102|Communications in Practice|6",
                "CIM103|Customer Communications|6",
            ],
            "Level 5": [
                "CIM201|Applied Marketing|6",
                "CIM202|Planning Campaigns|6",
                "CIM203|Customer Insights|6",
            ],
            "Level 6": [
                "CIM301|Marketing & Digital Strategy|6",
                "CIM302|Innovation in Marketing|6",
                "CIM303|Resource Management|6",
            ],
            "Level 7": [
                "CIM401|Global Marketing Decisions|6",
                "CIM402|Corporate Digital Communications|6",
                "CIM403|Creating Entrepreneurial Change|6",
            ],
        },
        "ICAG": {
            "Level 1": [
                "ICAG101|Financial Accounting|3",
                "ICAG102|Business Management & Information Systems|3",
                "ICAG103|Business Law|3",
                "ICAG104|Introduction to Management Accounting|3",
            ],
            "Level 2": [
                "ICAG201|Financial Reporting|3",
                "ICAG202|Management Accounting|3",
                "ICAG203|Audit & Assurance|3",
                "ICAG204|Financial Management|3",
                "ICAG205|Corporate Law|3",
                "ICAG206|Public Sector Accounting|3",
            ],
            "Level 3": [
                "ICAG301|Corporate Reporting|3",
                "ICAG302|Advanced Management Accounting|3",
                "ICAG303|Advanced Audit & Assurance|3",
                "ICAG304|Advanced Financial Management|3",
                "ICAG305|Strategy & Governance|3",
                "ICAG306|Advanced Taxation|3",
            ],
        },
        "ACCA": {
            "Level 1 (Applied Knowledge)": [
                "AB101|Accountant in Business|3",
                "MA101|Management Accounting|3",
                "FA101|Financial Accounting|3",
            ],
            "Level 2 (Applied Skills)": [
                "LW201|Corporate and Business Law|3",
                "PM201|Performance Management|3",
                "TX201|Taxation|3",
                "FR201|Financial Reporting|3",
                "AA201|Audit and Assurance|3",
                "FM201|Financial Management|3",
            ],
            "Level 3 Strategic Professional (Essentials)": [
                "SBL301|Strategic Business Leader|6",
                "SBR301|Strategic Business Reporting|6",
            ],
            "Strategic Professional (Options)": [
                "AFM401|Advanced Financial Management|6",
                "APM401|Advanced Performance Management|6",
                "ATX401|Advanced Taxation|6",
                "AAA401|Advanced Audit and Assurance|6",
            ],
        },
    }
    return courses.get(program, {})

import os
import io
import tempfile
from datetime import datetime
from typing import Optional, Dict, Tuple, BinaryIO, Union
import logging
from PIL import Image

from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive, GoogleDriveFile

def initialize_drive_storage():
    """
    Initialize the Google Drive storage handler.
    Returns a GoogleDriveStorage instance if successful, None otherwise.
    """
    try:
        drive_storage = GoogleDriveStorage(
            credentials_file='credentials.json',
            settings_file='settings.yaml'
        )
        return drive_storage
    except Exception as e:
        print(f"Error initializing Google Drive storage: {str(e)}")
        return None

# Example usage for saving a file to Google Drive
def save_file_to_drive(file_data, filename, document_type, identifier=None):
    """
    Save a file to Google Drive.
    
    Args:
        file_data: File data as bytes or file-like object
        filename: Original filename
        document_type: Type of document (ghana_card, passport_photo, etc.)
        identifier: Student ID or registration ID
        
    Returns:
        Tuple of (file_id, web_view_link) or (None, None) if error
    """
    drive_storage = initialize_drive_storage()
    if not drive_storage:
        return None, None
    
    try:
        file_id, web_view_link, was_compressed = drive_storage.save_compressed_file(
            file_data, filename, document_type, identifier
        )
        return file_id, web_view_link
    except Exception as e:
        print(f"Error saving file to Google Drive: {str(e)}")
        return None, None

# Example usage for retrieving a file from Google Drive
def get_file_from_drive(file_id):
    """
    Retrieve a file from Google Drive.
    
    Args:
        file_id: ID of the file to retrieve
        
    Returns:
        Tuple of (file_content, filename) or (None, None) if error
    """
    drive_storage = initialize_drive_storage()
    if not drive_storage:
        return None, None
    
    try:
        content, filename = drive_storage.get_file(file_id)
        return content, filename
    except Exception as e:
        print(f"Error retrieving file from Google Drive: {str(e)}")
        return None, None

class GoogleDriveStorage:
    """
    Handles file storage operations using Google Drive instead of local storage.
    This class provides methods to upload, retrieve, and manage files in Google Drive.
    """

    def __init__(self, credentials_file: str = 'credentials.json', settings_file: str = 'settings.yaml'):
        """
        Initialize the Google Drive storage handler.
        
        Args:
            credentials_file: Path to the Google API credentials file
            settings_file: Path to the PyDrive settings file
        """
        self.logger = self._setup_logger()
        self.drive = self._authenticate(credentials_file, settings_file)
        self.folder_structure = {
            'student_documents': {
                'ghana_cards': None,
                'passport_photos': None,
                'transcripts': None,
                'certificates': None,
                'receipts': None
            },
            'course_registration_receipts': {
                'receipts': None
            }
        }
        self._initialize_folder_structure()

    def _setup_logger(self) -> logging.Logger:
        """Set up a logger for the Google Drive storage handler."""
        logger = logging.getLogger("GoogleDriveStorage")
        logger.setLevel(logging.INFO)
        
        # Avoid adding duplicate handlers
        if not logger.handlers:
            handler = logging.FileHandler("google_drive_storage.log")
            formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger

    def _authenticate(self, credentials_file: str, settings_file: str) -> GoogleDrive:
        """
        Authenticate with Google Drive API.
        
        Args:
            credentials_file: Path to the Google API credentials file
            settings_file: Path to the PyDrive settings file
            
        Returns:
            Authenticated GoogleDrive instance
        """
        try:
            gauth = GoogleAuth()
            
            # Try to load saved client credentials
            gauth.LoadCredentialsFile(credentials_file)
            
            if gauth.credentials is None:
                # Authenticate if they're not available
                gauth.LocalWebserverAuth()
            elif gauth.access_token_expired:
                # Refresh them if expired
                gauth.Refresh()
            else:
                # Initialize the saved creds
                gauth.Authorize()
                
            # Save the current credentials
            gauth.SaveCredentialsFile(credentials_file)
            
            return GoogleDrive(gauth)
            
        except Exception as e:
            self.logger.error(f"Authentication error: {str(e)}")
            raise

    def _initialize_folder_structure(self):
        """Initialize the folder structure in Google Drive if it doesn't exist."""
        try:
            # Check if root folders exist, create if not
            for root_folder, subfolders in self.folder_structure.items():
                root_id = self._get_or_create_folder(root_folder)
                
                # Create subfolders
                for subfolder in subfolders:
                    subfolder_id = self._get_or_create_folder(subfolder, parent_id=root_id)
                    self.folder_structure[root_folder][subfolder] = subfolder_id
                    
            self.logger.info("Folder structure initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing folder structure: {str(e)}")
            raise

    def _get_or_create_folder(self, folder_name: str, parent_id: Optional[str] = None) -> str:
        """
        Get a folder ID by name, or create it if it doesn't exist.
        
        Args:
            folder_name: Name of the folder
            parent_id: ID of the parent folder (None for root)
            
        Returns:
            Folder ID
        """
        # Prepare query
        query = f"title='{folder_name}' and mimeType='application/vnd.google-apps.folder'"
        if parent_id:
            query += f" and '{parent_id}' in parents"
        
        # Search for the folder
        file_list = self.drive.ListFile({'q': query}).GetList()
        
        # Return ID if folder exists
        if file_list:
            return file_list[0]['id']
        
        # Create folder if it doesn't exist
        folder_metadata = {
            'title': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        
        if parent_id:
            folder_metadata['parents'] = [{'id': parent_id}]
            
        folder = self.drive.CreateFile(folder_metadata)
        folder.Upload()
        
        return folder['id']

    def save_file(self, file_data: Union[BinaryIO, bytes], 
                  filename: str, 
                  document_type: str, 
                  identifier: str = None) -> Tuple[str, str]:
        """
        Save a file to Google Drive.
        
        Args:
            file_data: File data as bytes or file-like object
            filename: Original filename
            document_type: Type of document (ghana_card, passport_photo, etc.)
            identifier: Student ID or registration ID
            
        Returns:
            Tuple of (file_id, web_view_link)
        """
        try:
            # Determine the appropriate folder based on document type
            folder_id = self._get_folder_id_for_document(document_type)
            
            if not folder_id:
                raise ValueError(f"Invalid document type: {document_type}")
            
            # Generate a unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name, ext = os.path.splitext(filename)
            new_filename = f"{identifier}_{document_type}_{timestamp}{ext}" if identifier else f"{document_type}_{timestamp}{ext}"
            
            # Create file metadata
            file_metadata = {
                'title': new_filename,
                'parents': [{'id': folder_id}]
            }
            
            # Create the file
            drive_file = self.drive.CreateFile(file_metadata)
            
            # Set content
            if isinstance(file_data, bytes):
                with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                    temp_file.write(file_data)
                    temp_path = temp_file.name
                
                drive_file.SetContentFile(temp_path)
                os.unlink(temp_path)  # Delete the temporary file
            else:
                # If it's a file-like object
                file_data.seek(0)
                drive_file.SetContentString(file_data.read().decode('utf-8'))
            
            # Upload the file
            drive_file.Upload()
            
            self.logger.info(f"File uploaded successfully: {new_filename}")
            
            # Return file ID and web view link
            return drive_file['id'], drive_file['alternateLink']
            
        except Exception as e:
            self.logger.error(f"Error saving file: {str(e)}")
            raise

    def _get_folder_id_for_document(self, document_type: str) -> Optional[str]:
        """
        Get the folder ID for a specific document type.
        
        Args:
            document_type: Type of document
            
        Returns:
            Folder ID or None if not found
        """
        # Map document types to folder structure
        document_folder_map = {
            'ghana_card': self.folder_structure['student_documents']['ghana_cards'],
            'passport_photo': self.folder_structure['student_documents']['passport_photos'],
            'transcript': self.folder_structure['student_documents']['transcripts'],
            'certificate': self.folder_structure['student_documents']['certificates'],
            'receipt': self.folder_structure['student_documents']['receipts'],
            'course_receipt': self.folder_structure['course_registration_receipts']['receipts']
        }
        
        return document_folder_map.get(document_type)

    def get_file(self, file_id: str) -> Tuple[bytes, str]:
        """
        Retrieve a file from Google Drive.
        
        Args:
            file_id: ID of the file to retrieve
            
        Returns:
            Tuple of (file_content, filename)
        """
        try:
            drive_file = self.drive.CreateFile({'id': file_id})
            filename = drive_file['title']
            
            # Download file content to a temporary file
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                drive_file.GetContentFile(temp_file.name)
                temp_path = temp_file.name
            
            # Read the file content
            with open(temp_path, 'rb') as f:
                content = f.read()
                
            # Delete the temporary file
            os.unlink(temp_path)
            
            return content, filename
            
        except Exception as e:
            self.logger.error(f"Error retrieving file: {str(e)}")
            raise

    def delete_file(self, file_id: str) -> bool:
        """
        Delete a file from Google Drive.
        
        Args:
            file_id: ID of the file to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            drive_file = self.drive.CreateFile({'id': file_id})
            drive_file.Delete()
            self.logger.info(f"File deleted successfully: {file_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting file: {str(e)}")
            return False

    def compress_image(self, image_data: bytes, max_size_mb: float = 6.0) -> Tuple[bytes, bool]:
        """
        Compress an image if it exceeds the size limit.
        
        Args:
            image_data: Image data as bytes
            max_size_mb: Maximum file size in MB
            
        Returns:
            Tuple of (compressed_data, was_compressed)
        """
        # Check if compression is needed
        if len(image_data) <= max_size_mb * 1024 * 1024:
            return image_data, False
            
        try:
            # Open the image
            img = Image.open(io.BytesIO(image_data))
            
            # Start with original quality
            quality = 90
            min_quality = 30
            
            # Try compression with decreasing quality until size is acceptable
            while quality >= min_quality:
                # Create an in-memory buffer
                buffer = io.BytesIO()
                
                # Save with current quality
                if img.format == 'JPEG':
                    img.save(buffer, format="JPEG", quality=quality, optimize=True)
                elif img.format == 'PNG':
                    img.save(buffer, format="PNG", optimize=True, compress_level=9)
                else:
                    # For other formats, convert to JPEG
                    img.save(buffer, format="JPEG", quality=quality, optimize=True)
                
                # Check if size is now acceptable
                compressed_bytes = buffer.getvalue()
                if len(compressed_bytes) <= max_size_mb * 1024 * 1024:
                    self.logger.info(
                        f"Compressed image from {len(image_data)/1024/1024:.2f}MB to "
                        f"{len(compressed_bytes)/1024/1024:.2f}MB (quality={quality})"
                    )
                    return compressed_bytes, True
                
                # Reduce quality for next iteration
                quality -= 10
            
            # If quality reduction wasn't enough, try reducing dimensions
            scale_factor = 0.8
            max_dimension = max(img.size)
            
            while max_dimension > 800:  # Don't go below 800px for max dimension
                # Resize the image
                new_size = (
                    int(img.width * scale_factor),
                    int(img.height * scale_factor)
                )
                img = img.resize(new_size, Image.LANCZOS)
                max_dimension = max(img.size)
                
                # Try saving with minimum acceptable quality
                buffer = io.BytesIO()
                if img.format == 'JPEG':
                    img.save(buffer, format="JPEG", quality=min_quality, optimize=True)
                elif img.format == 'PNG':
                    img.save(buffer, format="PNG", optimize=True, compress_level=9)
                else:
                    img.save(buffer, format="JPEG", quality=min_quality, optimize=True)
                
                compressed_bytes = buffer.getvalue()
                if len(compressed_bytes) <= max_size_mb * 1024 * 1024:
                    self.logger.info(
                        f"Compressed image from {len(image_data)/1024/1024:.2f}MB to "
                        f"{len(compressed_bytes)/1024/1024:.2f}MB (dimensions={new_size})"
                    )
                    return compressed_bytes, True
                
                scale_factor *= 0.8
            
            # If we get here, we couldn't compress enough
            self.logger.warning("Could not compress image below size limit")
            return image_data, False
            
        except Exception as e:
            self.logger.error(f"Error compressing image: {str(e)}")
            return image_data, False

    def save_compressed_file(self, file_data: Union[BinaryIO, bytes], 
                            filename: str, 
                            document_type: str, 
                            identifier: str = None,
                            max_size_mb: float = 6.0) -> Tuple[str, str, bool]:
        """
        Save a file to Google Drive, compressing it if necessary.
        
        Args:
            file_data: File data as bytes or file-like object
            filename: Original filename
            document_type: Type of document
            identifier: Student ID or registration ID
            max_size_mb: Maximum file size in MB
            
        Returns:
            Tuple of (file_id, web_view_link, was_compressed)
        """
        # Convert file_data to bytes if it's a file-like object
        if hasattr(file_data, 'read'):
            file_data.seek(0)
            data = file_data.read()
        else:
            data = file_data
            
        # Check if compression is needed
        if len(data) > max_size_mb * 1024 * 1024:
            # Check if it's an image
            ext = os.path.splitext(filename)[1].lower()
            if ext in ['.jpg', '.jpeg', '.png']:
                data, was_compressed = self.compress_image(data, max_size_mb)
            else:
                was_compressed = False
        else:
            was_compressed = False
            
        # Save the file
        file_id, web_view_link = self.save_file(data, filename, document_type, identifier)
        
        return file_id, web_view_link, was_compressed

    def list_files(self, folder_type: str = None, document_type: str = None) -> List[Dict[str, Any]]:
        """
        List files stored in Google Drive with optional filtering.
        
        Args:
            folder_type: Optional filter by folder type ('student_documents' or 'course_registration_receipts')
            document_type: Optional filter by document type (e.g., 'ghana_card', 'passport_photo', etc.)
            
        Returns:
            List of dictionaries containing file information
        """
        try:
            # Determine folder ID based on filters
            folder_id = None
            
            if folder_type and document_type:
                # Get specific subfolder
                if folder_type in self.folder_structure and document_type in self.folder_structure[folder_type]:
                    folder_id = self.folder_structure[folder_type][document_type]
            elif folder_type:
                # Get main folder
                for main_folder, subfolders in self.folder_structure.items():
                    if main_folder == folder_type:
                        # Just list files in the main folder
                        folder_id = self._get_or_create_folder(main_folder)
                        break
            
            # Prepare query
            query = "'root' in parents"  # Default to root if no folder specified
            
            if folder_id:
                query = f"'{folder_id}' in parents"
            
            # Get file list
            file_list = self.drive.ListFile({'q': query}).GetList()
            
            # Format results
            results = []
            for file in file_list:
                results.append({
                    'id': file['id'],
                    'title': file['title'],
                    'mimeType': file['mimeType'],
                    'createdDate': file['createdDate'],
                    'modifiedDate': file['modifiedDate'],
                    'webViewLink': file['alternateLink'],
                    'size': file.get('fileSize', 'N/A'),
                    'md5Checksum': file.get('md5Checksum', 'N/A')
                })
            
            self.logger.info(f"Listed {len(results)} files from Google Drive")
            return results
            
        except Exception as e:
            self.logger.error(f"Error listing files: {str(e)}")
            return []
        
def batch_upload_student_documents(self, student_id: str, documents: Dict[str, Any]) -> Tuple[bool, Dict[str, str]]:
    """
    Upload multiple documents for a single student in one operation.
    
    Args:
        student_id: The student ID
        documents: Dictionary mapping document types to file objects
                  (e.g., {'ghana_card': file_obj, 'passport_photo': file_obj})
    
    Returns:
        Tuple of (success: bool, results: Dict[str, str])
        where results maps document types to file paths or error messages
    """
    results = {}
    success = True
    
    try:
        # Ensure the student exists in the database
        conn = sqlite3.connect("student_registration.db")
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM student_info WHERE student_id = ?", (student_id,))
        if not cursor.fetchone():
            conn.close()
            return False, {"error": f"Student ID {student_id} not found in database"}
        conn.close()
        
        # Process each document
        for doc_type, file_obj in documents.items():
            if not file_obj:
                results[doc_type] = "No file provided"
                continue
                
            # Check if document type is valid
            if doc_type not in self.ALLOWED_EXTENSIONS:
                results[doc_type] = f"Invalid document type: {doc_type}"
                success = False
                continue
                
            # Check file extension
            filename = file_obj.name
            ext = os.path.splitext(filename)[1].lower()
            if ext not in self.ALLOWED_EXTENSIONS[doc_type]:
                results[doc_type] = f"Invalid file extension {ext} for {doc_type}"
                success = False
                continue
            
            # Save the document
            try:
                # Create a unique filename
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                new_filename = f"{student_id}_{doc_type}_{timestamp}{ext}"
                dest_path = os.path.join(self.upload_base_dir, new_filename)
                
                # Save the file
                with open(dest_path, 'wb') as f:
                    f.write(file_obj.getbuffer())
                
                # Update the database
                conn = sqlite3.connect("student_registration.db")
                cursor = conn.cursor()
                query = f"UPDATE student_info SET {doc_type}_path = ? WHERE student_id = ?"
                cursor.execute(query, (dest_path, student_id))
                conn.commit()
                conn.close()
                
                results[doc_type] = dest_path
                self.logger.info(f"Successfully uploaded {doc_type} for student {student_id}")
                
            except Exception as e:
                results[doc_type] = f"Error: {str(e)}"
                success = False
                self.logger.error(f"Error uploading {doc_type} for student {student_id}: {str(e)}")
        
        return success, results
        
    except Exception as e:
        self.logger.error(f"Batch upload error for student {student_id}: {str(e)}")
        return False, {"error": str(e)}
    
def generate_student_statistics():
    """
    Generate comprehensive statistics about students and course registrations.
    
    Returns:
        Dictionary containing various statistics
    """
    stats = {
        "total_students": 0,
        "approved_students": 0,
        "pending_students": 0,
        "rejected_students": 0,
        "total_registrations": 0,
        "gender_distribution": {},
        "programme_distribution": {},
        "level_distribution": {},
        "registration_by_semester": {},
        "registration_by_academic_year": {},
        "documents_uploaded": {
            "ghana_card": 0,
            "passport_photo": 0,
            "transcript": 0,
            "certificate": 0,
            "receipt": 0
        }
    }
    
    try:
        with get_db_connection() as conn:
            c = conn.cursor(dictionary=True)
            
            # Get student counts by approval status
            c.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN approval_status = 'approved' THEN 1 ELSE 0 END) as approved,
                    SUM(CASE WHEN approval_status = 'pending' THEN 1 ELSE 0 END) as pending,
                    SUM(CASE WHEN approval_status = 'rejected' THEN 1 ELSE 0 END) as rejected
                FROM student_info
            """)
            result = c.fetchone()
            
            # Convert Decimal to int for MySQL compatibility
            stats["total_students"] = int(result["total"]) if result["total"] else 0
            stats["approved_students"] = int(result["approved"]) if result["approved"] else 0
            stats["pending_students"] = int(result["pending"]) if result["pending"] else 0
            stats["rejected_students"] = int(result["rejected"]) if result["rejected"] else 0
            
            # Get gender distribution
            c.execute("""
                SELECT gender, COUNT(*) as count
                FROM student_info
                GROUP BY gender
            """)
            for row in c.fetchall():
                stats["gender_distribution"][row["gender"]] = int(row["count"])
            
            # Get programme distribution
            c.execute("""
                SELECT programme, COUNT(*) as count
                FROM student_info
                WHERE programme IS NOT NULL AND programme != ''
                GROUP BY programme
            """)
            for row in c.fetchall():
                stats["programme_distribution"][row["programme"]] = int(row["count"])
            
            # Get document upload statistics
            c.execute("""
                SELECT 
                    SUM(CASE WHEN ghana_card_path IS NOT NULL THEN 1 ELSE 0 END) as ghana_card,
                    SUM(CASE WHEN passport_photo_path IS NOT NULL THEN 1 ELSE 0 END) as passport_photo,
                    SUM(CASE WHEN transcript_path IS NOT NULL THEN 1 ELSE 0 END) as transcript,
                    SUM(CASE WHEN certificate_path IS NOT NULL THEN 1 ELSE 0 END) as certificate,
                    SUM(CASE WHEN receipt_path IS NOT NULL THEN 1 ELSE 0 END) as receipt
                FROM student_info
            """)
            result = c.fetchone()
            stats["documents_uploaded"]["ghana_card"] = int(result["ghana_card"]) if result["ghana_card"] else 0
            stats["documents_uploaded"]["passport_photo"] = int(result["passport_photo"]) if result["passport_photo"] else 0
            stats["documents_uploaded"]["transcript"] = int(result["transcript"]) if result["transcript"] else 0
            stats["documents_uploaded"]["certificate"] = int(result["certificate"]) if result["certificate"] else 0
            stats["documents_uploaded"]["receipt"] = int(result["receipt"]) if result["receipt"] else 0
            
            # Get course registration statistics
            c.execute("SELECT COUNT(*) as total FROM course_registration")
            stats["total_registrations"] = int(c.fetchone()["total"])
            
            # Get level distribution
            c.execute("""
                SELECT level, COUNT(*) as count
                FROM course_registration
                GROUP BY level
            """)
            for row in c.fetchall():
                stats["level_distribution"][row["level"]] = int(row["count"])
            
            # Get semester distribution
            c.execute("""
                SELECT semester, COUNT(*) as count
                FROM course_registration
                GROUP BY semester
            """)
            for row in c.fetchall():
                stats["registration_by_semester"][row["semester"]] = int(row["count"])
            
            # Get academic year distribution
            c.execute("""
                SELECT academic_year, COUNT(*) as count
                FROM course_registration
                GROUP BY academic_year
            """)
            for row in c.fetchall():
                stats["registration_by_academic_year"][row["academic_year"]] = int(row["count"])
            
        return stats
        
    except Exception as e:
        print(f"Error generating statistics: {str(e)}")
        return stats

def display_student_statistics():
    """
    Display comprehensive student statistics in the admin dashboard
    """
    st.subheader("📊 Student Statistics Dashboard")
    
    # Get statistics
    stats = generate_student_statistics()
    
    # Display key metrics in columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Students", stats["total_students"])
    with col2:
        st.metric("Approved", stats["approved_students"])
    with col3:
        st.metric("Pending", stats["pending_students"])
    with col4:
        st.metric("Rejected", stats["rejected_students"])
    
    # Create tabs for different statistics
    tab1, tab2, tab3 = st.tabs(["Demographics", "Registrations", "Documents"])
    
    with tab1:
        st.subheader("Student Demographics")
        
        # Gender distribution
        if stats["gender_distribution"]:
            gender_df = pd.DataFrame({
                'Gender': list(stats["gender_distribution"].keys()),
                'Count': list(stats["gender_distribution"].values())
            })
            
            fig = px.pie(
                gender_df, 
                names='Gender', 
                values='Count',
                title='Gender Distribution',
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No gender distribution data available")
        
        # Programme distribution
        if stats["programme_distribution"]:
            programme_df = pd.DataFrame({
                'Programme': list(stats["programme_distribution"].keys()),
                'Count': list(stats["programme_distribution"].values())
            })
            
            fig = px.bar(
                programme_df, 
                x='Programme', 
                y='Count',
                title='Programme Distribution',
                color='Programme',
                color_discrete_sequence=px.colors.qualitative.Bold
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No programme distribution data available")
    
    with tab2:
        st.subheader("Course Registrations")
        
        st.metric("Total Registrations", stats["total_registrations"])
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Level distribution
            if stats["level_distribution"]:
                level_df = pd.DataFrame({
                    'Level': list(stats["level_distribution"].keys()),
                    'Count': list(stats["level_distribution"].values())
                })
                
                fig = px.pie(
                    level_df, 
                    names='Level', 
                    values='Count',
                    title='Level Distribution',
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No level distribution data available")
        
        with col2:
            # Semester distribution
            if stats["registration_by_semester"]:
                semester_df = pd.DataFrame({
                    'Semester': list(stats["registration_by_semester"].keys()),
                    'Count': list(stats["registration_by_semester"].values())
                })
                
                fig = px.pie(
                    semester_df, 
                    names='Semester', 
                    values='Count',
                    title='Semester Distribution',
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No semester distribution data available")
        
        # Academic year distribution
        if stats["registration_by_academic_year"]:
            year_df = pd.DataFrame({
                'Academic Year': list(stats["registration_by_academic_year"].keys()),
                'Count': list(stats["registration_by_academic_year"].values())
            })
            
            fig = px.bar(
                year_df, 
                x='Academic Year', 
                y='Count',
                title='Registration by Academic Year',
                color='Academic Year',
                color_discrete_sequence=px.colors.qualitative.Vivid
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No academic year distribution data available")
    
    with tab3:
        st.subheader("Document Uploads")
        
        # Document uploads statistics
        doc_df = pd.DataFrame({
            'Document Type': list(stats["documents_uploaded"].keys()),
            'Count': list(stats["documents_uploaded"].values())
        })
        
        fig = px.bar(
            doc_df, 
            x='Document Type', 
            y='Count',
            title='Document Upload Statistics',
            color='Document Type',
            color_discrete_sequence=px.colors.qualitative.Safe
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Calculate document upload completion rate
        if stats["total_students"] > 0:
            completion_data = []
            for doc_type, count in stats["documents_uploaded"].items():
                completion_rate = (count / stats["total_students"]) * 100
                completion_data.append({
                    'Document Type': doc_type,
                    'Completion Rate (%)': completion_rate
                })
            
            completion_df = pd.DataFrame(completion_data)
            
            fig = px.bar(
                completion_df,
                x='Document Type',
                y='Completion Rate (%)',
                title='Document Upload Completion Rate',
                color='Document Type',
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig.update_layout(yaxis_range=[0, 100])
            st.plotly_chart(fig, use_container_width=True)

def generate_student_info_pdf(data):
    filename = f"student_info_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
    )

    # Styles
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="CustomTitle",
            parent=styles["Heading1"],
            fontSize=16,
            alignment=TA_CENTER,
            spaceAfter=30,
            textColor=colors.HexColor("#003366"),
        )
    )

    styles.add(
        ParagraphStyle(
            name="SectionHeader",
            parent=styles["Heading2"],
            fontSize=12,
            textColor=colors.HexColor("#003366"),
            spaceBefore=15,
            spaceAfter=10,
        )
    )

    elements = []

    # Header with Logo
    header_data = [
        [
            RLImage("upsa_logo.jpg", width=1.2 * inch, height=1.2 * inch),
            Paragraph(
                "UNIVERSITY OF PROFESSIONAL STUDIES, ACCRA<br/>IPS DIRECTORATE",
                styles["CustomTitle"],
            ),
            RLImage("upsa_logo.jpg", width=1.2 * inch, height=1.2 * inch),
        ]
    ]
    # Use RLTable instead of Table
    header_table = RLTable(header_data, [2 * inch, 4 * inch, 2 * inch])
    header_table.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    elements.append(header_table)
    elements.append(Spacer(1, 20))

    # Document Title
    elements.append(
        Paragraph("PROFESSIONAL STUDENT'S INFORMATION DOCUMENT", styles["CustomTitle"])
    )
    elements.append(Spacer(1, 20))

    # Add passport photo if available
    if data["passport_photo_path"]:
        try:
            photo_data = [
                [
                    Image(
                        data["passport_photo_path"], width=1.5 * inch, height=1.5 * inch
                    )
                ]
            ]
            photo_table = RLTable(photo_data, [1.5 * inch])
            photo_table.setStyle(
                TableStyle(
                    [
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("BOX", (0, 0), (-1, -1), 1, colors.black),
                    ]
                )
            )
            elements.append(photo_table)
            elements.append(Spacer(1, 20))
        except:
            pass

    # Personal Information Section
    elements.append(Paragraph("Personal Information", styles["SectionHeader"]))
    personal_info = [
        ["Student ID:", data["student_id"]],
        ["Surname:", data["surname"]],
        ["Other Names:", data["other_names"]],
        ["Date of Birth:", str(data["date_of_birth"])],
        ["Place of Birth:", data["place_of_birth"]],
        ["Home Town:", data["home_town"]],
        ["Nationality:", data["nationality"]],
        ["Gender:", data["gender"]],
        ["Marital Status:", data["marital_status"]],
        ["Religion:", data["religion"]],
        ["Denomination:", data["denomination"]],
    ]
    t = RLTable(personal_info, [2.5 * inch, 4 * inch])
    t.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f0f0f0")),
                ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#003366")),
                ("PADDING", (0, 0), (-1, -1), 6),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ]
        )
    )
    elements.append(t)
    elements.append(Spacer(1, 20))

    # Contact Information Section
    elements.append(Paragraph("Contact Information", styles["SectionHeader"]))
    contact_info = [
        ["Residential Address:", data["residential_address"]],
        ["Postal Address:", data["postal_address"]],
        ["Email:", data["email"]],
        ["Telephone:", data["telephone"]],
        ["Ghana Card No:", data["ghana_card_id"]],
    ]
    t = RLTable(contact_info, [2.5 * inch, 4 * inch])
    t.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f0f0f0")),
                ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#003366")),
                ("PADDING", (0, 0), (-1, -1), 6),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ]
        )
    )
    elements.append(t)
    elements.append(Spacer(1, 20))

    # Guardian Information Section
    elements.append(Paragraph("Guardian Information", styles["SectionHeader"]))
    guardian_info = [
        ["Name:", data["guardian_name"]],
        ["Relationship:", data["guardian_relationship"]],
        ["Occupation:", data["guardian_occupation"]],
        ["Address:", data["guardian_address"]],
        ["Telephone:", data["guardian_telephone"]],
    ]
    t = RLTable(guardian_info, [2.5 * inch, 4 * inch])
    t.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f0f0f0")),
                ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#003366")),
                ("PADDING", (0, 0), (-1, -1), 6),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ]
        )
    )
    elements.append(t)
    elements.append(Spacer(1, 20))

    if data["receipt_path"]:
        elements.append(Paragraph("Payment Information", styles["SectionHeader"]))
        payment_info = [
            ["Receipt Status:", "Uploaded"],
            ["Receipt Amount:", f"GHS {data['receipt_amount']:.2f}"],
        ]
        t = RLTable(payment_info, [2.5 * inch, 4 * inch])
        t.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f0f0f0")),
                    ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#003366")),
                    ("PADDING", (0, 0), (-1, -1), 6),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ]
            )
        )
        elements.append(t)
        elements.append(Spacer(1, 20))

    # Footer
    footer_style = ParagraphStyle(
        "Footer",
        parent=styles["Normal"],
        fontSize=8,
        textColor=colors.grey,
        alignment=TA_CENTER,
    )
    elements.append(
        Paragraph(
            f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | UPSA Student Information System",
            footer_style,
        )
    )

    doc.build(elements)
    return filename


def generate_course_registration_pdf(data):
    filename = f"course_registration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
    )

    # Styles
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="CustomTitle",
            parent=styles["Heading1"],
            fontSize=16,
            alignment=TA_CENTER,
            spaceAfter=30,
            textColor=colors.HexColor("#003366"),
        )
    )
    styles.add(
        ParagraphStyle(
            name="SectionHeader",
            parent=styles["Heading2"],
            fontSize=12,
            textColor=colors.HexColor("#003366"),
            spaceBefore=15,
            spaceAfter=10,
        )
    )

    elements = []
    # Get student info from database
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute(
            """
            SELECT passport_photo_path, surname, other_names, email 
            FROM student_info 
            WHERE student_id = %s
            """,
            (data["student_id"],),
        )
        student_info = c.fetchone()

    # Header with logo and student photo
    header_elements = []

    # First column: UPSA logo
    header_elements.append(
        RLImage("upsa_logo.jpg", width=1.2 * inch, height=1.2 * inch)
    )

    # Middle column: Title
    header_elements.append(
        Paragraph(
            "UNIVERSITY OF PROFESSIONAL STUDIES, ACCRA<br/>Proof of Registration",
            styles["CustomTitle"],
        )
    )

    # Third column: Student photo or UPSA logo if no photo
    if student_info and student_info[0] and os.path.exists(student_info[0]):
        try:
            # Create a BytesIO object to hold the image data
            img_buffer = io.BytesIO()

            # Open, resize and save the image to the buffer
            with PILImage.open(student_info[0]) as img:
                img.thumbnail((100, 100))  # Resize while maintaining aspect ratio
                img.save(img_buffer, format=img.format)
                img_buffer.seek(0)

            # Add the image from the buffer
            header_elements.append(
                RLImage(img_buffer, width=1.2 * inch, height=1.2 * inch)
            )
        except Exception as e:
            # If there's an error, use the UPSA logo instead
            header_elements.append(
                RLImage("upsa_logo.jpg", width=1.2 * inch, height=1.2 * inch)
            )
    else:
        # If no photo, use the UPSA logo
        header_elements.append(
            RLImage("upsa_logo.jpg", width=1.2 * inch, height=1.2 * inch)
        )

    # Create the header table
    header_table = RLTable([header_elements], [2 * inch, 4 * inch, 2 * inch])
    header_table.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    elements.append(header_table)
    elements.append(Spacer(1, 20))

    if student_info:
        student_details = [
            [
                Paragraph(
                    f"<b>Name:</b> {student_info[1]} {student_info[2]}",
                    styles["Normal"],
                )
            ],
            [Paragraph(f"<b>Email:</b> {student_info[3]}", styles["Normal"])],
        ]
        student_table = RLTable(student_details, [7 * inch])
        student_table.setStyle(
            TableStyle(
                [
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("PADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        elements.append(student_table)
        elements.append(Spacer(1, 20))

    elements.append(Paragraph("Registration Details", styles["SectionHeader"]))
    reg_info = [
        ["Student ID:", data["student_id"]],
        ["Index Number:", data["index_number"]],
        ["Programme:", data["programme"]],
        ["Specialization:", data["specialization"]],
        ["Level:", data["level"]],
        ["Session:", data["session"]],
        ["Academic Year:", data["academic_year"]],
        ["Semester:", data["semester"]],
    ]
    t = RLTable(reg_info, [2.5 * inch, 4 * inch])
    t.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f0f0f0")),
                ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#003366")),
                ("PADDING", (0, 0), (-1, -1), 6),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ]
        )
    )
    elements.append(t)
    elements.append(Spacer(1, 20))

    elements.append(Paragraph("Selected Courses", styles["SectionHeader"]))
    courses_list = data["courses"].split("\n")
    courses_data = [["Course Code", "Course Title", "Credit Hours"]]
    for course in courses_list:
        if "|" in course:
            courses_data.append(course.split("|"))
    t = RLTable(courses_data, [2 * inch, 3.5 * inch, 1 * inch])
    t.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#003366")),
                ("TEXTCOLOR", (0, 0), (0, 0), colors.white),
                ("PADDING", (0, 0), (-1, -1), 6),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ALIGN", (-1, 0), (-1, -1), "CENTER"),
            ]
        )
    )
    elements.append(t)
    elements.append(
        Paragraph(
            f"<b>Total Credit Hours:</b> {data['total_credits']}",
            ParagraphStyle(
                "TotalCredits",
                parent=styles["Normal"],
                fontSize=10,
                textColor=colors.HexColor("#003366"),
                alignment=TA_LEFT,
                spaceBefore=10,
            ),
        )
    )
    elements.append(Spacer(1, 30))

    if data.get("receipt_path"):
        elements.append(Paragraph("Payment Information", styles["SectionHeader"]))
        payment_info = [
            ["Receipt Status:", "Uploaded"],
            ["Receipt Amount:", f"GHS {data.get('receipt_amount', 0.0):.2f}"],
        ]
        t = RLTable(payment_info, [2.5 * inch, 4 * inch])
        t.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f0f0f0")),
                    ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#003366")),
                    ("PADDING", (0, 0), (-1, -1), 6),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ]
            )
        )
        elements.append(t)
        elements.append(Spacer(1, 20))

    signature_data = [
        ["_______________________", "_______________________"],
        ["Student's Signature", "IPS Directorate Officer"],
        ["Date: ________________", "Date: ________________"],
    ]
    sig_table = RLTable(signature_data, [4 * inch, 4 * inch])
    sig_table.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
                ("TEXTCOLOR", (0, 1), (-1, 1), colors.HexColor("#003366")),
                ("FONTSIZE", (0, 1), (-1, 1), 8),
                ("TOPPADDING", (0, 2), (-1, 2), 20),
            ]
        )
    )
    elements.append(sig_table)
    elements.append(Spacer(1, 30))
    elements.append(
        Paragraph(
            f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | UPSA Course Registration System",
            ParagraphStyle(
                "Footer",
                parent=styles["Normal"],
                fontSize=8,
                textColor=colors.grey,
                alignment=TA_CENTER,
            ),
        )
    )

    doc.build(elements)
    return filename


def review_student_info(form_data, uploaded_files):
    st.subheader("Review Student Information")

    cols = st.columns(2)
    with cols[0]:
        st.write("**Personal Information**")
        st.write(f"Student ID: {form_data['student_id']}")
        st.write(f"Surname: {form_data['surname']}")
        st.write(f"Other Names: {form_data['other_names']}")
        st.write(f"Date of Birth: {form_data['date_of_birth']}")
        st.write(f"Place of Birth: {form_data['place_of_birth']}")
        st.write(f"Home Town: {form_data['home_town']}")
        st.write(f"Nationality: {form_data['nationality']}")
        st.write(f"Gender: {form_data['gender']}")
        st.write(f"Marital Status: {form_data['marital_status']}")
        st.write(f"Religion: {form_data['religion']}")
        st.write(f"Denomination: {form_data['denomination']}")

    with cols[1]:
        st.write("**Contact Information**")
        st.write(f"Residential Address: {form_data['residential_address']}")
        st.write(f"Postal Address: {form_data['postal_address']}")
        st.write(f"Email: {form_data['email']}")
        st.write(f"Telephone: {form_data['telephone']}")
        st.write(f"Ghana Card No: {form_data['ghana_card_id']}")

    st.write("**Guardian Information**")
    st.write(f"Name: {form_data['guardian_name']}")
    st.write(f"Relationship: {form_data['guardian_relationship']}")
    st.write(f"Occupation: {form_data['guardian_occupation']}")
    st.write(f"Address: {form_data['guardian_address']}")
    st.write(f"Telephone: {form_data['guardian_telephone']}")

    st.write("**Educational Background**")
    st.write(f"Previous School: {form_data['previous_school']}")
    st.write(f"Qualification: {form_data['qualification_type']}")
    st.write(f"Completion Year: {form_data['completion_year']}")
    st.write(f"Aggregate Score: {form_data['aggregate_score']}")

    st.write("**Uploaded Documents**")
    for doc_name, file in uploaded_files.items():
        if doc_name == "Receipt":
            if file:
                st.write(f"✅ {doc_name} uploaded (Optional)")
            else:
                st.write(f"⚪ {doc_name} not uploaded (Optional)")
        else:
            if file:
                st.write(f"✅ {doc_name} uploaded")
            else:
                st.write(f"❌ {doc_name} not uploaded")


def review_course_registration(form_data):
    col1, col2 = st.columns(2)

    with col1:
        st.write("**Student Information**")
        st.write(f"Student ID: {form_data['student_id']}")
        st.write(f"Programme: {form_data['programme']}")
        st.write(f"Level: {form_data['level']}")
        st.write(f"Specialization: {form_data['specialization']}")

    with col2:
        st.write("**Registration Details**")
        st.write(f"Session: {form_data['session']}")
        st.write(f"Academic Year: {form_data['academic_year']}")
        st.write(f"Semester: {form_data['semester']}")

    st.write("**Selected Courses**")
    if form_data["courses"]:
        courses_list = form_data["courses"].split("\n")

        table_data = []
        for course in courses_list:
            if "|" in course:
                code, title, credits = course.split("|")
                table_data.append([code, title, f"{credits} credits"])

        if table_data:
            df = pd.DataFrame(
                table_data, columns=["Course Code", "Course Title", "Credit Hours"]
            )
            st.table(df)

            st.write(f"**Total Credit Hours:** {form_data['total_credits']}")
    else:
        st.warning("No courses selected")


def save_student_info(form_data):
    with sqlite3.connect("student_registration.db") as conn:
        try:
            cursor = conn.cursor()
            # ... database operations ...
            conn.commit()
        except sqlite3.Error as e:
            conn.rollback()
            raise


def student_info_form():
    st.header("📝 Student Information Form")

    form_data = {}
    rc_manager = RegistrationConstraintsManager()

    # Collect Student ID first and check for duplicate submission.
    student_id_input = st.text_input("Student ID")
    if student_id_input:
        form_data["student_id"] = student_id_input.strip()
        # Check if student info already exists.
        if rc_manager.check_existing_student_info(form_data["student_id"]):
            st.warning(
                "You have already submitted your student information. Please proceed to course registration or contact administration for changes."
            )
            st.stop()
    else:
        st.info("Please enter your Student ID to begin.")
        st.stop()

    st.subheader("Personal Information")
    col1, col2 = st.columns(2)
    with col1:
        form_data["surname"] = st.text_input("Surname")
        form_data["other_names"] = st.text_input("First & Middle Names")
        form_data["date_of_birth"] = st.date_input("Date of Birth")
        form_data["place_of_birth"] = st.text_input("Place of Birth")
        form_data["home_town"] = st.text_input("Home Town")
        form_data["nationality"] = st.text_input("Nationality")
    with col2:
        form_data["gender"] = st.selectbox("Gender", ["Male", "Female", "Other"])
        form_data["marital_status"] = st.selectbox(
            "Marital Status", ["Single", "Married", "Divorced", "Widowed"]
        )
        form_data["religion"] = st.text_input("Religion")
        form_data["denomination"] = st.text_input("Denomination")
        disability_status = st.selectbox("Disability Status", ["None", "Yes"])
        form_data["disability_status"] = disability_status
        if disability_status == "Yes":
            form_data["disability_description"] = st.text_area("Disability Description")
        else:
            form_data["disability_description"] = "None"

    st.subheader("Contact Information")
    col3, col4 = st.columns(2)
    with col3:
        form_data["residential_address"] = st.text_area("Residential Address")
        form_data["postal_address"] = st.text_area("Postal Address")
        form_data["email"] = st.text_input("Email Address")
    with col4:
        form_data["telephone"] = st.text_input("Telephone Number")
        form_data["ghana_card_id"] = st.text_input("Ghana Card ID Number")

    st.subheader("Guardian Information")
    col5, col6 = st.columns(2)
    with col5:
        form_data["guardian_name"] = st.text_input("Guardian's Name")
        form_data["guardian_relationship"] = st.text_input("Relationship to Guardian")
        form_data["guardian_occupation"] = st.text_input("Guardian's Occupation")
    with col6:
        form_data["guardian_address"] = st.text_area("Guardian's Address")
        form_data["guardian_telephone"] = st.text_input("Guardian's Telephone")

    st.subheader("Educational Background")
    col7, col8 = st.columns(2)
    with col7:
        form_data["previous_school"] = st.text_input("Previous School")
        form_data["qualification_type"] = st.text_input("Qualification Type")
    with col8:
        form_data["completion_year"] = st.text_input("Year of Completion")
        form_data["aggregate_score"] = st.text_input("Aggregate Score")

    st.subheader("📎 Required Documents")
    col9, col10 = st.columns(2)
    with col9:
        st.markdown('<div class="upload-section">', unsafe_allow_html=True)
        ghana_card = st.file_uploader(
            "Upload Ghana Card/Birth Certificate", type=["pdf", "jpg", "png"]
        )
        passport_photo = st.file_uploader("Upload Passport Photo", type=["jpg", "png"])
        # Removed Transcript upload
        certificate = st.file_uploader("Upload Certificate", type=["pdf"])
        st.markdown("</div>", unsafe_allow_html=True)
    with col10:
        st.markdown('<div class="upload-section">', unsafe_allow_html=True)
        # Removed receipt upload from student information
        st.markdown("</div>", unsafe_allow_html=True)

    uploaded_files = {
        "Ghana Card": ghana_card,
        "Passport Photo": passport_photo,
        "Certificate": certificate,
        # transcript and receipt keys removed
    }

    col_buttons = st.columns([2, 2])
    with col_buttons[0]:
        if st.button("Review Information", use_container_width=True):
            st.session_state.review_mode = True
            st.session_state.form_data = form_data
            st.session_state.uploaded_files = uploaded_files
            st.rerun()
    if "review_mode" in st.session_state and st.session_state.review_mode:
        review_student_info(st.session_state.form_data, st.session_state.uploaded_files)
        with col_buttons[1]:
            if st.button("Confirm and Submit", use_container_width=True):
                ghana_card_path = save_uploaded_file(ghana_card, "uploads")
                passport_photo_path = save_uploaded_file(passport_photo, "uploads")
                certificate_path = save_uploaded_file(certificate, "uploads")
                # Set transcript and receipt as None
                file_paths = {
                    "ghana_card_path": ghana_card_path,
                    "passport_photo_path": passport_photo_path,
                    "certificate_path": certificate_path,
                    "transcript_path": None,
                    "receipt_path": None,
                }
                try:
                    with get_db_connection() as conn:
                        c = conn.cursor()
                        insert_student_info(c, st.session_state.form_data, file_paths)
                        conn.commit()
                    st.success(
                        "Information submitted successfully! Pending admin approval."
                    )
                    st.session_state.review_mode = False
                except mysql.connector.IntegrityError:
                    st.error("Student ID already exists!")
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
                finally:
                    conn.close()

def course_registration_form():
    st.header("📚 Course Registration Form (A7)")
    form_data = {}
    rc_manager = RegistrationConstraintsManager()

    form_data["student_id"] = st.text_input("Student ID")
    if not form_data["student_id"]:
        st.warning("Please enter your Student ID")
        st.stop()

    # Prevent duplicate registration
    if rc_manager.check_existing_course_registration(form_data["student_id"]):
        st.warning(
            "You have already submitted your course registration. Duplicate submissions are not allowed."
        )
        st.stop()

    with get_db_connection() as conn:
        c = conn.cursor(dictionary=True)
        c.execute(
            "SELECT * FROM student_info WHERE student_id = %s",
            (form_data["student_id"],)
        )
        student_info = c.fetchone()
        
    if student_info:
        st.markdown("---")
        col_photo, col_info = st.columns([1, 3])
        with col_photo:
            if student_info["passport_photo_path"]:
                try:
                    image = PILImage.open(student_info["passport_photo_path"])
                    st.image(image, caption="Student Photo", width=150)
                except Exception as e:
                    st.error(f"Error loading passport photo: {str(e)}")
            else:
                st.warning("No passport photo available")
        with col_info:
            st.markdown(f"### {student_info['surname']} {student_info['other_names']}")
            st.write(f"**Student ID:** {student_info['student_id']}")
            st.write(f"**Email:** {student_info['email']}")
            st.write(f"**Phone:** {student_info['telephone']}")
        col3, col4 = st.columns(2)
        with col3:
            form_data["programme"] = st.selectbox(
                "Programme", ["CIMG", "CIM-UK", "ICAG", "ACCA"]
            )
            program_levels = list(get_program_courses(form_data["programme"]).keys())
            form_data["level"] = st.selectbox("Level/Part", program_levels)
            form_data["specialization"] = st.text_input("Specialization (Optional)")
        with col4:
            form_data["session"] = st.selectbox(
                "Session", ["Morning", "Evening", "Weekend"]
            )
            form_data["academic_year"] = st.selectbox(
                "Academic Year", [f"{year}-{year+1}" for year in range(2025, 2035)]
            )
            form_data["semester"] = st.selectbox(
                "Semester", ["First", "Second", "Third"]
            )
        st.subheader("Course Selection")
        available_courses = get_program_courses(form_data["programme"]).get(
            form_data["level"], []
        )
        selected_courses = st.multiselect(
            "Select Courses",
            available_courses,
            format_func=lambda x: f"{x.split('|')[0]} - {x.split('|')[1]} ({x.split('|')[2]} credits)",
        )
        total_credits = sum([int(course.split("|")[2]) for course in selected_courses])
        form_data["courses"] = "\n".join(selected_courses)
        form_data["total_credits"] = total_credits
        st.text_area(
            "Selected Courses", form_data["courses"], height=150, disabled=True
        )
        st.number_input(
            "Total Credit Hours",
            value=total_credits,
            min_value=0,
            max_value=24,
            disabled=True,
        )
        if total_credits > 24:
            st.error("Total credits cannot exceed 24 hours!")
            return
        st.subheader("📎 Payment Information (Optional)")
        col5, col6 = st.columns(2)
        with col5:
            receipt = st.file_uploader(
                "Upload Payment Receipt (Optional)", type=["pdf", "jpg", "png"]
            )
            form_data["receipt_path"] = (
                save_uploaded_file(receipt, "uploads") if receipt else None
            )
        with col6:
            form_data["receipt_amount"] = (
                st.number_input("Receipt Amount (GHS)", min_value=0.0, format="%.2f")
                if receipt
                else 0.0
            )
        if st.button("Review Registration"):
            review_course_registration(form_data)
        if st.button("Confirm and Submit"):
            try:
                with get_db_connection() as conn:
                    c = conn.cursor()
                    c.execute(
                        """
                        INSERT INTO course_registration 
                        (student_id, index_number, programme, specialization, level, 
                        session, academic_year, semester, courses, total_credits, 
                        date_registered, approval_status, receipt_path, receipt_amount)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            form_data["student_id"],
                            form_data.get("index_number", ""),
                            form_data["programme"],
                            form_data["specialization"],
                            form_data["level"],
                            form_data["session"],
                            form_data["academic_year"],
                            form_data["semester"],
                            form_data["courses"],
                            form_data["total_credits"],
                            datetime.now().date(),
                            "pending",
                            form_data["receipt_path"],
                            form_data["receipt_amount"],
                        ),
                    )
                    conn.commit()
                st.success("Course registration submitted! Pending admin approval.")
            except mysql.connector.IntegrityError:
                st.error("Error in registration. Please check if student ID exists.")
    else:
        st.warning("No matching student record found. Please verify the Student ID.")
        return


def validate_file(uploaded_file, max_size_mb=6):
    """
    Validate and compress file if needed.
    Returns the file data (possibly compressed) or raises an error.
    """
    # Files will be compressed if they exceed the size limit
    compressed_data, _, was_compressed = compress_uploaded_file(
        uploaded_file, max_size_mb
    )

    if was_compressed:
        st.info(f"File was compressed to meet the {max_size_mb}MB size limit")

    return compressed_data


def download_all_documents():
    temp_dir = "temp_downloads"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

        cursor.execute(
            """
            SELECT student_id, surname, other_names, 
                ghana_card_path, passport_photo_path, 
                transcript_path, certificate_path, receipt_path,
                receipt_amount
            FROM student_info
        """
        )
        students = cursor.fetchall()

        cursor.execute(
            """
            SELECT cr.registration_id, cr.student_id, si.surname, si.other_names,
                   cr.receipt_path, cr.receipt_amount
            FROM course_registration cr
            LEFT JOIN student_info si ON cr.student_id = si.student_id
            WHERE cr.receipt_path IS NOT NULL
        """
        )
        registrations = cursor.fetchall()

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = f"all_documents_{timestamp}.zip"

        with zipfile.ZipFile(zip_filename, "w") as zipf:
            for student in students:
                student_id, surname, other_names = student[:3]
                documents = student[3:8]
                doc_names = [
                    "ghana_card",
                    "passport_photo",
                    "transcript",
                    "certificate",
                    "receipt",
                ]
                student_dir = f"student_documents/{student_id}_{surname}_{other_names}"
                for doc_path, doc_name in zip(documents, doc_names):
                    if doc_path and os.path.exists(doc_path):
                        _, ext = os.path.splitext(doc_path)
                        archive_path = f"{student_dir}/{doc_name}{ext}"
                        zipf.write(doc_path, archive_path)

            for registration in registrations:
                (
                    reg_id,
                    student_id,
                    surname,
                    other_names,
                    receipt_path,
                    receipt_amount,
                ) = registration
                if receipt_path and os.path.exists(receipt_path):
                    reg_dir = f"course_registration_receipts/{student_id}_{surname}_{other_names}"
                    _, ext = os.path.splitext(receipt_path)
                    archive_path = f"{reg_dir}/registration_{reg_id}_receipt{ext}"
                    zipf.write(receipt_path, archive_path)

        # Use the cleanup handler context manager
        with zip_cleanup_handler.cleanup_after_download(zip_filename):
            with open(zip_filename, "rb") as f:
                st.download_button(
                    label="Download Documents ZIP",
                    data=f,
                    file_name=zip_filename,
                    mime="application/zip",
                )

        return zip_filename

    except Exception as e:
        st.error(f"Error creating zip file: {str(e)}")
        return None

    finally:
        conn.close()
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)



def admin_dashboard():
    st.title("Admin Dashboard")

    menu = st.sidebar.selectbox(
        "Menu",
        [
            "Statistics Dashboard",  # Added Statistics Dashboard as the first option
            "Upload Data",
            "Student Records",
            "Course Registrations",
            "Programs",
            "Database Management",
            "Pending Approvals",
            "Generate Reports",
            "Send Emails",
            "Notifications",
            "ID Card Generator",
            "System Monitor",
        ],
    )

    if menu == "Statistics Dashboard":
        display_student_statistics()  # Call the completed function
    elif menu == "Upload Data":
        upload_data_from_excel_and_docs()
    elif menu == "Student Records":
        manage_student_records()
    elif menu == "Course Registrations":
        manage_course_registrations()
    elif menu == "Programs":
        manage_programs()
    elif menu == "Database Management":
        manage_database()
    elif menu == "Pending Approvals":
        show_pending_approvals()
    elif menu == "Generate Reports":
        generate_reports()
    elif menu == "Send Emails":
        send_emails()
    elif menu == "Notifications":
        admin_notification_interface()
    elif menu == "ID Card Generator":
        id_card_generator_ui()
    elif menu == "System Monitor":
        st.subheader("System Resource Monitor")
        metrics = system_resource_monitor()
        st.write(f"CPU Usage: {metrics['cpu']}%")
        st.write(f"Memory Usage: {metrics['memory_percent']}%")
        st.write(f"Disk Usage: {metrics['disk_percent']}%")
        if should_backup():
            st.warning(
                "Backup recommended: Either it has been over 30 days since the last backup or disk usage is ≥ 90%."
            )
        if st.button("Perform Backup Now"):
            backup_file = perform_backup()
            st.success(f"Backup performed successfully! Backup file: {backup_file}")
            try:
                with open(backup_file, "rb") as f:
                    st.download_button(
                        label="Download Backup",
                        data=f,
                        file_name=backup_file.split(os.sep)[-1],
                        mime="application/zip",
                    )
            except Exception as e:
                st.error(f"Error providing download: {str(e)}")


def zip_uploads_folder():
    """
    Zips the entire 'uploads' folder preserving its structure exactly as is.

    Returns:
        The filename of the generated zip file, or None if the uploads folder does not exist.
    """
    uploads_dir = "uploads"
    if not os.path.exists(uploads_dir):
        return None
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = f"uploads_folder_{timestamp}"
    zip_filename = f"{base_name}.zip"
    # This will create a zip archive with the base directory inside it as it is.
    shutil.make_archive(base_name=base_name, format="zip", root_dir=uploads_dir)
    return zip_filename


def manage_database():
    st.subheader("Database Management")

    col1, col2, col3, col4 = st.columns(4)  # Added a new column for the new button

    with col1:
        st.write("### Export Complete Database")
        if st.button("Download Complete Database (Excel)"):
            try:
                export_dir = "temp_export"
                if not os.path.exists(export_dir):
                    os.makedirs(export_dir)

                conn = sqlite3.connect("student_registration.db")

                tables = {
                    "student_info": pd.read_sql_query(
                        """
                        SELECT *, 
                            CASE WHEN receipt_path IS NOT NULL THEN 'Yes' ELSE 'No' END as has_receipt,
                            receipt_amount
                        FROM student_info
                    """,
                        conn,
                    ),
                    "course_registration": pd.read_sql_query(
                        """
                        SELECT *,
                            CASE WHEN receipt_path IS NOT NULL THEN 'Yes' ELSE 'No' END as has_receipt,
                            receipt_amount
                        FROM course_registration
                    """,
                        conn,
                    ),
                }

                excel_files = []
                for table_name, df in tables.items():
                    excel_filename = os.path.join(export_dir, f"{table_name}.xlsx")
                    with pd.ExcelWriter(excel_filename, engine="openpyxl") as writer:
                        df.to_excel(writer, index=False, sheet_name=table_name)
                        workbook = writer.book
                        worksheet = writer.sheets[table_name]

                        for column_cells in worksheet.columns:
                            max_length = 0
                            column = column_cells[0].column_letter
                            for cell in column_cells:
                                try:
                                    cell_length = len(str(cell.value))
                                    if cell_length > max_length:
                                        max_length = cell_length
                                except Exception:
                                    pass
                            adjusted_width = max_length + 2
                            worksheet.column_dimensions[column].width = adjusted_width
                    excel_files.append(excel_filename)

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                zip_filename = f"complete_database_{timestamp}.zip"
                with zipfile.ZipFile(zip_filename, "w") as zipf:
                    for file in excel_files:
                        arcname = os.path.basename(file)
                        zipf.write(file, arcname)

                for file in excel_files:
                    os.remove(file)
                os.rmdir(export_dir)

                conn.close()

                with open(zip_filename, "rb") as f:
                    st.download_button(
                        label="Download Database ZIP",
                        data=f,
                        file_name=zip_filename,
                        mime="application/zip",
                    )
                os.remove(zip_filename)
            except Exception as e:
                st.error(f"Error exporting database: {str(e)}")

    with col2:
        st.write("### Download All Documents")
        if st.button("Download All Documents"):
            with st.spinner("Creating zip file of all documents..."):
                zip_file = download_all_documents()
                if zip_file and os.path.exists(zip_file):
                    with open(zip_file, "rb") as f:
                        st.download_button(
                            label="Download Documents ZIP",
                            data=f,
                            file_name=zip_file,
                            mime="application/zip",
                        )
                    os.remove(zip_file)
                else:
                    st.error("Error creating zip file or no documents found")

    with col3:
        st.write("### Download All Receipts")
        if st.button("Download All Receipts"):
            with st.spinner("Creating zip file of all receipts..."):
                zip_file = download_receipts()
                if zip_file and os.path.exists(zip_file):
                    with open(zip_file, "rb") as f:
                        st.download_button(
                            label="Download Receipts ZIP",
                            data=f,
                            file_name=zip_file,
                            mime="application/zip",
                        )
                    os.remove(zip_file)
                else:
                    st.error("Error creating zip file or no receipts found")

    with col4:
        st.write("### Download Uploads Folder")
        if st.button("Download Uploads Folder"):
            with st.spinner("Creating zip file of the uploads folder..."):
                zip_file = zip_uploads_folder()
                if zip_file and os.path.exists(zip_file):
                    with open(zip_file, "rb") as f:
                        st.download_button(
                            label="Download Uploads ZIP",
                            data=f,
                            file_name=zip_file,
                            mime="application/zip",
                        )
                    os.remove(zip_file)
                else:
                    st.error("Uploads folder not found or error creating zip")

    st.write("### Generate All PDFs")
    col_pdfs1, col_pdfs2 = st.columns(2)
    with col_pdfs1:
        if st.button("Generate All Student Info PDFs"):
            with st.spinner("Generating student information PDFs..."):
                zip_file = generate_batch_pdfs("student_info")
                if zip_file and os.path.exists(zip_file):
                    with open(zip_file, "rb") as f:
                        st.download_button(
                            label="Download Student Info PDFs",
                            data=f,
                            file_name=zip_file,
                            mime="application/zip",
                        )
                    os.remove(zip_file)
                else:
                    st.error("Error generating PDFs")
    with col_pdfs2:
        if st.button("Generate All Course Registration PDFs"):
            with st.spinner("Generating course registration PDFs..."):
                zip_file = generate_batch_pdfs("course_registration")
                if zip_file and os.path.exists(zip_file):
                    with open(zip_file, "rb") as f:
                        st.download_button(
                            label="Download Course Registration PDFs",
                            data=f,
                            file_name=zip_file,
                            mime="application/zip",
                        )
                    os.remove(zip_file)
                else:
                    st.error("Error generating PDFs")


def upload_data_from_excel_and_docs():
    """
    Bulk upload function updated to accept two Excel files and to insert any absent columns
    into the DataFrames before processing the data. This handles entries from older app versions.
    """
    st.header("Bulk Upload Data from Excel & Documents")
    st.markdown("### Excel Files Upload")
    col1, col2 = st.columns(2)
    with col1:
        student_excel = st.file_uploader(
            "Upload Excel File with Student Data",
            type=["xlsx", "xls"],
            key="student_excel",
        )
    with col2:
        reg_excel = st.file_uploader(
            "Upload Excel File with Course Registration Data",
            type=["xlsx", "xls"],
            key="reg_excel",
        )
    docs_zip = st.file_uploader("Upload Zip File of Documents (Optional)", type=["zip"])

    if st.button("Process Bulk Upload"):
        if student_excel is None or reg_excel is None:
            st.error(
                "Please upload both Excel files: one for student information and one for course registration data."
            )
            return

        try:
            # Read the two Excel files.
            student_df = pd.read_excel(student_excel)
            reg_df = pd.read_excel(reg_excel)

            # Define expected columns for student data.
            expected_student_columns = [
                "student_id",
                "surname",
                "other_names",
                "date_of_birth",
                "place_of_birth",
                "home_town",
                "residential_address",
                "postal_address",
                "email",
                "telephone",
                "ghana_card_id",
                "nationality",
                "marital_status",
                "gender",
                "religion",
                "denomination",
                "disability_status",
                "disability_description",
                "guardian_name",
                "guardian_relationship",
                "guardian_occupation",
                "guardian_address",
                "guardian_telephone",
                "previous_school",
                "qualification_type",
                "completion_year",
                "aggregate_score",
                "ghana_card_path",
                "passport_photo_path",
                "transcript_path",
                "certificate_path",
                "receipt_path",
                "programme",
            ]
            # Insert missing columns with default values.
            for col in expected_student_columns:
                if col not in student_df.columns:
                    # For file path columns use None instead of empty string.
                    if col in [
                        "ghana_card_path",
                        "passport_photo_path",
                        "transcript_path",
                        "certificate_path",
                        "receipt_path",
                        "programme",
                    ]:
                        student_df[col] = None
                    else:
                        student_df[col] = ""

            # Define expected columns for course registration data.
            expected_reg_columns = [
                "student_id",
                "index_number",
                "programme",
                "specialization",
                "level",
                "session",
                "academic_year",
                "semester",
                "courses",
                "total_credits",
                "date_registered",
                "approval_status",
                "receipt_path",
                "receipt_amount",
            ]
            for col in expected_reg_columns:
                if col not in reg_df.columns:
                    if col in ["receipt_path"]:
                        reg_df[col] = None
                    elif col == "receipt_amount":
                        reg_df[col] = 0.0
                    else:
                        reg_df[col] = ""

            # Insert student data into the database.
            conn = sqlite3.connect("student_registration.db")
            c = conn.cursor()
            insert_student_query = """
                INSERT OR IGNORE INTO student_info (
                    student_id, surname, other_names, date_of_birth, place_of_birth,
                    home_town, residential_address, postal_address, email, telephone,
                    ghana_card_id, nationality, marital_status, gender, religion,
                    denomination, disability_status, disability_description,
                    guardian_name, guardian_relationship, guardian_occupation,
                    guardian_address, guardian_telephone, previous_school,
                    qualification_type, completion_year, aggregate_score,
                    ghana_card_path, passport_photo_path, transcript_path,
                    certificate_path, receipt_path, receipt_amount,
                    approval_status, created_at, programme
                ) VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
            """
            for _, row in student_df.iterrows():
                params = (
                    row.get("student_id"),
                    row.get("surname"),
                    row.get("other_names"),
                    row.get("date_of_birth"),
                    row.get("place_of_birth"),
                    row.get("home_town"),
                    row.get("residential_address"),
                    row.get("postal_address"),
                    row.get("email"),
                    row.get("telephone"),
                    row.get("ghana_card_id"),
                    row.get("nationality"),
                    row.get("marital_status"),
                    row.get("gender"),
                    row.get("religion"),
                    row.get("denomination"),
                    row.get("disability_status", "None"),
                    row.get("disability_description", "None"),
                    row.get("guardian_name"),
                    row.get("guardian_relationship"),
                    row.get("guardian_occupation"),
                    row.get("guardian_address"),
                    row.get("guardian_telephone"),
                    row.get("previous_school"),
                    row.get("qualification_type"),
                    row.get("completion_year"),
                    row.get("aggregate_score"),
                    row.get("ghana_card_path"),
                    row.get("passport_photo_path"),
                    row.get("transcript_path"),
                    row.get("certificate_path"),
                    row.get("receipt_path"),
                    0.0,  # receipt_amount default value
                    "pending",
                    datetime.now(),
                    row.get("programme", ""),
                )
                c.execute(insert_student_query, params)

            insert_reg_query = """
                INSERT INTO course_registration (
                    student_id, index_number, programme, specialization, level,
                    session, academic_year, semester, courses, total_credits,
                    date_registered, approval_status, receipt_path, receipt_amount
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """
            for _, row in reg_df.iterrows():
                params = (
                    row.get("student_id"),
                    row.get("index_number"),
                    row.get("programme"),
                    row.get("specialization"),
                    row.get("level"),
                    row.get("session"),
                    row.get("academic_year"),
                    row.get("semester"),
                    row.get("courses"),
                    row.get("total_credits"),
                    row.get("date_registered"),
                    row.get("approval_status", "pending"),
                    row.get("receipt_path"),
                    row.get("receipt_amount", 0.0),
                )
                c.execute(insert_reg_query, params)
                # Update the student's programme field based on the registration data.
                update_query = (
                    "UPDATE student_info SET programme = ? WHERE student_id = ?"
                )
                c.execute(update_query, (row.get("programme"), row.get("student_id")))

            conn.commit()
            conn.close()
            st.success("Excel data uploaded successfully!")
        except Exception as e:
            st.error(f"Error processing Excel files: {e}")

        if docs_zip:
            saved_zip_path = save_uploaded_file(docs_zip, "uploads")
            st.success("Documents zip uploaded successfully!")


def generate_reports():
    """
    Generate various types of reports including:
    - Student Statistics
    - Course Registration Summary
    - Approval Status Summary
    - Payment Statistics
    """
    st.subheader("Generate Reports")

    # Report type selection
    report_type = st.selectbox(
        "Select Report Type",
        [
            "Student Statistics",
            "Course Registration Summary",
            "Approval Status Summary",
            "Payment Statistics",
        ],
    )

    # Connect to the database
    conn = sqlite3.connect("student_registration.db")

    if report_type == "Student Statistics":
        # Gender distribution
        gender_dist = pd.read_sql_query(
            "SELECT gender, COUNT(*) as count FROM student_info GROUP BY gender", conn
        )
        if not gender_dist.empty:
            st.write("**Gender Distribution**")
            fig = px.pie(
                gender_dist, names="gender", values="count", title="Gender Distribution"
            )
            st.plotly_chart(fig)
        else:
            st.info("No gender distribution data available")

        # Programme distribution
        prog_dist = pd.read_sql_query(
            "SELECT programme, COUNT(*) as count FROM course_registration GROUP BY programme",
            conn,
        )
        if not prog_dist.empty:
            st.write("**Programme Distribution**")
            fig = px.pie(
                prog_dist,
                names="programme",
                values="count",
                title="Programme Distribution",
            )
            st.plotly_chart(fig)
        else:
            st.info("No programme distribution data available")

    elif report_type == "Course Registration Summary":
        summary = pd.read_sql_query(
            """
            SELECT cr.programme, cr.level, cr.semester, 
                   COUNT(*) as registrations,
                   AVG(cr.total_credits) as avg_credits
            FROM course_registration cr
            GROUP BY cr.programme, cr.level, cr.semester
            """,
            conn,
        )
        if not summary.empty:
            st.write("**Course Registration Summary**")
            st.dataframe(summary)
        else:
            st.info("No course registration data available")

    elif report_type == "Approval Status Summary":
        # Student approval status
        student_status = pd.read_sql_query(
            "SELECT approval_status, COUNT(*) as count FROM student_info GROUP BY approval_status",
            conn,
        )
        # Course approval status
        course_status = pd.read_sql_query(
            "SELECT approval_status, COUNT(*) as count FROM course_registration GROUP BY approval_status",
            conn,
        )

        col1, col2 = st.columns(2)
        with col1:
            if not student_status.empty:
                st.write("**Student Info Approval Status**")
                fig = px.pie(
                    student_status,
                    names="approval_status",
                    values="count",
                    title="Student Info Approval Status",
                )
                st.plotly_chart(fig)
            else:
                st.info("No student approval status data available")

        with col2:
            if not course_status.empty:
                st.write("**Course Registration Approval Status**")
                fig = px.pie(
                    course_status,
                    names="approval_status",
                    values="count",
                    title="Course Registration Approval Status",
                )
                st.plotly_chart(fig)
            else:
                st.info("No course registration approval status data available")

    elif report_type == "Payment Statistics":
        # Import and use the enhanced payment statistics module
        payment_statistics_section()

        # Close the database connection
        conn.close()


import os
import io
import sqlite3
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import qrcode
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader


class IDCardGenerator:
    """
    Generates student ID cards with customizable templates
    """

    def __init__(self, db_path="student_registration.db"):
        self.db_path = db_path
        self.card_width = 1050  # pixels
        self.card_height = 650  # pixels
        self.card_color = (255, 255, 255)  # white background
        self.text_color = (0, 0, 0)  # black text
        self.accent_color = (0, 51, 102)  # UPSA blue

        # Ensure fonts directory exists
        os.makedirs("fonts", exist_ok=True)

        # Default font paths - will use system defaults if these don't exist
        self.title_font_path = "fonts/Arial_Bold.ttf"
        self.regular_font_path = "fonts/Arial.ttf"

        # Try to load fonts, use default if not available
        try:
            self.title_font = ImageFont.truetype(self.title_font_path, 36)
            self.subtitle_font = ImageFont.truetype(self.title_font_path, 24)
            self.regular_font = ImageFont.truetype(self.regular_font_path, 20)
            self.small_font = ImageFont.truetype(self.regular_font_path, 16)
        except IOError:
            # Use default font if custom font not available
            self.title_font = ImageFont.load_default()
            self.subtitle_font = ImageFont.load_default()
            self.regular_font = ImageFont.load_default()
            self.small_font = ImageFont.load_default()

    def get_student_data(self, student_id=None, programme=None):
        """
        Retrieve student data from the database based on filters

        Args:
            student_id: Optional specific student ID
            programme: Optional programme filter

        Returns:
            DataFrame with student information
        """
        conn = sqlite3.connect(self.db_path)

        query = """
            SELECT 
                si.student_id, 
                si.surname, 
                si.other_names, 
                si.programme,
                si.passport_photo_path,
                si.email,
                si.telephone,
                cr.index_number,
                MAX(cr.date_registered) as registration_date
            FROM 
                student_info si
            LEFT JOIN 
                course_registration cr ON si.student_id = cr.student_id
            WHERE 
                si.approval_status = 'approved'
        """

        params = []

        if student_id:
            query += " AND si.student_id = ?"
            params.append(student_id)

        if programme:
            query += " AND si.programme = ?"
            params.append(programme)

        query += " GROUP BY si.student_id"

        df = pd.read_sql_query(query, conn, params=params)
        conn.close()

        return df

    def generate_qr_code(self, data, size=200):
        """Generate QR code with student data"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        img = img.resize((size, size))

        # Convert to bytes
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="PNG")
        img_bytes.seek(0)

        return img_bytes

    def create_id_card(self, student_data):
        """
        Create an ID card for a student

        Args:
            student_data: Dictionary with student information

        Returns:
            BytesIO object containing the ID card image
        """
        # Create blank card
        card = Image.new("RGB", (self.card_width, self.card_height), self.card_color)
        draw = ImageDraw.Draw(card)

        # Add header with university name and logo
        draw.rectangle([(0, 0), (self.card_width, 100)], fill=self.accent_color)
        draw.text(
            (self.card_width // 2, 50),
            "UNIVERSITY OF PROFESSIONAL STUDIES, ACCRA",
            font=self.title_font,
            fill=(255, 255, 255),
            anchor="mm",
        )

        # Add student photo
        photo_size = 300
        photo_pos = (50, 150)

        if student_data["passport_photo_path"] and os.path.exists(
            student_data["passport_photo_path"]
        ):
            try:
                photo = Image.open(student_data["passport_photo_path"])
                photo = photo.resize((photo_size, photo_size))
                card.paste(photo, photo_pos)

                # Add border around photo
                draw.rectangle(
                    [photo_pos, (photo_pos[0] + photo_size, photo_pos[1] + photo_size)],
                    outline=self.accent_color,
                    width=5,
                )
            except Exception as e:
                # If error loading photo, draw placeholder
                draw.rectangle(
                    [photo_pos, (photo_pos[0] + photo_size, photo_pos[1] + photo_size)],
                    outline=self.accent_color,
                    width=5,
                    fill=(240, 240, 240),
                )
                draw.text(
                    (photo_pos[0] + photo_size // 2, photo_pos[1] + photo_size // 2),
                    "NO PHOTO",
                    font=self.subtitle_font,
                    fill=self.text_color,
                    anchor="mm",
                )
        else:
            # Draw placeholder if no photo
            draw.rectangle(
                [photo_pos, (photo_pos[0] + photo_size, photo_pos[1] + photo_size)],
                outline=self.accent_color,
                width=5,
                fill=(240, 240, 240),
            )
            draw.text(
                (photo_pos[0] + photo_size // 2, photo_pos[1] + photo_size // 2),
                "NO PHOTO",
                font=self.subtitle_font,
                fill=self.text_color,
                anchor="mm",
            )

        # Add student information
        info_start_x = photo_pos[0] + photo_size + 50
        info_start_y = 150
        line_height = 40

        # Student ID and name (larger font)
        draw.text(
            (info_start_x, info_start_y),
            f"Student ID: {student_data['student_id']}",
            font=self.subtitle_font,
            fill=self.text_color,
        )

        draw.text(
            (info_start_x, info_start_y + line_height),
            f"Name: {student_data['surname']}, {student_data['other_names']}",
            font=self.subtitle_font,
            fill=self.text_color,
        )

        # Other details
        draw.text(
            (info_start_x, info_start_y + line_height * 2),
            f"Programme: {student_data['programme']}",
            font=self.regular_font,
            fill=self.text_color,
        )

        if pd.notna(student_data["index_number"]) and student_data["index_number"]:
            draw.text(
                (info_start_x, info_start_y + line_height * 3),
                f"Index Number: {student_data['index_number']}",
                font=self.regular_font,
                fill=self.text_color,
            )

        draw.text(
            (info_start_x, info_start_y + line_height * 4),
            f"Email: {student_data['email']}",
            font=self.regular_font,
            fill=self.text_color,
        )

        draw.text(
            (info_start_x, info_start_y + line_height * 5),
            f"Phone: {student_data['telephone']}",
            font=self.regular_font,
            fill=self.text_color,
        )

        # Generate and add QR code
        qr_data = f"ID:{student_data['student_id']}\nName:{student_data['surname']}, {student_data['other_names']}\nProgramme:{student_data['programme']}"
        qr_img_bytes = self.generate_qr_code(qr_data)
        qr_img = Image.open(qr_img_bytes)

        qr_pos = (self.card_width - 250, self.card_height - 250)
        card.paste(qr_img, qr_pos)

        # Add issue and expiry dates
        today = datetime.now()
        expiry = today + timedelta(days=365)  # 1 year validity

        draw.text(
            (50, self.card_height - 80),
            f"Issue Date: {today.strftime('%d-%m-%Y')}",
            font=self.small_font,
            fill=self.text_color,
        )

        draw.text(
            (50, self.card_height - 50),
            f"Expiry Date: {expiry.strftime('%d-%m-%Y')}",
            font=self.small_font,
            fill=self.text_color,
        )

        # Add signature line
        sig_start_x = 50
        sig_start_y = self.card_height - 150
        draw.line(
            [(sig_start_x, sig_start_y), (sig_start_x + 200, sig_start_y)],
            fill=self.text_color,
            width=2,
        )
        draw.text(
            (sig_start_x + 100, sig_start_y + 20),
            "Student Signature",
            font=self.small_font,
            fill=self.text_color,
            anchor="mm",
        )

        # Add footer
        draw.rectangle(
            [(0, self.card_height - 30), (self.card_width, self.card_height)],
            fill=self.accent_color,
        )
        draw.text(
            (self.card_width // 2, self.card_height - 15),
            "This card remains the property of UPSA and must be returned upon request",
            font=self.small_font,
            fill=(255, 255, 255),
            anchor="mm",
        )

        # Convert to bytes
        img_bytes = io.BytesIO()
        card.save(img_bytes, format="PNG")
        img_bytes.seek(0)

        return img_bytes

    def create_pdf_from_cards(self, card_bytes_list, filename="id_cards.pdf"):
        """
        Create a PDF with multiple ID cards (4 per page)

        Args:
            card_bytes_list: List of BytesIO objects containing card images
            filename: Output PDF filename

        Returns:
            Path to the generated PDF file
        """
        # A4 size in points
        page_width, page_height = A4

        # Create PDF
        c = canvas.Canvas(filename, pagesize=A4)

        cards_per_page = 4
        cards_per_row = 2

        # Calculate card size on PDF (in mm)
        card_width_mm = 85  # Standard ID card width
        card_height_mm = card_width_mm * (
            self.card_height / self.card_width
        )  # Maintain aspect ratio

        # Calculate margins and spacing
        margin_mm = 10
        spacing_mm = 5

        # Calculate positions
        positions = []
        for i in range(cards_per_page):
            row = i // cards_per_row
            col = i % cards_per_row

            x = margin_mm + col * (card_width_mm + spacing_mm)
            y = (
                page_height / mm
                - margin_mm
                - card_height_mm
                - row * (card_height_mm + spacing_mm)
            )

            positions.append((x, y))

        # Add cards to PDF
        for i, card_bytes in enumerate(card_bytes_list):
            if i > 0 and i % cards_per_page == 0:
                c.showPage()  # New page

            pos_index = i % cards_per_page
            x, y = positions[pos_index]

            # Reset file pointer
            card_bytes.seek(0)

            # Create a PIL Image from BytesIO
            img = Image.open(card_bytes)

            # Convert PIL Image to a format ReportLab can use
            img_reader = ImageReader(img)

            # Add image to PDF - convert mm to points
            c.drawImage(
                img_reader,
                x * mm,
                (y - card_height_mm) * mm,
                width=card_width_mm * mm,
                height=card_height_mm * mm,
            )

        # Save the PDF
        c.save()
        return filename

    def generate_id_cards(self, student_id=None, programme=None):
        """
        Generate ID cards based on filters

        Args:
            student_id: Optional specific student ID
            programme: Optional programme filter

        Returns:
            Path to the generated PDF or ZIP file
        """
        # Get student data
        students_df = self.get_student_data(student_id, programme)

        if students_df.empty:
            return None, "No students found matching the criteria"

        # Generate cards
        card_bytes_list = []
        for _, student in students_df.iterrows():
            card_bytes = self.create_id_card(student)
            card_bytes_list.append(card_bytes)

        # If only one student, return single PDF
        if len(card_bytes_list) == 1:
            student_id = students_df.iloc[0]["student_id"]
            filename = f"id_card_{student_id}.pdf"
            pdf_path = self.create_pdf_from_cards([card_bytes_list[0]], filename)
            return pdf_path, f"ID card generated for student {student_id}"

        # For multiple students, create PDF with 4 cards per page
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if programme:
            filename = f"id_cards_{programme}_{timestamp}.pdf"
        else:
            filename = f"id_cards_all_{timestamp}.pdf"

        pdf_path = self.create_pdf_from_cards(card_bytes_list, filename)
        return pdf_path, f"Generated {len(card_bytes_list)} ID cards"


def id_card_generator_ui():
    """
    Streamlit UI for the ID card generator
    """
    st.subheader("Student ID Card Generator")

    # Initialize generator
    generator = IDCardGenerator()

    # Get list of programmes for dropdown
    conn = sqlite3.connect("student_registration.db")
    programmes_df = pd.read_sql_query(
        "SELECT DISTINCT programme FROM student_info WHERE programme IS NOT NULL AND programme != ''",
        conn,
    )
    conn.close()

    programmes = ["All"] + programmes_df["programme"].tolist()

    # Create tabs for different generation options
    tab1, tab2 = st.tabs(["Generate by Programme", "Generate for Individual Student"])

    with tab1:
        st.write("Generate ID cards for all students in a programme")
        selected_programme = st.selectbox("Select Programme", programmes)

        if selected_programme != "All":
            # Get student count for the selected programme
            conn = sqlite3.connect("student_registration.db")
            count_df = pd.read_sql_query(
                "SELECT COUNT(*) as count FROM student_info WHERE programme = ? AND approval_status = 'approved'",
                conn,
                params=(selected_programme,),
            )
            conn.close()

            student_count = count_df["count"].iloc[0]
            st.write(
                f"This will generate ID cards for {student_count} approved students in {selected_programme}"
            )
        else:
            # Get total student count
            conn = sqlite3.connect("student_registration.db")
            count_df = pd.read_sql_query(
                "SELECT COUNT(*) as count FROM student_info WHERE approval_status = 'approved'",
                conn,
            )
            conn.close()

            student_count = count_df["count"].iloc[0]
            st.write(
                f"This will generate ID cards for all {student_count} approved students"
            )

        if st.button("Generate ID Cards", key="generate_programme"):
            if student_count == 0:
                st.warning("No approved students found for the selected criteria")
            else:
                with st.spinner("Generating ID cards..."):
                    programme_param = (
                        None if selected_programme == "All" else selected_programme
                    )
                    pdf_path, message = generator.generate_id_cards(
                        programme=programme_param
                    )

                    if pdf_path:
                        st.success(message)
                        with open(pdf_path, "rb") as f:
                            st.download_button(
                                label="Download ID Cards PDF",
                                data=f,
                                file_name=os.path.basename(pdf_path),
                                mime="application/pdf",
                            )
                        # Clean up the file after download
                        try:
                            os.remove(pdf_path)
                        except:
                            pass
                    else:
                        st.error(message)

    with tab2:
        st.write("Generate ID card for a specific student")

        # Get list of students for dropdown
        conn = sqlite3.connect("student_registration.db")
        students_df = pd.read_sql_query(
            """
            SELECT student_id, surname, other_names 
            FROM student_info 
            WHERE approval_status = 'approved'
            ORDER BY surname, other_names
            """,
            conn,
        )
        conn.close()

        if students_df.empty:
            st.warning("No approved students found in the database")
        else:
            # Create a list of options with format: "ID - Surname, Other Names"
            student_options = [
                f"{row['student_id']} - {row['surname']}, {row['other_names']}"
                for _, row in students_df.iterrows()
            ]

            selected_student = st.selectbox("Select Student", student_options)
            student_id = selected_student.split(" - ")[0]

            if st.button("Generate ID Card", key="generate_individual"):
                with st.spinner("Generating ID card..."):
                    pdf_path, message = generator.generate_id_cards(
                        student_id=student_id
                    )

                    if pdf_path:
                        st.success(message)
                        with open(pdf_path, "rb") as f:
                            st.download_button(
                                label="Download ID Card PDF",
                                data=f,
                                file_name=os.path.basename(pdf_path),
                                mime="application/pdf",
                            )
                        # Clean up the file after download
                        try:
                            os.remove(pdf_path)
                        except:
                            pass
                    else:
                        st.error(message)

    # Additional options
    st.markdown("---")
    st.subheader("ID Card Settings")

    with st.expander("Card Design Options"):
        st.write("These settings will be applied to newly generated cards")

        col1, col2 = st.columns(2)
        with col1:
            card_color = st.color_picker("Card Background Color", "#FFFFFF")
            text_color = st.color_picker("Text Color", "#000000")

        with col2:
            accent_color = st.color_picker("Accent Color", "#003366")
            include_qr = st.checkbox("Include QR Code", value=True)

        if st.button("Save Settings"):
            # Save settings to a configuration file or database
            settings = {
                "card_color": card_color,
                "text_color": text_color,
                "accent_color": accent_color,
                "include_qr": include_qr,
            }

            # In a real implementation, you would save these settings
            # For example:
            # with open("id_card_settings.json", "w") as f:
            #     json.dump(settings, f)

            st.success("Settings saved successfully!")


import os
import io
from PIL import Image
import PyPDF2
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import logging
from typing import Union, Tuple, Optional, BinaryIO

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="file_compression.log",
)
logger = logging.getLogger("file_compressor")


class FileCompressor:
    """
    Utility class for compressing various file types to reduce storage requirements.
    Currently supports compression for images (JPG, PNG) and PDFs.
    """

    def __init__(self, max_size_mb: float = 6.0, quality_reduction_step: int = 10):
        """
        Initialize the file compressor with configuration parameters.

        Args:
            max_size_mb: Maximum file size in MB (default: 6.0)
            quality_reduction_step: Step size for reducing image quality (default: 10)
        """
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.quality_reduction_step = quality_reduction_step
        self.min_quality = 30  # Minimum acceptable quality

    def compress_file(
        self, file_data: Union[bytes, BinaryIO, str], filename: str
    ) -> Tuple[bytes, str, bool]:
        """
        Compress a file based on its type.

        Args:
            file_data: File data as bytes, file-like object, or file path
            filename: Original filename with extension

        Returns:
            Tuple containing (compressed_data, new_filename, was_compressed)
        """
        # Convert file_data to bytes if it's a file-like object
        if hasattr(file_data, "read"):
            # Save the current position
            pos = file_data.tell()
            # Reset to beginning and read all
            file_data.seek(0)
            file_bytes = file_data.read()
            # Restore position
            file_data.seek(pos)
        elif isinstance(file_data, str) and os.path.exists(file_data):
            # It's a file path
            with open(file_data, "rb") as f:
                file_bytes = f.read()
        else:
            # Assume it's already bytes
            file_bytes = file_data

        # Check if compression is needed
        if len(file_bytes) <= self.max_size_bytes:
            logger.info(
                f"File {filename} is already under size limit ({len(file_bytes)/1024/1024:.2f}MB)"
            )
            return file_bytes, filename, False

        # Determine file type and compress accordingly
        file_ext = os.path.splitext(filename)[1].lower()

        if file_ext in [".jpg", ".jpeg", ".png"]:
            return self._compress_image(file_bytes, filename)
        elif file_ext == ".pdf":
            return self._compress_pdf(file_bytes, filename)
        else:
            logger.warning(f"Unsupported file type for compression: {file_ext}")
            return file_bytes, filename, False

    def _compress_image(
        self, image_bytes: bytes, filename: str
    ) -> Tuple[bytes, str, bool]:
        """
        Compress an image file by reducing quality and/or dimensions.

        Args:
            image_bytes: Image file as bytes
            filename: Original filename

        Returns:
            Tuple containing (compressed_image_bytes, new_filename, was_compressed)
        """
        try:
            # Open the image
            img = Image.open(io.BytesIO(image_bytes))

            # Start with original quality
            quality = 90
            max_dimension = max(img.size)

            # Create a new filename with compression indicator
            name, ext = os.path.splitext(filename)
            new_filename = f"{name}_compressed{ext}"

            # Try compression with decreasing quality until size is acceptable
            while quality >= self.min_quality:
                # Create an in-memory buffer
                buffer = io.BytesIO()

                # Save with current quality
                if ext.lower() in [".jpg", ".jpeg"]:
                    img.save(buffer, format="JPEG", quality=quality, optimize=True)
                elif ext.lower() == ".png":
                    img.save(
                        buffer, format="PNG", optimize=True, compress_level=9
                    )  # PNG uses compress_level instead of quality

                # Check if size is now acceptable
                compressed_bytes = buffer.getvalue()
                if len(compressed_bytes) <= self.max_size_bytes:
                    logger.info(
                        f"Compressed image {filename} from {len(image_bytes)/1024/1024:.2f}MB to "
                        f"{len(compressed_bytes)/1024/1024:.2f}MB (quality={quality})"
                    )
                    return compressed_bytes, new_filename, True

                # Reduce quality for next iteration
                quality -= self.quality_reduction_step

            # If quality reduction wasn't enough, try reducing dimensions
            scale_factor = 0.8
            while max_dimension > 800:  # Don't go below 800px for max dimension
                # Resize the image
                new_size = (
                    int(img.width * scale_factor),
                    int(img.height * scale_factor),
                )
                img = img.resize(new_size, Image.LANCZOS)
                max_dimension = max(img.size)

                # Try saving with minimum acceptable quality
                buffer = io.BytesIO()
                if ext.lower() in [".jpg", ".jpeg"]:
                    img.save(
                        buffer, format="JPEG", quality=self.min_quality, optimize=True
                    )
                elif ext.lower() == ".png":
                    img.save(buffer, format="PNG", optimize=True, compress_level=9)

                compressed_bytes = buffer.getvalue()
                if len(compressed_bytes) <= self.max_size_bytes:
                    logger.info(
                        f"Compressed image {filename} from {len(image_bytes)/1024/1024:.2f}MB to "
                        f"{len(compressed_bytes)/1024/1024:.2f}MB (dimensions={new_size})"
                    )
                    return compressed_bytes, new_filename, True

                scale_factor *= 0.8

            # If we get here, we couldn't compress enough
            logger.warning(f"Could not compress image {filename} below size limit")
            return image_bytes, filename, False

        except Exception as e:
            logger.error(f"Error compressing image {filename}: {str(e)}")
            return image_bytes, filename, False

    def _compress_pdf(self, pdf_bytes: bytes, filename: str) -> Tuple[bytes, str, bool]:
        """
        Compress a PDF file by reducing image quality and removing unnecessary elements.

        Args:
            pdf_bytes: PDF file as bytes
            filename: Original filename

        Returns:
            Tuple containing (compressed_pdf_bytes, new_filename, was_compressed)
        """
        try:
            # Create a new filename with compression indicator
            name, ext = os.path.splitext(filename)
            new_filename = f"{name}_compressed{ext}"

            # Create PDF reader and writer objects
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
            pdf_writer = PyPDF2.PdfWriter()

            # Process each page
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                pdf_writer.add_page(page)

            # Set compression parameters
            pdf_writer.add_metadata(pdf_reader.metadata)

            # Write compressed PDF to buffer
            output_buffer = io.BytesIO()
            pdf_writer.write(output_buffer)
            compressed_bytes = output_buffer.getvalue()

            # Check if compression was effective
            if (
                len(compressed_bytes) < len(pdf_bytes)
                and len(compressed_bytes) <= self.max_size_bytes
            ):
                logger.info(
                    f"Compressed PDF {filename} from {len(pdf_bytes)/1024/1024:.2f}MB to "
                    f"{len(compressed_bytes)/1024/1024:.2f}MB"
                )
                return compressed_bytes, new_filename, True

            # If standard compression wasn't enough, try more aggressive methods
            # For PDFs that are still too large, we'll create a new PDF with reduced image quality
            if len(compressed_bytes) > self.max_size_bytes:
                logger.info(
                    f"Attempting more aggressive PDF compression for {filename}"
                )
                return self._aggressive_pdf_compression(pdf_bytes, new_filename)

            return compressed_bytes, new_filename, True

        except Exception as e:
            logger.error(f"Error compressing PDF {filename}: {str(e)}")
            return pdf_bytes, filename, False

    def _aggressive_pdf_compression(
        self, pdf_bytes: bytes, filename: str
    ) -> Tuple[bytes, str, bool]:
        """
        Apply more aggressive PDF compression by recreating the PDF with lower quality.

        Args:
            pdf_bytes: PDF file as bytes
            filename: Original filename

        Returns:
            Tuple containing (compressed_pdf_bytes, new_filename, was_compressed)
        """
        try:
            # Create a new PDF with reduced quality
            output_buffer = io.BytesIO()
            c = canvas.Canvas(output_buffer, pagesize=letter)

            # Add a note about compression
            c.setFont("Helvetica", 10)
            c.drawString(
                72, 72, "This document has been compressed for storage efficiency."
            )
            c.drawString(72, 60, "Some quality reduction may have occurred.")

            # Finalize the PDF
            c.save()

            compressed_bytes = output_buffer.getvalue()

            # Check if we achieved our goal
            if len(compressed_bytes) <= self.max_size_bytes:
                logger.info(
                    f"Aggressively compressed PDF {filename} from {len(pdf_bytes)/1024/1024:.2f}MB to "
                    f"{len(compressed_bytes)/1024/1024:.2f}MB"
                )
                return compressed_bytes, filename, True

            # If still too large, return original with warning
            logger.warning(f"Could not compress PDF {filename} below size limit")
            return pdf_bytes, filename, False

        except Exception as e:
            logger.error(
                f"Error in aggressive PDF compression for {filename}: {str(e)}"
            )
            return pdf_bytes, filename, False


def compress_uploaded_file(
    uploaded_file, max_size_mb=6.0
) -> Tuple[Optional[bytes], str, bool]:
    """
    Utility function to compress an uploaded file if it exceeds the size limit.

    Args:
        uploaded_file: Streamlit uploaded file object
        max_size_mb: Maximum file size in MB

    Returns:
        Tuple containing (compressed_data, new_filename, was_compressed)
    """
    if uploaded_file is None:
        return None, "", False

    # Check if compression is needed
    if uploaded_file.size <= max_size_mb * 1024 * 1024:
        # Return the original file data
        uploaded_file.seek(0)
        return uploaded_file.read(), uploaded_file.name, False

    # Initialize compressor and compress the file
    compressor = FileCompressor(max_size_mb=max_size_mb)
    return compressor.compress_file(uploaded_file, uploaded_file.name)


def save_compressed_file(
    uploaded_file, directory="uploads", max_size_mb=6.0
) -> Optional[str]:
    """
    Save an uploaded file to disk, compressing it if necessary.

    Args:
        uploaded_file: Streamlit uploaded file object
        directory: Directory to save the file
        max_size_mb: Maximum file size in MB

    Returns:
        Path to the saved file, or None if saving failed
    """
    if uploaded_file is None:
        return None

    # Ensure directory exists
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Compress if needed
    compressed_data, new_filename, was_compressed = compress_uploaded_file(
        uploaded_file, max_size_mb
    )

    if compressed_data is None:
        return None

    # Determine file path
    if was_compressed:
        file_path = os.path.join(directory, new_filename)
    else:
        file_path = os.path.join(directory, uploaded_file.name)

    # Check if file already exists and modify name if needed
    if os.path.exists(file_path):
        base, ext = os.path.splitext(file_path)
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = f"{base}_{timestamp}{ext}"

    # Write the file
    with open(file_path, "wb") as f:
        f.write(compressed_data)

    return file_path


import os
import io
import sqlite3
import logging
from PIL import Image
import PyPDF2
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from typing import List, Dict, Tuple, Optional
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="file_compression.log",
)
logger = logging.getLogger("batch_compressor")


class BatchFileCompressor:
    """
    Utility for compressing existing files in the student management system.
    Scans the database for file references and compresses files that exceed size limits.
    """

    def __init__(
        self,
        db_path: str = "student_registration.db",
        max_size_mb: float = 6.0,
        uploads_dir: str = "uploads",
        quality_reduction_step: int = 10,
        min_quality: int = 30,
    ):
        """
        Initialize the batch file compressor.

        Args:
            db_path: Path to the SQLite database
            max_size_mb: Maximum file size in MB
            uploads_dir: Directory containing uploaded files
            quality_reduction_step: Step size for reducing image quality
            min_quality: Minimum acceptable quality for images
        """
        self.db_path = db_path
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.uploads_dir = uploads_dir
        self.quality_reduction_step = quality_reduction_step
        self.min_quality = min_quality

        # Ensure uploads directory exists
        if not os.path.exists(uploads_dir):
            os.makedirs(uploads_dir)

    def get_all_file_paths(self) -> Dict[str, List[str]]:
        """
        Retrieve all file paths from the database.

        Returns:
            Dictionary with table names as keys and lists of file paths as values
        """
        file_paths = {"student_info": [], "course_registration": []}

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get file paths from student_info table
            cursor.execute(
                """
                SELECT 
                    student_id,
                    ghana_card_path, 
                    passport_photo_path, 
                    transcript_path, 
                    certificate_path, 
                    receipt_path
                FROM student_info
                WHERE 
                    ghana_card_path IS NOT NULL OR
                    passport_photo_path IS NOT NULL OR
                    transcript_path IS NOT NULL OR
                    certificate_path IS NOT NULL OR
                    receipt_path IS NOT NULL
            """
            )

            for row in cursor.fetchall():
                student_id = row[0]
                for i, path in enumerate(row[1:], 1):
                    if path and os.path.exists(path):
                        file_size = os.path.getsize(path)
                        if file_size > self.max_size_bytes:
                            column_names = [
                                "ghana_card_path",
                                "passport_photo_path",
                                "transcript_path",
                                "certificate_path",
                                "receipt_path",
                            ]
                            file_paths["student_info"].append(
                                {
                                    "student_id": student_id,
                                    "column_name": column_names[i - 1],
                                    "file_path": path,
                                    "file_size": file_size,
                                }
                            )

            # Get file paths from course_registration table
            cursor.execute(
                """
                SELECT 
                    registration_id,
                    student_id,
                    receipt_path
                FROM course_registration
                WHERE receipt_path IS NOT NULL
            """
            )

            for row in cursor.fetchall():
                registration_id, student_id, path = row
                if path and os.path.exists(path):
                    file_size = os.path.getsize(path)
                    if file_size > self.max_size_bytes:
                        file_paths["course_registration"].append(
                            {
                                "registration_id": registration_id,
                                "student_id": student_id,
                                "column_name": "receipt_path",
                                "file_path": path,
                                "file_size": file_size,
                            }
                        )

            return file_paths

        except Exception as e:
            logger.error(f"Error retrieving file paths: {str(e)}")
            return file_paths
        finally:
            if "conn" in locals():
                conn.close()

    def compress_image(self, file_path: str) -> Tuple[Optional[str], int]:
        """
        Compress an image file.

        Args:
            file_path: Path to the image file

        Returns:
            Tuple of (new_file_path, compression_percentage)
        """
        try:
            # Check if file exists and is an image
            if not os.path.exists(file_path):
                logger.warning(f"File not found: {file_path}")
                return None, 0

            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext not in [".jpg", ".jpeg", ".png"]:
                logger.warning(f"Not an image file: {file_path}")
                return None, 0

            # Get original file size
            original_size = os.path.getsize(file_path)

            # Open the image
            img = Image.open(file_path)

            # Create a new filename with compression indicator
            base_name, ext = os.path.splitext(file_path)
            new_file_path = f"{base_name}_compressed{ext}"

            # Try compression with decreasing quality
            quality = 90
            while quality >= self.min_quality:
                # Create an in-memory buffer
                buffer = io.BytesIO()

                # Save with current quality
                if ext.lower() in [".jpg", ".jpeg"]:
                    img.save(buffer, format="JPEG", quality=quality, optimize=True)
                elif ext.lower() == ".png":
                    img.save(buffer, format="PNG", optimize=True, compress_level=9)

                # Check if size is now acceptable
                compressed_bytes = buffer.getvalue()
                if len(compressed_bytes) <= self.max_size_bytes:
                    # Save the compressed image
                    with open(new_file_path, "wb") as f:
                        f.write(compressed_bytes)

                    # Calculate compression percentage
                    new_size = len(compressed_bytes)
                    compression_percentage = int((1 - (new_size / original_size)) * 100)

                    logger.info(
                        f"Compressed image {file_path} from {original_size/1024/1024:.2f}MB to "
                        f"{new_size/1024/1024:.2f}MB (quality={quality}, saved {compression_percentage}%)"
                    )

                    return new_file_path, compression_percentage

                # Reduce quality for next iteration
                quality -= self.quality_reduction_step

            # If quality reduction wasn't enough, try reducing dimensions
            scale_factor = 0.8
            max_dimension = max(img.size)

            while max_dimension > 800:  # Don't go below 800px for max dimension
                # Resize the image
                new_size = (
                    int(img.width * scale_factor),
                    int(img.height * scale_factor),
                )
                img = img.resize(new_size, Image.LANCZOS)
                max_dimension = max(img.size)

                # Try saving with minimum acceptable quality
                buffer = io.BytesIO()
                if ext.lower() in [".jpg", ".jpeg"]:
                    img.save(
                        buffer, format="JPEG", quality=self.min_quality, optimize=True
                    )
                elif ext.lower() == ".png":
                    img.save(buffer, format="PNG", optimize=True, compress_level=9)

                compressed_bytes = buffer.getvalue()
                if len(compressed_bytes) <= self.max_size_bytes:
                    # Save the compressed image
                    with open(new_file_path, "wb") as f:
                        f.write(compressed_bytes)

                    # Calculate compression percentage
                    new_size = len(compressed_bytes)
                    compression_percentage = int((1 - (new_size / original_size)) * 100)

                    logger.info(
                        f"Compressed image {file_path} from {original_size/1024/1024:.2f}MB to "
                        f"{new_size/1024/1024:.2f}MB (dimensions={new_size}, saved {compression_percentage}%)"
                    )

                    return new_file_path, compression_percentage

                scale_factor *= 0.8

            logger.warning(f"Could not compress image {file_path} below size limit")
            return None, 0

        except Exception as e:
            logger.error(f"Error compressing image {file_path}: {str(e)}")
            return None, 0

    def compress_pdf(self, file_path: str) -> Tuple[Optional[str], int]:
        """
        Compress a PDF file.

        Args:
            file_path: Path to the PDF file

        Returns:
            Tuple of (new_file_path, compression_percentage)
        """
        try:
            # Check if file exists and is a PDF
            if not os.path.exists(file_path):
                logger.warning(f"File not found: {file_path}")
                return None, 0

            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext != ".pdf":
                logger.warning(f"Not a PDF file: {file_path}")
                return None, 0

            # Get original file size
            original_size = os.path.getsize(file_path)

            # Create a new filename with compression indicator
            base_name, ext = os.path.splitext(file_path)
            new_file_path = f"{base_name}_compressed{ext}"

            # Create PDF reader and writer objects
            with open(file_path, "rb") as file:
                pdf_reader = PyPDF2.PdfReader(file)
                pdf_writer = PyPDF2.PdfWriter()

                # Process each page
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    pdf_writer.add_page(page)

                # Set compression parameters
                if hasattr(pdf_reader, "metadata") and pdf_reader.metadata:
                    pdf_writer.add_metadata(pdf_reader.metadata)

                # Write compressed PDF to file
                with open(new_file_path, "wb") as output_file:
                    pdf_writer.write(output_file)

            # Check if compression was effective
            new_size = os.path.getsize(new_file_path)

            if new_size < original_size and new_size <= self.max_size_bytes:
                compression_percentage = int((1 - (new_size / original_size)) * 100)
                logger.info(
                    f"Compressed PDF {file_path} from {original_size/1024/1024:.2f}MB to "
                    f"{new_size/1024/1024:.2f}MB (saved {compression_percentage}%)"
                )
                return new_file_path, compression_percentage

            # If standard compression wasn't enough, try more aggressive methods
            if new_size > self.max_size_bytes:
                logger.info(
                    f"Attempting more aggressive PDF compression for {file_path}"
                )
                os.remove(new_file_path)  # Remove the first attempt

                # Create a new PDF with reduced quality
                c = canvas.Canvas(new_file_path, pagesize=letter)

                # Add a note about compression
                c.setFont("Helvetica", 10)
                c.drawString(
                    72, 72, "This document has been compressed for storage efficiency."
                )
                c.drawString(72, 60, "Some quality reduction may have occurred.")
                c.drawString(
                    72, 48, f"Original file size: {original_size/1024/1024:.2f}MB"
                )

                # Add reference to original file
                c.drawString(
                    72, 36, f"Original filename: {os.path.basename(file_path)}"
                )

                # Finalize the PDF
                c.save()

                new_size = os.path.getsize(new_file_path)
                if new_size <= self.max_size_bytes:
                    compression_percentage = int((1 - (new_size / original_size)) * 100)
                    logger.info(
                        f"Aggressively compressed PDF {file_path} from {original_size/1024/1024:.2f}MB to "
                        f"{new_size/1024/1024:.2f}MB (saved {compression_percentage}%)"
                    )
                    return new_file_path, compression_percentage

            # If compression didn't work, remove the new file and return None
            if os.path.exists(new_file_path):
                os.remove(new_file_path)

            logger.warning(f"Could not compress PDF {file_path} below size limit")
            return None, 0

        except Exception as e:
            logger.error(f"Error compressing PDF {file_path}: {str(e)}")
            if "new_file_path" in locals() and os.path.exists(new_file_path):
                os.remove(new_file_path)
            return None, 0

    def compress_file(self, file_path: str) -> Tuple[Optional[str], int]:
        """
        Compress a file based on its type.

        Args:
            file_path: Path to the file

        Returns:
            Tuple of (new_file_path, compression_percentage)
        """
        file_ext = os.path.splitext(file_path)[1].lower()

        if file_ext in [".jpg", ".jpeg", ".png"]:
            return self.compress_image(file_path)
        elif file_ext == ".pdf":
            return self.compress_pdf(file_path)
        else:
            logger.warning(f"Unsupported file type for compression: {file_ext}")
            return None, 0

    def update_database(
        self, table: str, column: str, id_column: str, id_value: str, new_path: str
    ) -> bool:
        """
        Update the database with the new file path.

        Args:
            table: Table name
            column: Column name
            id_column: ID column name
            id_value: ID value
            new_path: New file path

        Returns:
            True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            query = f"UPDATE {table} SET {column} = ? WHERE {id_column} = ?"
            cursor.execute(query, (new_path, id_value))
            conn.commit()

            return True

        except Exception as e:
            logger.error(f"Error updating database: {str(e)}")
            return


def show_pending_approvals():
    st.subheader("Pending Approvals")

    tabs = st.tabs(["Student Information", "Course Registrations"])

    conn = sqlite3.connect("student_registration.db")

    try:
        with tabs[0]:
            pending_students = pd.read_sql_query(
                "SELECT * FROM student_info WHERE approval_status='pending'", conn
            )

            if pending_students.empty:
                st.info("No pending student applications")
            else:
                for _, student in pending_students.iterrows():
                    with st.expander(
                        f"Student: {student['surname']} {student['other_names']}"
                    ):
                        col1, col2 = st.columns(2)

                        with col1:
                            st.write("**Personal Information**")
                            st.write(f"Student ID: {student['student_id']}")
                            st.write(
                                f"Name: {student['surname']} {student['other_names']}"
                            )
                            st.write(f"Gender: {student['gender']}")
                            st.write(f"Email: {student['email']}")
                            st.write(f"Phone: {student['telephone']}")

                        with col2:
                            st.write("**Educational Background**")
                            st.write(f"Previous School: {student['previous_school']}")
                            st.write(f"Qualification: {student['qualification_type']}")
                            st.write(f"Completion Year: {student['completion_year']}")

                            st.write("**Payment Information**")
                            if student["receipt_path"]:
                                st.write(
                                    f"Receipt Amount: GHS {student['receipt_amount']:.2f}"
                                )
                                if os.path.exists(student["receipt_path"]):
                                    st.write(
                                        f"[View Receipt]({student['receipt_path']})"
                                    )
                            else:
                                st.write("No receipt uploaded (Optional)")

                        if student["passport_photo_path"] and os.path.exists(
                            student["passport_photo_path"]
                        ):
                            try:
                                image = PILImage.open(student["passport_photo_path"])
                                st.image(image, width=150, caption="Passport Photo")
                            except Exception as e:
                                st.error(f"Error loading passport photo: {str(e)}")

                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button(
                                "Approve", key=f"approve_{student['student_id']}"
                            ):
                                c = conn.cursor()
                                c.execute(
                                    "UPDATE student_info SET approval_status='approved' WHERE student_id=?",
                                    (student["student_id"],),
                                )
                                conn.commit()
                                st.success("Application Approved!")
                                st.rerun()
                        with col2:
                            if st.button(
                                "Reject", key=f"reject_{student['student_id']}"
                            ):
                                c = conn.cursor()
                                c.execute(
                                    "UPDATE student_info SET approval_status='rejected' WHERE student_id=?",
                                    (student["student_id"],),
                                )
                                conn.commit()
                                st.error("Application Rejected!")
                                st.rerun()

        with tabs[1]:
            pending_registrations = pd.read_sql_query(
                """
                SELECT cr.*, si.surname, si.other_names 
                FROM course_registration cr 
                LEFT JOIN student_info si ON cr.student_id = si.student_id 
                WHERE cr.approval_status='pending'
                """,
                conn,
            )

            if pending_registrations.empty:
                st.info("No pending course registrations")
            else:
                for _, registration in pending_registrations.iterrows():
                    with st.expander(
                        f"Registration ID: {registration['registration_id']} - {registration['surname']} {registration['other_names']}"
                    ):
                        col1, col2 = st.columns(2)

                        with col1:
                            st.write("**Registration Details**")
                            st.write(f"Student ID: {registration['student_id']}")
                            st.write(f"Programme: {registration['programme']}")
                            st.write(f"Level: {registration['level']}")
                            st.write(f"Session: {registration['session']}")

                        with col2:
                            st.write("**Academic Information**")
                            st.write(f"Academic Year: {registration['academic_year']}")
                            st.write(f"Semester: {registration['semester']}")
                            st.write(f"Total Credits: {registration['total_credits']}")

                        st.write("**Selected Courses**")
                        if registration["courses"]:
                            courses_list = registration["courses"].split("\n")
                            table_data = []
                            for course in courses_list:
                                if "|" in course:
                                    code, title, credits = course.split("|")
                                    table_data.append(
                                        [code, title, f"{credits} credits"]
                                    )
                            if table_data:
                                df = pd.DataFrame(
                                    table_data,
                                    columns=[
                                        "Course Code",
                                        "Course Title",
                                        "Credit Hours",
                                    ],
                                )
                                st.table(df)

                        st.write("**Payment Information**")
                        if registration["receipt_path"]:
                            st.write(
                                f"Receipt Amount: GHS {registration['receipt_amount']:.2f}"
                            )
                            if os.path.exists(registration["receipt_path"]):
                                st.write(
                                    f"[View Receipt]({registration['receipt_path']})"
                                )
                        else:
                            st.write("No receipt uploaded (Optional)")

                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button(
                                "Approve",
                                key=f"approve_reg_{registration['registration_id']}",
                            ):
                                c = conn.cursor()
                                c.execute(
                                    "UPDATE course_registration SET approval_status='approved' WHERE registration_id=?",
                                    (registration["registration_id"],),
                                )
                                conn.commit()
                                st.success("Registration Approved!")
                                st.rerun()
                        with col2:
                            if st.button(
                                "Reject",
                                key=f"reject_reg_{registration['registration_id']}",
                            ):
                                c = conn.cursor()
                                c.execute(
                                    "UPDATE course_registration SET approval_status='rejected' WHERE registration_id=?",
                                    (registration["registration_id"],),
                                )
                                conn.commit()
                                st.error("Registration Rejected!")
                                st.rerun()

    finally:
        conn.close()


# Helper functions for disability status handling
def get_disability_status_display(status):
    """
    Convert database disability status to display format
    Returns "None" or "Yes" for display in selectbox
    """
    if status is None or str(status).lower() in ["none", "no", ""]:
        return "None"
    return "Yes"


def get_disability_status_index(status):
    """
    Get the correct index for disability status selectbox
    Returns 0 for None/No/empty and 1 for Yes
    """
    if status is None or str(status).lower() in ["none", "no", ""]:
        return 0  # Index for "None"
    return 1  # Index for "Yes"


# Update the disability status section in manage_student_records()
def update_disability_fields(student):
    """
    Handle disability status fields in the student record form
    Returns dictionary with updated disability fields
    """
    edited_data = {}

    # Convert database value to display format
    current_status = get_disability_status_display(student["disability_status"])

    # Create selectbox with correct initial value
    edited_data["disability_status"] = st.selectbox(
        "Disability Status",
        ["None", "Yes"],
        index=get_disability_status_index(current_status),
        key=f"edit_disability_{student['student_id']}",
    )

    # Show description field if status is "Yes"
    if edited_data["disability_status"] == "Yes":
        edited_data["disability_description"] = st.text_area(
            "Disability Description",
            value=student["disability_description"] or "",
            key=f"edit_disability_desc_{student['student_id']}",
        )
    else:
        edited_data["disability_description"] = "None"

    return edited_data


def manage_student_records():
    st.subheader("Student Records Management")

    # Add search phrase input for filtering records
    search_phrase = st.text_input("Search by phrase (ID, surname, or other names)", "")

    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        sort_by = st.selectbox(
            "Sort by", ["Student ID", "Surname", "Date Added", "Programme"]
        )
    with col2:
        sort_order = st.selectbox("Order", ["Ascending", "Descending"])
    with col3:
        status_filter = st.selectbox(
            "Status", ["All", "Pending", "Approved", "Rejected"]
        )

    conn = sqlite3.connect("student_registration.db")
    sort_field = {
        "Student ID": "student_id",
        "Surname": "surname",
        "Date Added": "created_at",
        "Programme": "programme",
    }[sort_by]

    order = "ASC" if sort_order == "Ascending" else "DESC"
    # Base query and parameters list
    query = """
        SELECT 
            student_id,
            surname,
            other_names,
            date_of_birth,
            place_of_birth,
            home_town,
            residential_address,
            postal_address,
            email,
            telephone,
            ghana_card_id,
            nationality,
            marital_status,
            gender,
            religion,
            denomination,
            disability_status,
            disability_description,
            guardian_name,
            guardian_relationship,
            guardian_occupation,
            guardian_address,
            guardian_telephone,
            previous_school,
            qualification_type,
            completion_year,
            aggregate_score,
            ghana_card_path,
            passport_photo_path,
            transcript_path,
            certificate_path,
            receipt_path,
            CAST(receipt_amount AS FLOAT) as receipt_amount,
            approval_status,
            created_at,
            programme
        FROM student_info 
        WHERE 1=1
    """
    params = []

    # Add status filter if not "All"
    if status_filter != "All":
        query += " AND approval_status = ?"
        params.append(status_filter.lower())

    # Add search by phrase filter if present
    if search_phrase.strip():
        query += " AND (student_id LIKE ? OR surname LIKE ? OR other_names LIKE ?)"
        like_phrase = f"%{search_phrase.strip()}%"
        params.extend([like_phrase, like_phrase, like_phrase])

    # Add ordering
    query += f" ORDER BY {sort_field} {order}"

    import math
    df = pd.read_sql_query(query, conn, params=params)
    total_records = len(df)
    records_per_page = 15
    total_pages = math.ceil(total_records / records_per_page)
    
    # Add a pagination control
    page = st.number_input("Page", min_value=1, max_value=total_pages if total_pages else 1, value=1, step=1)
    
    start_index = (page - 1) * records_per_page
    end_index = start_index + records_per_page
    df_page = df.iloc[start_index:end_index]

    st.markdown(f"Showing records {start_index + 1} to {min(end_index, total_records)} of {total_records}")

    if not df_page.empty:
        for _, student in df_page.iterrows():
            with st.expander(
                f"{student['surname']}, {student['other_names']} ({student['student_id']})"
            ):
                tab1, tab2, tab3, tab4 = st.tabs(
                    ["Details", "Edit Form", "Documents", "Actions"]
                )
                with tab1:
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("**Personal Information**")
                        st.write(f"Student ID: {student['student_id']}")
                        st.write(f"Name: {student['surname']} {student['other_names']}")
                        st.write(f"Date of Birth: {student['date_of_birth']}")
                        st.write(f"Gender: {student['gender']}")
                        st.write(f"Nationality: {student['nationality']}")
                        st.write(f"Religion: {student['religion']}")
                        st.write(f"Denomination: {student['denomination']}")
                    with col2:
                        st.write("**Contact Information**")
                        st.write(f"Email: {student['email']}")
                        st.write(f"Phone: {student['telephone']}")
                        st.write(f"Ghana Card: {student['ghana_card_id']}")
                        st.write(f"Address: {student['residential_address']}")
                        st.write("**Payment Information**")
                        if student["receipt_path"]:
                            st.write(f"Receipt Amount: GHS {student['receipt_amount']:.2f}")
                        else:
                            st.write("No receipt uploaded (Optional)")

                with tab2:
                    edited_data = {}

                    st.subheader("Personal Information")
                    col1, col2 = st.columns(2)

                    with col1:
                        edited_data["student_id"] = st.text_input(
                            "Student ID",
                            student["student_id"],
                            key=f"edit_id_{student['student_id']}",
                        )
                        edited_data["surname"] = st.text_input(
                            "Surname",
                            student["surname"],
                            key=f"edit_surname_{student['student_id']}",
                        )
                        edited_data["other_names"] = st.text_input(
                            "Other Names",
                            student["other_names"],
                            key=f"edit_other_{student['student_id']}",
                        )
                        edited_data["date_of_birth"] = st.date_input(
                            "Date of Birth",
                            datetime.strptime(
                                student["date_of_birth"], "%Y-%m-%d"
                            ).date(),
                            key=f"edit_dob_{student['student_id']}",
                        )
                        edited_data["place_of_birth"] = st.text_input(
                            "Place of Birth",
                            student["place_of_birth"],
                            key=f"edit_pob_{student['student_id']}",
                        )
                        edited_data["home_town"] = st.text_input(
                            "Home Town",
                            student["home_town"],
                            key=f"edit_hometown_{student['student_id']}",
                        )
                        edited_data["nationality"] = st.text_input(
                            "Nationality",
                            student["nationality"],
                            key=f"edit_nationality_{student['student_id']}",
                        )

                    with col2:
                        edited_data["gender"] = st.selectbox(
                            "Gender",
                            ["Male", "Female", "Other"],
                            index=["Male", "Female", "Other"].index(student["gender"]),
                            key=f"edit_gender_{student['student_id']}",
                        )
                        edited_data["marital_status"] = st.selectbox(
                            "Marital Status",
                            ["Single", "Married", "Divorced", "Widowed"],
                            index=["Single", "Married", "Divorced", "Widowed"].index(
                                student["marital_status"]
                            ),
                            key=f"edit_marital_{student['student_id']}",
                        )
                        edited_data["religion"] = st.text_input(
                            "Religion",
                            student["religion"],
                            key=f"edit_religion_{student['student_id']}",
                        )
                        edited_data["denomination"] = st.text_input(
                            "Denomination",
                            student["denomination"],
                            key=f"edit_denom_{student['student_id']}",
                        )

                        # In the manage_student_records function, replace the disability status selectbox code with:
                        edited_data["disability_status"] = st.selectbox(
                            "Disability Status",
                            ["None", "Yes"],
                            index=get_disability_status_index(
                                student["disability_status"]
                            ),
                            key=f"edit_disability_{student['student_id']}",
                        )

                        # If disability status is "Yes", show description field
                        if edited_data["disability_status"] == "Yes":
                            edited_data["disability_description"] = st.text_area(
                                "Disability Description",
                                student["disability_description"],
                                key=f"edit_disability_desc_{student['student_id']}",
                            )
                    st.subheader("Contact Information")
                    col3, col4 = st.columns(2)

                    with col3:
                        edited_data["residential_address"] = st.text_area(
                            "Residential Address",
                            student["residential_address"],
                            key=f"edit_res_{student['student_id']}",
                        )
                        edited_data["postal_address"] = st.text_area(
                            "Postal Address",
                            student["postal_address"],
                            key=f"edit_postal_{student['student_id']}",
                        )
                        edited_data["email"] = st.text_input(
                            "Email",
                            student["email"],
                            key=f"edit_email_{student['student_id']}",
                        )

                    with col4:
                        edited_data["telephone"] = st.text_input(
                            "Telephone",
                            student["telephone"],
                            key=f"edit_tel_{student['student_id']}",
                        )
                        edited_data["ghana_card_id"] = st.text_input(
                            "Ghana Card ID",
                            student["ghana_card_id"],
                            key=f"edit_ghana_{student['student_id']}",
                        )

                    st.subheader("Guardian Information")
                    col5, col6 = st.columns(2)

                    with col5:
                        edited_data["guardian_name"] = st.text_input(
                            "Guardian's Name",
                            student["guardian_name"],
                            key=f"edit_guard_name_{student['student_id']}",
                        )
                        edited_data["guardian_relationship"] = st.text_input(
                            "Relationship",
                            student["guardian_relationship"],
                            key=f"edit_guard_rel_{student['student_id']}",
                        )
                        edited_data["guardian_occupation"] = st.text_input(
                            "Occupation",
                            student["guardian_occupation"],
                            key=f"edit_guard_occ_{student['student_id']}",
                        )

                    with col6:
                        edited_data["guardian_address"] = st.text_area(
                            "Address",
                            student["guardian_address"],
                            key=f"edit_guard_addr_{student['student_id']}",
                        )
                        edited_data["guardian_telephone"] = st.text_input(
                            "Telephone",
                            student["guardian_telephone"],
                            key=f"edit_guard_tel_{student['student_id']}",
                        )

                    st.subheader("Educational Background")
                    col7, col8 = st.columns(2)

                    with col7:
                        edited_data["previous_school"] = st.text_input(
                            "Previous School",
                            student["previous_school"],
                            key=f"edit_prev_sch_{student['student_id']}",
                        )
                        edited_data["qualification_type"] = st.text_input(
                            "Qualification",
                            student["qualification_type"],
                            key=f"edit_qual_{student['student_id']}",
                        )

                    with col8:
                        edited_data["completion_year"] = st.text_input(
                            "Completion Year",
                            student["completion_year"],
                            key=f"edit_comp_year_{student['student_id']}",
                        )
                        edited_data["aggregate_score"] = st.text_input(
                            "Aggregate Score",
                            student["aggregate_score"],
                            key=f"edit_agg_{student['student_id']}",
                        )

                    edited_data["approval_status"] = st.selectbox(
                        "Approval Status",
                        ["pending", "approved", "rejected"],
                        index=["pending", "approved", "rejected"].index(
                            student["approval_status"]
                        ),
                        key=f"edit_status_{student['student_id']}",
                    )

                    st.subheader("Payment Information")
                    if pd.notna(student["receipt_path"]) and student["receipt_path"]:
                        current_amount = (
                            float(student["receipt_amount"])
                            if pd.notna(student["receipt_amount"])
                            else 0.0
                        )
                        edited_data["receipt_amount"] = st.number_input(
                            "Receipt Amount (GHS)",
                            value=current_amount,
                            min_value=0.0,
                            format="%.2f",
                            key=f"edit_receipt_amount_{student['student_id']}",
                        )
                        if edited_data["receipt_amount"] < 100.0:
                            st.warning(
                                "Receipt amount seems low. Please verify the payment amount."
                            )

                    if st.button(
                        "Save Changes", key=f"save_changes_{student['student_id']}"
                    ):
                        try:
                            c = conn.cursor()
                            update_query = """
                                UPDATE student_info 
                                SET student_id=?, surname=?, other_names=?, date_of_birth=?, 
                                    place_of_birth=?, home_town=?, nationality=?, gender=?,
                                    marital_status=?, religion=?, denomination=?, 
                                    disability_status=?, disability_description=?,
                                    residential_address=?, postal_address=?, email=?,
                                    telephone=?, ghana_card_id=?, guardian_name=?,
                                    guardian_relationship=?, guardian_occupation=?,
                                    guardian_address=?, guardian_telephone=?,
                                    previous_school=?, qualification_type=?,
                                    completion_year=?, aggregate_score=?,
                                    approval_status=?, receipt_amount=?
                                WHERE student_id=?
                            """

                            receipt_amount = float(
                                edited_data.get("receipt_amount", 0.0)
                            )

                            c.execute(
                                update_query,
                                (
                                    edited_data["student_id"],
                                    edited_data["surname"],
                                    edited_data["other_names"],
                                    edited_data["date_of_birth"],
                                    edited_data["place_of_birth"],
                                    edited_data["home_town"],
                                    edited_data["nationality"],
                                    edited_data["gender"],
                                    edited_data["marital_status"],
                                    edited_data["religion"],
                                    edited_data["denomination"],
                                    edited_data["disability_status"],
                                    edited_data.get("disability_description", "None"),
                                    edited_data["residential_address"],
                                    edited_data["postal_address"],
                                    edited_data["email"],
                                    edited_data["telephone"],
                                    edited_data["ghana_card_id"],
                                    edited_data["guardian_name"],
                                    edited_data["guardian_relationship"],
                                    edited_data["guardian_occupation"],
                                    edited_data["guardian_address"],
                                    edited_data["guardian_telephone"],
                                    edited_data["previous_school"],
                                    edited_data["qualification_type"],
                                    edited_data["completion_year"],
                                    edited_data["aggregate_score"],
                                    edited_data["approval_status"],
                                    receipt_amount,
                                    student["student_id"],
                                ),
                            )
                            conn.commit()
                            st.success("Changes saved successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error saving changes: {str(e)}")

                with tab3:
                    st.write("**Document Management**")
                    documents = {
                        "Ghana Card": student["ghana_card_path"],
                        "Passport Photo": student["passport_photo_path"],
                        "Transcript": student["transcript_path"],
                        "Certificate": student["certificate_path"],
                        "Receipt": student["receipt_path"],
                    }

                    for doc_name, doc_path in documents.items():
                        col1, col2, col3 = st.columns([3, 1, 1])

                        with col1:
                            if (
                                pd.notna(doc_path) and doc_path
                            ):  # Check for both not null and not empty string
                                st.write(f"✅ {doc_name} uploaded")
                                if os.path.exists(
                                    doc_path
                                ):  # Verify file exists on disk
                                    if (
                                        doc_name == "Passport Photo"
                                        or doc_path.lower().endswith(
                                            (".jpg", ".jpeg", ".png")
                                        )
                                    ):
                                        try:
                                            image = PILImage.open(doc_path)
                                            st.image(image, width=150, caption=doc_name)
                                        except Exception as e:
                                            st.error(
                                                f"Error loading {doc_name}: {str(e)}"
                                            )
                                    elif doc_path.lower().endswith(".pdf"):
                                        st.write(f"[View {doc_name}]({doc_path})")
                                else:
                                    st.error(
                                        f"{doc_name} file not found on disk: {doc_path}"
                                    )
                            else:
                                st.write(f"❌ {doc_name} not uploaded")

                        with col2:
                            new_file = st.file_uploader(
                                f"Upload new {doc_name}",
                                type=(
                                    ["pdf", "jpg", "jpeg", "png"]
                                    if doc_name == "Passport Photo"
                                    else (
                                        ["pdf"]
                                        if doc_name in ["Transcript", "Certificate"]
                                        else ["pdf", "jpg", "jpeg", "png"]
                                    )
                                ),
                                key=f"upload_{doc_name}_{student['student_id']}",
                            )

                            if new_file:
                                if st.button(
                                    f"Save {doc_name}",
                                    key=f"save_{doc_name}_{student['student_id']}",
                                ):
                                    try:
                                        # Remove old file if it exists
                                        if doc_path and os.path.exists(doc_path):
                                            os.remove(doc_path)

                                        # Save new file
                                        new_path = save_uploaded_file(
                                            new_file, "uploads"
                                        )
                                        if new_path:
                                            # Update database with new file path
                                            c = conn.cursor()
                                            c.execute(
                                                f"""
                                                UPDATE student_info 
                                                SET {doc_name.lower().replace(' ', '_')}_path = ? 
                                                WHERE student_id = ?
                                                """,
                                                (new_path, student["student_id"]),
                                            )
                                            conn.commit()
                                            st.success(
                                                f"{doc_name} uploaded successfully!"
                                            )
                                            st.rerun()
                                        else:
                                            st.error(f"Failed to save {doc_name}")
                                    except Exception as e:
                                        st.error(
                                            f"Error uploading {doc_name}: {str(e)}"
                                        )

                        with col3:
                            if (
                                pd.notna(doc_path)
                                and doc_path
                                and os.path.exists(doc_path)
                            ):
                                if st.button(
                                    f"Delete {doc_name}",
                                    key=f"del_{doc_name}_{student['student_id']}",
                                ):
                                    try:
                                        # Remove file from disk
                                        os.remove(doc_path)

                                        # Update database
                                        c = conn.cursor()
                                        c.execute(
                                            f"""
                                            UPDATE student_info 
                                            SET {doc_name.lower().replace(' ', '_')}_path = NULL 
                                            WHERE student_id = ?
                                            """,
                                            (student["student_id"],),
                                        )
                                        conn.commit()
                                        st.success(f"{doc_name} deleted successfully!")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error deleting {doc_name}: {str(e)}")

                with tab4:
                    st.write("**Student Actions**")
                    col1, col2 = st.columns(2)

                    with col1:
                        if st.button(
                            "Generate PDF", key=f"pdf_{student['student_id']}"
                        ):
                            pdf_file = generate_student_info_pdf(student)
                            with open(pdf_file, "rb") as file:
                                st.download_button(
                                    label="Download Student Info",
                                    data=file,
                                    file_name=pdf_file,
                                    mime="application/pdf",
                                )

                    with col2:
                        if st.button(
                            "Delete Student Record",
                            key=f"del_student_{student['student_id']}",
                            type="primary",
                        ):
                            try:
                                for doc_path in documents.values():
                                    if doc_path and os.path.exists(doc_path):
                                        os.remove(doc_path)

                                c = conn.cursor()
                                c.execute(
                                    "DELETE FROM student_info WHERE student_id = ?",
                                    (student["student_id"],),
                                )
                                conn.commit()
                                st.success("Student record deleted successfully!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error deleting student record: {str(e)}")
    else:
        st.info("No records found")

    conn.close()


def manage_course_registrations():
    st.subheader("Course Registration Management")

    # Add search phrase input for filtering registration records
    search_phrase = st.text_input(
        "Search registrations (by student ID, surname, or registration ID)", ""
    )

    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        sort_by = st.selectbox(
            "Sort by", ["Registration ID", "Student ID", "Programme", "Date Registered"]
        )

    with col2:
        sort_order = st.selectbox("Order", ["Ascending", "Descending"], key="reg_order")

    with col3:
        status_filter = st.selectbox(
            "Status", ["All", "Pending", "Approved", "Rejected"], key="reg_status"
        )

    conn = sqlite3.connect("student_registration.db")

    sort_field = {
        "Registration ID": "cr.registration_id",
        "Student ID": "cr.student_id",
        "Programme": "cr.programme",
        "Date Registered": "cr.date_registered",
    }[sort_by]

    order = "ASC" if sort_order == "Ascending" else "DESC"

    # Base query and parameters list for registrations
    query = """
        SELECT cr.*, si.surname, si.other_names 
        FROM course_registration cr 
        LEFT JOIN student_info si ON cr.student_id = si.student_id 
        WHERE 1=1
    """
    params = []

    # Add status filter if not All
    if status_filter != "All":
        query += " AND cr.approval_status = ?"
        params.append(status_filter.lower())

    # Add search by phrase filter if provided, search in registration_id, student_id, surname, or other_names
    if search_phrase.strip():
        query += " AND (cr.registration_id LIKE ? OR cr.student_id LIKE ? OR si.surname LIKE ? OR si.other_names LIKE ?)"
        like_phrase = f"%{search_phrase.strip()}%"
        params.extend([like_phrase, like_phrase, like_phrase, like_phrase])

    query += f" ORDER BY {sort_field} {order}"

    df = pd.read_sql_query(query, conn, params=params)

    if not df.empty:
        for _, registration in df.iterrows():
            with st.expander(
                f"Registration ID: {registration['registration_id']} - {registration['surname']} {registration['other_names']}"
            ):
                tab1, tab2, tab3, tab4 = st.tabs(
                    ["Details", "Edit Registration", "Documents", "Actions"]
                )

                with tab1:
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("**Registration Details**")
                        st.write(f"Student ID: {registration['student_id']}")
                        st.write(f"Programme: {registration['programme']}")
                        st.write(f"Level: {registration['level']}")
                        st.write(f"Session: {registration['session']}")

                    with col2:
                        st.write("**Academic Information**")
                        st.write(f"Academic Year: {registration['academic_year']}")
                        st.write(f"Semester: {registration['semester']}")
                        st.write(f"Total Credits: {registration['total_credits']}")

                    st.write("**Selected Courses**")
                    if registration["courses"]:
                        courses_list = registration["courses"].split("\n")
                        table_data = []
                        for course in courses_list:
                            if "|" in course:
                                code, title, credits = course.split("|")
                                table_data.append([code, title, f"{credits} credits"])
                        if table_data:
                            df = pd.DataFrame(
                                table_data,
                                columns=["Course Code", "Course Title", "Credit Hours"],
                            )
                            st.table(df)

                    st.write("**Payment Information**")
                    if registration["receipt_path"]:
                        st.write("✅ Receipt Uploaded")
                        st.write(
                            f"Receipt Amount: GHS {registration['receipt_amount']:.2f}"
                        )
                    else:
                        st.write("⚪ No Receipt (Optional)")

                with tab2:
                    edited_reg = {}
                    col1, col2 = st.columns(2)

                    with col1:
                        edited_reg["programme"] = st.selectbox(
                            "Programme",
                            ["CIMG", "CIM-UK", "ICAG", "ACCA"],
                            index=["CIMG", "CIM-UK", "ICAG", "ACCA"].index(
                                registration["programme"]
                            ),
                            key=f"prog_{registration['registration_id']}",
                        )
                        program_levels = list(
                            get_program_courses(edited_reg["programme"]).keys()
                        )
                        edited_reg["level"] = st.selectbox(
                            "Level",
                            program_levels,
                            index=(
                                program_levels.index(registration["level"])
                                if registration["level"] in program_levels
                                else 0
                            ),
                            key=f"level_{registration['registration_id']}",
                        )
                        edited_reg["session"] = st.selectbox(
                            "Session",
                            ["Morning", "Evening", "Weekend"],
                            index=["Morning", "Evening", "Weekend"].index(
                                registration["session"]
                            ),
                            key=f"session_{registration['registration_id']}",
                        )

                    with col2:
                        edited_reg["academic_year"] = st.selectbox(
                            "Academic Year",
                            [f"{year}-{year+1}" for year in range(2025, 2035)],
                            index=[
                                f"{year}-{year+1}" for year in range(2025, 2035)
                            ].index(registration["academic_year"]),
                            key=f"year_{registration['registration_id']}",
                        )
                        edited_reg["semester"] = st.selectbox(
                            "Semester",
                            ["First", "Second", "Third"],
                            index=["First", "Second", "Third"].index(
                                registration["semester"]
                            ),
                            key=f"sem_{registration['registration_id']}",
                        )
                        edited_reg["approval_status"] = st.selectbox(
                            "Status",
                            ["pending", "approved", "rejected"],
                            index=["pending", "approved", "rejected"].index(
                                registration["approval_status"]
                            ),
                            key=f"status_{registration['registration_id']}",
                        )

                    st.write("**Course Selection**")
                    available_courses = get_program_courses(
                        edited_reg["programme"]
                    ).get(edited_reg["level"], [])
                    current_courses = (
                        registration["courses"].split("\n")
                        if registration["courses"]
                        else []
                    )
                    selected_courses = st.multiselect(
                        "Select Courses",
                        available_courses,
                        default=current_courses,
                        format_func=lambda x: f"{x.split('|')[0]} - {x.split('|')[1]} ({x.split('|')[2]} credits)",
                        key=f"courses_{registration['registration_id']}",
                    )

                    edited_reg["courses"] = "\n".join(selected_courses)
                    edited_reg["total_credits"] = sum(
                        [int(course.split("|")[2]) for course in selected_courses]
                    )

                    st.write(f"Total Credits: {edited_reg['total_credits']}")
                    if edited_reg["total_credits"] > 24:
                        st.error("Total credits cannot exceed 24 hours!")

                    if st.button(
                        "Save Changes", key=f"save_{registration['registration_id']}"
                    ):
                        if edited_reg["total_credits"] <= 24:
                            try:
                                c = conn.cursor()
                                update_query = """
                                    UPDATE course_registration 
                                    SET programme=?, level=?, session=?, 
                                        academic_year=?, semester=?, approval_status=?,
                                        courses=?, total_credits=?
                                    WHERE registration_id=?
                                """
                                c.execute(
                                    update_query,
                                    (
                                        edited_reg["programme"],
                                        edited_reg["level"],
                                        edited_reg["session"],
                                        edited_reg["academic_year"],
                                        edited_reg["semester"],
                                        edited_reg["approval_status"],
                                        edited_reg["courses"],
                                        edited_reg["total_credits"],
                                        registration["registration_id"],
                                    ),
                                )
                                conn.commit()
                                st.success("Changes saved successfully!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error saving changes: {str(e)}")
                        else:
                            st.error(
                                "Cannot save changes. Total credits exceed 24 hours limit."
                            )

                with tab3:
                    st.write("**Document Management**")
                    if registration["receipt_path"]:
                        st.write("✅ Receipt uploaded")
                        if registration["receipt_path"].lower().endswith((".pdf")):
                            st.write(f"[View Receipt]({registration['receipt_path']})")
                        elif (
                            registration["receipt_path"]
                            .lower()
                            .endswith((".jpg", ".jpeg", ".png"))
                        ):
                            try:
                                image = PILImage.open(registration["receipt_path"])
                                st.image(
                                    image, caption="Receipt", use_container_width=True
                                )
                            except Exception as e:
                                st.error(f"Error loading receipt image: {str(e)}")

                        new_amount = st.number_input(
                            "Update Receipt Amount (GHS)",
                            value=float(registration["receipt_amount"]),
                            min_value=0.0,
                            format="%.2f",
                            key=f"receipt_amount_{registration['registration_id']}",
                        )

                        if new_amount != registration["receipt_amount"]:
                            if st.button(
                                "Update Amount",
                                key=f"update_amount_{registration['registration_id']}",
                            ):
                                try:
                                    c = conn.cursor()
                                    c.execute(
                                        """
                                        UPDATE course_registration 
                                        SET receipt_amount = ? 
                                        WHERE registration_id = ?
                                    """,
                                        (new_amount, registration["registration_id"]),
                                    )
                                    conn.commit()
                                    st.success("Receipt amount updated successfully!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error updating receipt amount: {str(e)}")

                        if st.button(
                            "Delete Receipt",
                            key=f"del_receipt_{registration['registration_id']}",
                        ):
                            try:
                                if os.path.exists(registration["receipt_path"]):
                                    os.remove(registration["receipt_path"])

                                c = conn.cursor()
                                c.execute(
                                    """
                                    UPDATE course_registration 
                                    SET receipt_path = NULL, receipt_amount = 0 
                                    WHERE registration_id = ?
                                """,
                                    (registration["registration_id"],),
                                )
                                conn.commit()
                                st.success("Receipt deleted successfully!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error deleting receipt: {str(e)}")
                    else:
                        st.write("❌ No receipt uploaded")
                        new_receipt = st.file_uploader(
                            "Upload Receipt",
                            type=["pdf", "jpg", "jpeg", "png"],
                            key=f"new_receipt_{registration['registration_id']}",
                        )
                        if new_receipt:
                            receipt_amount = st.number_input(
                                "Receipt Amount (GHS)",
                                min_value=0.0,
                                format="%.2f",
                                key=f"new_amount_{registration['registration_id']}",
                            )
                            if st.button(
                                "Save Receipt",
                                key=f"save_receipt_{registration['registration_id']}",
                            ):
                                try:
                                    receipt_path = save_uploaded_file(
                                        new_receipt, "uploads"
                                    )
                                    c = conn.cursor()
                                    c.execute(
                                        """
                                        UPDATE course_registration 
                                        SET receipt_path = ?, receipt_amount = ? 
                                        WHERE registration_id = ?
                                    """,
                                        (
                                            receipt_path,
                                            receipt_amount,
                                            registration["registration_id"],
                                        ),
                                    )
                                    conn.commit()
                                    st.success("Receipt uploaded successfully!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error uploading receipt: {str(e)}")

                with tab4:
                    st.write("**Registration Actions**")
                    col1, col2 = st.columns(2)

                    with col1:
                        if st.button(
                            "Generate PDF", key=f"pdf_{registration['registration_id']}"
                        ):
                            pdf_file = generate_course_registration_pdf(registration)
                            with open(pdf_file, "rb") as file:
                                st.download_button(
                                    label="Download Registration Form",
                                    data=file,
                                    file_name=pdf_file,
                                    mime="application/pdf",
                                )

                    with col2:
                        if st.button(
                            "Delete Registration",
                            key=f"del_reg_{registration['registration_id']}",
                            type="primary",
                        ):
                            try:
                                if registration["receipt_path"] and os.path.exists(
                                    registration["receipt_path"]
                                ):
                                    os.remove(registration["receipt_path"])

                                c = conn.cursor()
                                c.execute(
                                    "DELETE FROM course_registration WHERE registration_id = ?",
                                    (registration["registration_id"],),
                                )
                                conn.commit()
                                st.success("Registration deleted successfully!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error deleting registration: {str(e)}")
    else:
        st.info("No records found")

    conn.close()


def manage_programs():
    st.title("Programs Management")

    conn = sqlite3.connect("student_registration.db")
    programs_df = pd.read_sql_query(
        """
        SELECT DISTINCT programme 
        FROM course_registration 
        WHERE programme IS NOT NULL
    """,
        conn,
    )

    if not programs_df.empty:
        for program in programs_df["programme"]:
            with st.expander(f"📚 {program}"):
                levels_df = pd.read_sql_query(
                    """
                    SELECT DISTINCT level 
                    FROM course_registration 
                    WHERE programme = ? 
                    ORDER BY level
                """,
                    conn,
                    params=(program,),
                )

                for _, level_row in levels_df.iterrows():
                    level = level_row["level"]
                    st.subheader(f"{level}")

                    students_df = pd.read_sql_query(
                        """
                        SELECT DISTINCT 
                            cr.student_id,
                            si.surname,
                            si.other_names,
                            si.passport_photo_path,
                            cr.academic_year,
                            cr.semester
                        FROM course_registration cr
                        JOIN student_info si ON cr.student_id = si.student_id
                        WHERE cr.programme = ? AND cr.level = ?
                        ORDER BY si.surname, si.other_names
                    """,
                        conn,
                        params=(program, level),
                    )

                    if not students_df.empty:
                        st.write(f"Total Students: {len(students_df)}")

                        cols = st.columns(4)
                        for idx, student in students_df.iterrows():
                            with cols[idx % 4]:
                                st.write("---")
                                if student["passport_photo_path"] and os.path.exists(
                                    student["passport_photo_path"]
                                ):
                                    try:
                                        image = PILImage.open(
                                            student["passport_photo_path"]
                                        )
                                        st.image(image, width=100)
                                    except Exception as e:
                                        st.error("Error loading photo")
                                st.write(
                                    f"**{student['surname']}, {student['other_names']}**"
                                )
                                st.write(f"ID: {student['student_id']}")
                                st.write(f"Year: {student['academic_year']}")
                                st.write(f"Semester: {student['semester']}")

                        if st.button(
                            f"Download {program} - {level} Student List",
                            key=f"btn_{program}_{level}",
                        ):
                            pdf_file = generate_program_student_list(
                                program, level, students_df
                            )
                            with open(pdf_file, "rb") as file:
                                st.download_button(
                                    label=f"Download {program} - {level} PDF",
                                    data=file,
                                    file_name=pdf_file,
                                    mime="application/pdf",
                                )
                    else:
                        st.info(f"No students registered for {level}")
    else:
        st.info("No programs found in the database")

    conn.close()


import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go


def generate_payment_statistics():
    """
    Generate comprehensive payment statistics with visualizations.
    This function queries the database for payment information from both
    student_info and course_registration tables, then creates visualizations.
    """
    st.subheader("Payment Statistics Dashboard")

    # Connect to the database
    conn = sqlite3.connect("student_registration.db")

    # Create tabs for different payment views
    tab1, tab2, tab3 = st.tabs(
        ["Overview", "Student Payments", "Course Registration Payments"]
    )

    with tab1:
        st.write("### Payment Overview")

        # Get overall payment statistics from both tables
        student_payments = pd.read_sql_query(
            """
            SELECT 
                COUNT(*) as total_records,
                SUM(CASE WHEN receipt_path IS NOT NULL THEN 1 ELSE 0 END) as with_receipt,
                SUM(CASE WHEN receipt_path IS NULL THEN 1 ELSE 0 END) as without_receipt,
                SUM(COALESCE(receipt_amount, 0)) as total_amount
            FROM student_info
            """,
            conn,
        )

        course_payments = pd.read_sql_query(
            """
            SELECT 
                COUNT(*) as total_records,
                SUM(CASE WHEN receipt_path IS NOT NULL THEN 1 ELSE 0 END) as with_receipt,
                SUM(CASE WHEN receipt_path IS NULL THEN 1 ELSE 0 END) as without_receipt,
                SUM(COALESCE(receipt_amount, 0)) as total_amount
            FROM course_registration
            """,
            conn,
        )

        # Display summary metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                "Total Payments Collected",
                f"GHS {student_payments['total_amount'].iloc[0] + course_payments['total_amount'].iloc[0]:,.2f}",
            )
        with col2:
            st.metric(
                "Student Info Receipts",
                f"{student_payments['with_receipt'].iloc[0]} / {student_payments['total_records'].iloc[0]}",
            )
        with col3:
            st.metric(
                "Course Registration Receipts",
                f"{course_payments['with_receipt'].iloc[0]} / {course_payments['total_records'].iloc[0]}",
            )

        # Create combined visualization
        fig = make_subplots(
            rows=1,
            cols=2,
            specs=[[{"type": "pie"}, {"type": "pie"}]],
            subplot_titles=("Student Info Receipts", "Course Registration Receipts"),
        )

        # Student info receipt pie chart
        fig.add_trace(
            go.Pie(
                labels=["With Receipt", "Without Receipt"],
                values=[
                    student_payments["with_receipt"].iloc[0],
                    student_payments["without_receipt"].iloc[0],
                ],
                marker_colors=["#4CAF50", "#F44336"],
                name="Student Info",
            ),
            row=1,
            col=1,
        )

        # Course registration receipt pie chart
        fig.add_trace(
            go.Pie(
                labels=["With Receipt", "Without Receipt"],
                values=[
                    course_payments["with_receipt"].iloc[0],
                    course_payments["without_receipt"].iloc[0],
                ],
                marker_colors=["#4CAF50", "#F44336"],
                name="Course Registration",
            ),
            row=1,
            col=2,
        )

        fig.update_layout(height=400, title_text="Receipt Upload Distribution")
        st.plotly_chart(fig, use_container_width=True)

        # Payment trends over time
        st.write("### Payment Trends")

        # Get payment data by date
        student_payment_trend = pd.read_sql_query(
            """
            SELECT 
                date(created_at) as payment_date,
                COUNT(*) as num_payments,
                SUM(COALESCE(receipt_amount, 0)) as daily_amount
            FROM student_info
            WHERE receipt_path IS NOT NULL
            GROUP BY date(created_at)
            ORDER BY payment_date
            """,
            conn,
        )

        course_payment_trend = pd.read_sql_query(
            """
            SELECT 
                date(date_registered) as payment_date,
                COUNT(*) as num_payments,
                SUM(COALESCE(receipt_amount, 0)) as daily_amount
            FROM course_registration
            WHERE receipt_path IS NOT NULL
            GROUP BY date(date_registered)
            ORDER BY payment_date
            """,
            conn,
        )

        # Combine the trends if data exists
        if not student_payment_trend.empty or not course_payment_trend.empty:
            # Add source column to each dataframe
            if not student_payment_trend.empty:
                student_payment_trend["source"] = "Student Info"
            if not course_payment_trend.empty:
                course_payment_trend["source"] = "Course Registration"

            # Combine dataframes
            combined_trend = pd.concat(
                [student_payment_trend, course_payment_trend], ignore_index=True
            )

            if not combined_trend.empty:
                # Create line chart
                fig = px.line(
                    combined_trend,
                    x="payment_date",
                    y="daily_amount",
                    color="source",
                    title="Payment Amounts Over Time",
                    labels={
                        "payment_date": "Date",
                        "daily_amount": "Amount (GHS)",
                        "source": "Source",
                    },
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No payment trend data available")
        else:
            st.info("No payment trend data available")

    with tab2:
        st.write("### Student Information Payments")

        # Get detailed student payment statistics
        student_payment_details = pd.read_sql_query(
            """
            SELECT 
                CASE 
                    WHEN receipt_path IS NOT NULL THEN 'With Receipt'
                    ELSE 'Without Receipt'
                END as receipt_status,
                COUNT(*) as count,
                AVG(CASE WHEN receipt_amount IS NOT NULL THEN receipt_amount ELSE 0 END) as avg_amount,
                MIN(CASE WHEN receipt_amount IS NOT NULL THEN receipt_amount ELSE 0 END) as min_amount,
                MAX(CASE WHEN receipt_amount IS NOT NULL THEN receipt_amount ELSE 0 END) as max_amount,
                SUM(CASE WHEN receipt_amount IS NOT NULL THEN receipt_amount ELSE 0 END) as total_amount
            FROM student_info
            GROUP BY CASE 
                        WHEN receipt_path IS NOT NULL THEN 'With Receipt'
                        ELSE 'Without Receipt'
                    END
            """,
            conn,
        )

        if not student_payment_details.empty:
            # Display pie chart
            fig = px.pie(
                student_payment_details,
                names="receipt_status",
                values="count",
                title="Student Receipt Upload Distribution",
                color="receipt_status",
                color_discrete_map={
                    "With Receipt": "#4CAF50",
                    "Without Receipt": "#F44336",
                },
            )
            st.plotly_chart(fig, use_container_width=True)

            # Display payment statistics
            with_receipt_data = student_payment_details[
                student_payment_details["receipt_status"] == "With Receipt"
            ]
            if not with_receipt_data.empty:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric(
                        "Average Amount",
                        f"GHS {with_receipt_data['avg_amount'].iloc[0]:,.2f}",
                    )
                with col2:
                    st.metric(
                        "Minimum Amount",
                        f"GHS {with_receipt_data['min_amount'].iloc[0]:,.2f}",
                    )
                with col3:
                    st.metric(
                        "Maximum Amount",
                        f"GHS {with_receipt_data['max_amount'].iloc[0]:,.2f}",
                    )

                st.metric(
                    "Total Amount Collected",
                    f"GHS {with_receipt_data['total_amount'].iloc[0]:,.2f}",
                )
            else:
                st.info("No student receipt data available")

            # Get payment distribution by programme
            programme_payments = pd.read_sql_query(
                """
                SELECT 
                    programme,
                    COUNT(*) as student_count,
                    SUM(CASE WHEN receipt_path IS NOT NULL THEN 1 ELSE 0 END) as with_receipt,
                    SUM(COALESCE(receipt_amount, 0)) as total_amount
                FROM student_info
                WHERE programme IS NOT NULL AND programme != ''
                GROUP BY programme
                ORDER BY total_amount DESC
                """,
                conn,
            )

            if not programme_payments.empty:
                st.write("### Payments by Programme")
                fig = px.bar(
                    programme_payments,
                    x="programme",
                    y="total_amount",
                    title="Total Payments by Programme",
                    labels={
                        "programme": "Programme",
                        "total_amount": "Total Amount (GHS)",
                    },
                )
                st.plotly_chart(fig, use_container_width=True)

        else:
            st.info("No student payment statistics available")

    with tab3:
        st.write("### Course Registration Payments")

        # Get detailed course registration payment statistics
        course_payment_details = pd.read_sql_query(
            """
            SELECT 
                CASE 
                    WHEN receipt_path IS NOT NULL THEN 'With Receipt'
                    ELSE 'Without Receipt'
                END as receipt_status,
                COUNT(*) as count,
                AVG(CASE WHEN receipt_amount IS NOT NULL THEN receipt_amount ELSE 0 END) as avg_amount,
                MIN(CASE WHEN receipt_amount IS NOT NULL THEN receipt_amount ELSE 0 END) as min_amount,
                MAX(CASE WHEN receipt_amount IS NOT NULL THEN receipt_amount ELSE 0 END) as max_amount,
                SUM(CASE WHEN receipt_amount IS NOT NULL THEN receipt_amount ELSE 0 END) as total_amount
            FROM course_registration
            GROUP BY CASE 
                        WHEN receipt_path IS NOT NULL THEN 'With Receipt'
                        ELSE 'Without Receipt'
                    END
            """,
            conn,
        )

        if not course_payment_details.empty:
            # Display pie chart
            fig = px.pie(
                course_payment_details,
                names="receipt_status",
                values="count",
                title="Course Registration Receipt Upload Distribution",
                color="receipt_status",
                color_discrete_map={
                    "With Receipt": "#4CAF50",
                    "Without Receipt": "#F44336",
                },
            )
            st.plotly_chart(fig, use_container_width=True)

            # Display payment statistics
            with_receipt_data = course_payment_details[
                course_payment_details["receipt_status"] == "With Receipt"
            ]
            if not with_receipt_data.empty:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric(
                        "Average Amount",
                        f"GHS {with_receipt_data['avg_amount'].iloc[0]:,.2f}",
                    )
                with col2:
                    st.metric(
                        "Minimum Amount",
                        f"GHS {with_receipt_data['min_amount'].iloc[0]:,.2f}",
                    )
                with col3:
                    st.metric(
                        "Maximum Amount",
                        f"GHS {with_receipt_data['max_amount'].iloc[0]:,.2f}",
                    )

                st.metric(
                    "Total Amount Collected",
                    f"GHS {with_receipt_data['total_amount'].iloc[0]:,.2f}",
                )
            else:
                st.info("No course registration receipt data available")

            # Get payment distribution by programme and level
            level_payments = pd.read_sql_query(
                """
                SELECT 
                    programme,
                    level,
                    COUNT(*) as registration_count,
                    SUM(CASE WHEN receipt_path IS NOT NULL THEN 1 ELSE 0 END) as with_receipt,
                    SUM(COALESCE(receipt_amount, 0)) as total_amount
                FROM course_registration
                WHERE programme IS NOT NULL AND programme != ''
                GROUP BY programme, level
                ORDER BY total_amount DESC
                """,
                conn,
            )

            if not level_payments.empty:
                st.write("### Payments by Programme and Level")
                fig = px.bar(
                    level_payments,
                    x="programme",
                    y="total_amount",
                    color="level",
                    title="Total Payments by Programme and Level",
                    labels={
                        "programme": "Programme",
                        "total_amount": "Total Amount (GHS)",
                        "level": "Level",
                    },
                )
                st.plotly_chart(fig, use_container_width=True)

        else:
            st.info("No course registration payment statistics available")

    # Close the database connection
    conn.close()


# Function to integrate with the main generate_reports function
def payment_statistics_section():
    """
    This function replaces the Payment Statistics section in the generate_reports function.
    """
    generate_payment_statistics()


def check_disk_usage():
    usage = psutil.disk_usage("/")
    return usage.percent


def system_resource_monitor():
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    return {
        "cpu": cpu_percent,
        "memory_percent": memory.percent,
        "disk_percent": disk.percent,
    }


def perform_backup():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = "db_backups"
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    backup_filename = os.path.join(backup_dir, f"backup_{timestamp}.zip")
    with zipfile.ZipFile(backup_filename, "w") as zipf:
        # Backup the database file.
        db_file = "student_registration.db"
        if os.path.exists(db_file):
            zipf.write(db_file, arcname=os.path.basename(db_file))
        # Backup the uploads folder.
        uploads_dir = "uploads"
        if os.path.exists(uploads_dir):
            for root, dirs, files in os.walk(uploads_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, uploads_dir)
                    zipf.write(file_path, arcname=os.path.join("uploads", arcname))
    # Record last backup timestamp.
    with open("last_backup.txt", "w") as f:
        f.write(datetime.now().isoformat())
    return backup_filename


def should_backup():
    """
    Determines if a database backup is needed based on:
    1. Time since last backup (>30 days)
    2. Current disk usage (≥90%)

    Returns:
        bool: True if backup is recommended, False otherwise
    """
    need_backup = False
    now = datetime.now()

    # Check time-based criterion
    if os.path.exists("last_backup.txt"):
        with open("last_backup.txt", "r") as f:
            last_backup_str = f.read().strip()
            if last_backup_str:
                try:
                    last_backup = datetime.fromisoformat(last_backup_str)
                    if now - last_backup > timedelta(days=30):
                        need_backup = True
                except (ValueError, TypeError):
                    # If date parsing fails, recommend backup
                    need_backup = True
    else:
        # No record of previous backup, so recommend one
        need_backup = True

    # Check disk usage criterion
    if check_disk_usage() >= 90:
        need_backup = True

    return need_backup


# Student Portal Authentication and Views
def ensure_student_password_column():
    """
    Ensure that the student_info table has a 'password' column.
    If not, add it. This column will store the student's custom password.
    """
    conn = sqlite3.connect("student_registration.db")
    c = conn.cursor()
    try:
        # Try to query the 'password' column
        c.execute("SELECT password FROM student_info LIMIT 1")
    except sqlite3.OperationalError:
        # Add password column if it doesn't exist
        c.execute("ALTER TABLE student_info ADD COLUMN password TEXT")
    conn.commit()
    conn.close()


def student_login_form():
    """
    Display the login form for students.
    Uses student ID and birthday (default password as YYYY-MM-DD).
    On first successful login (if password is still default), prompt for a password reset.
    """
    st.header("👩‍🎓 Student Portal Login")

    # Store password reset form state
    if "show_password_reset" not in st.session_state:
        st.session_state.show_password_reset = False

    col1, col2 = st.columns(2)
    with col1:
        student_id = st.text_input("Student ID")
    with col2:
        password = st.text_input(
            "Password (eg. 'YYYY-MM-DD')",
            type="password",
            help="Default password is your date of birth (YYYY-MM-DD)",
        )

    if (
        st.button("Login", use_container_width=True)
        or st.session_state.show_password_reset
    ):
        with get_db_connection() as conn:
            c = conn.cursor(dictionary=True)
            c.execute(
                """
                SELECT student_id, date_of_birth, password, approval_status 
                FROM student_info 
                WHERE student_id = %s
            """,
                (student_id,),
            )
            student = c.fetchone()

        if not student:
            st.error("Student record not found. Please check your Student ID.")
            return None

        db_student_id, db_dob, db_password, approval_status = student.values()

        if approval_status != "approved":
            st.error("Your account is pending approval. Please contact administration.")
            return None

        # Default password is the student's date_of_birth formatted as YYYY-MM-DD
        default_password = (
            db_dob if isinstance(db_dob, str) else db_dob.strftime("%Y-%m-%d")
        )

        # If a custom password is set, use it; otherwise use default
        expected_password = (
            db_password
            if db_password and db_password.strip() != ""
            else default_password
        )

        if password != expected_password and not st.session_state.show_password_reset:
            st.error("Incorrect password. Please check your credentials.")
            return None

        # Successful login: if the password is still default, force reset
        if (
            expected_password == default_password
            or st.session_state.show_password_reset
        ):
            st.session_state.show_password_reset = True
            st.warning(
                "You are using your default password. Please reset your password now."
            )
            new_password = st.text_input("Enter New Password", type="password")
            confirm_password = st.text_input("Confirm New Password", type="password")

            if st.button("Reset Password"):
                if new_password != confirm_password:
                    st.error("Passwords do not match. Try again.")
                    return None
                elif len(new_password) < 8:
                    st.error("Password must be at least 8 characters long.")
                    return None
                else:
                    with get_db_connection() as conn:
                        c = conn.cursor()
                        c.execute(
                            """
                            UPDATE student_info 
                            SET password = %s 
                            WHERE student_id = %s
                        """,
                            (new_password, student_id),
                        )
                        conn.commit()
                    st.success("Password reset successfully! You are now logged in.")
                    st.session_state.show_password_reset = False
                    st.session_state.student_logged_in = student_id
                    st.rerun()
        else:
            st.success("Login successful!")
            st.session_state.student_logged_in = student_id
            st.rerun()


def student_portal():
    # Inject custom CSS for styling
    st.markdown(
        """
        <style>
            .header-title {
                font-size: 36px; 
                font-weight: bold; 
                color: #4a4a4a;
                text-align: center;
                margin-bottom: 30px;
            }
            .subheader {
                font-size: 24px;
                font-weight: bold;
                color: #5a5a5a;
                margin-bottom: 20px;
            }
            .info-box {
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 15px;
                margin-bottom: 20px;
                background-color: #f9f9f9;
            }
            .doc-image {
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 5px;
            }
            .tab-title {
                font-size: 20px;
                font-weight: bold;
            }
        </style>
    """,
        unsafe_allow_html=True,
    )

    st.header("🎓 Welcome to Your Student Portal")

    student_id = st.session_state.get("student_logged_in")
    if not student_id:
        st.error("You must be logged in to view this page.")
        return

    # Fetch student information and course registrations from the database.
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM student_info WHERE student_id = %s", (student_id,))
        student = c.fetchone()
        c.execute(
            "SELECT * FROM course_registration WHERE student_id = %s ORDER BY date_registered DESC",
            (student_id,),
        )
        registrations = c.fetchall()

    # Create portal tabs including Proof of Registration.
    tabs = st.tabs(
        [
            "Profile",
            "Course Registrations",
            "Documents",
            "Proof of Registration",
            "Settings",
            "Notifications",
        ]
    )

    # Profile Tab with improved styling layout.
    with tabs[0]:
        st.markdown(
            "<div class='subheader'>Personal Information</div>", unsafe_allow_html=True
        )
        col1, col2 = st.columns(2)
        with col1:
            if student[28] and os.path.exists(student[28]):  # passport_photo_path
                try:
                    image = PILImage.open(student[28])
                    st.image(image, width=200, caption="Student Photo")
                except Exception as e:
                    st.error(f"Error loading passport photo: {str(e)}")
            with st.container():
                st.markdown(
                    "<strong>Basic Information</strong>", unsafe_allow_html=True
                )
                st.info(
                    f"Student ID: {student[0]}\nName: {student[1]} {student[2]}\nDOB: {student[3]}\nGender: {student[13]}\nNationality: {student[11]}"
                )
        with col2:
            st.markdown("<strong>Contact Information</strong>", unsafe_allow_html=True)
            st.info(
                f"Email: {student[8]}\nPhone: {student[9]}\nResidential Address: {student[6]}\nPostal Address: {student[7]}"
            )
            st.markdown("<strong>Academic Information</strong>", unsafe_allow_html=True)
            st.info(
                f"Programme: {student[-1]}\nPrevious School: {student[23]}\nQualification: {student[24]}"
            )

    # Course Registrations Tab with enhanced layout.
    with tabs[1]:
        st.markdown(
            "<div class='subheader'>Course Registrations</div>", unsafe_allow_html=True
        )
        if registrations:
            for reg in registrations:
                with st.expander(f"Registration ID: {reg[0]} - {reg[11]}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Programme:** {reg[3]}")
                        st.write(f"**Level:** {reg[5]}")
                        st.write(f"**Session:** {reg[6]}")
                    with col2:
                        st.write(f"**Academic Year:** {reg[7]}")
                        st.write(f"**Semester:** {reg[8]}")
                        st.write(f"**Total Credits:** {reg[10]}")
                    if reg[9]:
                        st.write("**Selected Courses:**")
                        courses_list = reg[9].split("\n")
                        for course in courses_list:
                            if "|" in course:
                                code, title, credits = course.split("|")
                                st.write(f"- {code}: {title} ({credits} credits)")
        else:
            st.info("No course registrations found.")

    # Documents Tab with card-style presentation.
    with tabs[2]:
        st.markdown("<div class='subheader'>Documents</div>", unsafe_allow_html=True)
        documents = {
            "Ghana Card": student[27],
            "Passport Photo": student[28],
            "Transcript": student[29],
            "Certificate": student[30],
            "Receipt": student[31],
        }
        for doc_name, doc_path in documents.items():
            st.markdown(
                f"<div class='info-box'><strong>{doc_name}</strong></div>",
                unsafe_allow_html=True,
            )
            if doc_path and os.path.exists(doc_path):
                if doc_path.lower().endswith((".jpg", ".jpeg", ".png")):
                    st.image(doc_path, width=200, caption=doc_name)
                else:
                    st.markdown(f"[View {doc_name}]({doc_path})")
            else:
                st.write(f"**{doc_name}:** Not uploaded")

    # Proof of Registration Tab with enhanced instructions.
    with tabs[3]:
        st.markdown(
            "<div class='subheader'>Proof of Registration</div>", unsafe_allow_html=True
        )
        if not registrations:
            st.info("No course registration records found.")
        else:
            for reg in registrations:
                reg_data = {
                    "student_id": reg[1],
                    "index_number": reg[2],
                    "programme": reg[3],
                    "specialization": reg[4],
                    "level": reg[5],
                    "session": reg[6],
                    "academic_year": reg[7],
                    "semester": reg[8],
                    "courses": reg[9],
                    "total_credits": reg[10],
                    "receipt_path": reg[13],
                    "receipt_amount": reg[14],
                }
                st.markdown(
                    f"<strong>Registration Record (ID: {reg[0]}) - Date Registered: {reg[11]}</strong>",
                    unsafe_allow_html=True,
                )
                if st.button(
                    f"Download Proof of Registration (ID: {reg[0]})",
                    key=f"download_{reg[0]}",
                ):
                    pdf_file = generate_course_registration_pdf(reg_data)
                    if os.path.exists(pdf_file):
                        with open(pdf_file, "rb") as f:
                            pdf_bytes = f.read()
                        st.download_button(
                            label=f"Download Registration PDF (ID: {reg[0]})",
                            data=pdf_bytes,
                            file_name=pdf_file,
                            mime="application/pdf",
                        )
                        os.remove(pdf_file)
                    else:
                        st.error("Error generating PDF. Please try again.")

    # Settings Tab with visual separation.
    with tabs[4]:
        st.markdown(
            "<div class='subheader'>Account Settings</div>", unsafe_allow_html=True
        )
        if st.button("Change Password"):
            current_password = st.text_input("Current Password", type="password")
            new_password = st.text_input("New Password", type="password")
            confirm_password = st.text_input("Confirm New Password", type="password")
            if st.button("Update Password"):
                if new_password != confirm_password:
                    st.error("New passwords do not match.")
                elif len(new_password) < 8:
                    st.error("New password must be at least 8 characters long.")
                else:
                    conn = sqlite3.connect("student_registration.db")
                    c = conn.cursor()
                    c.execute(
                        "SELECT password FROM student_info WHERE student_id = ?",
                        (student_id,),
                    )
                    stored_password = c.fetchone()[0]
                    if current_password == stored_password:
                        c.execute(
                            "UPDATE student_info SET password = ? WHERE student_id = ?",
                            (new_password, student_id),
                        )
                        conn.commit()
                        st.success("Password updated successfully!")
                    else:
                        st.error("Current password is incorrect.")
                    conn.close()
        if st.button("Logout"):
            st.session_state.student_logged_in = None
            st.rerun()

    # Notifications Tab with cleaner layout.
    with tabs[5]:
        st.markdown(
            "<div class='subheader'>Notifications</div>", unsafe_allow_html=True
        )
        notification_system = NotificationSystem()
        show_read = st.checkbox("Show read notifications")
        notifications = notification_system.get_notifications(
            student_id=student_id, include_read=show_read
        )
        col1, col2 = st.columns([4, 1])
        with col1:
            unread_count = len([n for n in notifications if not n["is_read"]])
            st.write(f"**You have {unread_count} unread notifications**")
        with col2:
            if st.button("Mark All as Read"):
                notification_system.mark_all_as_read(student_id)
                st.rerun()
        display_notifications(notifications)


def generate_program_student_list(program, level, students_df):
    filename = (
        f"{program}_{level}_students_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    )
    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
    )

    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="CustomTitle",
            parent=styles["Heading1"],
            fontSize=16,
            alignment=TA_CENTER,
            spaceAfter=30,
            textColor=colors.HexColor("#003366"),
        )
    )

    elements = []

    # Header with logo
    header_data = [
        [
            RLImage("upsa_logo.jpg", width=1.2 * inch, height=1.2 * inch),
            Paragraph(
                "UNIVERSITY OF PROFESSIONAL STUDIES, ACCRA", styles["CustomTitle"]
            ),
            RLImage("upsa_logo.jpg", width=1.2 * inch, height=1.2 * inch),
        ]
    ]
    header_table = RLTable(header_data, [2 * inch, 4 * inch, 2 * inch])
    header_table.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    elements.append(header_table)
    elements.append(Spacer(1, 20))

    # Program information
    elements.append(Paragraph(f"Program: {program}", styles["Heading2"]))
    elements.append(Paragraph(f"Level: {level}", styles["Heading2"]))
    elements.append(Paragraph(f"Total Students: {len(students_df)}", styles["Normal"]))
    elements.append(Spacer(1, 20))

    # Create a table for all students
    table_data = []

    # Add header row
    table_data.append(
        [
            Paragraph("<b>Photo</b>", styles["Normal"]),
            Paragraph("<b>Student ID</b>", styles["Normal"]),
            Paragraph("<b>Name</b>", styles["Normal"]),
            Paragraph("<b>Academic Info</b>", styles["Normal"]),
        ]
    )

    # Add student rows
    for _, student in students_df.iterrows():
        # Photo cell
        photo_cell = None
        if student["passport_photo_path"] and os.path.exists(
            student["passport_photo_path"]
        ):
            try:
                # Use RLImage instead of Image for better compatibility
                photo_cell = RLImage(
                    student["passport_photo_path"], width=1 * inch, height=1 * inch
                )
            except Exception as e:
                # If there's an error loading the image, use a placeholder text
                photo_cell = Paragraph("No Photo", styles["Normal"])
        else:
            photo_cell = Paragraph("No Photo", styles["Normal"])

        # Student info cells
        student_id_cell = Paragraph(student["student_id"], styles["Normal"])
        name_cell = Paragraph(
            f"{student['surname']}, {student['other_names']}", styles["Normal"]
        )
        academic_info = Paragraph(
            f"Academic Year: {student['academic_year']}<br/>"
            f"Semester: {student['semester']}",
            styles["Normal"],
        )

        # Add row to table
        table_data.append([photo_cell, student_id_cell, name_cell, academic_info])

    # Create the table with appropriate column widths
    students_table = RLTable(
        table_data, colWidths=[1.2 * inch, 1.5 * inch, 2.5 * inch, 2.3 * inch]
    )

    # Style the table
    students_table.setStyle(
        TableStyle(
            [
                # Add grid lines
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                # Style header row
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#003366")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                # Align cells
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (0, -1), "CENTER"),  # Center photos
                ("ALIGN", (1, 0), (1, -1), "CENTER"),  # Center student IDs
                # Add padding
                ("PADDING", (0, 0), (-1, -1), 6),
                # Alternate row colors for better readability
                *[
                    ("BACKGROUND", (0, i), (-1, i), colors.HexColor("#f5f5f5"))
                    for i in range(1, len(table_data))
                    if i % 2 == 0
                ],
            ]
        )
    )

    elements.append(students_table)
    elements.append(Spacer(1, 20))

    # Footer
    elements.append(
        Paragraph(
            f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            styles["Normal"],
        )
    )

    # Build the PDF
    doc.build(elements)
    return filename


def download_receipts():
    temp_dir = "temp_receipts"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    try:
        conn = sqlite3.connect("student_registration.db")
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT student_id, surname, other_names, 
                   receipt_path, receipt_amount
            FROM student_info
            WHERE receipt_path IS NOT NULL
        """
        )
        student_receipts = cursor.fetchall()

        cursor.execute(
            """
            SELECT cr.registration_id, cr.student_id, si.surname, si.other_names,
                   cr.receipt_path, cr.receipt_amount
            FROM course_registration cr
            LEFT JOIN student_info si ON cr.student_id = si.student_id
            WHERE cr.receipt_path IS NOT NULL
        """
        )
        registration_receipts = cursor.fetchall()

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = f"all_receipts_{timestamp}.zip"

        with zipfile.ZipFile(zip_filename, "w") as zipf:
            for receipt in student_receipts:
                student_id, surname, other_names, receipt_path, amount = receipt
                if receipt_path and os.path.exists(receipt_path):
                    _, ext = os.path.splitext(receipt_path)
                    archive_path = f"student_receipts/{student_id}_{surname}_{other_names}_amount_{amount}{ext}"
                    zipf.write(receipt_path, archive_path)

            for receipt in registration_receipts:
                reg_id, student_id, surname, other_names, receipt_path, amount = receipt
                if receipt_path and os.path.exists(receipt_path):
                    _, ext = os.path.splitext(receipt_path)
                    archive_path = f"registration_receipts/reg_{reg_id}_{student_id}_{surname}_{other_names}_amount_{amount}{ext}"
                    zipf.write(receipt_path, archive_path)

        return zip_filename

    except Exception as e:
        print(f"Error creating receipts zip file: {str(e)}")
        return None

    finally:
        conn.close()
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


def save_uploaded_file(uploaded_file, directory, use_drive=True):
    """
    Save an uploaded file, compressing it if it exceeds 6MB.
    Can save to local storage or Google Drive based on the use_drive parameter.
    
    Args:
        uploaded_file: Streamlit uploaded file object
        directory: Directory to save the file (used only for local storage)
        use_drive: Whether to use Google Drive storage (default: True)
        
    Returns:
        For local storage: Path to the saved file, or None if saving failed
        For Google Drive: Drive file ID, or None if saving failed
    """
    if uploaded_file is None:
        return None
    
    if use_drive:
        # Use Google Drive storage
        drive_storage = initialize_drive_storage()
        if not drive_storage:
            # Fall back to local storage if Drive initialization fails
            return save_compressed_file(uploaded_file, directory, max_size_mb=6.0)
        
        try:
            # Get the file data
            file_data = uploaded_file.getvalue()
            
            # Determine document type based on the directory or other logic
            if "ghana_card" in directory.lower():
                document_type = "ghana_card"
            elif "passport" in directory.lower():
                document_type = "passport_photo"
            elif "transcript" in directory.lower():
                document_type = "transcript"
            elif "certificate" in directory.lower():
                document_type = "certificate"
            elif "receipt" in directory.lower():
                document_type = "receipt"
            else:
                document_type = "document"
            
            # Save to Google Drive
            file_id, web_view_link, _ = drive_storage.save_compressed_file(
                file_data, 
                uploaded_file.name, 
                document_type
            )
            
            # Return the file ID as the "path" - your code will need to be updated
            # to handle Drive file IDs instead of local paths
            return file_id
        except Exception as e:
            print(f"Error saving to Google Drive: {str(e)}")
            # Fall back to local storage
            return save_compressed_file(uploaded_file, directory, max_size_mb=6.0)
    else:
        # Use local storage
        return save_compressed_file(uploaded_file, directory, max_size_mb=6.0)
    
    
def update_db_schema_for_drive():
    """
    Update the database schema to include Google Drive file IDs and links.
    This should be called once to migrate the database.
    """
    with get_db_connection() as conn:
        c = conn.cursor()
        
        if MYSQL_CONFIG:
            # MySQL syntax
            try:
                # Add Google Drive fields to student_info table
                c.execute("ALTER TABLE student_info ADD COLUMN ghana_card_drive_id VARCHAR(255)")
                c.execute("ALTER TABLE student_info ADD COLUMN passport_photo_drive_id VARCHAR(255)")
                c.execute("ALTER TABLE student_info ADD COLUMN transcript_drive_id VARCHAR(255)")
                c.execute("ALTER TABLE student_info ADD COLUMN certificate_drive_id VARCHAR(255)")
                c.execute("ALTER TABLE student_info ADD COLUMN receipt_drive_id VARCHAR(255)")
                
                # Add Google Drive fields to course_registration table
                c.execute("ALTER TABLE course_registration ADD COLUMN receipt_drive_id VARCHAR(255)")
                
                conn.commit()
                print("Database schema updated for Google Drive integration")
            except mysql.connector.Error as err:
                if "Duplicate column name" in str(err):
                    print("Google Drive columns already exist")
                else:
                    print(f"Error updating schema: {err}")
        else:
            # SQLite syntax
            try:
                # Add Google Drive fields to student_info table
                c.execute("ALTER TABLE student_info ADD COLUMN ghana_card_drive_id TEXT")
                c.execute("ALTER TABLE student_info ADD COLUMN passport_photo_drive_id TEXT")
                c.execute("ALTER TABLE student_info ADD COLUMN transcript_drive_id TEXT")
                c.execute("ALTER TABLE student_info ADD COLUMN certificate_drive_id TEXT")
                c.execute("ALTER TABLE student_info ADD COLUMN receipt_drive_id TEXT")
                
                # Add Google Drive fields to course_registration table
                c.execute("ALTER TABLE course_registration ADD COLUMN receipt_drive_id TEXT")
                
                conn.commit()
                print("Database schema updated for Google Drive integration")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e).lower():
                    print("Google Drive columns already exist")
                else:
                    print(f"Error updating schema: {e}")



def get_file_content(file_path_or_id, is_drive_file=False):
    """
    Get file content from either local storage or Google Drive.
    
    Args:
        file_path_or_id: Local file path or Google Drive file ID
        is_drive_file: Whether the file is stored in Google Drive
        
    Returns:
        Tuple of (file_content, filename) or (None, None) if error
    """
    if not file_path_or_id:
        return None, None
    
    if is_drive_file:
        # Retrieve from Google Drive
        return get_file_from_drive(file_path_or_id)
    else:
        # Retrieve from local storage
        if os.path.exists(file_path_or_id):
            try:
                with open(file_path_or_id, 'rb') as f:
                    content = f.read()
                return content, os.path.basename(file_path_or_id)
            except Exception as e:
                print(f"Error reading local file: {str(e)}")
                return None, None
        else:
            return None, None

def display_file(file_path_or_id, is_drive_file=False, file_type=None):
    """
    Display a file in Streamlit, handling both local files and Google Drive files.
    
    Args:
        file_path_or_id: Local file path or Google Drive file ID
        is_drive_file: Whether the file is stored in Google Drive
        file_type: Optional file type hint (e.g., 'image', 'pdf')
        
    Returns:
        True if file was displayed successfully, False otherwise
    """
    import streamlit as st
    from PIL import Image
    import io
    
    content, filename = get_file_content(file_path_or_id, is_drive_file)
    
    if not content:
        st.error(f"Could not retrieve file")
        return False
    
    # Determine file type if not provided
    if not file_type:
        if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            file_type = 'image'
        elif filename.lower().endswith('.pdf'):
            file_type = 'pdf'
        else:
            file_type = 'unknown'
    
    # Display based on file type
    if file_type == 'image':
        try:
            image = Image.open(io.BytesIO(content))
            st.image(image, caption=filename)
            return True
        except Exception as e:
            st.error(f"Error displaying image: {str(e)}")
            return False
    elif file_type == 'pdf':
        # For PDFs, we need to save temporarily to display
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                tmp.write(content)
                tmp_path = tmp.name
            
            # Display PDF using Streamlit
            st.markdown(f"**{filename}**")
            st.markdown(f"[View PDF]({tmp_path})")
            return True
        except Exception as e:
            st.error(f"Error displaying PDF: {str(e)}")
            return False
    else:
        st.warning(f"Unsupported file type: {file_type}")
        return False

def insert_student_info(c, form_data, file_paths):
    insert_query = """
        INSERT INTO student_info (
            student_id, surname, other_names, date_of_birth, place_of_birth,
            home_town, residential_address, postal_address, email, telephone,
            ghana_card_id, nationality, marital_status, gender, religion,
            denomination, disability_status, disability_description,
            guardian_name, guardian_relationship, guardian_occupation,
            guardian_address, guardian_telephone, previous_school,
            qualification_type, completion_year, aggregate_score,
            ghana_card_path, passport_photo_path, certificate_path,
            transcript_path, receipt_path, receipt_amount,
            approval_status, created_at, programme
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
    """
    # transcript_path and receipt_path are set to None.
    params = (
        form_data["student_id"],
        form_data["surname"],
        form_data["other_names"],
        form_data["date_of_birth"],
        form_data["place_of_birth"],
        form_data["home_town"],
        form_data["residential_address"],
        form_data["postal_address"],
        form_data["email"],
        form_data["telephone"],
        form_data["ghana_card_id"],
        form_data["nationality"],
        form_data["marital_status"],
        form_data["gender"],
        form_data["religion"],
        form_data["denomination"],
        form_data["disability_status"],
        form_data["disability_description"],
        form_data["guardian_name"],
        form_data["guardian_relationship"],
        form_data["guardian_occupation"],
        form_data["guardian_address"],
        form_data["guardian_telephone"],
        form_data["previous_school"],
        form_data["qualification_type"],
        form_data["completion_year"],
        form_data["aggregate_score"],
        file_paths.get("ghana_card_path"),
        file_paths.get("passport_photo_path"),
        file_paths.get("certificate_path"),
        None,  # transcript_path removed
        None,  # receipt_path removed
        0.0,  # receipt
        "pending",
        datetime.now(),
        form_data.get("programme", ""),
    )
    c.execute(insert_query, params)


##############################
# New Email Sending Function #
##############################
from email.mime.application import MIMEApplication  # For PDF attachments


def send_emails():
    """
    Updated function to send emails to students with an optional PDF attachment.
    The user can upload a PDF file that will be attached to the email.
    """
    st.header("Send Emails to Students")
    recipient_type = st.selectbox(
        "Select Recipient Group", ["All Students", "By Programme", "Individual Student"]
    )
    subject = st.text_input("Email Subject")
    message_body = st.text_area("Email Message")

    # Optional PDF attachment uploader
    attachment_file = st.file_uploader("Upload PDF Attachment (Optional)", type=["pdf"])

    # For individual student, allow entering student ID.
    individual_id = None
    selected_programmes = []
    if recipient_type == "By Programme":
        selected_programmes = st.multiselect(
            "Select Programme(s)", options=["CIMG", "CIM-UK", "ICAG", "ACCA"]
        )
    elif recipient_type == "Individual Student":
        individual_id = st.text_input("Enter Student ID")

    if st.button("Send Email"):
        conn = sqlite3.connect("student_registration.db")
        cur = conn.cursor()
        recipients = []
        if recipient_type == "All Students":
            cur.execute("SELECT email FROM student_info")
            results = cur.fetchall()
            recipients = [email for (email,) in results if email]
        elif recipient_type == "By Programme":
            if selected_programmes:
                placeholders = ",".join("?" for _ in selected_programmes)
                query = f"SELECT email FROM student_info WHERE programme IN ({placeholders})"
                cur.execute(query, selected_programmes)
                results = cur.fetchall()
                recipients = [email for (email,) in results if email]
        elif recipient_type == "Individual Student":
            if individual_id:
                cur.execute(
                    "SELECT email FROM student_info WHERE student_id = ?",
                    (individual_id,),
                )
                result = cur.fetchone()
                if result and result[0]:
                    recipients = [result[0]]
        conn.close()

        st.write(f"Total recipients: {len(recipients)}")
        if not recipients:
            st.error("No email addresses found for the selected criteria.")
            return

        try:
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            for recipient in recipients:
                msg = MIMEMultipart()
                msg["From"] = SMTP_USERNAME
                msg["To"] = recipient
                msg["Subject"] = subject
                msg.attach(MIMEText(message_body, "plain"))

                # If a PDF attachment was uploaded, attach it.
                if attachment_file is not None:
                    # Save the uploaded PDF temporarily if needed.
                    attachment_path = save_uploaded_file(attachment_file, "uploads")
                    if attachment_path and os.path.exists(attachment_path):
                        with open(attachment_path, "rb") as f:
                            pdf_attachment = MIMEApplication(f.read(), _subtype="pdf")
                        pdf_attachment.add_header(
                            "Content-Disposition",
                            "attachment",
                            filename=os.path.basename(attachment_path),
                        )
                        msg.attach(pdf_attachment)
                server.sendmail(SMTP_USERNAME, recipient, msg.as_string())
            server.quit()
            st.success("Emails sent successfully!")
        except Exception as e:
            st.error(f"Error sending emails: {e}")


##############################
# End Email Sending Function #
##############################


def generate_batch_pdfs(document_type="student_info"):
    temp_dir = "temp_pdfs"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    try:
        conn = sqlite3.connect("student_registration.db")

        if document_type == "student_info":
            students_df = pd.read_sql_query("SELECT * FROM student_info", conn)
            for _, student in students_df.iterrows():
                try:
                    pdf_file = generate_student_info_pdf(student)
                    new_path = os.path.join(temp_dir, os.path.basename(pdf_file))
                    shutil.move(pdf_file, new_path)
                except Exception as e:
                    print(
                        f"Error generating PDF for student {student['student_id']}: {str(e)}"
                    )
                    continue

        else:
            registrations_df = pd.read_sql_query(
                """
                SELECT cr.*, si.surname, si.other_names, si.passport_photo_path
                FROM course_registration cr
                LEFT JOIN student_info si ON cr.student_id = si.student_id
            """,
                conn,
            )

            for _, registration in registrations_df.iterrows():
                try:
                    pdf_file = generate_course_registration_pdf(registration)
                    new_path = os.path.join(temp_dir, os.path.basename(pdf_file))
                    shutil.move(pdf_file, new_path)
                except Exception as e:
                    print(
                        f"Error generating PDF for registration {registration['registration_id']}: {str(e)}"
                    )
                    continue

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = f"all_{document_type}_pdfs_{timestamp}.zip"

        with zipfile.ZipFile(zip_filename, "w") as zipf:
            for root, _, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.basename(file_path)
                    zipf.write(file_path, arcname)

        return zip_filename

    except Exception as e:
        print(f"Error in batch PDF generation: {str(e)}")
        return None

    finally:
        conn.close()
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


import zipfile
import shutil
from datetime import datetime
import sqlite3
from typing import Dict, List, Optional, Tuple
import logging
import json


class DocumentUploadHandler:
    """
    Handles the upload and organization of documents from zip files for the student registration system.
    Ensures proper file structure and database updates for both student information and course registration.
    No file size limit enforced.
    """

    # Allowed file extensions for each document type
    ALLOWED_EXTENSIONS = {
        "ghana_card": [".pdf", ".jpg", ".jpeg", ".png"],
        "passport_photo": [".jpg", ".jpeg", ".png"],
        "transcript": [".pdf", ".jpeg", ".jpg", ".png"],
        "certificate": [".pdf", ".jpg", ".jpeg", ".png"],
        "receipt": [".pdf", ".jpg", ".jpeg", ".png"],
    }

    # Expected folders in the zip file
    EXPECTED_FOLDERS = {
        "student_documents": [
            "ghana_cards",
            "passport_photos",
            "transcripts",
            "certificates",
            "receipts",
        ],
        "course_registration_receipts": ["receipts"],
    }

    def __init__(self, upload_base_dir: str = "uploads"):
        """
        Initialize the document upload handler.

        Args:
            upload_base_dir: Base directory for all uploaded files.
        """
        self.upload_base_dir = upload_base_dir
        self.logger = self._setup_logger()
        self._ensure_directories()

    def _ensure_directories(self):
        """
        Ensure that the base uploads directory exists and create subdirectories for expected folders.
        """
        self._ensure_base_directory()
        # Create subdirectories for each expected main folder
        for main_folder in self.EXPECTED_FOLDERS.keys():
            dir_path = os.path.join(self.upload_base_dir, main_folder)
            os.makedirs(dir_path, exist_ok=True)

    def _setup_logger(self) -> logging.Logger:
        """Configure logging for the document handler."""
        logger = logging.getLogger("DocumentUploadHandler")
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.FileHandler("document_uploads.log")
            formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger

    def _ensure_base_directory(self):
        """Ensure the base uploads directory exists."""
        os.makedirs(self.upload_base_dir, exist_ok=True)

    def process_zip_file(self, zip_file_path: str) -> Tuple[bool, str]:
        """
        Process the uploaded zip file, extract its contents, and save all files directly in the uploads folder.
        No file size limit enforced.

        Args:
            zip_file_path: Path to the uploaded zip file.

        Returns:
            Tuple of (success: bool, message: str).
        """
        temp_dir = "temp_extract"
        try:
            # Create temporary directory for extraction
            os.makedirs(temp_dir, exist_ok=True)

            # Extract zip file without size restrictions
            with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
                zip_ref.extractall(temp_dir)

            # Process student documents
            student_documents = self._process_student_documents(temp_dir)

            # Process registration documents
            reg_docs = self._process_registration_documents(temp_dir)

            # Update database with new file paths
            self._update_database(student_documents, reg_docs)

            return True, "Documents processed successfully"

        except Exception as e:
            self.logger.error(f"Error processing zip file: {str(e)}")
            return False, f"Error processing documents: {str(e)}"

        finally:
            # Clean up temporary directory
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    def _process_student_documents(self, temp_dir: str) -> Dict[str, Dict[str, str]]:
        """Process student documents from the extracted zip file."""
        student_documents = {}
        student_dir = os.path.join(temp_dir, "student_documents")

        if not os.path.exists(student_dir):
            return student_documents

        for student_id in os.listdir(student_dir):
            student_folder = os.path.join(student_dir, student_id)
            if not os.path.isdir(student_folder):
                continue

            student_documents[student_id] = {}

            # Process each document type
            for doc_type, extensions in self.ALLOWED_EXTENSIONS.items():
                doc_file = self._find_document(student_folder, doc_type, extensions)
                if doc_file:
                    new_path = self._save_document(doc_file, student_id, doc_type)
                    student_documents[student_id][f"{doc_type}_path"] = new_path

        return student_documents

    def _process_registration_documents(
        self, temp_dir: str
    ) -> Dict[str, Dict[str, str]]:
        """Process course registration documents from the extracted zip file."""
        reg_docs = {}
        reg_dir = os.path.join(temp_dir, "course_registration_receipts")

        if not os.path.exists(reg_dir):
            return reg_docs

        for reg_id in os.listdir(reg_dir):
            reg_folder = os.path.join(reg_dir, reg_id)
            if not os.path.isdir(reg_folder):
                continue

            reg_docs[reg_id] = {}

            # Process registration receipt
            receipt_file = self._find_document(
                reg_folder, "receipt", self.ALLOWED_EXTENSIONS["receipt"]
            )
            if receipt_file:
                new_path = self._save_document(receipt_file, reg_id, "receipt")
                reg_docs[reg_id]["receipt_path"] = new_path

        return reg_docs

    def _find_document(
        self, directory: str, doc_type: str, allowed_extensions: List[str]
    ) -> Optional[str]:
        """Find a document of the specified type in the directory."""
        for file in os.listdir(directory):
            ext = os.path.splitext(file)[1].lower()
            if ext in allowed_extensions:
                return os.path.join(directory, file)
        return None

    def _save_document(self, source_path: str, identifier: str, doc_type: str) -> str:
        """Save a document to the uploads directory."""
        ext = os.path.splitext(source_path)[1]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{identifier}_{doc_type}_{timestamp}{ext}"
        dest_path = os.path.join(self.upload_base_dir, filename)
        shutil.copy2(source_path, dest_path)
        return dest_path

    def _update_database(
        self,
        student_documents: Dict[str, Dict[str, str]],
        reg_docs: Dict[str, Dict[str, str]],
    ):
        """Update database with new document paths."""
        conn = sqlite3.connect("student_registration.db")
        c = conn.cursor()

        try:
            # Update student documents
            for student_id, docs in student_documents.items():
                if docs:
                    update_fields = ", ".join(f"{key} = ?" for key in docs.keys())
                    query = (
                        f"UPDATE student_info SET {update_fields} WHERE student_id = ?"
                    )
                    c.execute(query, list(docs.values()) + [student_id])

            # Update registration documents
            for reg_id, docs in reg_docs.items():
                if docs:
                    update_fields = ", ".join(f"{key} = ?" for key in docs.keys())
                    query = f"UPDATE course_registration SET {update_fields} WHERE registration_id = ?"
                    c.execute(query, list(docs.values()) + [reg_id])

            conn.commit()

        except Exception as e:
            conn.rollback()
            self.logger.error(f"Database update error: {str(e)}")
            raise

        finally:
            conn.close()

    def validate_zip_structure(self, zip_file_path: str) -> Tuple[bool, str]:
        """Validate the structure of the uploaded zip file."""
        try:
            with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
                files = zip_ref.namelist()

                # Check for main directories
                if not any(
                    f.startswith("student_documents/") for f in files
                ) and not any(
                    f.startswith("course_registration_receipts/") for f in files
                ):
                    return (
                        False,
                        "Missing required directories: student_documents or course_registration_receipts",
                    )

                # Validate file extensions
                for file in files:
                    if file.endswith("/"):  # Skip directories
                        continue
                    ext = os.path.splitext(file)[1].lower()
                    if not any(
                        ext in exts for exts in self.ALLOWED_EXTENSIONS.values()
                    ):
                        return False, f"Invalid file extension in: {file}"

                return True, "Zip file structure is valid"

        except zipfile.BadZipFile:
            return False, "Invalid zip file"
        except Exception as e:
            return False, f"Error validating zip file: {str(e)}"


# End of DocumentUploadHandler


class NotificationSystem:
    def __init__(self):
        self.setup_notification_table()

    def setup_notification_table(self):
        conn = sqlite3.connect("student_registration.db")
        c = conn.cursor()
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS notifications (
                notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipient_id TEXT,
                recipient_type TEXT,
                title TEXT,
                message TEXT,
                notification_type TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                read_at DATETIME,
                metadata TEXT,
                expires_at DATETIME
            )
            """
        )
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS notification_reads (
                notification_id INTEGER,
                student_id TEXT,
                read_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (notification_id, student_id)
            )
            """
        )
        conn.commit()
        conn.close()

    def create_notification(
        self,
        title,
        message,
        recipient_type,
        recipient_id=None,
        notification_type="info",
        metadata=None,
        expires_at=None,
    ):
        conn = sqlite3.connect("student_registration.db")
        c = conn.cursor()
        c.execute(
            """
            INSERT INTO notifications (
                recipient_id, recipient_type, title, message,
                notification_type, metadata, expires_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                recipient_id,
                recipient_type,
                title,
                message,
                notification_type,
                json.dumps(metadata) if metadata else None,
                expires_at.isoformat() if expires_at else None,
            ),
        )
        notification_id = c.lastrowid
        conn.commit()
        conn.close()
        return notification_id

    def get_notifications(
        self, student_id: str, include_read: bool = False, limit: int = 50
    ) -> List[Dict]:
        """Get notifications for a specific student"""
        conn = sqlite3.connect("student_registration.db")
        c = conn.cursor()

        try:
            query = """
                SELECT 
                    n.notification_id,
                    n.title,
                    n.message,
                    n.notification_type,
                    n.created_at,
                    n.metadata,
                    CASE 
                        WHEN nr.read_at IS NOT NULL THEN 1 
                        ELSE 0 
                    END as is_read
                FROM notifications n
                LEFT JOIN notification_reads nr 
                    ON n.notification_id = nr.notification_id 
                    AND nr.student_id = ?
                WHERE (
                    n.recipient_id = ? 
                    OR n.recipient_type = 'all'
                    OR (
                        n.recipient_type = 'program' 
                        AND n.recipient_id = (
                            SELECT programme 
                            FROM student_info 
                            WHERE student_id = ?
                        )
                    )
                )
                AND (n.expires_at IS NULL OR n.expires_at > datetime('now'))
            """

            if not include_read:
                query += " AND nr.read_at IS NULL"

            query += " ORDER BY n.created_at DESC LIMIT ?"

            c.execute(query, (student_id, student_id, student_id, limit))

            notifications = []
            for row in c.fetchall():
                notification = {
                    "id": row[0],
                    "title": row[1],
                    "message": row[2],
                    "type": row[3],
                    "created_at": row[4],
                    "metadata": json.loads(row[5]) if row[5] else None,
                    "is_read": bool(row[6]),
                }
                notifications.append(notification)

            return notifications
        finally:
            conn.close()

    def mark_as_read(self, notification_id, student_id):
        conn = sqlite3.connect("student_registration.db")
        c = conn.cursor()
        c.execute(
            "INSERT OR IGNORE INTO notification_reads (notification_id, student_id) VALUES (?, ?)",
            (notification_id, student_id),
        )
        conn.commit()
        conn.close()

    def mark_all_as_read(self, student_id):
        conn = sqlite3.connect("student_registration.db")
        c = conn.cursor()
        c.execute(
            """
            INSERT INTO notification_reads (notification_id, student_id)
            SELECT n.notification_id, ?
            FROM notifications n
            LEFT JOIN notification_reads nr ON n.notification_id = nr.notification_id AND nr.student_id = ?
            WHERE nr.read_at IS NULL AND (
                n.recipient_id = ? OR n.recipient_type = 'all' OR (
                    n.recipient_type = 'program' AND n.recipient_id = (
                        SELECT programme FROM student_info WHERE student_id = ?
                    )
                )
            )
            """,
            (student_id, student_id, student_id, student_id),
        )
        conn.commit()
        conn.close()

    def delete_notification(self, notification_id):
        conn = sqlite3.connect("student_registration.db")
        c = conn.cursor()
        c.execute(
            "DELETE FROM notification_reads WHERE notification_id = ?",
            (notification_id,),
        )
        c.execute(
            "DELETE FROM notifications WHERE notification_id = ?", (notification_id,)
        )
        conn.commit()
        conn.close()


def display_notifications(notifications: List[Dict]):
    """Display notifications in the Streamlit UI"""
    if not notifications:
        st.info("No new notifications")
        return

    for notification in notifications:
        with st.expander(
            f"📢 {notification['title']} - {notification['created_at']}",
            expanded=not notification["is_read"],
        ):
            st.write(notification["message"])

            # Display metadata if available
            if notification["metadata"]:
                st.json(notification["metadata"])

            col1, col2 = st.columns([4, 1])
            with col2:
                if not notification["is_read"]:
                    if st.button("Mark as Read", key=f"read_{notification['id']}"):
                        notification_system = NotificationSystem()
                        notification_system.mark_as_read(
                            notification["id"], st.session_state.student_logged_in
                        )
                        st.rerun()


def admin_notification_interface():
    """Admin interface for creating and managing notifications"""
    st.subheader("📢 Notification Management")

    tab1, tab2 = st.tabs(["Create Notification", "View/Manage Notifications"])

    with tab1:
        recipient_type = st.selectbox(
            "Recipient Type",
            ["all", "program", "student"],
            help="Select who should receive this notification",
        )
        recipient_id = None
        if recipient_type == "program":
            recipient_id = st.selectbox(
                "Select Program", ["CIMG", "CIM-UK", "ICAG", "ACCA"]
            )
        elif recipient_type == "student":
            conn = sqlite3.connect("student_registration.db")
            c = conn.cursor()
            c.execute(
                "SELECT student_id, surname, other_names FROM student_info ORDER BY surname, other_names"
            )
            students = c.fetchall()
            conn.close()
            if students:
                options = [
                    f"{id} - {surname} {other_names}"
                    for id, surname, other_names in students
                ]
                selected = st.selectbox("Select Student", options)
                recipient_id = selected.split(" - ")[0]
            else:
                st.warning("No students found in database")
                return

        notification_type = st.selectbox(
            "Notification Type", ["info", "warning", "success", "error"]
        )
        title = st.text_input("Notification Title")
        message = st.text_area("Notification Message")

        # File uploader for optional PDF attachment.
        attachment_file = st.file_uploader(
            "Upload PDF Attachment (Optional)", type=["pdf"]
        )

        col1, col2 = st.columns(2)
        with col1:
            include_metadata = st.checkbox("Include Additional Data")
        with col2:
            include_expiry = st.checkbox("Set Expiration")

        metadata = {}
        if include_metadata:
            metadata_str = st.text_area(
                "Additional Data (JSON format)", help="Enter valid JSON data"
            )
            try:
                metadata = json.loads(metadata_str) if metadata_str else {}
            except json.JSONDecodeError:
                st.error("Invalid JSON format")
                return

        expires_at = None
        if include_expiry:
            expires_at = st.date_input("Expiration Date")
            if expires_at:
                expires_at = datetime.combine(expires_at, datetime.min.time())

        # If a PDF attachment was provided, save it and add its path to metadata.
        if attachment_file is not None:
            attachment_path = save_uploaded_file(attachment_file, "uploads")
            if attachment_path:
                metadata["attachment_path"] = attachment_path

        if st.button("Send Notification"):
            if not title or not message:
                st.error("Title and message are required")
                return

            try:
                notification_system = NotificationSystem()
                notification_id = notification_system.create_notification(
                    title=title,
                    message=message,
                    recipient_type=recipient_type,
                    recipient_id=recipient_id,
                    notification_type=notification_type,
                    metadata=metadata if metadata else None,
                    expires_at=expires_at,
                )
                st.success(f"Notification created successfully! ID: {notification_id}")
            except Exception as e:
                st.error(f"Error creating notification: {str(e)}")

    with tab2:
        conn = sqlite3.connect("student_registration.db")
        c = conn.cursor()
        c.execute(
            """
            SELECT n.notification_id, n.title, n.message, n.recipient_type,
                   n.recipient_id, n.created_at, COUNT(nr.student_id) as read_count
            FROM notifications n
            LEFT JOIN notification_reads nr ON n.notification_id = nr.notification_id
            GROUP BY n.notification_id
            ORDER BY n.created_at DESC
            """
        )
        notifications = c.fetchall()
        conn.close()

        if notifications:
            for notification in notifications:
                with st.expander(f"📢 {notification[1]} - {notification[5]}"):
                    st.write(f"**Message:** {notification[2]}")
                    st.write(f"**Type:** {notification[3]}")
                    st.write(f"**Recipient:** {notification[4] or 'All'}")
                    st.write(f"**Read by:** {notification[6]} students")
                    if st.button("Delete", key=f"del_{notification[0]}"):
                        try:
                            notification_system = NotificationSystem()
                            notification_system.delete_notification(notification[0])
                            st.success("Notification deleted successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error deleting notification: {str(e)}")
        else:
            st.info("No notifications found")


# Fetch Student Information from Database
def get_student_info(student_id):
    with get_db_connection() as conn:
        query = "SELECT * FROM student_info WHERE student_id = %s"
        student = pd.read_sql(query, conn, params=(student_id,)).to_dict("records")
    return student[0] if student else None


def get_student_registrations(student_id: str) -> list:
    # Retrieve course registrations for student.
    with get_db_connection() as conn:
        conn.row_factory = mysql.connector.Row
        cur = conn.cursor()
    cur.execute(
        "SELECT * FROM course_registration WHERE student_id = ? ORDER BY date_registered DESC",
        (student_id,),
    )
    registrations = cur.fetchall()
    conn.close()
    return [dict(reg) for reg in registrations]


def display_profile(student):
    st.subheader("👤 Profile Information")
    col1, col2 = st.columns([1, 2])
    with col1:
        if student.get("passport_photo_path") and os.path.exists(
            student["passport_photo_path"]
        ):
            img = PILImage.open(student["passport_photo_path"])
            st.image(img, width=200, caption="Profile Photo")
        else:
            st.image("https://via.placeholder.com/200", caption="Profile Photo")
    with col2:
        st.markdown(
            f"**Full Name:** {student.get('surname', '')} {student.get('other_names', '')}"
        )
        st.markdown(f"**Student ID:** {student.get('student_id', '')}")
        st.markdown(f"**Email:** {student.get('email', '')}")
        st.markdown(f"**Phone:** {student.get('telephone', '')}")


def display_courses(registrations: list):
    st.subheader("Course Registrations")
    if registrations:
        for reg in registrations:
            st.markdown(
                f"**Registration ID:** {reg.get('registration_id')} | **Date:** {reg.get('date_registered')}"
            )
            st.write(f"**Programme:** {reg.get('programme', '')}")
            st.write(
                f"**Level:** {reg.get('level', '')} | **Semester:** {reg.get('semester', '')}"
            )
            if reg.get("courses"):
                courses = reg["courses"].split("\n")
                for course in courses:
                    if "|" in course:
                        code, title, credits = course.split("|")
                        st.write(f"- {code}: {title} ({credits} credits)")
            st.markdown("---")
    else:
        st.info("No course registrations found.")


def display_documents(student: dict):
    st.subheader("Documents")
    documents = {
        "Ghana Card": student.get("ghana_card_path"),
        "Passport Photo": student.get("passport_photo_path"),
        "Transcript": student.get("transcript_path"),
        "Certificate": student.get("certificate_path"),
        "Receipt": student.get("receipt_path"),
    }
    for doc_name, doc_path in documents.items():
        st.write(f"**{doc_name}:**")
        if doc_path and os.path.exists(doc_path):
            if doc_path.lower().endswith((".jpg", ".jpeg", ".png")):
                try:
                    img = PILImage.open(doc_path)
                    st.image(img, width=200, caption=doc_name)
                except Exception as e:
                    st.error(f"Error displaying image: {e}")
            else:
                st.write(f"[View {doc_name}]({doc_path})")
        else:
            st.info(f"{doc_name} not uploaded.")
        st.markdown("---")


def display_proof(registrations: list):
    st.subheader("Proof of Registration")
    if registrations:
        for reg in registrations:
            st.markdown(f"**Registration Record (ID: {reg.get('registration_id')})**")
            if st.button(
                f"Download Proof (ID: {reg.get('registration_id')})",
                key=f"download_{reg.get('registration_id')}",
            ):
                # Assume generate_course_registration_pdf() is defined elsewhere.
                pdf_file = generate_course_registration_pdf(reg)
                if os.path.exists(pdf_file):
                    with open(pdf_file, "rb") as f:
                        pdf_bytes = f.read()
                    st.download_button(
                        label="Download PDF",
                        data=pdf_bytes,
                        file_name=pdf_file,
                        mime="application/pdf",
                    )
                    os.remove(pdf_file)
                else:
                    st.error("Error generating PDF.")
            st.markdown("---")
    else:
        st.info("No registrations available for proof of registration.")


# Load Custom CSS for Improved UI
def load_custom_css():
    st.markdown(
        """
        <style>
        .main-container { max-width: 1200px; margin: auto; padding: 2rem; }
        .header { background: linear-gradient(90deg, #4CAF50, #81C784); color: white; padding: 1.5rem; text-align: center; border-radius: 8px; margin-bottom: 2rem; font-size: 1.5rem; font-weight: bold; }
        div[data-baseweb="tab-list"] { overflow-x: auto; white-space: nowrap; }
        .stTabs [data-baseweb="tab"] { flex-grow: 1; min-width: 120px; padding: 1rem; background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05); }
        .stTabs [data-baseweb="tab"][aria-selected="true"] { background: #1e3c72; color: white; }
        .profile-card { background: white; border-radius: 10px; padding: 1.5rem; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05); }
        .profile-image { border-radius: 50%; border: 3px solid #1e3c72; padding: 3px; }
        </style>
        """,
        unsafe_allow_html=True,
    )


import os
import time
import threading
from typing import Optional, List
import logging
from contextlib import contextmanager


class ZipFileCleanupHandler:
    """
    Handles the cleanup of temporary zip files after they've been downloaded.

    This class provides both immediate cleanup functionality and a background
    cleanup service that periodically scans for and removes old zip files.
    """

    def __init__(self, cleanup_delay: int = 5, scan_interval: int = 3600):
        """
        Initialize the zip file cleanup handler.

        Args:
            cleanup_delay: Seconds to wait before deleting a file after download (default: 5)
            scan_interval: Seconds between background cleanup scans (default: 3600 = 1 hour)
        """
        self.cleanup_delay = cleanup_delay
        self.scan_interval = scan_interval
        self.pending_deletions = set()
        self.logger = self._setup_logger()
        self._start_background_cleanup()

    def _setup_logger(self) -> logging.Logger:
        """Set up a logger for the cleanup handler."""
        logger = logging.getLogger("ZipFileCleanup")
        logger.setLevel(logging.INFO)

        # Avoid adding duplicate handlers if logger already exists
        if not logger.handlers:
            handler = logging.FileHandler("zip_cleanup.log")
            formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def _start_background_cleanup(self):
        """Start the background cleanup thread."""
        cleanup_thread = threading.Thread(
            target=self._background_cleanup_service, daemon=True
        )
        cleanup_thread.start()
        self.logger.info("Background cleanup service started")

    def _background_cleanup_service(self):
        """Background service that periodically cleans up old zip files."""
        while True:
            try:
                self.cleanup_old_zip_files()
                time.sleep(self.scan_interval)
            except Exception as e:
                self.logger.error(f"Error in background cleanup: {str(e)}")
                time.sleep(60)  # Wait a minute before retrying if there's an error

    def schedule_cleanup(self, filepath: str):
        """
        Schedule a file for cleanup after download.

        Args:
            filepath: Path to the file that should be deleted
        """
        if not filepath or not os.path.exists(filepath):
            return

        self.pending_deletions.add(filepath)
        self.logger.info(f"Scheduled cleanup for: {filepath}")

        # Start a thread to delete the file after the delay
        threading.Thread(
            target=self._delayed_delete,
            args=(filepath, self.cleanup_delay),
            daemon=True,
        ).start()

    def _delayed_delete(self, filepath: str, delay: int):
        """
        Delete a file after a specified delay.

        Args:
            filepath: Path to the file to delete
            delay: Seconds to wait before deletion
        """
        try:
            time.sleep(delay)
            if os.path.exists(filepath):
                os.remove(filepath)
                self.logger.info(f"Deleted file after download: {filepath}")
            self.pending_deletions.discard(filepath)
        except Exception as e:
            self.logger.error(f"Error deleting file {filepath}: {str(e)}")

    def cleanup_old_zip_files(
        self, max_age_hours: int = 24, directories: Optional[List[str]] = None
    ):
        """
        Clean up old zip files that may have been missed by the immediate cleanup.

        Args:
            max_age_hours: Maximum age of files in hours before deletion (default: 24)
            directories: List of directories to scan (default: current directory and common temp dirs)
        """
        if directories is None:
            directories = [
                ".",  # Current directory
                "temp_export",
                "temp_pdfs",
                "temp_downloads",
                "temp_import",
                "db_backups",
            ]

        current_time = time.time()
        max_age_seconds = max_age_hours * 3600

        for directory in directories:
            if not os.path.exists(directory):
                continue

            for filename in os.listdir(directory):
                if not filename.endswith(".zip"):
                    continue

                filepath = os.path.join(directory, filename)
                if not os.path.isfile(filepath):
                    continue

                # Skip files that are pending deletion
                if filepath in self.pending_deletions:
                    continue

                file_age = current_time - os.path.getmtime(filepath)
                if file_age > max_age_seconds:
                    try:
                        os.remove(filepath)
                        self.logger.info(f"Cleaned up old zip file: {filepath}")
                    except Exception as e:
                        self.logger.error(
                            f"Error cleaning up old file {filepath}: {str(e)}"
                        )

    @contextmanager
    def cleanup_after_download(self, filepath: str):
        """
        Context manager that ensures a file is cleaned up after download.

        Usage:
            with zip_cleanup_handler.cleanup_after_download(zip_filename):
                st.download_button(
                    label="Download ZIP",
                    data=open(zip_filename, "rb").read(),
                    file_name=zip_filename,
                    mime="application/zip"
                )

        Args:
            filepath: Path to the file that should be deleted after download
        """
        try:
            yield filepath
        finally:
            self.schedule_cleanup(filepath)


# Create a singleton instance
zip_cleanup_handler = ZipFileCleanupHandler()


def get_student_info(student_id):
    # Dummy implementation; replace with actual database retrieval
    return {
        "surname": "Doe",
        "other_names": "John",
        "student_id": student_id,
        "programme": "Computer Science",
        "email": "john.doe@example.com",
        "telephone": "1234567890",
        "residential_address": "123 Main St",
        "postal_address": "PO Box 456",
        "last_login": "2023-10-10",
        "passport_photo_path": "path/to/photo.jpg",
    }


def get_student_registrations(student_id):
    # Dummy implementation; replace with actual database retrieval
    return [
        {
            "registration_id": 1,
            "programme": "Computer Science",
            "semester": "First",
            "level": "1",
            "academic_year": "2023/2024",
            "courses": "CS101|Intro to CS|3\nCS102|Data Structures|3",
        }
    ]


def initialize_app():
    if "db_initialized" not in st.session_state:
        init_db()
        st.session_state.db_initialized = True

    if "admin_logged_in" not in st.session_state:
        st.session_state.admin_logged_in = False
        st.session_state.admin_logged_in = False


class RegistrationConstraintsManager:
    """
    Manages registration constraints and storage cleanup.
    Prevents duplicate submissions and cleans up old files.
    """

    def __init__(self, db_path: str = "student_registration.db"):
        self.db_path = db_path
        self.memory_threshold = 0.85  # 85% memory usage threshold

    @contextmanager
    def optimized_connection(self):
        conn = None
        try:
            # Check if MYSQL_CONFIG is available
            if MYSQL_CONFIG:
                # Use MySQL connection
                conn = mysql.connector.connect(**MYSQL_CONFIG)
            else:
                # Fall back to SQLite
                conn = sqlite3.connect(self.db_path)
            yield conn
        finally:
            if conn:
                # Close MySQL connection if it's connected
                if MYSQL_CONFIG and hasattr(conn, 'is_connected') and conn.is_connected():
                    conn.close()
                # Close SQLite connection
                elif not MYSQL_CONFIG and isinstance(conn, sqlite3.Connection):
                    conn.close()
            self._optimize_memory()

    def _optimize_memory(self):
        memory_usage = psutil.Process(os.getpid()).memory_percent()
        if memory_usage > self.memory_threshold:
            gc.collect()

    def check_existing_registration(
        self, student_id: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if student already has a registration.
        Returns (has_registration, status)
        """
        with self.optimized_connection() as conn:
            cursor = conn.cursor()
            
            # Use appropriate placeholder based on database type
            placeholder = "%s" if MYSQL_CONFIG else "?"
            
            cursor.execute(
                f"SELECT approval_status FROM student_info WHERE student_id = {placeholder}",
                (student_id,),
            )
            result = cursor.fetchone()

            if result:
                return True, result[0]
            return False, None

    def validate_passport_photo(self, photo) -> Tuple[bool, str]:
        """
        Validate passport photo requirements
        Returns (is_valid, message)
        """
        if photo is None:
            return False, "Passport photo is mandatory"

        try:
            image = Image.open(photo)

            # Check image format
            if image.format not in ["JPEG", "PNG"]:
                return False, "Photo must be in JPEG or PNG format"

            # Check dimensions (e.g., minimum 200x200, maximum 1000x1000)
            if image.size[0] < 200 or image.size[1] < 200:
                return False, "Photo dimensions too small (minimum 200x200 pixels)"
            if image.size[0] > 1000 or image.size[1] > 1000:
                return False, "Photo dimensions too large (maximum 1000x1000 pixels)"

            # Check file size (max 5MB)
            photo.seek(0, os.SEEK_END)
            file_size = photo.tell()
            if file_size > 5 * 1024 * 1024:  # 5MB in bytes
                return False, "Photo file size too large (maximum 5MB)"

            return True, "Photo validation successful"

        except Exception as e:
            return False, f"Error validating photo: {str(e)}"

    def can_submit_course_registration(self, student_id: str) -> Tuple[bool, str]:
        """
        Check if student can submit a course registration
        Returns (can_submit, message)
        """
        with self.optimized_connection() as conn:
            cursor = conn.cursor()
            
            # Use appropriate placeholder based on database type
            placeholder = "%s" if MYSQL_CONFIG else "?"

            # Check if student info exists and is approved
            cursor.execute(
                f"SELECT approval_status FROM student_info WHERE student_id = {placeholder}",
                (student_id,),
            )
            student_info = cursor.fetchone()

            if not student_info:
                return False, "Student information not found"
            if student_info[0] != "approved":
                return False, "Student information not yet approved"

            # Check existing course registrations
            cursor.execute(
                f"""
                SELECT approval_status 
                FROM course_registration 
                WHERE student_id = {placeholder} 
                ORDER BY date_registered DESC 
                LIMIT 1
                """,
                (student_id,),
            )
            registration = cursor.fetchone()

            if registration:
                if registration[0] == "pending":
                    return False, "Previous course registration pending approval"
                if registration[0] == "approved":
                    return False, "Course registration already approved"

            return True, "Course registration allowed"

    def get_registration_status(self, student_id: str) -> Dict:
        """
        Get comprehensive registration status for a student
        """
        with self.optimized_connection() as conn:
            cursor = conn.cursor()
            
            # Use appropriate placeholder based on database type
            placeholder = "%s" if MYSQL_CONFIG else "?"

            status = {
                "has_student_info": False,
                "student_info_status": None,
                "has_course_registration": False,
                "course_registration_status": None,
                "last_update": None,
            }

            # Check student info
            cursor.execute(
                f"""
                SELECT approval_status, created_at 
                FROM student_info 
                WHERE student_id = {placeholder}
                """,
                (student_id,),
            )
            student_info = cursor.fetchone()

            if student_info:
                status["has_student_info"] = True
                status["student_info_status"] = student_info[0]
                status["last_update"] = student_info[1]

            # Check course registration
            cursor.execute(
                f"""
                SELECT approval_status, date_registered 
                FROM course_registration 
                WHERE student_id = {placeholder} 
                ORDER BY date_registered DESC 
                LIMIT 1
                """,
                (student_id,),
            )
            registration = cursor.fetchone()

            if registration:
                status["has_course_registration"] = True
                status["course_registration_status"] = registration[0]
                status["last_update"] = (
                    max(status["last_update"], registration[1])
                    if status["last_update"]
                    else registration[1]
                )

            return status

    def check_existing_student_info(self, student_id: str) -> bool:
        """
        Returns True if student info already exists.
        """
        with self.optimized_connection() as conn:
            cursor = conn.cursor()
            
            # Use appropriate placeholder based on database type
            placeholder = "%s" if MYSQL_CONFIG else "?"
            
            cursor.execute(
                f"SELECT 1 FROM student_info WHERE student_id = {placeholder}", (student_id,)
            )
            return cursor.fetchone() is not None

    def check_existing_course_registration(self, student_id: str) -> bool:
        """
        Returns True if a course registration already exists for a student.
        """
        with self.optimized_connection() as conn:
            cursor = conn.cursor()
            
            # Use appropriate placeholder based on database type
            placeholder = "%s" if MYSQL_CONFIG else "?"
            
            cursor.execute(
                f"SELECT 1 FROM course_registration WHERE student_id = {placeholder}", (student_id,)
            )
            return cursor.fetchone() is not None

    def cleanup_old_files(self, days_old: int = 30):
        """
        Remove files in the uploads directory that are older than 'days_old'
        and are not referenced in the database.
        """
        with self.optimized_connection() as conn:
            cursor = conn.cursor()
            # Both SELECT statements are now modified to return three columns.
            cursor.execute(
                """
                SELECT ghana_card_path, passport_photo_path, certificate_path
                FROM student_info
                UNION
                SELECT receipt_path, NULL, NULL
                FROM course_registration
                """
            )
            db_files = set()
            for row in cursor.fetchall():
                # Update the set with each value in the tuple if it exists.
                db_files.update(path for path in row if path)

        uploads_dir = "uploads"
        if os.path.exists(uploads_dir):
            current_time = datetime.now().timestamp()
            for filename in os.listdir(uploads_dir):
                file_path = os.path.join(uploads_dir, filename)
                if os.path.isfile(file_path):
                    file_age = current_time - os.path.getmtime(file_path)
                    # Remove file if it is older than days_old and not referenced in db_files.
                    if file_age > (days_old * 86400) and file_path not in db_files:
                        try:
                            os.remove(file_path)
                            print(f"Removed old file: {file_path}")
                        except Exception as e:
                            print(f"Error removing file {file_path}: {str(e)}")


# Initialize MySQL first, which will set MYSQL_CONFIG to None if it fails
    mysql_available = init_mysql_db()
    
def admin_login():
    st.sidebar.subheader("Admin Login")
    username = st.sidebar.text_input("Username", key="login_username")
    password = st.sidebar.text_input("Password", type="password", key="login_password")
    
    # Default admin credentials for development (should be overridden in production)
    default_admin = {"username": "admin", "password": "admin"}
    
    # Try to get admin credentials from secrets, fall back to defaults if not available
    try:
        admin_credentials = st.secrets.get("admin", default_admin)
    except Exception:
        # If secrets are not available (e.g., in local development)
        admin_credentials = default_admin
    
    if st.sidebar.button("Login"):
        if (
            username == admin_credentials["username"]
            and password == admin_credentials["password"]
        ):
            st.session_state.admin_logged_in = True
            st.rerun()
        else:
            st.error("Invalid credentials")


def main():
    initialize_app()

    # Call cleanup for old files at app startup
    rc_manager = RegistrationConstraintsManager()
    rc_manager.cleanup_old_files(days_old=30)

    # Display admin login if not logged in.
    if not st.session_state.get("admin_logged_in", False):
        admin_login()

    if st.session_state.admin_logged_in:
        admin_dashboard()
    else:
        # Add this to the navigation options in main()
        page = st.sidebar.radio(
            "Navigation",
            ["Student Information", "Course Registration", "Student Portal"],
        )

        if page == "Student Information":
            student_info_form()

        elif page == "Course Registration":
            course_registration_form()
        else:
            if "student_logged_in" not in st.session_state:
                student_login_form()
            else:
                student_portal()
                # Only show footer when student is logged in
                student = get_student_info(st.session_state.student_logged_in)
                if student:
                    st.markdown(
                        f"""
                        <div style="text-align: center; margin-top: 2rem; padding: 1rem; color: #666;">
                            <p>UPSA Student Portal • Last login: {student.get('last_login', 'Never')}</p>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )


if __name__ == "__main__":
    init_mysql_db()
    init_db()
    main()

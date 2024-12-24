"""
Email Date Fixer

This script fixes and standardizes .eml email files, particularly those with issues from
email client migrations (e.g., Apple iCloud to Microsoft 365).

Key Functions:
1. Standardizes email headers by keeping only essential ones
2. Fixes incorrect dates using the original Date header
3. Handles Norwegian special characters (æ,ø,å) that may have been corrupted

Usage:
    python 1-email_date_fixer.py

Input:
    Expects .eml files in the 'originals' directory:
    ./0-originals/
    ├── folder1/
    │   └── email1.eml
    └── folder2/
        └── email2.eml

Output:
    Creates a timestamped directory with fixed files:
    ./1-fixed/YYYYMMDD_HHMMSS/
    Preserves the original folder structure

Note:
    After running this script, you can use delete_duplicates.py to remove any duplicate
    emails that might exist across different folders.
"""

import os
import sys
import email
import email.utils
from color_utils import *
from datetime import datetime
import re
from pathlib import Path
from folder_utils import setup_output_directory
import re
from datetime import datetime
import email.utils
from dateutil import parser as date_parser
import pytz


def parse_date_header(email_content, filename=None):
    """
    Extract and parse dates from email content with multiple fallback methods.
    Returns a datetime object or None if no valid date found.
    """
    import re
    from datetime import datetime
    import email.utils
    from dateutil import parser as date_parser
    import pytz

    def try_parse_date(date_str):
        """Try to parse a date string using multiple methods."""
        try:
            # First try email utils parser
            parsed = email.utils.parsedate_to_datetime(date_str)
            if parsed:
                return parsed

            # Then try dateutil parser with fuzzy matching
            return date_parser.parse(date_str, fuzzy=True)
        except:
            return None

    def try_parse_datetime_parts(date_str, time_str=None):
        """Try to parse date and optional time components."""
        try:
            # If we have both date and time, combine them
            if time_str:
                full_datetime_str = f"{date_str} {time_str}"
                return date_parser.parse(full_datetime_str, fuzzy=True)
            return date_parser.parse(date_str, fuzzy=True)
        except:
            return None

    try:
        msg = email.message_from_string(email_content)
        
        # 1. Try standard Date header first
        date_str = msg.get('Date')
        if date_str:
            parsed_date = try_parse_date(date_str)
            if parsed_date:
                return parsed_date

        # 2. Define date patterns with optional time components
        date_patterns = [
            # Format like "1 November 2021 20:00"
            r'(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})(?:\s+(\d{1,2}:\d{2}))?',
            
            # Format like "1 Nov 2021 20:00"
            r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4})(?:\s+(\d{1,2}:\d{2}))?',
            
            # Norwegian month names
            r'(\d{1,2}\s+(?:januar|februar|mars|april|mai|juni|juli|august|september|oktober|november|desember)\s+\d{4})(?:\s+(\d{1,2}:\d{2}))?',
            
            # dd.mm.yyyy HH:MM or dd/mm/yyyy HH:MM
            r'(\d{1,2}[./]\d{1,2}[./]\d{2,4})(?:\s+(\d{1,2}:\d{2}))?',
            
            # yyyy-mm-dd HH:MM
            r'(\d{4}-\d{1,2}-\d{1,2})(?:\s+(\d{1,2}:\d{2}))?',
            
            # Compact formats
            r'(\d{8})(?:_?(\d{4}))?',  # YYYYMMDD_HHMM or YYYYMMDD
            r'(\d{6})',                 # YYMMDD
        ]

        # Process email content
        def search_content(text):
            for pattern in date_patterns:
                matches = re.finditer(pattern, text)
                for match in matches:
                    if len(match.groups()) == 2:
                        date_part, time_part = match.groups()
                        if date_part:
                            parsed = try_parse_datetime_parts(date_part, time_part)
                            if parsed:
                                return parsed
                    elif len(match.groups()) == 1:
                        date_part = match.group(1)
                        parsed = try_parse_datetime_parts(date_part)
                        if parsed:
                            return parsed
            return None

        # First check the email body
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() in ['text/plain', 'text/html']:
                    try:
                        content = part.get_payload(decode=True).decode('utf-8', errors='replace')
                        parsed_date = search_content(content)
                        if parsed_date:
                            return parsed_date
                    except:
                        continue
        else:
            try:
                content = msg.get_payload(decode=True).decode('utf-8', errors='replace')
                parsed_date = search_content(content)
                if parsed_date:
                    return parsed_date
            except:
                pass

        # Then check headers
        for header in ['Subject', 'Message-ID', 'X-Mail-Created-Date']:
            header_value = msg.get(header, '')
            if header_value:
                parsed_date = search_content(header_value)
                if parsed_date:
                    return parsed_date

        # If still no date found, try the filename itself as the last resort
        if filename:
            # First try formats with time components
            filename_patterns = [
                (r'(\d{8})_(\d{6})', '%Y%m%d_%H%M%S'),  # YYYYMMDD_HHMMSS
                (r'(\d{14})', '%Y%m%d%H%M%S'),          # YYYYMMDDHHMMSS
            ]
            
            for pattern, fmt in filename_patterns:
                match = re.search(pattern, filename)
                if match:
                    try:
                        if len(match.groups()) == 2:
                            date_str, time_str = match.groups()
                            return datetime.strptime(f"{date_str}_{time_str}", fmt)
                        else:
                            return datetime.strptime(match.group(1), fmt)
                    except ValueError:
                        continue
            
            # Then try date-only formats (assume 00:00:00 for time)
            date_only_patterns = [
                (r'(\d{4})-(\d{2})-(\d{2})', '%Y-%m-%d'),      # yyyy-mm-dd
                (r'(\d{4})(\d{2})(\d{2})', '%Y%m%d'),          # yyyymmdd
                (r'(\d{2})(\d{2})(\d{2})', '%y%m%d'),          # yymmdd
                (r'(\d{2})-(\d{2})-(\d{4})', '%d-%m-%Y'),      # dd-mm-yyyy
                (r'(\d{2})(\d{2})(\d{4})', '%d%m%Y'),          # ddmmyyyy
                (r'(\d{2})/(\d{2})/(\d{4})', '%d/%m/%Y'),      # dd/mm/yyyy
                (r'(\d{2})\.(\d{2})\.(\d{4})', '%d.%m.%Y'),    # dd.mm.yyyy
                (r'(\d{4})/(\d{2})/(\d{2})', '%Y/%m/%d'),      # yyyy/mm/dd
                (r'(\d{4})\.(\d{2})\.(\d{2})', '%Y.%m.%d'),    # yyyy.mm.dd
            ]
            
            for pattern, fmt in date_only_patterns:
                match = re.search(pattern, filename)
                if match:
                    try:
                        if len(match.groups()) == 3:
                            # Join the groups with the format's separator
                            sep = fmt[2]  # Get separator from format string
                            date_str = sep.join(match.groups())
                            parsed_date = datetime.strptime(date_str, fmt)
                            # Set time to midnight (00:00:00)
                            return parsed_date.replace(hour=0, minute=0, second=0)
                    except ValueError:
                        continue

        return None

    except Exception as e:
        print(f"Error parsing date: {e}")
        return None
    
def try_decode_with_encodings(raw_body, declared_charset=None):
    """Try to decode the raw body with various encodings, with special handling for ISO-8859-1."""
    
    # Check if we have the f8 byte sequence which indicates ISO-8859-1 'ø'
    has_f8 = b'\xf8' in raw_body
    
    if has_f8:
        try:
            # If we see f8, prioritize ISO-8859-1
            decoded = raw_body.decode('iso-8859-1')
            print("Decoded with ISO-8859-1 (found f8 byte)")
            return decoded
        except UnicodeDecodeError:
            print("Failed to decode with ISO-8859-1 despite finding f8 byte")
    
    # Try the declared charset first if we have one
    if declared_charset:
        try:
            decoded = raw_body.decode(declared_charset)
            print(f"Successfully decoded with declared charset: {declared_charset}")
            return decoded
        except UnicodeDecodeError:
            print(f"Failed to decode with declared charset: {declared_charset}")
    
    # Try our list of encodings
    encodings = ['utf-8', 'iso-8859-1', 'windows-1252', 'cp1252']
    for encoding in encodings:
        try:
            decoded = raw_body.decode(encoding)
            print(f"Successfully decoded with: {encoding}")
            return decoded
        except UnicodeDecodeError:
            continue
    
    # If all else fails, use replace mode
    print("Warning: Falling back to UTF-8 with replacement")
    return raw_body.decode('utf-8', errors='replace')

def setup_fixed_directory(root_path):
    """Create fixed directory structure with timestamp."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    fixed_root = root_path / '1-fixed' / timestamp
    fixed_root.mkdir(parents=True, exist_ok=True)
    return fixed_root

def process_eml_file(file_path, original_root, fixed_root):
    """Process a single .eml file and standardize its dates while preserving attachments."""
    try:
        # Calculate relative path from original_root
        rel_path = file_path.relative_to(original_root)
        fixed_path = fixed_root / rel_path
        fixed_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Get the original send date, passing both content and filename
        original_date = parse_date_header(content, str(file_path.name))
        if not original_date:
            raise ValueError(f"Could not find or parse Date header in {file_path.name}")

        # Parse the original message
        msg = email.message_from_string(content)
        
        # Create new message preserving the original MIME structure
        new_msg = email.message.Message()
        
        # Format the canonical date string
        formatted_date = email.utils.formatdate(original_date.timestamp(), localtime=True)
        
        # Add core headers first
        new_msg['From'] = msg.get('From', '')
        new_msg['To'] = msg.get('To', '')
        new_msg['Subject'] = msg.get('Subject', '')
        new_msg['Message-ID'] = msg.get('Message-ID', '')
        new_msg['Date'] = formatted_date
        
        # Preserve original Content-Type and structure
        content_type = msg.get_content_type()
        if msg.is_multipart():
            # For multipart messages, preserve the original boundary
            orig_boundary = msg.get_boundary()
            params = dict(msg.get_params())
            params['boundary'] = orig_boundary
            new_msg['Content-Type'] = msg.get('Content-Type')
        else:
            new_msg['Content-Type'] = msg.get('Content-Type', 'text/plain; charset="UTF-8"')
        
        new_msg['MIME-Version'] = '1.0'
        new_msg['Content-Transfer-Encoding'] = msg.get('Content-Transfer-Encoding', '7bit')

        # Add Exchange-specific headers
        received_time = formatted_date
        new_msg['X-MS-Exchange-Organization-MessageDirectionality'] = 'Incoming'
        new_msg['X-MS-Exchange-Organization-AuthAs'] = 'Internal'
        new_msg['X-MS-Exchange-Organization-AuthSource'] = 'mail.protection.outlook.com'
        new_msg['X-MS-Exchange-Organization-Network-Message-Id'] = (
            f'{original_date.strftime("%Y%m%d%H%M%S")}-{msg.get("Message-ID", "unknown")}'
        )
        
        # Add Received chain
        received_headers = [
            f'from mail.protection.outlook.com (2603:10a6:e10:20::12)\n by mailbox.outlook.com with HTTPS;\n {received_time}',
            f'from exchange.outlook.com (2603:10a6:e10:39::20)\n by mail.protection.outlook.com with Microsoft SMTP Server (version=TLS1_2);\n {received_time}',
            f'from smtp.original.com by exchange.outlook.com with Microsoft SMTP Server id 15.20.8272.18;\n {received_time}'
        ]
        
        for received in received_headers:
            new_msg['Received'] = received

        # Preserve the message body and all attachments
        if msg.is_multipart():
            # For multipart messages, copy all parts
            new_msg.set_payload(msg.get_payload())
        else:
            # For single part messages, preserve the body
            raw_body = msg.get_payload(decode=True)
            charset = msg.get_content_charset()
            if charset:
                try:
                    body = raw_body.decode(charset)
                except UnicodeDecodeError:
                    body = try_decode_with_encodings(raw_body, charset)
            else:
                body = try_decode_with_encodings(raw_body)
            new_msg.set_payload(body)
        
        # Write the complete message
        with open(fixed_path, 'w', encoding='utf-8') as f:
            f.write(str(new_msg))
            
        return True
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False
    
def process_folder(input_path: Path):
    """Process all .eml files in the specified folder structure."""
    print(header("Email Date Fixer"))
    
    if not input_path.exists():
        print(error(f"Input folder not found at {input_path}!"))
        return
        
    # Setup directory structure
    fixed_root = setup_output_directory(input_path, "1-fixed")
    
    successful = 0
    failed_files = []
    
    # Process all .eml files while preserving directory structure
    print(section("Processing Files"))
    for eml_file in input_path.rglob('*.eml'):
        try:
            if process_eml_file(eml_file, input_path, fixed_root):
                successful += 1
            else:
                failed_files.append((str(eml_file.relative_to(input_path)), "Could not find or parse Date header"))
        except Exception as e:
            failed_files.append((str(eml_file.relative_to(input_path)), str(e)))
    
    # Print final summary after all files are processed
    print(section("Processing Results"))
    print(success(f"Successfully processed: {successful} files"))
    print(error(f"Failed to process: {len(failed_files)} files"))
    
    if failed_files:
        print(section("Failed Files"))
        for file_path, error_msg in failed_files:
            print(cross(f"{file_path}"))
            print(error(f"  Error: {error_msg}"))
    
    print(section("Output Location"))
    print(info(f"Fixed files can be found in: {fixed_root}"))

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python 1-email_date_fixer.py ./originals/2006")
        print("Output will be created in: ./1-fixed/2006")
        sys.exit(1)
        
    process_folder(Path(sys.argv[1]))
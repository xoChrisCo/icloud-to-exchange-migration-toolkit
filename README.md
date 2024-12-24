# Email Migration Tools for Apple Mail to Microsoft Exchange/Outlook

This repository contains a suite of Python tools for fixing and standardizing email files during migration, particularly focused on resolving issues when moving emails from Apple Mail/iCloud to Microsoft Exchange/Outlook 365.

## 🎯 Purpose

When migrating emails from Apple Mail/iCloud to Microsoft Exchange/Outlook, you might encounter issues with:

- Incorrect email dates in Outlook
- Duplicated emails
- Corrupted headers from multiple migrations
- Special character encoding problems (particularly with non-ASCII characters)

This toolkit helps resolve these issues by cleaning and standardizing the email files before the final import.

## 🔍 Why These Issues Occur

Apple Mail and Microsoft Outlook interpret email headers differently. When emails have been migrated multiple times between different email clients, they can accumulate multiple or incorrect header fields. This particularly affects:

- Date interpretations
- Character encoding
- Message-ID handling
- Header field ordering

## 📋 Prerequisites

- Python 3.8 or higher
- Apple Mail
- Microsoft Exchange account set up in Apple Mail
- Basic familiarity with running commands in Terminal

## 🛠️ Installation

1. Clone this repository:

   ```bash
   git clone https://github.com/yourusername/email-migration-tools.git
   cd email-migration-tools
   ```

2. Set up a Python virtual environment (recommended):

   ```bash
   python -m venv venv
   source venv/bin/activate  # On macOS/Linux
   # or
   venv\Scripts\activate  # On Windows
   ```

3. Install required packages:

   ```bash
   pip install -r requirements.txt
   ```

## 📝 Step-by-Step Migration Guide

### 1. Prepare Your Environment

1. Add your Exchange email account to Apple Mail
2. Create a temporary folder for the migration (e.g., `~/temp/mbox/`)

### 2. Export from Apple Mail

1. In Apple Mail, select the mailbox you want to migrate
2. Go to `Mailbox` → `Export Mailbox`
3. Choose your temporary folder as the destination
4. Repeat for each year/folder you want to migrate
   - TIP: Exporting one year at a time gives you better control and reduces the risk of overloading the process

### 3. Run the Migration Scripts

For each exported mbox file, run these scripts in order:

1. **Unpack the mbox file:**

   ```bash
   python 0-mbox_to_eml.py ~/temp/mbox/2024.mbox/mbox ./0-originals/2024
   ```

2. **Fix email headers:**

   ```bash
   python 1-email_date_fixer.py ./0-originals/2024/
   ```

3. **Remove duplicates:**

   ```bash
   python 2-delete_duplicates.py ./1-fixed/2024/
   ```

4. **Repack to mbox:**

   ```bash
   # For single year:
   python 3-eml_to_mbox.py ./2-deduplicated/2024 ./3-mbox/2024.mbox
   
   # Or, to combine all years into one mbox:
   python 3-eml_to_mbox.py ./2-deduplicated/ ./3-mbox/all.mbox
   ```

### 4. Import and Move to Exchange

1. In Apple Mail, go to `File` → `Import Mailboxes`
2. Choose "Files in mbox format"
3. Select your processed mbox file from the `3-mbox` folder
4. Once imported, drag emails from the imported archive to your Exchange account
   - TIP: Hold Option while dragging to copy instead of move (safer)
   - Double-check dates and attachments before proceeding

### 5. Final Sync

1. Wait for Apple Mail to sync emails to Exchange
   - This can take several hours for large archives
   - View progress with `Command + Option + 0`
2. Verify emails in Outlook after sync completes

## 📁 Directory Structure

```directories
email-migration/
├── 0-originals/           # Unpacked .eml files
├── 1-fixed/               # Files with corrected headers
├── 2-deduplicated/        # Cleaned files (duplicates removed)
├── 3-mbox/                # Final mbox files for import
├── 0-mbox_to_eml.py       # Unpacks mbox to eml to folder 0-originals
├── 1-email_date_fixer.py  # Fixes email headers. Outputs to 1-fixed
├── 2-delete_duplicates.py # Deletes duplicates. Outputs to 2-deduplicated
├── 3-eml_to_mbox.py       # Packs everything back to mbox to folder provided
└── requirements.txt
```

## 🔧 Troubleshooting

- If scripts fail, check Python version and package installation
- For large mailboxes, process one year at a time
- If special characters appear corrupted, the script will attempt multiple encoding fixes
- Monitor Apple Mail's sync progress window (`Command + Option + 0`)

## ⚡ Performance Tips

- Process smaller batches (e.g., one year) for better control
- Keep original exports until migration is verified
- Run one script at a time to avoid memory issues
- Allow plenty of time for final sync to Exchange

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🔍 Keywords

email migration, Apple Mail to Outlook, iCloud to Exchange, email date fix, email deduplication, mbox conversion, email header fix, Outlook 365 migration, Apple Mail export, Exchange import, email archive tools

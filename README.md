# College Portal DBMS Project

This repository contains the Database Management System (DBMS) project files for a College Portal system.

## Project Structure

- `backend.py` - Python script for database operations
- `complex_query.sql` - Complex SQL queries for the database
- `Sql_Cmd.sql` - SQL commands and database setup
- `index.html` - Web interface file

## Description

This project implements a college portal system using a combination of:
- SQL for database management
- Python for backend operations
- HTML for the user interface

## Files Overview

### SQL Files
- `complex_query.sql` - Contains advanced SQL queries for complex data operations
- `Sql_Cmd.sql` - Basic SQL commands and database initialization scripts

### Python Files
- `backend.py` - Handles the connection between the database and the web interface

### Web Interface
- `index.html` - Main interface file

## Dependencies

### Python Packages
Install the required Python packages using pip:

```bash
pip install flask               # Web framework for the backend
pip install flask-cors         # Handle Cross-Origin Resource Sharing
pip install mysql-connector-python  # MySQL database connectivity
pip install python-dotenv      # Environment variable management
pip install werkzeug          # Security and password hashing
pip install pandas            # Data manipulation (for reports and analytics)
```

### Database
- MySQL Server (version 5.7 or higher)

## Getting Started

1. Install Dependencies
   ```bash
   pip install -r requirements.txt
   ```

2. Set up your database server
   - Install MySQL
   - Create a new database
   - Configure database credentials in `.env` file

3. Database Setup
   ```bash
   mysql -u your_username -p your_database_name < Sql_Cmd.sql
   ```

4. Run the Python backend server
   ```bash
   python backend.py
   ```

5. Access the web interface by opening `index.html` in a web browser


## User Roles and Features

### Student Features
- View personal academic records and grades
- Access course materials and assignments
- Check attendance records
- View exam schedules and results
- Submit assignments and projects
- Register for courses

### Teacher Features
- Manage course materials 
- Take attendance
- Input and manage student grades
- Generate performance reports

### Chairperson Features
- Oversee department activities
- Manage course allocations
- View department statistics and Review student performance metrics
- Generate department reports
- Manage faculty assignments
- Handle administrative requests

## Author

Created by Manya Shetty

## Repository Information

- Repository Name: Collage-Porta
- Owner: manyashetty20
- Branch: main
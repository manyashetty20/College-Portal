import mysql.connector
from mysql.connector import errorcode
from datetime import date, datetime
from flask import Flask, render_template, g, jsonify, request, send_file
from io import BytesIO #

# --- Database Configuration ---
DB_CONFIG = { 'user': 'root', 
             'password': 'manya@2005',
               'host': 'localhost', 
               'database': 'mini_project', 
               'autocommit': True }

app = Flask(__name__, template_folder='.')

# --- DB Connection ---
def get_db():
    # Use 'miniproj' database from the config
    if 'db' not in g:
        try:
            g.db = mysql.connector.connect(**DB_CONFIG)
        except mysql.connector.Error as err:
            # Handle common connection errors
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                return None, "Database access denied. Check user/password."
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                return None, "Database does not exist."
            else:
                return None, str(err)
    return g.db, None

@app.teardown_appcontext
def close_connection(exception):
    db = g.pop('db', None)
    if db is not None: 
        db.close()

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code, safely handling None types."""
    if obj is None: 
        return None # 🌟 FIX: Handle None (NULL) types by returning None or an empty string
        
    if isinstance(obj, (datetime, date)): 
        return obj.isoformat()
        
    raise TypeError(f"Type {type(obj)} not serializable")

# --- API Endpoints ---
# LOGIN & DASHBOARDS
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    db, err = get_db();
    if err: return jsonify({'success': False, 'message': err}), 500
    cursor = db.cursor(dictionary=True)
    # NOTE: Password storage is insecure, use hashing in a real app
    cursor.execute("SELECT user_id, email, role FROM Users WHERE email = %s AND password = %s", (data.get('email'), data.get('password')))
    user = cursor.fetchone()
    cursor.close()
    if user: return jsonify({'success': True, 'user': user})
    else: return jsonify({'success': False, 'message': 'Invalid credentials'}), 401

@app.route('/api/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    db, err = get_db();
    if err: return jsonify({'success': False, 'message': err}), 500
    cursor = db.cursor(dictionary=True)
    stats = {}
    queries = {"students":"SELECT COUNT(*) as c FROM Students", "teachers":"SELECT COUNT(*) as c FROM Teachers", "courses":"SELECT COUNT(*) as c FROM Courses", "departments":"SELECT COUNT(*) as c FROM Departments"}
    for key, query in queries.items():
        cursor.execute(query)
        stats[key] = cursor.fetchone()['c']
    cursor.close()
    return jsonify(stats)

# MiniProj/backend.py (UPDATED)

@app.route('/api/dashboard/student/<string:s_id>', methods=['GET'])
def get_student_dashboard_data(s_id):
    db, err = get_db();
    if err: return jsonify({'courses': [], 'grades': []}), 500
    
    # Use buffered cursor (dictionary=True) for easy result handling
    cursor = db.cursor(dictionary=True)
    
    # --- 🌟 NEW: Call Student_Courses Stored Procedure 🌟 ---
    try:
        # 1. Execute the stored procedure
        cursor.callproc('Student_Courses', (s_id,))
        
        # 2. Fetch all result sets (the courses list)
        courses = []
        # Use stored_results() to fetch results from the SP
        for result in cursor.stored_results():
            courses.extend(result.fetchall())
    
    except mysql.connector.Error as e:
        # Handle potential errors during procedure execution
        cursor.close()
        # In a dashboard context, returning empty data is safer than a 500 error
        print(f"Error calling Student_Courses SP: {e}")
        courses = []
    
    # 3. Proceed with grades query (as before)
    # Note: Grade calculation is handled by a trigger, simplifying this query
    cursor.execute("SELECT c.c_name, g.assessment, g.grade FROM Grades g JOIN Courses c ON g.c_id = c.c_id WHERE g.s_id = %s ORDER BY g.date DESC LIMIT 5", (s_id,))
    grades = cursor.fetchall()
    
    cursor.close()
    return jsonify({'courses': courses, 'grades': grades})

@app.route('/api/dashboard/teacher/<string:t_id>', methods=['GET'])
def get_teacher_dashboard_data(t_id):
    db, err = get_db();
    if err: return jsonify({'courses': []}), 500
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT c.c_id, c.c_name, c.t_id, (SELECT COUNT(*) FROM Student_Courses sc WHERE sc.c_id = c.c_id) as student_count FROM Courses c WHERE t_id = %s", (t_id,))
    courses = cursor.fetchall()
    cursor.close()
    return jsonify({'courses': courses})

# STUDENT FEATURES
@app.route('/api/student/<string:s_id>/grades', methods=['GET'])
def get_student_grades(s_id):
    db, err = get_db()
    if err: return jsonify([]), 500
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT c.c_name, g.assessment, g.total_marks, g.marks_obtained, g.grade, g.date FROM Grades g JOIN Courses c ON g.c_id = c.c_id WHERE g.s_id = %s ORDER BY g.date DESC", (s_id,))
    grades = cursor.fetchall()
    cursor.close()
    return jsonify([dict(row, date=json_serial(row['date'])) for row in grades])

@app.route('/api/student/<string:s_id>/attendance', methods=['GET'])
def get_student_attendance(s_id):
    db, err = get_db();
    if err: return jsonify([]), 500
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT c.c_name, a.date, a.status FROM Attendance a JOIN Courses c ON a.c_id = c.c_id WHERE a.s_id = %s ORDER BY a.date DESC", (s_id,))
    attendance = cursor.fetchall()
    cursor.close()
    return jsonify([dict(row, date=json_serial(row['date'])) for row in attendance])

@app.route('/api/student/enroll', methods=['POST'])
def enroll_student():
    data = request.get_json()
    db, err = get_db();
    if err: return jsonify({'success': False, 'message': err}), 500
    cursor = db.cursor()
    try:
        cursor.execute("INSERT INTO Student_Courses (s_id, c_id) VALUES (%s, %s)", (data.get('s_id'), data.get('c_id')))
        return jsonify({'success': True, 'message': 'Enrollment successful!'})
    except mysql.connector.Error as e:
        # Check for duplicate key error (already enrolled)
        if e.errno == errorcode.ER_DUP_ENTRY:
             return jsonify({'success': False, 'message': "Already enrolled in this course."}), 409
        return jsonify({'success': False, 'message': f"Enrollment failed: {str(e)}"})
    finally:
        cursor.close()

# TEACHER FEATURES
@app.route('/api/teacher/<string:t_id>/courses', methods=['GET'])
def get_teacher_courses(t_id):
    db, err = get_db();
    if err: return jsonify([]), 500
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT c_id, c_name FROM Courses WHERE t_id = %s", (t_id,))
    courses = cursor.fetchall()
    cursor.close()
    return jsonify(courses)

@app.route('/api/course/<string:c_id>/students', methods=['GET'])
def get_course_students(c_id):
    db, err = get_db();
    if err: return jsonify([]), 500
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT s.s_id, s.name FROM Students s JOIN Student_Courses sc ON s.s_id = sc.s_id WHERE sc.c_id = %s", (c_id,))
    students = cursor.fetchall()
    cursor.close()
    return jsonify(students)

@app.route('/api/attendance', methods=['POST'])
def post_attendance():
    records = request.get_json()
    db, err = get_db();
    if err: return jsonify({'success': False, 'message': err}), 500
    cursor = db.cursor()
    # Use ON DUPLICATE KEY UPDATE to allow a teacher to correct a previous day's attendance
    query = "INSERT INTO Attendance (s_id, c_id, `date`, status) VALUES (%s, %s, %s, %s) ON DUPLICATE KEY UPDATE status = VALUES(status)"
    values = [(r['s_id'], r['c_id'], r['date'], r['status']) for r in records]
    
    try:
        cursor.executemany(query, values)
        cursor.close()
        return jsonify({'success': True, 'message': 'Attendance submitted!'})
    except mysql.connector.Error as e:
        cursor.close()
        return jsonify({'success': False, 'message': str(e)}), 400


@app.route('/api/grades', methods=['POST'])
def post_grades():
    records = request.get_json()
    db, err = get_db()
    if err: return jsonify({'success': False, 'message': err}), 500
    
    cursor = db.cursor()
    # Note: Grade calculation is now handled by the trg_before_grade_insert_update trigger in MySQL.
    # We remove the Python grade calculation logic here to rely on the trigger.
    query = """
        INSERT INTO Grades (s_id, c_id, assessment, total_marks, marks_obtained, `date`) 
        VALUES (%s, %s, %s, %s, %s, %s) 
        ON DUPLICATE KEY UPDATE 
        total_marks = VALUES(total_marks), 
        marks_obtained = VALUES(marks_obtained),
        grade = VALUES(grade)
    """
    
    values = []
    for r in records:
        values.append((
            r['s_id'], r['c_id'], r['assessment'], 
            r['total_marks'], r['marks_obtained'], r['date']
        ))
        
    try:
        cursor.executemany(query, values)
        cursor.close()
        return jsonify({'success': True, 'message': 'Grades submitted successfully!'})
    except mysql.connector.Error as e:
        cursor.close()
        return jsonify({'success': False, 'message': str(e)}), 400

# PAYMENTS & GRIEVANCES
@app.route('/api/payments/<string:user_id>', methods=['GET'])
def get_payments(user_id):
    db, err = get_db();
    if err: return jsonify([]), 500
    cursor = db.cursor(dictionary=True)
    # The query in the original b1.py was correct for displaying a user's payments
    cursor.execute("SELECT p.transaction_id, p.amt, p.type, p.date, p.status FROM Payments p WHERE p.user_id = %s ORDER BY p.date DESC", (user_id,))
    payments = cursor.fetchall()
    cursor.close()
    return jsonify([dict(row, date=json_serial(row['date'])) for row in payments])

@app.route('/api/grievances/<string:user_id>', methods=['GET'])
def get_grievances(user_id):
    db, err = get_db();
    if err: return jsonify([]), 500
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT g_id, title, date_submitted, status FROM Grievances WHERE user_id = %s ORDER BY date_submitted DESC", (user_id,))
    grievances = cursor.fetchall()
    cursor.close()
    return jsonify([dict(row, date_submitted=json_serial(row['date_submitted'])) for row in grievances])

@app.route('/api/grievances', methods=['POST'])
def add_grievance():
    data = request.get_json()
    db, err = get_db();
    if err: return jsonify({'success': False, 'message': err}), 500
    cursor = db.cursor()
    try:
        # Status defaults to 'Pending' in DB, no need to set it here unless specified
        cursor.execute("INSERT INTO Grievances (user_id, title, description, date_submitted) VALUES (%s, %s, %s, %s)", (data['user_id'], data['title'], data['description'], date.today()))
        return jsonify({'success': True, 'message': 'Grievance submitted'}), 201
    except mysql.connector.Error as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    finally:
        cursor.close()

# Grievance Management for Chairperson/Teacher (NEW ENDPOINTS)
@app.route('/api/grievances/all', methods=['GET'])
def get_all_grievances():
    db, err = get_db()
    if err: return jsonify([]), 500
    cursor = db.cursor(dictionary=True)
    query = """
        SELECT g.g_id, u.email as submitted_by, g.title, g.description, g.date_submitted, g.status 
        FROM Grievances g 
        JOIN Users u ON g.user_id = u.user_id 
        ORDER BY g.date_submitted DESC
    """
    cursor.execute(query)
    grievances = cursor.fetchall()
    cursor.close()
    return jsonify([dict(row, date_submitted=json_serial(row['date_submitted'])) for row in grievances])

@app.route('/api/grievances/resolve/<int:g_id>', methods=['PUT'])
def resolve_grievance(g_id):
    db, err = get_db()
    if err: return jsonify({'success': False, 'message': err}), 500
    cursor = db.cursor()
    try:
        # Note: In a real system, you would also track the user resolving it.
        cursor.execute("UPDATE Grievances SET status = 'Resolved' WHERE g_id = %s", (g_id,))
        cursor.close()
        return jsonify({'success': True, 'message': 'Grievance has been marked as resolved.'})
    except mysql.connector.Error as e:
        cursor.close()
        return jsonify({'success': False, 'message': str(e)}), 400

# GENERAL MANAGEMENT
@app.route('/api/<string:item_type>', methods=['GET'])
def get_items(item_type):
    if item_type not in ['students', 'teachers', 'departments', 'courses', 'announcements', 'grades/all', 'attendance/all']:
        return jsonify([]), 404
        
    db, err = get_db()
    if err: return jsonify([]), 500
    cursor = db.cursor(dictionary=True)

    if item_type == 'courses':
        s_id = request.args.get('s_id')  # Get student ID from query parameter for enrollment check
        
        # Subquery to count enrolled students for all courses
        enrollment_count_subquery = """
            (SELECT COUNT(*) FROM Student_Courses sc WHERE sc.c_id = c.c_id) AS student_count
        """

        if s_id:
            # Student course listing: Check enrollment status: 1 if enrolled, 0 otherwise
            query = f"""
                SELECT c.c_id, c.c_name, c.credits, d.d_name as department, t.name as teacher_name, c.t_id,
                (CASE WHEN sc.s_id IS NOT NULL THEN 1 ELSE 0 END) as is_enrolled,
                {enrollment_count_subquery}  -- Include student count for all users
                FROM Courses c
                LEFT JOIN Departments d ON c.d_id = d.d_id
                LEFT JOIN Teachers t ON c.t_id = t.t_id
                LEFT JOIN Student_Courses sc ON c.c_id = sc.c_id AND sc.s_id = %s
            """
            cursor.execute(query, (s_id,))
        else:
            # General course listing for Chairperson/Management
            query = f"""
                SELECT c.c_id, c.c_name, c.credits, d.d_name as department, t.name as teacher_name, c.t_id,
                {enrollment_count_subquery} -- Include student count
                FROM Courses c 
                LEFT JOIN Departments d ON c.d_id = d.d_id
                LEFT JOIN Teachers t ON c.t_id = t.t_id
            """
            cursor.execute(query)
    else:
        # ... (rest of the original 'else' logic for other item_types)
        queries = {
            'students': "SELECT s.s_id, s.name, s.enrollment_no, u.email, s.dob FROM Students s JOIN Users u ON s.s_id = u.user_id",
            'teachers': "SELECT t.t_id, t.name, t.designation, d.d_name as department, u.email FROM Teachers t JOIN Users u ON t.t_id = u.user_id LEFT JOIN Departments d ON t.d_id = d.d_id",
            'departments': "SELECT * FROM Departments",
            'announcements': "SELECT * FROM Announcements ORDER BY date_posted DESC",
            'grades/all': "SELECT g.g_id, s.name as student_name, c.c_name, g.assessment, g.grade FROM Grades g JOIN Students s ON g.s_id = s.s_id JOIN Courses c ON g.c_id = c.c_id ORDER BY g.date DESC",
            'attendance/all': "SELECT a.a_id, s.name as student_name, c.c_name, a.date, a.status FROM Attendance a JOIN Students s ON a.s_id = s.s_id JOIN Courses c ON a.c_id = c.c_id ORDER BY a.date DESC"
        }
        cursor.execute(queries[item_type])


    items = cursor.fetchall()
    cursor.close()
    
    # Corrected serialization of the boolean field 'is_enrolled'
    for item in items:
        for key, val in item.items():
            if isinstance(val, (datetime, date)):
                item[key] = json_serial(val)
            elif key == 'is_enrolled':
                item[key] = bool(val)  # Convert 1/0 to true/false

    return jsonify(items)

# TEACHER FEATURES - New endpoint to fetch all grades for a course
@app.route('/api/grades/course/<string:c_id>', methods=['GET'])
def get_course_grades(c_id):
    db, err = get_db()
    if err: return jsonify([]), 500
    cursor = db.cursor(dictionary=True)
    # Fetch all grade records for the course, including the assessment name and marks
    query = "SELECT s_id, assessment, total_marks, marks_obtained FROM Grades WHERE c_id = %s"
    cursor.execute(query, (c_id,))
    grades = cursor.fetchall()
    cursor.close()
    return jsonify(grades)

@app.route('/api/<string:item_type>', methods=['POST'])
def add_item(item_type):
    data = request.get_json()
    db, err = get_db();
    if err: return jsonify({'success': False, 'message': err}), 500
    cursor = db.cursor()
    try:
        if item_type == 'students':
            # Insert into Users first
            cursor.execute("INSERT INTO Users (user_id, email, password, role) VALUES (%s, %s, %s, 'student')", (data['s_id'], data['email'], data['password']))
            # Insert into Students
            cursor.execute("INSERT INTO Students (s_id, name, enrollment_no, dob, sem, d_id) VALUES (%s, %s, %s, %s, %s, %s)", (data['s_id'], data['name'], data['enrollment_no'], data['dob'], data['sem'], data['d_id']))
        elif item_type == 'teachers':
             # Insert into Users first
             cursor.execute("INSERT INTO Users (user_id, email, password, role) VALUES (%s, %s, %s, 'teacher')", (data['t_id'], data['email'], data['password']))
             # Insert into Teachers
             cursor.execute("INSERT INTO Teachers (t_id, name, designation, d_id) VALUES (%s, %s, %s, %s)", (data['t_id'], data['name'], data['designation'], data['d_id']))
        elif item_type == 'departments':
            cursor.execute("INSERT INTO Departments (d_id, d_name) VALUES (%s, %s)", (data['d_id'], data['d_name']))
        elif item_type == 'courses':
            cursor.execute("INSERT INTO Courses (c_id, c_name, credits, d_id, t_id) VALUES (%s, %s, %s, %s, %s)", (data['c_id'], data['c_name'], data['credits'], data['d_id'], data['t_id']))
        elif item_type == 'announcements':
            # user_id is passed from the frontend and is the creator's ID
            cursor.execute("INSERT INTO Announcements (user_id, title, content) VALUES (%s, %s, %s)", (data['user_id'], data['title'], data['content']))
        return jsonify({'success': True, 'message': f'{item_type[:-1].capitalize()} added'}), 201
    except mysql.connector.Error as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    finally:
        cursor.close()

@app.route('/api/student/attendance/course/<string:s_id>/<string:c_id>', methods=['GET'])
def get_course_attendance_percentage(s_id, c_id):
    """
    Calls the CalculateAttendance UDF to get attendance percentage 
    for a specific student in a specific course.
    """
    db, err = get_db()
    if err: return jsonify({'percentage': 0.00}), 500
    cursor = db.cursor()

    # 🌟 THIS IS WHERE THE FUNCTION IS EXPLICITLY CALLED 🌟
    query = "SELECT CalculateAttendance(%s, %s) AS attendance_percent"
    
    try:
        cursor.execute(query, (s_id, c_id))
        result = cursor.fetchone()
        cursor.close()
        
        percentage = result[0] if result and result[0] is not None else 0.00
        
        # Returns the result in a clean JSON format
        return jsonify({'percentage': float(percentage)})
    except mysql.connector.Error as e:
        cursor.close()
        print(f"Error calling CalculateAttendance function: {e}")
        return jsonify({'percentage': 0.00, 'error': str(e)}), 500

@app.route('/api/<string:item_type>/<string:item_id>', methods=['DELETE'])
def delete_item(item_type, item_id):
    db, err = get_db()
    if err:
        return jsonify({'success': False, 'message': err}), 500
    cursor = db.cursor()
    deleted_total = 0
    try:
        if item_type == 'students':
            cursor.execute("DELETE FROM Grades WHERE s_id = %s", (item_id,))
            deleted_total += cursor.rowcount
            cursor.execute("DELETE FROM Attendance WHERE s_id = %s", (item_id,))
            deleted_total += cursor.rowcount
            cursor.execute("DELETE FROM Student_Courses WHERE s_id = %s", (item_id,))
            deleted_total += cursor.rowcount
            # final: remove student record
            cursor.execute("DELETE FROM Students WHERE s_id = %s", (item_id,))
            deleted_total += cursor.rowcount
            # optional: remove from Users (if Users.user_id == s_id)
            cursor.execute("DELETE FROM Users WHERE user_id = %s", (item_id,))
            deleted_total += cursor.rowcount

        elif item_type == 'teachers':
            cursor.execute("DELETE FROM Course_Materials WHERE uploaded_by_t_id = %s", (item_id,))
            deleted_total += cursor.rowcount
            cursor.execute("DELETE FROM Teachers WHERE t_id = %s", (item_id,))
            deleted_total += cursor.rowcount
            cursor.execute("DELETE FROM Users WHERE user_id = %s", (item_id,))
            deleted_total += cursor.rowcount

        elif item_type == 'departments':
            cursor.execute("DELETE FROM Departments WHERE d_id = %s", (item_id,))
            deleted_total += cursor.rowcount
        elif item_type == 'courses':
            cursor.execute("DELETE FROM Courses WHERE c_id = %s", (item_id,))
            deleted_total += cursor.rowcount
        elif item_type == 'announcements':
            cursor.execute("DELETE FROM Announcements WHERE a_id = %s", (item_id,))
            deleted_total += cursor.rowcount
        else:
            # unknown item_type
            cursor.close()
            return jsonify({'success': False, 'message': 'Unknown item type'}), 400

        db.commit()
        return jsonify({'success': True, 'message': 'Item deleted', 'rows_affected': deleted_total})
    except mysql.connector.Error as e:
        db.rollback()
        print(f"SQL Deletion Error: {e}")
        cursor.close()
        return jsonify({'success': False, 'message': str(e)}), 400
    finally:
        cursor.close()


# --- Frontend Route ---
@app.route('/')
def index():
    return render_template('index.html')

# --- BLOB Storage/Streaming Features ---

@app.route('/api/materials/course/<string:c_id>', methods=['GET'])
def get_course_materials(c_id):
    """Retrieves list of materials (metadata only) for a specific course."""
    db, err = get_db()
    if err: return jsonify([]), 500
    cursor = db.cursor(dictionary=True)
    # IMPORTANT: DO NOT SELECT file_content BLOB data here
    query = "SELECT material_id, title, file_name, upload_date FROM Course_Materials WHERE c_id = %s ORDER BY upload_date DESC"
    cursor.execute(query, (c_id,))
    materials = cursor.fetchall()
    cursor.close()
    return jsonify([dict(row, upload_date=json_serial(row['upload_date'])) for row in materials])

@app.route('/api/materials/upload', methods=['POST'])
def upload_course_material():
    """Handles teacher upload of a PDF file (BLOB insertion)."""
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file part'}), 400
    
    file = request.files['file']
    c_id = request.form.get('c_id')
    title = request.form.get('title')
    t_id = request.form.get('t_id') # Teacher ID

    if file.filename == '' or not file.filename.lower().endswith('.pdf'):
        return jsonify({'success': False, 'message': 'No selected file or file is not a PDF.'}), 400
    if not c_id or not title or not t_id:
        return jsonify({'success': False, 'message': 'Missing course ID, title, or teacher ID'}), 400
    
    file_name = file.filename
    file_content = file.read() # Read the entire file content into memory

    try:
        db, err = get_db();
        if err: return jsonify({'success': False, 'message': err}), 500
        cursor = db.cursor()
        
        # Insert BLOB data
        query = "INSERT INTO Course_Materials (c_id, title, file_content, file_name, uploaded_by_t_id) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(query, (c_id, title, file_content, file_name, t_id))
        cursor.close()
        
        return jsonify({'success': True, 'message': f'File {file_name} uploaded and stored in BLOB successfully!'}), 201
        
    except mysql.connector.Error as e:
        return jsonify({'success': False, 'message': f'BLOB insertion failed: {str(e)}'}), 500

@app.route('/api/materials/download/<int:material_id>', methods=['GET'])
def download_material(material_id):
    """Streams the BLOB file content from the database."""
    db, err = get_db()
    if err: return jsonify({'success': False, 'message': err}), 500
    cursor = db.cursor(dictionary=True)
    
    query = "SELECT file_content, file_name FROM Course_Materials WHERE material_id = %s"
    cursor.execute(query, (material_id,))
    material = cursor.fetchone()
    cursor.close()

    if not material:
        return jsonify({'success': False, 'message': 'Material not found'}), 404
    
    # Use BytesIO to create a file-like object from binary data for send_file
    return send_file(
        BytesIO(material['file_content']),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=material['file_name']
    )

@app.route('/api/materials/teacher/<string:t_id>', methods=['GET'])
def get_teacher_materials(t_id):
    """Retrieves all materials uploaded by a specific teacher (metadata only)."""
    db, err = get_db()
    if err: return jsonify([]), 500
    cursor = db.cursor(dictionary=True)
    query = """
        SELECT m.material_id, m.title, m.file_name, m.upload_date, c.c_name
        FROM Course_Materials m
        JOIN Courses c ON m.c_id = c.c_id
        WHERE m.uploaded_by_t_id = %s
        ORDER BY m.upload_date DESC
    """
    cursor.execute(query, (t_id,))
    materials = cursor.fetchall()
    cursor.close()
    return jsonify([dict(row, upload_date=json_serial(row['upload_date'])) for row in materials])

# --- NEW: Reporting & Analytics Endpoints ---

@app.route('/api/report/course_summary', methods=['GET'])
def get_department_course_summary():
    """Calls the Department_Course_Summary_V View."""
    db, err = get_db()
    if err: return jsonify([]), 500
    cursor = db.cursor(dictionary=True)
    # 1. Calls the view
    query = "SELECT * FROM Department_Course_Summary_V"
    cursor.execute(query)
    summary = cursor.fetchall()
    cursor.close()
    return jsonify(summary)
"""
@app.route('/api/report/course_performance_summary/<string:c_id>/<string:assessment>', methods=['GET'])
def get_course_performance_summary_detail(c_id, assessment):
    #Calls GetCoursePerformanceSummary Stored Procedure.
    db, err = get_db()
    if err: return jsonify({}), 500
    # Use unbuffered cursor for stored procedure call
    cursor = db.cursor()
    
    query = "CALL GetCoursePerformanceSummary(%s, %s)"
    
    try:
        cursor.execute(query, (c_id, assessment))
        
        # Fetch results
        result = None
        columns = [col[0] for col in cursor.description]
        data = cursor.fetchone()
        if data:
            result = dict(zip(columns, data))
            
        cursor.close()
        return jsonify(result)

    except mysql.connector.Error as e:
        print(f"MySQL Error in performance SP call: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if cursor: cursor.close()
"""
@app.route('/api/report/high_attendance/<string:min_att_str>', methods=['GET'])
def get_high_attendance_students(min_att_str):
    """
    Calls the Nested Stored Procedure. 
    NOTE: The UI input is used as the threshold, regardless of whether 
    the underlying procedure is 'High' or 'Below' (now using 'Below').
    """
    db, err = get_db()
    if err: return jsonify([]), 500
    cursor = db.cursor() 
    
    try:
        # Convert the string parameter to a float
        min_att = float(min_att_str) 
    except ValueError:
        return jsonify({'error': 'Invalid attendance percentage format provided.'}), 400
    
    # 🌟 CRITICAL CHANGE: Calling the new stored procedure name
    query = "CALL GetStudentsBelowAttendanceMax_Nested(%s)"
    
    try:
        cursor.execute(query, (min_att,))
        
        results = []
        columns = [col[0] for col in cursor.description]
        
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
            
        cursor.close()
        return jsonify(results)
        
    except mysql.connector.Error as e:
        print(f"MySQL Error in attendance SP call: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if cursor: cursor.close()

@app.route('/api/report/grade_dist/<string:c_id>/<string:assessment>', methods=['GET'])
def get_grade_distribution_stats(c_id, assessment):
    """Calls GetCourseGradeDistributionStats Stored Procedure (CTE)."""
    db, err = get_db()
    if err: return jsonify({}), 500
    cursor = db.cursor()
    # 3. Calls the CTE SP
    query = "CALL GetCourseGradeDistributionStats(%s, %s)"
    cursor.execute(query, (c_id, assessment))
    
    # Fetch results
    result = None
    columns = [col[0] for col in cursor.description]
    data = cursor.fetchone()
    if data:
        result = dict(zip(columns, data))
        
    cursor.close()
    return jsonify(result)


@app.route('/api/report/unassigned_teachers', methods=['GET'])
def get_unassigned_teachers():
    """Calls GetUnassignedTeachers Stored Procedure (NOT IN)."""
    db, err = get_db()
    if err: return jsonify([]), 500
    cursor = db.cursor()
    # 4. Calls the NOT IN SP
    query = "CALL GetUnassignedTeachers()"
    cursor.execute(query)
    
    # Fetch results
    results = []
    columns = [col[0] for col in cursor.description]
    for row in cursor.fetchall():
        results.append(dict(zip(columns, row)))

    cursor.close()
    return jsonify(results)

@app.route('/api/report/student_ranking/<string:assessment>', methods=['GET'])
def get_student_assessment_ranking(assessment):
    """Calls GetStudentAssessmentRanking Stored Procedure (Window Function)."""
    db, err = get_db()
    if err: return jsonify([]), 500
    # Use unbuffered cursor for stored procedure call
    cursor = db.cursor() 
    
    query = "CALL GetStudentAssessmentRanking(%s)"
    
    try:
        cursor.execute(query, (assessment,))
        
        # Fetch results: Correct procedure for fetching from a stored procedure call
        results = []
        # Get column names before fetching data
        columns = [col[0] for col in cursor.description] 
        
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
            
        cursor.close()
        return jsonify(results)
        
    except mysql.connector.Error as e:
        # Log and return a specific JSON error message
        print(f"MySQL Error during ranking SP call: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if cursor: cursor.close()
# TEACHER FEATURES - New endpoint to fetch attendance history by course
@app.route('/api/attendance/course/<string:c_id>/history', methods=['GET'])
def get_course_attendance_history(c_id):
    db, err = get_db()
    if err: return jsonify([]), 500
    cursor = db.cursor(dictionary=True)
    
    # Query to fetch ALL attendance records for the course, joined with student name
    query = """
        SELECT a.s_id, s.name, a.date, a.status 
        FROM Attendance a 
        JOIN Students s ON a.s_id = s.s_id 
        WHERE a.c_id = %s 
        ORDER BY a.date DESC, s.name ASC
    """
    
    try:
        cursor.execute(query, (c_id,))
        history = cursor.fetchall()
        cursor.close()
        # Ensure date is serialized correctly
        return jsonify([dict(row, date=json_serial(row['date'])) for row in history])
    except mysql.connector.Error as e:
        cursor.close()
        return jsonify({'error': str(e)}), 500
    
# TEACHER FEATURES - New endpoint to fetch attendance by course and date
@app.route('/api/attendance/course/<string:c_id>/date/<string:date_str>', methods=['GET'])
def get_course_attendance_by_date(c_id, date_str):
    db, err = get_db()
    if err: return jsonify([]), 500
    cursor = db.cursor(dictionary=True)
    
    # Query to fetch the status for all students in that course on that specific date
    query = "SELECT s_id, status FROM Attendance WHERE c_id = %s AND date = %s"
    
    try:
        # Note: date_str is expected to be in ISO format (YYYY-MM-DD)
        cursor.execute(query, (c_id, date_str))
        attendance_records = cursor.fetchall()
        cursor.close()
        return jsonify(attendance_records)
    except mysql.connector.Error as e:
        cursor.close()
        return jsonify({'error': str(e)}), 500
    
@app.route('/api/student/summary/<string:s_id>', methods=['GET'])
def get_student_summary(s_id):
    """Fetches comprehensive academic and personal data for a single student."""
    db, err = get_db()
    if err: return jsonify({'error': err}), 500
    cursor = db.cursor(dictionary=True)

    summary = {}

    # 1. Student Personal Info
    cursor.execute("""
        SELECT s.s_id, s.name, s.enrollment_no, s.sem, d.d_name as department
        FROM Students s
        JOIN Departments d ON s.d_id = d.d_id
        WHERE s.s_id = %s
    """, (s_id,))
    student_info = cursor.fetchone()
    if not student_info:
        cursor.close()
        return jsonify({'error': 'Student not found'}), 404
    summary.update(student_info)

    # 2. Enrolled Courses and Attendance Summary
    cursor.execute("""
        SELECT
            C.c_id,
            C.c_name,
            C.credits,
            T.name AS teacher_name,
            -- Calculates course-specific attendance using the UDF
            CalculateAttendance(SC.s_id, C.c_id) AS attendance_percent
        FROM Student_Courses SC
        JOIN Courses C ON SC.c_id = C.c_id
        LEFT JOIN Teachers T ON C.t_id = T.t_id
        WHERE SC.s_id = %s
    """, (s_id,))
    enrolled_courses = cursor.fetchall()
    summary['courses'] = enrolled_courses
    
    # 3. Overall Statistics (Overall Attendance Average)
    if enrolled_courses:
        total_credits = sum(c['credits'] for c in enrolled_courses)
        avg_attendance = sum(c['attendance_percent'] for c in enrolled_courses) / len(enrolled_courses)
        summary['total_credits'] = total_credits
        summary['overall_attendance_avg'] = round(avg_attendance, 2)
    else:
        summary['total_credits'] = 0
        summary['overall_attendance_avg'] = 0.00
        
    # 4. Grades
    cursor.execute("""
        SELECT C.c_name, G.assessment, G.marks_obtained, G.total_marks, G.grade
        FROM Grades G
        JOIN Courses C ON G.c_id = C.c_id
        WHERE G.s_id = %s
        ORDER BY C.c_name, G.date DESC
    """, (s_id,))
    summary['grades'] = cursor.fetchall()

    cursor.close()
    return jsonify(summary)


# --- Main Execution ---
if __name__ == '__main__':
    print("\nStarting Flask server... Open http://127.0.0.1:5001 in your browser.")
    app.run(debug=True, host='0.0.0.0', port=5001)
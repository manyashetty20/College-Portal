CREATE USER 'Student'@'localhost' IDENTIFIED BY 'pass123';
GRANT SELECT ON mini_project.Students TO 'Student'@'localhost';
GRANT SELECT ON mini_project.Courses TO 'Student'@'localhost';
GRANT SELECT ON mini_project.Departments TO 'Student'@'localhost';
GRANT SELECT ON mini_project.Teachers TO 'Student'@'localhost';
GRANT SELECT ON mini_project.Grades TO 'Student'@'localhost';
GRANT SELECT ON mini_project.Attendance TO 'Student'@'localhost';
GRANT SELECT ON mini_project.Announcements TO 'Student'@'localhost';
GRANT SELECT ON mini_project.Grievances TO 'Student'@'localhost';
GRANT SELECT ON mini_project.Student_Courses TO 'Student'@'localhost';

GRANT INSERT, DELETE ON mini_project.Student_Courses TO 'Student'@'localhost';
GRANT INSERT ON mini_project.Grievances TO 'Student'@'localhost';


--user cmd
mysql -u Student -p
pass123
use mini_project;
select * from attendance;
INSERT INTO Grievances (user_id, title, description) VALUES ('S001', 'Test', 'Test grievance');
INSERT INTO Student_Courses (s_id, c_id) VALUES ('S002', 'CS102');
DELETE FROM Student_Courses WHERE s_id = 'S002' AND c_id = 'CS102';
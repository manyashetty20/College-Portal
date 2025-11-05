CREATE DATABASE IF NOT EXISTS mini_project;
use mini_project;

-- 1. PREREQUISITE TABLES (No Foreign Keys pointing to others)

DROP TABLE IF EXISTS `Users`;
CREATE TABLE `Users` (
  `user_id` varchar(10) NOT NULL,
  `email` varchar(50) NOT NULL,
  `password` varchar(50) NOT NULL,
  `role` enum('student','teacher','chairperson') NOT NULL,
  PRIMARY KEY (`user_id`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `Departments`;
CREATE TABLE `Departments` (
  `d_id` varchar(10) NOT NULL,
  `d_name` varchar(50) NOT NULL,
  PRIMARY KEY (`d_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 2. CORE IDENTITY TABLES (Depend on Users and Departments)

DROP TABLE IF EXISTS `Students`;
CREATE TABLE `Students` (
  `s_id` varchar(10) NOT NULL,
  `name` varchar(50) NOT NULL,
  `enrollment_no` varchar(20) NOT NULL,
  `dob` date DEFAULT NULL,
  `sem` int DEFAULT NULL,
  `contact_no` varchar(15) DEFAULT NULL,
  `d_id` varchar(10) DEFAULT NULL,
  PRIMARY KEY (`s_id`),
  UNIQUE KEY `enrollment_no` (`enrollment_no`),
  KEY `d_id` (`d_id`),
  CONSTRAINT `students_ibfk_1` FOREIGN KEY (`s_id`) REFERENCES `Users` (`user_id`) ON DELETE CASCADE,
  CONSTRAINT `students_ibfk_2` FOREIGN KEY (`d_id`) REFERENCES `Departments` (`d_id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `Teachers`;
CREATE TABLE `Teachers` (
  `t_id` varchar(10) NOT NULL,
  `name` varchar(50) NOT NULL,
  `designation` varchar(50) DEFAULT NULL,
  `d_id` varchar(10) DEFAULT NULL,
  PRIMARY KEY (`t_id`),
  KEY `d_id` (`d_id`),
  CONSTRAINT `teachers_ibfk_1` FOREIGN KEY (`t_id`) REFERENCES `Users` (`user_id`) ON DELETE CASCADE,
  CONSTRAINT `teachers_ibfk_2` FOREIGN KEY (`d_id`) REFERENCES `Departments` (`d_id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `Courses`;
CREATE TABLE `Courses` (
  `c_id` varchar(10) NOT NULL,
  `c_name` varchar(50) NOT NULL,
  `credits` int DEFAULT NULL,
  `d_id` varchar(10) DEFAULT NULL,
  `t_id` varchar(10) DEFAULT NULL,
  PRIMARY KEY (`c_id`),
  KEY `d_id` (`d_id`),
  KEY `t_id` (`t_id`),
  CONSTRAINT `courses_ibfk_1` FOREIGN KEY (`d_id`) REFERENCES `Departments` (`d_id`) ON DELETE SET NULL,
  CONSTRAINT `courses_ibfk_2` FOREIGN KEY (`t_id`) REFERENCES `Teachers` (`t_id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 3. UTILITY AND DATA TABLES (Depend on Students, Teachers, and Courses)

DROP TABLE IF EXISTS `Student_Courses`;
CREATE TABLE `Student_Courses` (
  `s_id` varchar(10) NOT NULL,
  `c_id` varchar(10) NOT NULL,
  PRIMARY KEY (`s_id`,`c_id`),
  KEY `c_id` (`c_id`),
  CONSTRAINT `student_courses_ibfk_1` FOREIGN KEY (`s_id`) REFERENCES `Students` (`s_id`) ON DELETE CASCADE,
  CONSTRAINT `student_courses_ibfk_2` FOREIGN KEY (`c_id`) REFERENCES `Courses` (`c_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `Announcements`;
CREATE TABLE `Announcements` (
  `a_id` int NOT NULL AUTO_INCREMENT,
  `user_id` varchar(10) DEFAULT NULL,
  `title` varchar(100) NOT NULL,
  `content` text,
  `date_posted` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`a_id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `announcements_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `Users` (`user_id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `Attendance`;
CREATE TABLE `Attendance` (
  `a_id` int NOT NULL AUTO_INCREMENT,
  `s_id` varchar(10) DEFAULT NULL,
  `c_id` varchar(10) DEFAULT NULL,
  `date` date NOT NULL,
  `status` enum('Present','Absent') NOT NULL,
  PRIMARY KEY (`a_id`),
  UNIQUE KEY `s_id` (`s_id`,`c_id`,`date`),
  KEY `c_id` (`c_id`),
  CONSTRAINT `attendance_ibfk_1` FOREIGN KEY (`s_id`) REFERENCES `Students` (`s_id`) ON DELETE CASCADE,
  CONSTRAINT `attendance_ibfk_2` FOREIGN KEY (`c_id`) REFERENCES `Courses` (`c_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `Grades`;
CREATE TABLE `Grades` (
  `g_id` int NOT NULL AUTO_INCREMENT,
  `s_id` varchar(10) DEFAULT NULL,
  `c_id` varchar(10) DEFAULT NULL,
  `assessment` varchar(50) NOT NULL,
  `total_marks` int DEFAULT NULL,
  `grade` varchar(2) DEFAULT NULL,
  `date` date DEFAULT NULL,
  `marks_obtained` int DEFAULT NULL,
  PRIMARY KEY (`g_id`),
  UNIQUE KEY `s_id` (`s_id`,`c_id`,`assessment`),
  KEY `c_id` (`c_id`),
  CONSTRAINT `grades_ibfk_1` FOREIGN KEY (`s_id`) REFERENCES `Students` (`s_id`) ON DELETE CASCADE,
  CONSTRAINT `grades_ibfk_2` FOREIGN KEY (`c_id`) REFERENCES `Courses` (`c_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `Grievances`;
CREATE TABLE `Grievances` (
  `g_id` int NOT NULL AUTO_INCREMENT,
  `user_id` varchar(10) DEFAULT NULL,
  `title` varchar(100) NOT NULL,
  `description` text,
  `date_submitted` date DEFAULT NULL,
  `status` enum('Pending','In Progress','Resolved','Submitted') DEFAULT 'Pending',
  `resolved_by_t_id` varchar(10) DEFAULT NULL,
  PRIMARY KEY (`g_id`),
  KEY `user_id` (`user_id`),
  KEY `resolved_by_t_id` (`resolved_by_t_id`),
  CONSTRAINT `grievances_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `Users` (`user_id`) ON DELETE CASCADE,
  CONSTRAINT `grievances_ibfk_2` FOREIGN KEY (`resolved_by_t_id`) REFERENCES `Teachers` (`t_id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=20 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `Payments`;
CREATE TABLE `Payments` (
  `p_id` int NOT NULL AUTO_INCREMENT,
  `user_id` varchar(10) DEFAULT NULL,
  `transaction_id` varchar(50) NOT NULL,
  `date` date NOT NULL,
  `amt` decimal(10,2) NOT NULL,
  `type` varchar(50) DEFAULT NULL,
  `status` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`p_id`),
  UNIQUE KEY `transaction_id` (`transaction_id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `payments_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `Users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `User_Audit_Log`;
CREATE TABLE `User_Audit_Log` (
  `log_id` int NOT NULL AUTO_INCREMENT,
  `user_id` varchar(10) DEFAULT NULL,
  `old_role` varchar(20) DEFAULT NULL,
  `new_role` varchar(20) DEFAULT NULL,
  `change_timestamp` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`log_id`),
  KEY `user_id_idx` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- 4. INSERT STATEMENTS (Order adjusted to match CREATE TABLE order)

INSERT INTO `Users` VALUES 
('C01','chair.cs@example.com','pass123','chairperson'),
('S001','manya@example.com','pass123','student'),
('S002','sans@example.com','password123','student'),
('S003','manya.shetty@example.com','password123','student'),
('T01','ila@example.com','pass123','teacher'),
('T02','madhura@example.com','pass123','teacher');

INSERT INTO `Departments` VALUES 
('D01','Computer Science'),
('D02','Mechanical');

INSERT INTO `Students` VALUES 
('S001','Manya','EN12345','2005-05-20',3,NULL,'D01'),
('S002','Sansi','EN12346','2005-08-22',3,NULL,'D01'),
('S003','Manya Shetty','EN123457','2025-03-20',5,NULL,'D01');

INSERT INTO `Teachers` VALUES 
('C01','Dr. A','Chairperson','D01'),
('T01','Ila','Professor','D01'),
('T02','Madhura','Professor','D01');

INSERT INTO `Courses` VALUES 
('CS101','Programming',4,'D01','T01'),
('CS102','Math',5,'D01','T02'),
('CS103','DBMS',5,'D01','C01');

INSERT INTO `Student_Courses` VALUES 
('S001','CS101'),
('S003','CS101'),
('S001','CS102'),
('S001','CS103'),
('S003','CS103');

INSERT INTO `Announcements` VALUES 
(1,'C01','Mid-term Exams','Schedule has been posted.','2025-09-30 15:15:38'),
(3,'C01','Code','This code is working','2025-10-02 09:21:35');

INSERT INTO `Attendance` VALUES 
(1,'S001','CS101','2025-09-29','Present'),
(3,'S001','CS102','2025-10-02','Present'),
(4,'S001','CS102','2025-10-01','Absent');

INSERT INTO `Grades` VALUES 
(1,'S001','CS101','ISA',88,'A','2025-09-20',NULL),
(3,'S001','CS101','ESA',100,'B','2025-10-02',89);

-- CORRECTED: Removed extra closing parenthesis (was causing ERROR 1064)
INSERT INTO `Grievances` VALUES 
(1,'S001','Library Timin','The library closes too late','2025-09-10','In Progress',NULL),
(2,'S001','Library Timing','The library closes too late','2025-09-10','In Progress',NULL);

INSERT INTO `Payments` VALUES 
(1,'S001','TXN12345','2025-08-15',5000.00,'Tuition Fee','Completed');

INSERT INTO `User_Audit_Log` VALUES 
(1,'S002','student','teacher','2025-10-24 14:00:56'),
(2,'S002','teacher','student','2025-10-24 14:00:56');


DROP TABLE IF EXISTS `Course_Materials`;
CREATE TABLE `Course_Materials` (
  `material_id` INT NOT NULL AUTO_INCREMENT,
  `c_id` VARCHAR(10) NOT NULL,
  `title` VARCHAR(100) NOT NULL,
  `file_content` LONGBLOB NOT NULL, -- Storing the file content as BLOB
  `file_name` VARCHAR(255) NOT NULL, -- Store the original file name/type for headers
  `uploaded_by_t_id` VARCHAR(10) DEFAULT NULL,
  `upload_date` DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`material_id`),
  KEY `c_id` (`c_id`),
  KEY `uploaded_by_t_id` (`uploaded_by_t_id`),
  CONSTRAINT `course_materials_ibfk_1` FOREIGN KEY (`c_id`) REFERENCES `Courses` (`c_id`) ON DELETE CASCADE,
  CONSTRAINT `course_materials_ibfk_2` FOREIGN KEY (`uploaded_by_t_id`) REFERENCES `Teachers` (`t_id`) ON DELETE SET NULL
)

-- 5. ROUTINES AND TRIGGERS

DELIMITER ;;

-- FIX: Added `READS SQL DATA` to resolve ERROR 1418
DROP FUNCTION IF EXISTS CalculateAttendance;
CREATE FUNCTION CalculateAttendance(
    p_student_id VARCHAR(10),
    p_course_id VARCHAR(10)
) RETURNS decimal(5,2)
    READS SQL DATA
BEGIN
    -- Declare variables to hold the counts
    DECLARE v_present_days INT DEFAULT 0;
    DECLARE v_total_days INT DEFAULT 0;
    DECLARE v_percentage DECIMAL(5, 2) DEFAULT 0.00;

    -- Count the number of 'Present' records
    SELECT COUNT(*)
    INTO v_present_days
    FROM `Attendance`
    WHERE s_id = p_student_id
      AND c_id = p_course_id
      AND `status` = 'Present';

    -- Count the total number of attendance records (Present + Absent)
    SELECT COUNT(*)
    INTO v_total_days
    FROM `Attendance`
    WHERE s_id = p_student_id
      AND c_id = p_course_id;

    -- Check for division by zero if there are no records
    IF v_total_days > 0 THEN
        SET v_percentage = (v_present_days / v_total_days) * 100.00;
    END IF;

    -- Return the calculated percentage
    RETURN v_percentage;
END ;;

DROP PROCEDURE IF EXISTS Student_Courses;
CREATE PROCEDURE Student_Courses(IN p_student_id VARCHAR(10))
BEGIN
    SELECT
        c.c_id,
        c.c_name,
        c.credits,
        t.name AS teacher_name
    FROM `Courses` c
    JOIN `Student_Courses` sc ON c.c_id = sc.c_id
    LEFT JOIN `Teachers` t ON c.t_id = t.t_id
    WHERE sc.s_id = p_student_id;
END ;;

DROP TRIGGER IF EXISTS `role_update`;
CREATE TRIGGER `role_update`
AFTER UPDATE ON `Users`
FOR EACH ROW
BEGIN
    IF OLD.role <> NEW.role THEN
        INSERT INTO `User_Audit_Log` (user_id, old_role, new_role)
        VALUES (OLD.user_id, OLD.role, NEW.role);
    END IF;
END ;;

-- New Triggers/Procedures/Functions added in previous interactions:

DROP TRIGGER IF EXISTS trg_before_department_delete;
CREATE TRIGGER trg_before_department_delete
BEFORE DELETE ON Departments
FOR EACH ROW
BEGIN
    DECLARE course_count INT;
    SELECT COUNT(*) INTO course_count
    FROM Courses
    WHERE d_id = OLD.d_id;
    IF course_count > 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Cannot delete department while active courses are assigned to it.';
    END IF;
END ;;

DROP TRIGGER IF EXISTS trg_before_grade_insert_update;
CREATE TRIGGER trg_before_grade_insert_update
BEFORE INSERT ON Grades
FOR EACH ROW
BEGIN
    DECLARE percentage DECIMAL(5, 2);

    IF NEW.marks_obtained IS NOT NULL AND NEW.total_marks IS NOT NULL AND NEW.total_marks > 0 THEN
        SET percentage = (NEW.marks_obtained / NEW.total_marks) * 100;

        IF percentage >= 90 THEN
            SET NEW.grade = 'S';
        ELSEIF percentage >= 80 THEN
            SET NEW.grade = 'A';
        ELSEIF percentage >= 70 THEN
            SET NEW.grade = 'B';
        ELSEIF percentage >= 60 THEN
            SET NEW.grade = 'C';
        ELSEIF percentage >= 50 THEN
            SET NEW.grade = 'D';
        ELSEIF percentage >= 40 THEN
            SET NEW.grade = 'E';
        ELSE
            SET NEW.grade = 'F';
        END IF;
    ELSE
        SET NEW.grade = NULL;
    END IF;
END ;;

DROP PROCEDURE IF EXISTS GetCoursePerformanceSummary;
CREATE PROCEDURE GetCoursePerformanceSummary(
    IN p_course_id VARCHAR(10),
    IN p_assessment_type VARCHAR(50)
)
BEGIN
    SELECT
        C.c_name,
        COUNT(DISTINCT SC.s_id) AS Total_Enrolled_Students,
        AVG(G.marks_obtained) AS Average_Assessment_Marks,
        MAX(G.total_marks) AS Total_Marks_for_Assessment
    FROM Courses C
    JOIN Student_Courses SC ON C.c_id = SC.c_id
    LEFT JOIN Grades G ON C.c_id = G.c_id AND G.assessment = p_assessment_type
    WHERE C.c_id = p_course_id
    GROUP BY C.c_name;
END ;;

DROP FUNCTION IF EXISTS GetTotalCourseCredits;
CREATE FUNCTION GetTotalCourseCredits(
    p_student_id VARCHAR(10)
) RETURNS INT
DETERMINISTIC
BEGIN
    DECLARE total_credits INT DEFAULT 0;

    SELECT SUM(C.credits)
    INTO total_credits
    FROM Student_Courses SC
    JOIN Courses C ON SC.c_id = C.c_id
    WHERE SC.s_id = p_student_id;
    RETURN COALESCE(total_credits, 0);
END ;;

DELIMITER ;

-- Dump completed on 2025-10-24 14:18:25



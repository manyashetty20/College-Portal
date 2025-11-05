DELIMITER $$

-- 1. High-Attendance Students (NESTED SUBQUERY)
DROP PROCEDURE IF EXISTS GetStudentsHighOverallAttendance_Nested$$
CREATE PROCEDURE GetStudentsHighOverallAttendance_Nested(IN p_min_attendance DECIMAL(5, 2))
BEGIN
    SELECT
        S.s_id,
        S.name,
        ROUND(AVG(CourseAttendance.attendance_percent), 2) AS overall_avg_attendance_percent
    FROM
        Students S
    JOIN
        Student_Courses SC ON S.s_id = SC.s_id
    JOIN (
        -- DERIVED TABLE: Calculates the attendance percentage for EACH student-course pair
        SELECT
            A.s_id,
            A.c_id,
            (SUM(CASE WHEN A.status = 'Present' THEN 1 ELSE 0 END) * 100.00) / COUNT(A.a_id) AS attendance_percent
        FROM
            Attendance A
        GROUP BY
            A.s_id, A.c_id
    ) AS CourseAttendance ON S.s_id = CourseAttendance.s_id AND SC.c_id = CourseAttendance.c_id
    GROUP BY
        S.s_id, S.name
    HAVING
        ROUND(AVG(CourseAttendance.attendance_percent), 2) >= p_min_attendance
    ORDER BY
        overall_avg_attendance_percent DESC;
END$$


-- 3. Course-Wise Grade Distribution (CTE and Conditional Aggregation)
DROP PROCEDURE IF EXISTS GetCourseGradeDistributionStats$$
CREATE PROCEDURE GetCourseGradeDistributionStats(
    IN p_course_id VARCHAR(10),
    IN p_assessment_type VARCHAR(50)
)
BEGIN
    -- CTE: Filter the Grades table down to the required course and assessment type
    WITH FilteredGrades AS (
        SELECT
            s_id,
            grade
        FROM
            Grades
        WHERE
            c_id = p_course_id AND assessment = p_assessment_type
    )
    SELECT
        (SELECT c_name FROM Courses WHERE c_id = p_course_id) AS c_name,
        p_assessment_type AS assessment_type,
        COUNT(FG.s_id) AS total_assessed_students,
        SUM(CASE WHEN FG.grade IN ('S', 'A') THEN 1 ELSE 0 END) AS high_grade_count,
        SUM(CASE WHEN FG.grade IN ('B', 'C', 'D', 'E') THEN 1 ELSE 0 END) AS passing_grade_count,
        SUM(CASE WHEN FG.grade = 'F' THEN 1 ELSE 0 END) AS failing_grade_count
    FROM
        FilteredGrades FG;
END$$


-- 4. Teachers without a Course (Nested Subquery using NOT IN)
DROP PROCEDURE IF EXISTS GetUnassignedTeachers$$
CREATE PROCEDURE GetUnassignedTeachers()
BEGIN
    SELECT
        T.t_id,
        T.name,
        T.designation,
        D.d_name AS department_name
    FROM
        Teachers T
    JOIN
        Departments D ON T.d_id = D.d_id
    WHERE
        T.t_id NOT IN (
            SELECT
                t_id
            FROM
                Courses
            WHERE
                t_id IS NOT NULL
            GROUP BY
                t_id
        );
END$$


-- 5. Student Performance and Course Load Ranking (Window Function)
DROP PROCEDURE IF EXISTS GetStudentAssessmentRanking$$
CREATE PROCEDURE GetStudentAssessmentRanking(
    IN p_assessment_type VARCHAR(50)
)
BEGIN
    SELECT
        S.s_id,
        S.name,
        GetTotalCourseCredits(S.s_id) AS total_enrolled_credits,
        AVG(G.marks_obtained) AS avg_assessment_marks,
        RANK() OVER (ORDER BY AVG(G.marks_obtained) DESC) AS performance_rank
    FROM
        Students S
    LEFT JOIN
        Grades G ON S.s_id = G.s_id AND G.assessment = p_assessment_type
    GROUP BY
        S.s_id, S.name
    ORDER BY
        performance_rank, S.name;
END$$

DELIMITER ;

-- 2. Department Course Load View (Must be outside DELIMITER block)
DROP VIEW IF EXISTS Department_Course_Summary_V;
CREATE VIEW Department_Course_Summary_V AS
SELECT
    D.d_id,
    D.d_name,
    COUNT(C.c_id) AS total_courses_offered,
    COALESCE(SUM(C.credits), 0) AS total_department_credits,
    T.name AS chairperson_name
FROM
    Departments D
LEFT JOIN
    Courses C ON D.d_id = C.d_id
LEFT JOIN
    Teachers T ON D.d_id = T.d_id
LEFT JOIN
    Users U ON T.t_id = U.user_id AND U.role = 'chairperson'
GROUP BY
    D.d_name, D.d_id, T.name;
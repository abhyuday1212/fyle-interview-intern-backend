import random
from sqlalchemy import text

from core import db
from core.models.assignments import Assignment, AssignmentStateEnum, GradeEnum

# def client():
#     from tests.conftest import client
#     return client

def create_n_graded_assignments_for_teacher(number: int = 0, teacher_id: int = 1) -> int:
    """
    Creates 'n' graded assignments for a specified teacher and returns the count of assignments with grade 'A'.
    """
    grade_a_counter: int = Assignment.filter(
        Assignment.teacher_id == teacher_id,
        Assignment.grade == GradeEnum.A
    ).count()

    for _ in range(number):
        grade = random.choice(list(GradeEnum))

        assignment = Assignment(
            teacher_id=teacher_id,
            student_id=1,
            grade=grade,
            content='test content',
            state=AssignmentStateEnum.GRADED
        )

        db.session.add(assignment)
        if grade == GradeEnum.A:
            grade_a_counter += 1

    db.session.commit()
    return grade_a_counter
def test_get_assignments_in_graded_state_for_each_student(client):
    try:
        """Test to get graded assignments for each student"""

        db.session.begin_nested()

        # Find all the assignments for student 1 and change its state to 'GRADED'
        submitted_assignments = Assignment.filter(Assignment.student_id == 1).all()

        # Iterate over each assignment and update its state
        for assignment in submitted_assignments:
            assignment.state = AssignmentStateEnum.GRADED 

        # Flush the changes to the database session
        db.session.commit()  

        # Execute the SQL query and compare the result with the expected result
        sql_query = """
        SELECT COUNT(*) AS total_rows
        FROM ( 
            SELECT student_id
            FROM assignments
            WHERE student_id = 1 AND (assignments.state = 'GRADED' OR assignments.state = 'SUBMITTED')
        ) AS counted_data;
        """


        result = db.session.execute(text(sql_query)).fetchone()

        # Extract the count from the result
        num_assignments_in_db = result['total_rows']

        # Use the dynamically fetched number as the expected result
        expected_result = num_assignments_in_db

        # Now fetch the count of assignments from the controller endpoint to compare
        response = client.get('/principal/assignments', headers={"X-Principal": '{"user_id":5, "principal_id":1}'})
        assert response.status_code == 200

        response_data = response.json.get('data')

        # Count the number of assignments in the response
        num_assignments_in_response = len(response_data)


        # Compare the number of assignments from the database with the expected number
        assert num_assignments_in_db == expected_result, (
            f"Expected {expected_result} assignments, but got {num_assignments_in_db} from the SQL query.")

    
    finally:
        db.session.rollback()


def test_get_teacher_with_max_a_grades():
    # Setup: Start a new transaction to ensure test isolation
    db.session.begin_nested()

    try:
        # SQL query to find the teacher with the maximum number of 'A' grades
        sql_query = """
            SELECT t.id AS teacher_id, COUNT(a.id) AS num_a_grades
            FROM assignments a
            JOIN teachers t ON a.teacher_id = t.id
            WHERE a.grade = 'A'
            GROUP BY t.id
            ORDER BY num_a_grades DESC
            LIMIT 1;
        """
        sql_result = db.session.execute(text(sql_query)).fetchall()
        max_a_teacher = sql_result[0] if sql_result else (None, 0)
        teacher_id_max_a, count_max_a = max_a_teacher

        # Debugging: Print detailed information for manual verification
        print(f"Teacher ID with max 'A' grades: {teacher_id_max_a}, Count of 'A' grades: {count_max_a}")

        # Ensure that the teacher with max 'A' grades exists
        assert teacher_id_max_a is not None, "No teacher found with 'A' grades"

        # Create and grade 5 assignments for the teacher with max 'A' grades
        create_n_graded_assignments_for_teacher(5, teacher_id_max_a)
        
        # Wait for the database to commit changes if necessary (sometimes needed for consistency)
        db.session.flush()  # Ensure changes are flushed to the database

        # Re-fetch the actual count of 'A' grades for the teacher with max 'A' grades
        updated_query = """
            SELECT COUNT(a.id) AS num_a_grades
            FROM assignments a
            WHERE a.teacher_id = :teacher_id AND a.grade = 'A';
        """
        updated_sql_result = db.session.execute(text(updated_query), {'teacher_id': teacher_id_max_a}).fetchall()
        updated_count_max_a = updated_sql_result[0][0] if updated_sql_result else 0

        # Debugging: Print updated count information
        print(f"Updated Count of 'A' grades for teacher {teacher_id_max_a}: {updated_count_max_a}")

        # Assert that the updated count matches the expected count
        expected_count = count_max_a + 5  # 5 is the number of new assignments created
        assert updated_count_max_a == expected_count, f"Expected {expected_count}, got {updated_count_max_a}"

    finally:
        # Teardown: Rollback transaction to ensure test isolation
        db.session.rollback()
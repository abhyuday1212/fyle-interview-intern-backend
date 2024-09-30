from flask import Blueprint, jsonify,make_response
from core import db
from core.apis import decorators
from core.apis.responses import APIResponse
from core.models.assignments import Assignment
from core.models.assignments import Assignment,GradeEnum

from .schema import AssignmentSchema, AssignmentGradeSchema
teacher_assignments_resources = Blueprint('teacher_assignments_resources', __name__)


@teacher_assignments_resources.route('/assignments', methods=['GET'], strict_slashes=False)
@decorators.authenticate_principal
def list_assignments(p):
    """Returns list of assignments"""
    teacher_id = getattr(p, 'teacher_id', None) 

    if teacher_id is None:
        return APIResponse.error(message="Teacher ID not found in the authenticated principal.", status_code=400)

    teachers_assignments = Assignment.get_assignments_by_teacher(teacher_id)
    teachers_assignments_dump = AssignmentSchema().dump(teachers_assignments, many=True)
    
    return APIResponse.respond(data=teachers_assignments_dump)


@teacher_assignments_resources.route('/assignments/grade', methods=['POST'], strict_slashes=False)
@decorators.accept_payload
@decorators.authenticate_principal
def grade_assignment(p, incoming_payload):
    """Grade an assignment"""

    teacher_id_from_request = p.teacher_id
    assignment_id = incoming_payload.get('id')
    grade = incoming_payload.get('grade')

    assignment = Assignment.query.get(assignment_id)

    if not assignment:
        return make_response(jsonify({"error": "FyleError"}), 404)
    
            
    elif incoming_payload['grade'] not in GradeEnum.__members__:
        return make_response(jsonify({"error": "ValidationError"}), 400)
    
    # Check if the assignment is submitted
    elif assignment.state == "SUBMITTED":
       db.session.close()
       response = jsonify({
            "error": "FyleError",
            "message": "only a Submitted assignment can be graded"
            })
       return make_response(response, 400)

    elif assignment.teacher_id != teacher_id_from_request:
        return make_response(jsonify({'error': 'FyleError'}), 400)  

         
    grade_assignment_payload = AssignmentGradeSchema().load(incoming_payload)

    graded_assignment = Assignment.mark_grade(
        _id=grade_assignment_payload.id,
        teacher_id=p.teacher_id,
        grade=grade_assignment_payload.grade,
        auth_principal=p
    )
    db.session.commit()
    graded_assignment_dump = AssignmentSchema().dump(graded_assignment)
    return APIResponse.respond(data=graded_assignment_dump)

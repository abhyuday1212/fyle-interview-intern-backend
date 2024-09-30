from flask import Blueprint
from core import db
from core.apis import decorators
from core.apis.responses import APIResponse
from core.models.assignments import Assignment,GradeEnum, AssignmentStateEnum
from core.models.teachers import Teacher
from core.apis.responses import APIResponse
from flask import jsonify
from sqlalchemy.orm import Session
from sqlalchemy import create_engine

from .schema import AssignmentSchema, AssignmentGradeSchema
principal_assignments_resources = Blueprint('principal_assignments_resources', __name__) 

@principal_assignments_resources.route('/assignments', methods=['GET'], strict_slashes=False)
@decorators.authenticate_principal
def list_assignments(p):
    """Returns list of assignments""" 
    principal_id = getattr(p, 'principal_id', None) 

    if principal_id is None:
        return APIResponse.error(message="principal ID not found in the authenticated principal.", status_code=400)

    principals_assignments = Assignment.get_assignments_by_principal()
    principals_assignments_dump = AssignmentSchema().dump(principals_assignments, many=True)
        
    return APIResponse.respond(data=principals_assignments_dump) 


@principal_assignments_resources.route('/teachers/list', methods=['POST'], strict_slashes=False)
@decorators.accept_payload
@decorators.authenticate_principal
def list_teachers(p):
    """List all the teachers"""
    principal_id = getattr(p, 'principal_id', None) 

    if principal_id is None:
        return APIResponse.error(message="principal ID not found in the authenticated principal.", status_code=400)

    all_teachers = Teacher.get_all_teachers()
 
    response_data = [{"id": teacher.id, "created_at": str(teacher.created_at), "updated_at": str(teacher.updated_at), "user_id": teacher.user_id} for teacher in all_teachers]

    return APIResponse.respond(data=response_data)

@principal_assignments_resources.route('/assignments/grade', methods=['POST'], strict_slashes=False)
@decorators.accept_payload
@decorators.authenticate_principal
def regrade_assignment(p, incoming_payload):
    """Grade an assignment"""

    principal_id = getattr(p, 'principal_id', None)
    assignment_id = incoming_payload.get('id')
    assignment = Assignment.query.get(assignment_id)

    if assignment.state == AssignmentStateEnum.DRAFT.value: 
        return jsonify({"error": "Cannot grade an assignment in draft state."}), 400
    
    if principal_id is None:
        return jsonify({"error": "Principal ID not found in the authenticated principal."}), 400 
     
    if not assignment_id:
        return jsonify({"error": "Missing assignment ID in the request payload."}), 400 
    

    grade_assignment_payload = AssignmentGradeSchema().load(incoming_payload)

    if not grade_assignment_payload.id or not grade_assignment_payload.grade:
        return jsonify({"error": "Missing required fields in the request payload."}), 400
     
    
    if grade_assignment_payload.grade not in GradeEnum.__members__.values():
        return APIResponse.error(message=f"Invalid grade '{grade_assignment_payload.grade}'. Please use a valid grade value.", status_code=400)

    try: 
        graded_assignment = Assignment.mark_principal_grade(
            _id=grade_assignment_payload.id,
            grade=grade_assignment_payload.grade,
            auth_principal=p
        )
         
        graded_assignment_dump = AssignmentSchema().dump(graded_assignment)
        return APIResponse.respond(data=graded_assignment_dump)
    except Exception as e:  
        return APIResponse.error(message=str(e), status_code=500)
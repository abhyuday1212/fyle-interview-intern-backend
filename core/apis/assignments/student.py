from flask import Blueprint
from core import db
from core.apis import decorators
from core.apis.responses import APIResponse
from core.models.assignments import Assignment
from flask import request,json, jsonify, make_response
from core.libs.exceptions import FyleError

from .schema import AssignmentSchema, AssignmentSubmitSchema
student_assignments_resources = Blueprint('student_assignments_resources', __name__)


@student_assignments_resources.route('/assignments', methods=['GET'], strict_slashes=False)
@decorators.authenticate_principal
def list_assignments(p):
    """Returns list of assignments"""
    students_assignments = Assignment.get_assignments_by_student(p.student_id)
    students_assignments_dump = AssignmentSchema().dump(students_assignments, many=True)
    return APIResponse.respond(data=students_assignments_dump)


@student_assignments_resources.route('/assignments', methods=['POST'], strict_slashes=False)
@decorators.accept_payload
@decorators.authenticate_principal
def upsert_assignment(p, incoming_payload):
    """Create or Edit an assignment"""

    x_principal_header = request.headers.get('X-Principal')

    if not x_principal_header:
        return APIResponse.respond({"error": "Missing X-Principal header"}, status_code=400)
    
    try:
        x_principal = json.loads(x_principal_header)
    except json.JSONDecodeError:
        return APIResponse.respond({"error": "Invalid X-Principal header format"}, status_code=400)

    incoming_payload = request.get_json()

    if incoming_payload.get("content") is None:
        return APIResponse.respond({"error": "Content cannot be null"}, status_code=400)

    assignment_instance = AssignmentSchema().load(incoming_payload)
    
    assignment_data = {
        "id": getattr(assignment_instance, "id", None),
        "content": getattr(assignment_instance, "content", None),
    }
    assignment_data["student_id"] = p.student_id

 
    assignment_instance = Assignment(**assignment_data)
 
    if assignment_instance.id is not None:
        upserted_assignment = Assignment.upsert(assignment_instance)
    else:
        created_assignment = Assignment.create(**assignment_data)
        upserted_assignment = created_assignment

    db.session.commit()
    upserted_assignment_dump = AssignmentSchema().dump(upserted_assignment)
    return APIResponse.respond(data=upserted_assignment_dump)


@student_assignments_resources.route('/assignments/submit', methods=['POST'], strict_slashes=False)
@decorators.accept_payload
@decorators.authenticate_principal
def submit_assignment(p, incoming_payload): 
    """Submit an assignment"""

    try:
        submit_assignment_payload = AssignmentSubmitSchema().load(incoming_payload)

        assignment = Assignment.get_by_id(submit_assignment_payload.id)
 
         # Check if the assignment is graded
        if assignment.state != "GRADED":
            response = jsonify({
               "error": "FyleError",
              "message": "only a graded assignment can be submitted"
            })
            return make_response(response, 400)
        

    except Exception as e:
        return jsonify({"error": "An internal server error occurred"}), 500

    submitted_assignment = Assignment.submit(
        _id=submit_assignment_payload.id,
        teacher_id=submit_assignment_payload.teacher_id,
        auth_principal=p
    ) 

    db.session.commit() 

    submitted_assignment_dump = AssignmentSchema().dump(submitted_assignment)
   
    return APIResponse.respond(data=submitted_assignment_dump)

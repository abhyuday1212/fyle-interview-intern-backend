from flask import Flask
from flask import jsonify
from marshmallow.exceptions import ValidationError
from core import app
from core.apis.assignments import student_assignments_resources, teacher_assignments_resources,principal_assignments_resources
from core.libs import helpers
from core.libs.exceptions import FyleError
from werkzeug.exceptions import HTTPException

from sqlalchemy.exc import IntegrityError

app.register_blueprint(student_assignments_resources, url_prefix='/student')
app.register_blueprint(teacher_assignments_resources, url_prefix='/teacher')
app.register_blueprint(principal_assignments_resources, url_prefix='/principal')


@app.route('/')
def ready():
    response = jsonify({
        'status': 'ready',
        'time': helpers.get_utc_now()
    })

    return response


@app.errorhandler(Exception)
def handle_error(err):
    error_handlers = {
        FyleError: lambda e: (jsonify(error='FyleError', message=e.message), e.status_code),
        ValidationError: lambda e: (jsonify(error='ValidationError', message=e.messages), 400),
        IntegrityError: lambda e: (jsonify(error='IntegrityError', message=str(e.orig)), 400),
        HTTPException: lambda e: (jsonify(error='HTTPException', message=str(e)), e.code),
    }
    
    handler = error_handlers.get(type(err), lambda e: (jsonify(error='InternalServerError', message='An unexpected error occurred'), 500))
    return handler(err)
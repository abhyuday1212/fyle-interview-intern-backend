from flask import Response, jsonify, make_response

class APIResponse(Response):
    @classmethod
    def respond(cls, data, status_code=None):
        """Generates a response with optional status code."""
        response = make_response(jsonify(data=data))
        if status_code is not None:
            response.status_code = status_code
        return response
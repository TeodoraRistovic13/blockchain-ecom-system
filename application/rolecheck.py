from functools import wraps
from flask_jwt_extended import verify_jwt_in_request, get_jwt
from flask import jsonify, Response

def role_check(role):
    def innerRole(function):
        @wraps(function)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if ("roles" in claims) and (role in claims["roles"]):
                return function(*args, **kwargs)
            else:
                return jsonify (msg = "Missing Authorization Header"), 401
        return decorator
    return innerRole
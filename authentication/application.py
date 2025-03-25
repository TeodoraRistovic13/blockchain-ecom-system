from flask import Flask, request, Response, jsonify
from configuration import Configuration
from models import database, User, Role, UserRole
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt
from sqlalchemy import and_
import jwt
import re

application = Flask (__name__)
application.config.from_object(Configuration)

jwtManager = JWTManager(application)

@application.route("/register_customer", methods=["POST"])
def register_customer():

    email = request.json.get("email", "")
    password = request.json.get("password", "")
    forename = request.json.get("forename", "")
    surname = request.json.get("surname", "")

    email_empty = len(email) == 0
    password_empty = len (password) == 0
    forename_empty = len(forename) == 0
    surname_empty = len(surname) == 0

    if email_empty or password_empty or forename_empty or surname_empty:
        field = ""
        if forename_empty:
            field = "forename"
        elif surname_empty:
            field = "surname"
        elif email_empty:
            field = "email"
        elif password_empty:
            field = "password"

        return jsonify(message=f"Field {field} is missing."), 400

    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    if not re.match(pattern, email):
        return jsonify(message = "Invalid email."), 400

    if len(password) < 8:
        return jsonify(message="Invalid password."), 400

    user = User.query.filter(User.email == email).first()

    if user:
        return jsonify(message="Email already exists."), 400

    user = User(email = email, password = password, forename= forename, surname= surname)
    database.session.add(user)
    database.session.commit()

    userRole = UserRole (userId = user.id, roleId = 2)
    database.session.add( userRole)
    database.session.commit()

    return Response(status = 200)

@application.route("/register_courier", methods=["POST"])
def register_courier():

    email = request.json.get("email", "")
    password = request.json.get("password", "")
    forename = request.json.get("forename", "")
    surname = request.json.get("surname", "")

    email_empty = len(email) == 0
    password_empty = len (password) == 0
    forename_empty = len(forename) == 0
    surname_empty = len(surname) == 0

    if email_empty or password_empty or forename_empty or surname_empty:
        field=""
        if forename_empty:
            field = "forename"
        elif surname_empty:
            field= "surname"
        elif email_empty:
            field="email"
        elif password_empty:
            field="password"

        return jsonify(message=f"Field {field} is missing."), 400

    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    # Use the re.match function to search for a match at the beginning of the string
    if not re.match(pattern, email):
        return jsonify(message="Invalid email."), 400

    if len(password) < 8:
        return jsonify(message="Invalid password."), 400


    #treba da se proveri da li vec postoji email sa tom adresom
    user = User.query.filter(User.email == email).first()

    if user:
        return jsonify(message="Email already exists."), 400

    user = User(email = email, password = password, forename= forename, surname= surname)
    database.session.add(user)
    database.session.commit()

    #treba da bude id uloge kurir
    userRole = UserRole (userId = user.id, roleId = 3)
    database.session.add(userRole)
    database.session.commit()

    return Response(status = 200)

@application.route("/login", methods=["POST"])
def login():

    email = request.json.get("email", "")
    password = request.json.get("password", "")

    email_empty = len (email) == 0
    password_empty = len(password) == 0

    if email_empty or password_empty:
        field = ""
        if email_empty:
            field = "email"
        elif password_empty:
            field = "password"

        return jsonify(message = f"Field {field} is missing."), 400

    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    if not re.match(pattern, email):
        return jsonify(message="Invalid email."), 400

    user = User.query.filter( and_(User.email == email, User.password == password)).first()

    if not user:
        return jsonify(message = "Invalid credentials."), 400

    additional_claims = {
        "forename" : user.forename,
        "surname" : user.surname,
        "roles" : [str (role) for role in user.roles]
    }

    access_token = create_access_token(identity=user.email, additional_claims= additional_claims)

    return jsonify(accessToken=access_token), 200

@application.route("/check", methods=["POST"])
@jwt_required()
def check():
    return "Token is valid!"

@application.route("/delete", methods=["POST"])
@jwt_required()
def deleteUser():

    authorization_header = request.headers.get('Authorization')
    jwt_token = authorization_header.split(' ')[1]
    decoded_token = jwt.decode(jwt_token, Configuration.JWT_SECRET_KEY, algorithms=['HS256'])
    email = decoded_token['sub']

    user = User.query.filter(and_(User.email == email)).first()

    if not user:
        return jsonify(message="Unknown user."), 400

    database.session.delete(user)
    database.session.commit()

    return Response(status = 200)

@application.route("/", methods=["GET"])
def index():
    return "Hello world!"


if __name__ == "__main__":
    database.init_app(application)
    application.run( debug=True, host ="0.0.0.0", port= 5002)

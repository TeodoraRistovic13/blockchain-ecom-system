import os
from datetime import timedelta

databaseUrl = os.environ["DATABASE_URL"]

class Configuration ():
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://root:root@{databaseUrl}/authentication"
    JWT_SECRET_KEY = "JWT_SECRET_KEY"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta (seconds= 3600)
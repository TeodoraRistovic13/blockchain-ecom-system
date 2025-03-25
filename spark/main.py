from flask import Flask, Response, jsonify
from flask import request
import json

application = Flask (__name__)

import os
import subprocess

@application.route ( "/cat_stat" )
def category_statistics():
    os.environ["SPARK_APPLICATION_PYTHON_LOCATION"] = "/app/category_stat.py"
    os.environ["SPARK_SUBMIT_ARGS"] = "--driver-class-path /app/mysql-connector-j-8.0.33.jar --jars /app/mysql-connector-j-8.0.33.jar"
    try:
        result = subprocess.check_output(["/template.sh"])
        return Response(result.decode(), status=200)

    except subprocess.CalledProcessError as e:
        return Response(f"Error: {e.output.decode()}", status=500, content_type='text/plain')


@application.route ( "/prod_stat" )
def product_statistics():
    os.environ["SPARK_APPLICATION_PYTHON_LOCATION"] = "/app/product_stat.py"
    os.environ["SPARK_SUBMIT_ARGS"] = "--driver-class-path /app/mysql-connector-j-8.0.33.jar --jars /app/mysql-connector-j-8.0.33.jar"
    try:
        result = subprocess.check_output(["/template.sh"])
        return Response(result.decode ( ), status = 200)

    except subprocess.CalledProcessError as e:
        return Response(f"Error: {e.output.decode()}", status=500, content_type='text/plain')


if __name__ == "__main__":
    application.run ( host = "0.0.0.0" , port=5000)
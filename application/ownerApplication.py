import io
import csv

from flask import Flask, request, Response, jsonify
from configuration import Configuration
from models import database, Product, Category, ProductCategory, ProductOrder, Order
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt
from sqlalchemy import and_, or_
import requests

import jwt
from rolecheck import role_check

application = Flask (__name__)
application.config.from_object( Configuration )

jwtManager = JWTManager(application)

@application.route("/update", methods=["POST"])
@role_check(role="vlasnik")
def update():

    if 'file' not in request.files:
        return jsonify(message = "Field file is missing."), 400

    content = request.files["file"].stream.read().decode("utf-8")
    stream = io.StringIO(content)
    reader = csv.reader(stream)

    i = 0
    products = []
    category_names = []
    category_objects = []
    product_category = {}

    for row in reader:

        if len(row) != 3:
            return jsonify(message = f"Incorrect number of values on line {i}."), 400

        categories = row[0].split("|")
        name = row[1]

        try:
            price = float(row[2])
        except ValueError:
            return jsonify(message = f"Incorrect price on line {i}."), 400

        if price <= 0:
            return jsonify(message = f"Incorrect price on line {i}."), 400

        # Check if there are product duplicates in JSON file
        found = False
        for p in products:
            if p.name == name:
                found = True
                break

        if found:
            return jsonify(message=f"Product {name} already exists."), 400

        # Check if product already in the DB
        p = Product.query.filter(Product.name == name).first()
        if p:
            return jsonify(message=f"Product {name} already exists."), 400

        product = Product(name = name, price = price)
        products.append(product)
        product_category[name] = categories

        for category_name in categories:
            if category_name not in category_names:
                if not (Category.query.filter(Category.name == category_name).first()):
                    category = Category(name = category_name)
                    category_names.append(category_name)
                    category_objects.append(category)

        i = i + 1

    database.session.add_all(products)
    database.session.commit()

    database.session.add_all(category_objects)
    database.session.commit()

    for name, category_names in product_category.items():
        product = Product.query.filter(Product.name == name).first()

        for category_name in category_names:
            category = Category.query.filter(Category.name == category_name).first()
            if not (ProductCategory.query.filter(and_(
                        ProductCategory.productId == product.id,
                        ProductCategory.categoryId == category.id
                    )).first()):

                product_category_obj = ProductCategory(productId = product.id, categoryId = category.id)
                database.session.add(product_category_obj)
                database.session.commit()

    return Response(status = 200)

@application.route("/read_from_file", methods=["GET"])
@role_check(role="vlasnik")
def product_statistics():

    statistics =[]
    products = Product.query.all()
    for product in products:
        orders = Order.query.join(ProductOrder).filter(
            ProductOrder.productId == product.id
        ).all()

        sold = 0
        waiting = 0

        for order in  orders:

            data = ProductOrder.query.filter(
                and_(
                    ProductOrder.orderId == order.id,
                    ProductOrder.productId == product.id
                )
            ).first()

            if order.status == "COMPLETE":
                sold += data.quantity
            elif order.status in ["PENDING", "CREATED"]:
                waiting += data.quantity

        if sold >= 1 or waiting >= 1:
            obj = {
                "name": product.name,
                "sold": sold,
                "waiting": waiting
            }
            statistics.append(obj)

    return jsonify(statistics=statistics), 200


@application.route("/cat_stat_try", methods=["GET"])
@role_check(role="vlasnik")
def category_statistics():

    cat_dict = {}
    categories = Category.query.all()

    for cat in categories:

        products = Product.query.join(ProductCategory).filter(
            ProductCategory.categoryId == cat.id
        ).all()

        info = ProductOrder.query.join(Order).filter(
            and_(
                ProductOrder.productId.in_([p.id for p in products]),
                Order.status == "COMPLETE"
            )).all()

        number = 0

        for data in info:
            number += data.quantity

        cat_dict[cat.name] = number

    statistics = dict(sorted(cat_dict.items(), key = lambda x: (-x[1], x[0])))
    result = list(statistics)

    return jsonify(statistics=result), 200


@application.route("/product_statistics", methods=["GET"])
@role_check(role="vlasnik")
def read_data():

    products = []
    target_container_hostname = 'sparkapp'
    target_service_url = f'http://{target_container_hostname}:5000/prod_stat'
    response = requests.get(target_service_url)

    if response.status_code == 200:
        with open('/data/product_statistics.txt', 'r') as file:
            lines = file.readlines()
            for line in lines:
                data = line.strip().split("|")
                obj = {
                    "name": data[0],
                    "sold": int(data[1]),
                    "waiting": int(data[2])
                }
                products.append(obj)
        return jsonify(statistics=products), 200
    else:
        return jsonify(msg="ERROR"), 400


@application.route("/category_statistics", methods=["GET"])
@role_check(role="vlasnik")
def function():
    
    categories = []
    target_container_hostname = 'sparkapp'
    target_service_url = f'http://{target_container_hostname}:5000/cat_stat'
    response = requests.get(target_service_url)

    if response.status_code == 200:
        with open('/data/category_statistics.txt', 'r') as file:
            lines = file.readlines()
            for line in lines:
                data = line.strip()
                categories.append(data)
        return jsonify(statistics=categories), 200
    else:
        return jsonify(msg="ERROR"), 400


if __name__ == "__main__":
    database.init_app(application)
    application.run( debug=True, host ="0.0.0.0", port= 5003)



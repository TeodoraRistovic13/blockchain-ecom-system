from flask import Flask, request, Response, jsonify
from configuration import Configuration
from models import database, Product, Category, ProductCategory, ProductOrder, Order
from flask_jwt_extended import JWTManager
from sqlalchemy import and_
import jwt
from rolecheck import role_check
from datetime import datetime
import web3
from web3.exceptions import ContractLogicError
from web3 import Web3
from web3 import HTTPProvider
from web3 import Account
import secrets
import json
import re

application = Flask(__name__)
application.config.from_object(Configuration)

jwtManager = JWTManager(application)

web3 = Web3(HTTPProvider("http://ganacheContainer:8545"))

def read_file (path):
    with open (path, "r") as file:
        return file.read()

def is_valid_ethereum_address(address):
    pattern = r'^0x[0-9a-fA-F]{40}$'
    return bool(re.match(pattern, address))

@application.route("/search", methods=["GET"])
@role_check(role="kupac")
def search():

    products_res = []
    category_set = set()

    items = request.args.items()
    params={}

    search_result = []

    for item in items:
        params[item[0]]=item[1]

    if len(params) == 2:

        name = params['name']
        category = params['category']

        search_result = ProductCategory.query.join(Product).join(Category).filter(
            and_(
                Product.name.like(f"%{name}%"),
                Category.name.like(f"%{category}%")
            )

        ).all()

    elif len(params) == 1:
        if 'name' in params:
            name = params['name']
            search_result = ProductCategory.query.join(Product).join(Category).filter(
                Product.name.like(f"%{name}%"),
            ).all()
        elif 'category' in params:
            category = params['category']
            print(category)
            search_result = ProductCategory.query.join(Product).join(Category).filter(
                Category.name.like(f"%{category}%")
            ).all()
    else:
        search_result = ProductCategory.query.join(Product).join(Category).all()

    product_names = []

    for product_category_pair in search_result:
        categories = Category.query.join(ProductCategory).filter(
            ProductCategory.productId == product_category_pair.productId
        ).all()

        product = Product.query.filter(Product.id == product_category_pair.productId).first()
        category = Category.query.filter(Category.id == product_category_pair.categoryId).first()
        category_set.add(category.name)

        if product.name in product_names:
            continue
        else:
            product_names.append(product.name)
            product_data = {
                "categories": [category.name for category in categories],
                "id": product.id,
                "name": product.name,
                "price": float(product.price)
            }
            products_res.append(product_data)

    categories_res = list(category_set)

    return jsonify(categories=categories_res, products=products_res), 200

@application.route("/order", methods=["POST"])
@role_check(role="kupac")
def order():

    request_data = request.get_json()

    if 'requests' not in request_data:
        return jsonify(message = "Field requests is missing."), 400

    requests = request.json.get("requests", "")

    authorization_header = request.headers.get('Authorization')
    jwt_token = authorization_header.split(' ')[1]
    decoded_token = jwt.decode(jwt_token, Configuration.JWT_SECRET_KEY, algorithms=['HS256'])
    email = decoded_token['sub']

    totalPrice = 0
    i = 0
    product_dict={}

    for req in requests:

        if "id" not in req:
            return jsonify(message=f"Product id is missing for request number {i}."), 400

        if "quantity" not in req:
            return jsonify(message=f"Product quantity is missing for request number {i}."), 400

        product_id = req["id"]
        quantity = req["quantity"]

        if (not isinstance(product_id, int)) or product_id <=0:
            return jsonify(message=f"Invalid product id for request number {i}."), 400

        if (not isinstance(quantity, int)) or quantity <=0:
            return jsonify(message=f"Invalid product quantity for request number {i}."), 400

        product = Product.query.filter(Product.id == product_id).first()

        if not product:
            return jsonify(message=f"Invalid product for request number {i}."), 400

        totalPrice += quantity * product.price

        if product.id in product_dict:
            product_dict[product.id] += quantity
        else :
            product_dict[product.id] = quantity

        i += 1


    if 'address' not in request_data:
        return jsonify(message = "Field address is missing."), 400

    buyer = request.json.get("address", "")

    if len(buyer)== 0:
        return jsonify(message="Field address is missing."), 400

    if not is_valid_ethereum_address(buyer):
        return jsonify(message="Invalid address."), 400

    bytecode = read_file("./OrderContract.bin")
    abi = read_file("./OrderContract.abi")
    owner = web3.eth.accounts[0]

    contract = web3.eth.contract(abi=abi, bytecode=bytecode)
    price = int(totalPrice)
    transaction_hash = contract.constructor(buyer, price).transact({
        "from": owner
    })

    receipt = web3.eth.wait_for_transaction_receipt(transaction_hash)
    contractAddress = receipt.contractAddress
    timestamp = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')

    new_order = Order(
        totalPrice = totalPrice,
        status = "CREATED",
        timestamp = timestamp,
        user = email,
        address = contractAddress
    )

    database.session.add(new_order)
    database.session.commit()

    for proId, quantity in product_dict.items():
        productOrder = ProductOrder(productId= proId, orderId= new_order.id, quantity= quantity)
        database.session.add(productOrder)

    database.session.commit()
    return jsonify(id=new_order.id), 200

@application.route("/status", methods=["GET"])
@role_check(role="kupac")
def status():

    authorization_header = request.headers.get('Authorization')
    jwt_token = authorization_header.split(' ')[1]
    decoded_token = jwt.decode(jwt_token, Configuration.JWT_SECRET_KEY, algorithms=['HS256'])
    email = decoded_token['sub']
    orders = Order.query.filter(Order.user == email).all()

    result = []

    for order in orders:

        order_products = ProductOrder.query.filter(
            ProductOrder.orderId == order.id
        ).all()

        products_data = []
        for data in order_products:

            product = Product.query.filter(
                Product.id == data.productId
            ).first()

            categories = Category.query.join(ProductCategory).filter(
                ProductCategory.productId == data.productId
            ).all()

            product_data = {
                "categories":[str(category.name) for category in categories],
                "name": product.name,
                "price":float(product.price),
                "quantity": data.quantity
            }

            products_data.append(product_data)

        totalPrice = float(order.totalPrice)

        data_order = {
            "products": products_data,
            "price": totalPrice,
            "status": order.status,
            "timestamp":order.timestamp
        }

        result.append(data_order)

    return jsonify(orders=result), 200

@application.route("/delivered", methods=["POST"])
@role_check(role="kupac")
def delivered():

    request_data = request.get_json()

    # Check if a specific field is in the request data
    if 'id' not in request_data:
        return jsonify(message="Missing order id."), 400

    id = request.json.get("id")

    if (not isinstance(id, int)) or id <= 0:
        return jsonify(message="Invalid order id."), 400

    order = Order.query.filter(
        and_(
            Order.id == id,
            Order.status == "PENDING"
        )
    ).first()

    order_none = order == None

    if id <= 0 or order_none:
        return jsonify(message="Invalid order id."), 400

    if 'keys' not in request_data:
        return jsonify(message="Missing keys."), 400

    data = request.json.get("keys")
    if len(data) == 0:
        return jsonify(message="Missing keys."), 400

    if 'passphrase' not in request_data:
        return jsonify(message="Missing passphrase."), 400
    elif len(request.json.get('passphrase')) == 0:
        return jsonify(message="Missing passphrase."), 400

    passphrase = request.json.get("passphrase")

    try:
        data_updated = data.replace("'", "\"")
        keys = json.loads(data_updated)
        private_key = Account.decrypt(keys, passphrase).hex()
    except (json.decoder.JSONDecodeError, ValueError) as e:
        return jsonify(message="Invalid credentials."), 400

    buyer = web3.to_checksum_address(keys["address"])
    abi = read_file("./OrderContract.abi")
    contract_address = order.address
    contract = web3.eth.contract(address=contract_address, abi=abi)
    try:
        contract.functions.confirmDelivery().transact({
            "from": buyer
        })
    except ContractLogicError as error:
        error_msg = str(error)
        if "Only the buyer can call this function" in error_msg:
            return jsonify(message= "Invalid customer account."), 400
        elif "CREATED" in error_msg:
            return jsonify(message="Transfer not complete."), 400
        elif "PAID" in error_msg:
            return jsonify(message="Delivery not complete."), 400
        else:
            return jsonify(message=f"Some other error: {error_msg}"), 400

    order.status = "COMPLETE"
    database.session.commit()
    return Response(status= 200)

@application.route("/pay", methods=["POST"])
@role_check(role="kupac")
def pay():

    request_data = request.get_json()

    if 'id' not in request_data:
        return jsonify(message="Missing order id."), 400

    id = request.json.get("id")
    if (not isinstance(id, int)) or id <= 0:
        return jsonify(message="Invalid order id."), 400

    order = Order.query.filter(Order.id == id).first()

    order_none = order == None

    if order_none:
        return jsonify(message="Invalid order id."), 400

    if 'keys' not in request_data:
        return jsonify(message="Missing keys."), 400

    data = request.json.get("keys")
    if len(data) == 0:
        return jsonify(message="Missing keys."), 400

    if 'passphrase' not in request_data:
        return jsonify(message="Missing passphrase."), 400
    elif len(request.json.get('passphrase')) == 0:
        return jsonify(message="Missing passphrase."), 400

    passphrase = request.json.get("passphrase")

    try:
        data_updated = data.replace("'", "\"")
        keys = json.loads(data_updated)
        private_key = Account.decrypt(keys, passphrase).hex()
    except (json.decoder.JSONDecodeError, ValueError) as e:
        return jsonify(message="Invalid credentials."), 400

    buyer = web3.to_checksum_address(keys["address"])

    abi = read_file("./OrderContract.abi")

    contract_address = order.address

    contract = web3.eth.contract(address=contract_address, abi=abi)
    buyer_balance =  web3.eth.get_balance (buyer)

    if buyer_balance < int(order.totalPrice):
        return jsonify(message="Insufficient funds."), 400
    try:
        contract.functions.makePayment().transact({
            "from": buyer,
            "value": int(order.totalPrice)
        })

    except ContractLogicError as error:
        error_msg = str(error)
        if "Only the buyer can call this function" in error_msg:
            return jsonify(message="Invalid customer account."), 400
        elif "PAID" in error_msg :
            return jsonify(message="Transfer already complete."), 400
        else:
            return jsonify(message="Some other error..."), 400

    return Response(status=200)


if __name__ == "__main__":
    database.init_app(application)
    application.run(debug=True, host="0.0.0.0", port=5004)



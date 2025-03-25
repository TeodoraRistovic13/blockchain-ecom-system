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
import re

web3 = Web3(HTTPProvider("http://ganacheContainer:8545"))

application = Flask(__name__)
application.config.from_object(Configuration)

jwtManager = JWTManager(application)

def read_file (path):
    with open (path, "r") as file:
        return file.read ( )


def is_valid_ethereum_address(address):
    pattern = r'^0x[0-9a-fA-F]{40}$'
    return bool(re.match(pattern, address))


@application.route("/pick_up_order", methods=["POST"])
@role_check(role="kurir")
def pick_up_order():

    request_data = request.get_json()

    if 'id' not in request_data:
        return jsonify(message="Missing order id."), 400

    id = request.json.get("id")

    if (not isinstance(id, int)) or id <= 0:
        return jsonify(message="Invalid order id."), 400

    order = Order.query.filter(
    and_(
        Order.id == id,
        Order.status == "CREATED"
    )
    ).first()

    order_none = order == None

    if order_none:
        return jsonify(message="Invalid order id."), 400

    if 'address' not in request_data:
        return jsonify(message = "Missing address."), 400

    courier = request.json.get("address", "")
    if len (courier) == 0:
        return jsonify(message="Missing address."), 400

    if not is_valid_ethereum_address(courier):
        return jsonify(message="Invalid address."), 400

    abi = read_file("./OrderContract.abi")

    contract_address = order.address

    # kreiramo intancu ugovora
    contract = web3.eth.contract(address=contract_address, abi=abi)
    owner = web3.eth.accounts[0]

    try:
        contract.functions.acceptOrder(courier).transact({
            "from": owner
        })
        order.status = "PENDING"
        database.session.commit()
        return Response(status=200)

    except ContractLogicError as error:
        errorMsg = str(error)
        if "Order already assigned to a courier" in errorMsg:
            return jsonify(message="Order already assigned to a courier"), 400
        elif "CREATED" in errorMsg :
            return jsonify(message="Transfer not complete."), 400
        else:
            return jsonify(message="Some other error"), 400


@application.route("/orders_to_deliver", methods=["GET"])
@role_check(role="kurir")
def orders_to_deliver():

    result = []
    orders = Order.query.filter(Order.status == "CREATED")

    for order in orders:
        data = {
            "id":order.id,
            "email":order.user
        }
        result.append(data)

    return jsonify(orders=result), 200


if __name__ == "__main__":
    database.init_app(application)
    application.run(debug=True, host="0.0.0.0", port=5005)



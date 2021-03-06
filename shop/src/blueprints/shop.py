from flask import Flask, Blueprint, render_template, make_response, redirect, request
import json
import logging
import os
import sys

# Routes for the shop tab

import src.support.outbound_routing as ob
import src.support.settings as config
import src.transaction_logic as trans

shop = Blueprint('shop', __name__)

@shop.route("/home/shop", methods=["GET"])
def render_shop_actions():
    stage = config.agent_data.get_stage()

    if config.role == "user":
        details = config.agent_data.get_transaction_values()
    else:
        details = {"none": "none"}

    if config.agent_data.has_public:
        did = get_public_did()
        return render_template('shop.html', name=config.role.capitalize(), stage=stage, did=did, **details)
    else:
        return render_template('shop.html', name=config.role.capitalize(), stage=stage, **details)

# for when the shipping service received a package
@shop.route("/home/shop/package/input", methods=["POST"])
def input_package_no():
    logging.debug("input detected")

    if config.role != "shipper":
        return make_response({"code": "not allowed for this agent"}, 404)

    package_data = request.data.decode("utf-8")

    if len(package_data) > 8:
        number = package_data.split("=")[1].strip()
        config.agent_data.update_package_no(number)
        return make_response({"code": "package number received"}, 200)
    else:
        return make_response({"code":"no number submitted"}, 200)

@shop.route("/home/shop/transaction", methods=["GET"])
def get_state():
    if config.role == "user":
        vals = config.agent_data.get_transaction_values()
        print(vals)
        return make_response(json.dumps(vals), 200)

    value_dict = config.get_transaction_values()
    print("value dict: ", value_dict)
    if not value_dict:
        return make_response({"code": "starting state"})
    else:
        return make_response(json.dumps(value_dict), 200)

@shop.route("/home/shop/transaction/reset", methods=["GET"])
def reset():
    config.reset()
    return make_response({"code": "success"}, 200)


@shop.route("/home/shop/request/item", methods=["POST"])
def request_item():

    if not ob.hasActiveConnection():
        return make_response({"code": "failure", "reason": "agent has no active connections"})

    data = request.data.decode("utf-8")
    print(data)
    print(type(data))

    product = data.split("=")[1].strip()

    if len(product) > 3:
        print("Purchase request for product : ", product)
        config.agent_data.update_product_id(product)
        trans.send_payment_agreement_proposal(product)

    return make_response({"code": "success"})


def get_public_did():
    resp = ob.get_public_did()
    res = resp["result"]
    if "did" in res:
        return res["did"]
    else:
        return None


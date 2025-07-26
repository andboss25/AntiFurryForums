from flask import request, jsonify
from functools import wraps
import utils.GeneralUtils as GeneralUtils
import utils.IpData as IpData

import requests
import json

configs = json.loads(open("config.json").read())

def logdata():
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if request.remote_addr == "127.0.0.1":
                ip = request.headers.get("X-Real-IP")
            else:
                ip = request.remote_addr
            
            if ip == None:
                ip = "localhost"

            # BUG mild vulnerability where request might appear as from other user beacuse get username from token gets "username' of token whithout checking validity'"

            username = None
            try:
                username = GeneralUtils.GetUsernameFromToken(request.args["token"])
            except:
                pass

            try:
                username = GeneralUtils.GetUsernameFromToken(request.json["token"])
            except:
                pass
            
            GeneralUtils.TrackIp(username,True,request.path,ip=ip)

            return func(*args, **kwargs)

        return wrapper
    return decorator

def guard_api(addr_list_getter):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            
            # Call the function to get the actual addr_list dict
            if callable(addr_list_getter):
                addr_list = addr_list_getter()
            else:
                # If someone passes dict directly (backwards compatibility)
                addr_list = addr_list_getter

            # Determine IP address
            if request.remote_addr == "127.0.0.1":
                ip = request.headers.get("X-Real-IP")
            else:
                ip = request.remote_addr

            if GeneralUtils.IsIpBlocked(ip):
                requests.post(configs["webhook_url"], json={"content": f"A banned ip tried accessing the website '{ip}'"})
                return jsonify({"Error": "This IP is blocked"}), 403

            if GeneralUtils.CooldownCheck(ip, addr_list):
                return jsonify({"Error": "Temporary cooldown triggered, resource requested too many times!"}), 429
            
            if not IpData.ValidateIp(ip):
                return jsonify({"Error": "Ip automatically blocked due to VPN or TOR!"}), 429
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

def require_json_with_fields(required_fields: list, nolist=True):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not request.is_json:
                return jsonify({"Error": "Request must be in JSON format"}), 400

            try:
                data = request.get_json(force=False, silent=False)
                if not isinstance(data, dict):
                    raise ValueError
            except Exception:
                return jsonify({"Error": "Malformed JSON"}), 400

            # Check for missing fields
            missing = [field for field in required_fields if field not in data or data[field] in [None, ""]]
            if missing:
                return jsonify({"Error": f"Missing one or more required fields: {', '.join(missing)}"}), 400

            # Type validation
            if nolist:
                invalid_type_fields = [
                    field for field in required_fields
                    if not isinstance(data[field], (str, int, float))
                ]
                if invalid_type_fields:
                    return jsonify({
                        "Error": f"Invalid type for fields: {', '.join(invalid_type_fields)}. "
                                 f"Only strings and numbers are allowed."
                    }), 400

            return func(*args, **kwargs)
        return wrapper
    return decorator

def require_query_params(required_fields: list):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            missing = [field for field in required_fields if not request.args.get(field)]
            if missing:
                return jsonify({
                    "Error": f"Missing one or more required query parameters: {', '.join(missing)}"
                }), 400

            return func(*args, **kwargs)
        return wrapper
    return decorator

def require_form_params(required_fields: list):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            missing = [field for field in required_fields if not request.form.get(field)]
            if missing:
                return jsonify({
                    "Error": f"Missing one or more required query parameters: {', '.join(missing)}"
                }), 400

            return func(*args, **kwargs)
        return wrapper
    return decorator
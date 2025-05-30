from flask import request, jsonify
from functools import wraps
import utils.GeneralUtils as GeneralUtils

def guard_api(addr_list:dict):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            ip = request.remote_addr

            if GeneralUtils.IsIpBlocked(ip):
                return jsonify({"Error": "This IP is blocked"}), 403

            if GeneralUtils.CooldownCheck(ip, addr_list):
                return jsonify({"Error": "Temporary cooldown triggered, resource requested too many times!"}), 429

            return func(*args, **kwargs)
        return wrapper
    return decorator

def require_json_with_fields(required_fields: list):
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

            missing = [field for field in required_fields if field not in data or not data[field]]
            if missing:
                # Optional: log the failure
                GeneralUtils.TrackIp(None, False, request.path, request.remote_addr)
                return jsonify({"Error": f"Missing one or more required fields: {', '.join(missing)}"}), 400

            return func(*args, **kwargs)
        return wrapper
    return decorator


def require_query_params(required_fields: list):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            missing = [field for field in required_fields if not request.args.get(field)]
            if missing:
                # Optional: IP tracking on error
                GeneralUtils.TrackIp(None, False, request.path, request.remote_addr)
                return jsonify({
                    "Error": f"Missing one or more required query parameters: {', '.join(missing)}"
                }), 400

            return func(*args, **kwargs)
        return wrapper
    return decorator
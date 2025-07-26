from flask import Blueprint, request, jsonify , current_app ,send_file

from werkzeug.utils import safe_join
import hashlib, time, requests
import random
import os

import json
import utils

image_bp = Blueprint('image', __name__)

configs = json.loads(open("config.json").read())

# Image API

@image_bp.route("add", methods=["POST"])
@utils.Wrappers.guard_api(lambda: current_app.config["ADDR_LIST"])
@utils.Wrappers.logdata()
def UploadImage():
    ALLOWED_MIMETYPES = {"image/png", "image/jpeg", "image/gif", "video/mp4"}

    cursor, conn = utils.GeneralUtils.InnitDB()

    if 'token' not in request.cookies:
        return jsonify({"Error": "No token found"}), 403
    token = request.cookies.get('token')

    username = utils.GeneralUtils.GetUsernameFromToken(token)

    if not username:
        return jsonify({"Error": "Invalid token"}), 401
    
    user = cursor.execute("SELECT id FROM users WHERE token=?", (token,)).fetchone()
    if not user:
        return jsonify({"Error": "Token is invalid"}), 401

    if 'file' not in request.files:
        return jsonify({"Error": "No image attached"}), 400

    image = request.files['file']
    
    if image.mimetype not in ALLOWED_MIMETYPES:
        return jsonify({"Error": "Invalid file"}), 400

    file_bytes = image.read()
    if len(file_bytes) > configs["MaxUploadSize"] * 1024 * 1024: 
        return jsonify({"Error": "File too large"}), 413
    
    image.seek(0)

    file_type_base = {"image/png":"png", "image/jpeg":"jpeg", "image/gif":"gif", "video/mp4":"mp4"}

    rint = random.randrange(1000,9999)

    filepath = os.path.join("Images", f"{username}-{rint}.{file_type_base[image.mimetype]}")
    image.save(filepath, 2048)

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"Message": "Successfully uploaded file","Url":f"/api/images/view/{username}-{rint}.{file_type_base[image.mimetype]}"}), 200

@image_bp.route("view/<image>", methods=["GET"])
@utils.Wrappers.guard_api(lambda: current_app.config["ADDR_LIST"])
@utils.Wrappers.logdata()
def ViewImage(image):

    cursor, conn = utils.GeneralUtils.InnitDB()
    
    if 'token' not in request.cookies:
        return jsonify({"Error": "No token found"}), 403
    token = request.cookies.get('token')

    username = utils.GeneralUtils.GetUsernameFromToken(token)
    if not username:
        return jsonify({"Error": "Invalid token"}), 401
    
    user = cursor.execute("SELECT id FROM users WHERE token=?", (token,)).fetchone()
    if not user:
        return jsonify({"Error": "Token is invalid"}), 401

    image_dir = os.path.abspath("Images")
    image_path = safe_join(image_dir, image)

    if not image_path or not os.path.isfile(image_path):
        return jsonify({"Error": "Image not found!"}), 404
    
    conn.commit()
    cursor.close()
    conn.close()

    try:
        return send_file(image_path)
    except Exception as e:
        return jsonify({"Error": "Failed to send image"}), 500
    

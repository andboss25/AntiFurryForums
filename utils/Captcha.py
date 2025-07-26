
import requests
from utils import GeneralUtils
import json

configs = json.loads(open("config.json").read())

def VerifyRecaptcha(re_token):
    if configs['re_captcha_enabled']:
        response = requests.post(
            "https://www.google.com/recaptcha/api/siteverify",
            data={
                "secret": configs['re_captcha_secret_key'],
                "response": re_token
            }
        )
        result = response.json()
        return result.get("success", False)
    else:
        return True
import dns.resolver
import json
import requests

configs = json.loads(open("config.json").read())

def HasMxRecord(email):
    try:
        domain = email.split('@')[-1]
        answers = dns.resolver.resolve(domain, 'MX')
        return len(answers) > 0
    except:
        return False
    
def IsBlockedDomain(email):
    domain = email.split('@')[-1].lower()
    return domain in configs["blocked_email_domains"]

def SendEmail(mailto,subject,html):
    API_KEY = configs['brevo_api_key']

    data = {
        "sender": {
            "name": "Anti-Furry Forums",
            "email": "contact@forums.af-comms.net"
        },
        "to": [
            {
                "email": mailto,
                "name": "Recipient Name"
            }
        ],
        "subject": subject,
        "htmlContent": html
    }

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "api-key": API_KEY
    }

    response = requests.post(
        "https://api.brevo.com/v3/smtp/email",
        json=data,
        headers=headers
    )

    return response

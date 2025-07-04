
import json
import requests

# VPN/Tor/Proxy IP detection cuz ppl tried spamming.
# The IP will not be queired every time a ip visits the site , only if its a unique ip then it stores it

ip_list = {}

configs = json.loads(open("config.json").read())

def ValidateIp(ip):
    if ip == None:
        ip = configs["testipaddr"]
    
    if not configs["CheckIpViaVPNApi"]:
        return True

    if ip not in ip_list:
        try:
            print(f"Making a request for ip [{ip}]")
            response = requests.get(f"https://vpnapi.io/api/{ip}?key={configs['VpnApiKey']}")
            response.raise_for_status()
            data = response.json()
            print(response.json())

            anon_data = data.get("security", {})
            is_vpn = anon_data.get("vpn", False)
            is_proxy = anon_data.get("proxy", False)
            is_tor = anon_data.get("tor", False)

            ip_list[ip] = {"vpn": is_vpn, "tor": is_tor , "proxy": is_proxy}

        except requests.RequestException as e:
            print(f"Request failed for ip [{ip}]: {e}")
            return False

    is_vpn = ip_list[ip]["vpn"]
    is_tor = ip_list[ip]["tor"]
    is_proxy = ip_list[ip]["proxy"]

    if is_tor:
        print(f"[!] IP [{ip}] flagged as Tor by API response.")
        return False
    if is_vpn and configs["BlockAllVPNIps"]:
        print(f"[!] IP [{ip}] flagged as VPN by API response.")
        return False
    if is_proxy and configs["BlockAllVPNIps"]:
        print(f"[!] IP [{ip}] flagged as Proxy by API response.")
        return False

    return True
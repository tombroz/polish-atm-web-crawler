import random
import re
import bs4
import urllib3
from stem import Signal
from stem.control import Controller
import requests
import socket

ip_list = []
check_ip_timeout = 3
retry = 300
code_check_ip_blocked = "Sprawdzanie IP - kod nie 2xx."
code_check_ip_retry = "Sprawdzanie IP - zbyt wiele prob."
my_servers = [
'http://www.whatsmydns.net/whats-my-ip-address.html',
'http://www.ip-adress.eu/',
'http://www.iplocation.net/',
'http://www.displaymyip.com/',
'http://myexternalip.com/raw',
'http://ipecho.net/plain',
'http://ip-lookup.net/',
'http://wtfismyip.com/',
'http://www.howtofindmyipaddress.com/',
'http://www.ip-adress.com/',
'http://www.my-ip-address.net/',
'http://ip-lookup.net/',
'http://www.ip-adress.eu/',
'http://www.privateinternetaccess.com/pages/whats-my-ip/',
'http://www.iplocation.net/',
'http://myexternalip.com/raw',
'http://icanhazip.com/',
'http://www.ip-adress.com/',
'http://www.privateinternetaccess.com/pages/whats-my-ip/',
'http://www.iplocation.net/',
'http://www.privateinternetaccess.com/pages/whats-my-ip/',
'http://www.my-ip-address.net/',
'http://ip.my-proxy.com/',
'http://checkmyip.com/',
'http://www.ip-adress.eu/',
'http://www.privateinternetaccess.com/pages/whats-my-ip/',
'http://icanhazip.com/',
'http://www.ip-adress.com/',
'http://ip-lookup.net/',
'http://wtfismyip.com/',
'http://www.privateinternetaccess.com/pages/whats-my-ip/',
'http://ip.my-proxy.com/',
'http://www.iplocation.net/',
'http://www.iplocation.net/',
'http://www.displaymyip.com/',
'http://wtfismyip.com/',
'http://www.ip-adress.eu/',
'http://icanhazip.com/',
'http://myexternalip.com/raw',
'http://www.iplocation.net/',
'http://www.iplocation.net/',
'http://www.displaymyip.com/',
'http://myexternalip.com/raw',
'http://www.ip-adress.eu/',
'http://www.geoiptool.com/',
'http://icanhazip.com/',
'http://www.whatsmydns.net/whats-my-ip-address.html',
'http://www.ip-adress.eu/',
'http://www.ip-adress.eu/',
'http://ip-lookup.net/',
'http://www.ip-adress.eu/',
'http://www.ip-adress.com/',
'http://www.ip-adress.eu/',
'http://www.whatsmydns.net/whats-my-ip-address.html',
'http://www.whatsmydns.net/whats-my-ip-address.html',
'http://www.ip-adress.eu/',
'http://www.howtofindmyipaddress.com/',
'http://www.howtofindmyipaddress.com/',
'http://www.howtofindmyipaddress.com/',
'http://www.my-ip-address.net/',
'http://wtfismyip.com/',
'http://www.whatsmydns.net/whats-my-ip-address.html',
'http://www.ip-adress.eu/',
'http://myexternalip.com/raw',
'http://icanhazip.com/',
'http://www.ip-adress.eu/',
'http://www.whatsmydns.net/whats-my-ip-address.html',
'http://icanhazip.com/',
'http://www.displaymyip.com/',
'http://icanhazip.com/',
'http://check.torproject.org/',
'http://www.ip-adress.eu/',
'http://myexternalip.com/raw',
'http://myexternalip.com/raw',
'http://myexternalip.com/raw',
'http://icanhazip.com/',
'http://www.iplocation.net/',
'http://www.ip-adress.com/',
'http://ipecho.net/plain',
'http://www.whatsmydns.net/whats-my-ip-address.html',
'http://check.torproject.org/',
'http://www.whatsmydns.net/whats-my-ip-address.html',
'http://www.ip-adress.com/',
'http://www.iplocation.net/',
'http://www.whatsmydns.net/whats-my-ip-address.html',
'http://icanhazip.com/',
'http://ip.my-proxy.com/',
'http://www.my-ip-address.net/',
'http://www.whatsmydns.net/whats-my-ip-address.html',
'http://check.torproject.org/',
'http://myexternalip.com/raw',
'http://wtfismyip.com/',
'http://www.iplocation.net/',
'http://www.displaymyip.com/',
'http://icanhazip.com/',
'http://check.torproject.org/',
'http://www.iplocation.net/',
'http://myexternalip.com/raw',
'http://www.iplocation.net/',
'http://www.geoiptool.com/'
]


def save_curr_ip():
    result_file = open("../../zle_serwery.txt", 'a', encoding='utf-8')
    result_file_good = open("../../dobre_serwery.txt", 'a', encoding='utf-8')
    for i in range(retry):
        result = None
        print("Sprawdzam IP... ", end='')
        try:
            choice = random.choice(my_servers)
            result = get_url(choice, check_ip_timeout)
        except (socket.timeout,requests.HTTPError ,requests.exceptions.ProxyError,
                urllib3.exceptions.MaxRetryError) as error:
            output = 'dane z {} nie otrzymano bo: {}'.format(choice, error)
            print(output)
            result_file.write(output + "\n")
            continue
        if result is None:
            print("przekroczono limit {}s oczekiwania na sprawdzenie IP. "
                  "Proba {}. {}".format(check_ip_timeout, i, choice))
        elif not (200 <= result.status_code <= 299):
            output = "{}. Proba {}. {}".format(code_check_ip_blocked, i, choice)
            result_file.write(output + "\n")
            print(output)
        else:
            result.encoding = 'utf-8'
            soup = bs4.BeautifulSoup(result.text, "html.parser")
            ip = soup.find(string=re.compile(
                "^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)"))
            if ip is not None:
                print(ip)
                result_file_good.write(choice +"\n")
                break
            else:
                output = "zwrocono tekst niebedacy prawidlowym IP. Proba {}. {}".format(i, choice)
                result_file.write(output + "\n")
                print(output)
    result_file.close()
    result_file_good.close()
    if result is None:
        return code_check_ip_retry
    ip_list.append(ip)


def set_new_ip():
    """Change IP using TOR"""
    with Controller.from_port(port=9051) as controller:
        controller.authenticate(password='1234')
        controller.signal(Signal.NEWNYM)
    res = save_curr_ip()
    return res


local_proxy = '127.0.0.1:8118'
http_proxy = {
    'http': local_proxy,
    'https': local_proxy
}


def get_url(my_url, timeo):
    try:
        current_ip = requests.get(
            url=my_url,
            proxies=http_proxy,
            verify=False,
            timeout=timeo
        )
    except requests.exceptions.Timeout:
        return None
    return current_ip


def change_ip(unique_ip_count):
    """
        change ip so a given IP address is reused only when "unique_ip_count" different IP addresses were used before.
    :param unique_ip_count: how many unique ips we want to make requests from
    :return:
    """
    if len(ip_list) == 0:
        res = save_curr_ip()
        if res in (code_check_ip_blocked, code_check_ip_retry):
            return res
    while 1:
        if len(ip_list) > unique_ip_count:
            del ip_list[0]
        print("Zmieniam IP:")
        res = set_new_ip()
        if res in (code_check_ip_blocked, code_check_ip_retry):
            return res
        if ip_list[-1] not in ip_list[:-1]:
            break

import random
import re
import time

import bs4
import urllib3
from stem import Signal
from stem.control import Controller
import requests
import win32serviceutil
import ipgetter
import socket

ip_list = []
check_ip_timeout = 5
retry = 100
code_check_ip_blocked = "Sprawdzanie IP - kod nie 2xx."
code_check_ip_retry = "Sprawdzanie IP - zbyt wiele prob."


def valid_ip(address):
    try:
        socket.inet_aton(address)
        return True
    except:
        return False


def save_curr_ip():
    result_file = open("../../zle_serwery.txt", 'a', encoding='utf-8')
    result_file_good = open("../../dobre_serwery.txt", 'a', encoding='utf-8')
    for i in range(retry):
        result = None
        print("Sprawdzam IP... ", end='')
        try:
            choice = random.choice(ipgetter.IPgetter().server_list)
            result = get_url(choice, check_ip_timeout)
        except (socket.timeout,requests.HTTPError, requests.exceptions.ProxyError,
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
            soup = bs4.BeautifulSoup(result.text, "html.parser")
            ip = soup.find(string=re.compile(
                "^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)"))
            if ip is not None:
                print(ip)
                result_file(choice +"\n")
                break
            else:
                output = "zwrocono tekst niebedacy prawidlowym IP. Proba {}. {}".format(i, choice)
                result_file.write(output + "\n")
                print(output)
    result_file.close()
    if result is None:
        return code_check_ip_retry
    ip_list.append(ip)


def set_new_ip():
    """Change IP using TOR"""
    with Controller.from_port(port=9051) as controller:
        controller.authenticate(password='brzoza11')
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


def reset_privoxy_tor():
    win32serviceutil.StopService('privoxy')
    time.sleep(1)
    win32serviceutil.StartService('privoxy')
    time.sleep(1)
    with Controller.from_port(port=9051) as controller:
        controller.reconnect()
    time.sleep(1)

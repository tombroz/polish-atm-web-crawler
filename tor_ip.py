from stem import Signal
from stem.control import Controller
import requests


ip_list = []
check_ip_timeout = 15
retry = 5
code_check_ip_blocked = "Sprawdzanie IP - kod nie 2xx."
code_check_ip_retry = "Sprawdzanie IP - zbyt wiele prób. Sprobuj pozniej lub wydłuż czas oczekiwania i powtorzeń"


def save_curr_ip():
    # ip_list.append(ipgetter.myip())
    result = None
    for i in range(retry):
        print("Sprawdzam IP = ",end='')
        result = get_url('http://icanhazip.com/', check_ip_timeout)
        try:
            print(result.text)
        except AttributeError:
            print("Sprawdzanie IP - null")
        if result is None:
            print("Przekroczono limit {}s oczekiwania na sprawdzenie IP. "
                  "Sprawdzam IP po raz {}".format(check_ip_timeout, i))
        elif 200 <= result.status_code <= 299:
            break
        elif not (200 <= result.status_code <= 299):
            return code_check_ip_blocked
    if result is None:
        return code_check_ip_retry
    ip_list.append(result.text[:-1])


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
    if len(ip_list)==0:
        res = save_curr_ip()
        if res in (code_check_ip_blocked, code_check_ip_retry):
            return res
    while 1:
        if len(ip_list) > unique_ip_count:
            del ip_list[0]
        print("Zmieniam IP:")
        res = set_new_ip()
        if res in (code_check_ip_blocked,code_check_ip_retry):
            return res
        if ip_list[-1] not in ip_list[:-1]:
            break

# set_new_ip()
# print(ip_list)
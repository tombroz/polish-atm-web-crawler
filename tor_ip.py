from stem import Signal
from stem.control import Controller
import requests

ip_list = []


def save_curr_ip():
   # ip_list.append(ipgetter.myip())
   ip_list.append(get_url('http://icanhazip.com/').text)


def set_new_ip():
    """Change IP using TOR"""
    with Controller.from_port(port=9051) as controller:
        controller.authenticate(password='brzoza11')
        controller.signal(Signal.NEWNYM)
    save_curr_ip()


local_proxy = '127.0.0.1:8118'
http_proxy = {
    'http': local_proxy,
    'https': local_proxy
}


def get_url(my_url):
    current_ip = requests.get(
        url=my_url,
        proxies=http_proxy,
        verify=False
    )
    return current_ip


def change_ip(unique_ip_count):
    """
        change ip so a given IP address is reused only when "unique_ip_count" different IP addresses were used before.
    :param unique_ip_count: how many unique ips we want to make requests from
    :return:
    """
    while 1:
        save_curr_ip()
        if len(ip_list) > unique_ip_count:
            del ip_list[0]
        set_new_ip()
        if len(set(ip_list)) == len(ip_list):
            break

import random
import re
import time
import bs4
import requests
import winsound

base_atm_url = "http://www.karty.pl/bankomaty.php?bankomat="
base_city_url = "http://www.karty.pl/bankomaty.php?miejscowosc="
base_region_url = "http://www.karty.pl/bankomaty.php?wojewodztwo="
region_urls = (base_region_url + "dolnoslaskie",
               base_region_url + "kujawsko-pomorskie",
               base_region_url + "lubelskie",
               base_region_url + "lubuskie",
               base_region_url + "lodzkie",
               base_region_url + "malopolskie",
               base_region_url + "mazowieckie",
               base_region_url + "opolskie",
               base_region_url + "podkarpackie",
               base_region_url + "podlaskie",
               base_region_url + "pomorskie",
               base_region_url + "slaskie",
               base_region_url + "swietokrzyskie",
               base_region_url + "warminsko-mazurskie",
               base_region_url + "wielkopolskie",
               base_region_url + "zachodniopomorskie")
driver_path = "C:/phantomjs-2.1.1-windows/bin/phantomjs"
notif_dur = 500  # millisecond
notif_freq_success = 600  # Hz
notif_freq_fail = int(float(220)/(9.0/8.0))  # Hz


def get_region_cities(region_url):
    region_cities = []
    # prepare html data from url
    response = requests.get(region_url)
    html = response.text
    soup = bs4.BeautifulSoup(html, "html.parser")
    if soup.find('title', string="503 Service Unavailable"):
        return None
    content = soup.find_all('ul')[-1] \
        .find_all(href=re.compile("miejscowosc"))
    for element in content:
        region_cities.append(element.get('href')[26:])
    return region_cities


def get_city_atms_numbers(city_url):
    city_atms_numbers = []
    # prepare html data from url
    response = requests.get(city_url)
    html = response.text
    soup = bs4.BeautifulSoup(html, "html.parser")
    if soup.find('title', string="503 Service Unavailable"):
        return None
    # get city atms numbers from url
    # content = soup.find_all(href=re.compile("bankomat="))
    # for element in content:
    #     city_atms_numbers.append(element.get('href')[10:])
    content = soup.find_all('dd')
    for element in content:
        city_atms_numbers.append(element.find('a').get('href')[10:])
    return city_atms_numbers


def get_atm_data(atm_url,region_id):
    atm_data = []
    # prepare html data from url
    response = requests.get(atm_url)
    response.encoding = 'utf-8'
    html = response.text
    soup = bs4.BeautifulSoup(html, "html.parser")
    if soup.find('title', string="503 Service Unavailable"):
        return None

    # get atm's data from url
    content = soup.find_all('dd')
    content_ids = soup.find_all('dt')
    ids_strings = []
    for el in content_ids:
        ids_strings.append(el.get_text())
    for i in range(8):
        try:
            if i == 0:
                atm_data.append(region_urls[region_id][46:])
                continue
            if i == 1:
                ind = [j for j, item in enumerate(ids_strings) if re.search('Miejsco', item)][0]
            elif i ==2:
                ind = [j for j, item in enumerate(ids_strings) if re.search('Lokaliz', item)][0]
            elif i ==3:
                ind = [j for j, item in enumerate(ids_strings) if re.search('Bankomat nale', item)][0]
            elif i ==4:
                ind = [j for j, item in enumerate(ids_strings) if re.search('Dost', item)][0]
            elif i ==5:
                ind = [j for j, item in enumerate(ids_strings) if re.search('Numer banko', item)][0]
            elif i ==6:
                ind = [j for j, item in enumerate(ids_strings) if re.search('Funkcja depo', item)][0]
            elif i ==7:
                ind = [j for j, item in enumerate(ids_strings) if re.search('Produ', item)][0]
        except IndexError:
            ind=-1
        if ind is not -1:
            atm_data.append(content[ind].get_text())
        else:
            atm_data.append("null")
    return atm_data


def get_all_atms_data_rec(start_point, end_point):
    """
    Downloads atms data from karty.pl from starting region, city, atm_nr
    until given region (end_point) is reached.
    Writes real start and end points ((region, city, atm_nr) ids) to file
    :param start_point: tuple containing (region, city, atm_nr) ids from which
    to start downloading data
    :param end_point: region id (from region_urls) to which downloading is continued
    :return: None
    """
    i, j, k = 0, 0, 0
    for i in range(len(region_urls)):
        if i < start_point[0]:
            continue
        elif i >= end_point:
            break
        print("Obtaining data for: region{} = {}".format(i, region_urls[i][46:]))
        region_cities = get_region_cities(region_urls[i])
        if region_cities is None:
            return result_file_output(i, j, k, True)
        time.sleep(float(random.randint(sleep_min, sleep_max)) * sleep_coeff)
        for j in range(len(region_cities)):
            if j < start_point[1] and i == st[0]:
                continue
            print("Obtaining data for: region{} = {}\t| city{} = {}"
                  .format(i, region_urls[i][46:], j, region_cities[j]))
            city_atms_numbers = get_city_atms_numbers(base_city_url + region_cities[j])
            if city_atms_numbers is None:
                return result_file_output(i, j, k, True)
            time.sleep(float(random.randint(sleep_min, sleep_max)) * sleep_coeff)
            for k in range(len(city_atms_numbers)):
                if k < start_point[2] and j == st[1]:
                    continue
                print("Obtaining data for: region{} = {}\t| city{} = {}\t| atm{} = {}"
                      .format(i, region_urls[i][46:], j, region_cities[j], k, city_atms_numbers[k]))
                atm_data = get_atm_data(base_atm_url + city_atms_numbers[k],i)
                if atm_data is None:
                    return result_file_output(i, j, k, True)
                with open("all_atms_data.txt", 'a', encoding='utf-8') as atms_data_file:
                    for x in range(len(atm_data)):
                        atms_data_file.write(atm_data[x])
                        if x != len(atm_data) - 1:
                            atms_data_file.write("|")
                    atms_data_file.write("\n")
                time.sleep(float(random.randint(sleep_min, sleep_max)) * sleep_coeff)
    return result_file_output(i, j, k, False)


def result_file_output(i, j, k, user_blocked):
    with open("result_end_point.txt", 'a', encoding='utf-8') as result_file:
        if user_blocked:
            output = 'Blocked. From/to: (region,city,atm_nr) = {},{},{} / {},{},{}\n'.format(st[0], st[1], st[2], i, j, k)
            sound_notif(0)
        else:
            output = 'Successful. From/to: (region,city,atm_nr) = {},{},{} / {},{},{}\n'.format(st[0], st[1], st[2], i, j, k)
            sound_notif(1)
        result_file.write(output)
        print(output)


def gen_sound(freq, dur, wait_after=0.0, count=1):
    for i in range(count):
        winsound.Beep(freq, dur)
        time.sleep(wait_after)


def sound_notif(succ):
    if succ:
        gen_sound(notif_freq_success, int(float(notif_dur) / 2.0), 0.1,3)
    else:
        notif_freq_fail_low = int(float(notif_freq_fail) / (4.0 / 3.0))
        notif_freq_fail_high = int(float(notif_freq_fail) * 6.0 / 5.0)
        short_dur = int(float(notif_dur) / 4.0)
        medium_dur = int(float(notif_dur) / (4.0/3.0))
        gen_sound(notif_freq_fail, notif_dur, 0.1, 3)
        gen_sound(notif_freq_fail_low, medium_dur)
        gen_sound(notif_freq_fail_high, (short_dur))
        gen_sound(notif_freq_fail, (notif_dur), 0.1)
        gen_sound(notif_freq_fail_low, (medium_dur))
        gen_sound(notif_freq_fail_high, (short_dur))
        gen_sound(notif_freq_fail, (notif_dur), 0.1)


# 4/3, 6/5

# st = starting region,city, atm. This should be the same as region,city,atm
#      from last failed request.
# e = end region id. Alphabetically. Example: dolnoslaskie = 0,...
st = (0, 0, 0)
e = 1

sleep_min = 10
sleep_max = 20
sleep_coeff = 0.01

get_all_atms_data_rec(st, e)

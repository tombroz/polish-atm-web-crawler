import random
import re
import time
import bs4
import tor_ip
from sounds import sound_notif

base_atm_url = "http://www.karty.pl/bankomaty.php?bankomat="
base_warsaw_distr_url = "http://www.karty.pl/bankomaty.php?miejscowosc=warszawa&amp;dzielnica="#od 49 znaku
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

sleep_min = 10
sleep_max = 30
sleep_coeff = 0.01

requests_limit = 66
unique_ips = 10
retry_count = 100
timeout = 6

code_stopped = "Zatrzymano program"
code_blocked = "Zablokowano IP"
code_retry = "Zbyt wiele prób zmiany IP"
code_succ = "Zakończono pobieranie"
code_privoxy = "Blad privoxy. Resetuje usluge privoxy i ponownie lacze z Tor..."


def get_url_content(url, how_many_retry):
    for i in range(how_many_retry):
        print("Pobieranie url...")
        response = tor_ip.get_url(url, timeout)
        if response is None:
            print("Przekroczono limit {}s oczekiwania na odpowiedz. "
                  "Zmieniam IP po raz {}...".format(timeout, i))
            res = tor_ip.change_ip(unique_ips)
            if res is not None:
                return res
        else:
            break
    if response is None:
        return code_retry
    else:
        response.encoding = 'utf-8'
        html = response.text
        soup = bs4.BeautifulSoup(html, "html.parser")
        print(soup.find('title').get_text())
        if soup.find('title', string=re.compile("Privox", flags=re.IGNORECASE)):
            return code_privoxy
        if soup.find('title', string=re.compile("unavailable", flags=re.IGNORECASE)):
            return code_blocked
        return soup


def get_url_content_retry(url, how_many_retry):
    for i in range(retry_count):
        url_content = get_url_content(url, retry_count)
        if url_content in (tor_ip.code_check_ip_blocked, tor_ip.code_check_ip_retry, code_retry):
            return url_content
        elif (url_content is code_blocked) or (url_content is code_privoxy):
            if url_content is code_blocked:
                print("{}. "
                      "Zmieniam IP po raz {}...".format(code_blocked, i))
            if url_content is code_privoxy:
                print("{}".format(code_privoxy))
                tor_ip.reset_privoxy_tor()
                print("Zmieniam IP po raz {}...".format(i))
            res = tor_ip.change_ip(unique_ips)
            if res is not None:
                return res
            continue
        # elif url_content is code_privoxy:
        #     return url_content
        else:
            break
    return url_content


def get_region_cities(region_url,urls_offset):
    region_cities = []
    # prepare html data from url
    url_content = get_url_content_retry(region_url, retry_count)
    if url_content in (
            tor_ip.code_check_ip_blocked, tor_ip.code_check_ip_retry, code_retry, code_blocked, code_privoxy):
        return url_content
    content = url_content.find_all('ul')[-1] \
        .find_all(href=re.compile("miejscowosc"))
    for element in content:
        region_cities.append(element.get('href')[urls_offset:])
    return region_cities


def get_city_atms_numbers(city_url):
    city_atms_numbers = []
    # prepare html data from url
    url_content = get_url_content_retry(city_url, retry_count)
    if url_content in (
            tor_ip.code_check_ip_blocked, tor_ip.code_check_ip_retry, code_retry, code_blocked, code_privoxy):
        return url_content
    content = url_content.find_all('dd')
    for element in content:
        city_atms_numbers.append(element.find('a').get('href')[10:])
    return city_atms_numbers


def get_atm_data(atm_url, region_id):
    atm_data = []
    # prepare html data from url
    url_content = get_url_content_retry(atm_url, retry_count)
    if url_content in (
            tor_ip.code_check_ip_blocked, tor_ip.code_check_ip_retry, code_retry, code_blocked, code_privoxy):
        return url_content
    # get atm's data from url
    content = url_content.find_all('dd')
    content_ids = url_content.find_all('dt')
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
            elif i == 2:
                ind = [j for j, item in enumerate(ids_strings) if re.search('Lokaliz', item)][0]
            elif i == 3:
                ind = [j for j, item in enumerate(ids_strings) if re.search('Bankomat nale', item)][0]
            elif i == 4:
                ind = [j for j, item in enumerate(ids_strings) if re.search('Dost', item)][0]
            elif i == 5:
                ind = [j for j, item in enumerate(ids_strings) if re.search('Numer banko', item)][0]
            elif i == 6:
                ind = [j for j, item in enumerate(ids_strings) if re.search('Funkcja depo', item)][0]
            elif i == 7:
                ind = [j for j, item in enumerate(ids_strings) if re.search('Produ', item)][0]
        except IndexError:
            ind = -1
        if ind is not -1:
            atm_data.append(content[ind].get_text())
        else:
            atm_data.append("null")
    return atm_data


def get_all_atms_data_rec(st_p, end_p):
    """
    Downloads atms data from karty.pl from starting region, city, atm_nr
    until given region (end_point) is reached.
    Writes real start and end points ((region, city, atm_nr) ids) to file
    :param st_p: tuple containing (region, city, atm_nr) ids from which
    to start downloading data
    :param end_p: region id (from region_urls) to which downloading is continued
    :return: None
    """
    count_download = 0
    count = 0

    def check_change_ip(cou, req_limit, uniq_ips):
        if cou > req_limit:
            tor_ip.change_ip(uniq_ips)
            nonlocal count
            count = 0

    i, j, k = 0, 0, 0
    for i in range(len(region_urls)):
        if i < st_p[0]:
            continue
        elif i >= end_p:
            break
        print("Pobieranie dla: wojew_{} = {}".format(i, region_urls[i][46:]))
        result_file_output(st_p, i, j, k, count_download, code_stopped)
        count += 1
        check_change_ip(count, requests_limit, unique_ips)
        region_cities = get_region_cities(region_urls[i],26)
        if region_cities in (
                code_blocked, code_retry, tor_ip.code_check_ip_blocked, tor_ip.code_check_ip_retry, code_privoxy):
            return result_file_output(st_p, i, j, k, count_download, region_cities)
        time.sleep(float(random.randint(sleep_min, sleep_max)) * sleep_coeff)
        for j in range(len(region_cities)):
            if j < st_p[1] and i == st_p[0]:
                continue
            print("Pobieranie dla: wojew_{} = {}\t| miasto_{} = {}"
                  .format(i, region_urls[i][46:], j, region_cities[j]))
            result_file_output(st_p, i, j, k, count_download, code_stopped)
            count += 1
            check_change_ip(count, requests_limit, unique_ips)
            city_atms_numbers = get_city_atms_numbers(base_city_url + region_cities[j])
            if city_atms_numbers in (
                    code_blocked, code_retry, tor_ip.code_check_ip_blocked, tor_ip.code_check_ip_retry, code_privoxy):
                return result_file_output(st_p, i, j, k, count_download, city_atms_numbers)
            time.sleep(float(random.randint(sleep_min, sleep_max)) * sleep_coeff)
            for k in range(len(city_atms_numbers)):
                if k < st_p[2] and j == st_p[1]:
                    continue
                print("Pobieranie dla: wojew_{} = {}\t| miasto_{} = {}\t| nr_bankom_{} = {}"
                      .format(i, region_urls[i][46:], j, region_cities[j], k, city_atms_numbers[k]))
                count += 1
                check_change_ip(count, requests_limit, unique_ips)
                result_file_output(st_p, i, j, k, count_download, code_stopped)
                atm_data = get_atm_data(base_atm_url + city_atms_numbers[k], i)
                if atm_data in (
                        code_blocked, code_retry, tor_ip.code_check_ip_blocked, tor_ip.code_check_ip_retry,
                        code_privoxy):
                    return result_file_output(st_p, i, j, k, count_download, atm_data)
                with open("../../bankomaty_dane.txt", 'a', encoding='utf-8') as atms_data_file:
                    for x in range(len(atm_data)):
                        atms_data_file.write(atm_data[x])
                        if x != len(atm_data) - 1:
                            atms_data_file.write("|")
                    atms_data_file.write("\n")
                count_download += 1
                time.sleep(float(random.randint(sleep_min, sleep_max)) * sleep_coeff)
    return result_file_output(st_p, i, j, k, count_download, code_succ)


def result_file_output(st_p, i, j, k, data_count, code):
    if i < st_p[0]:
        i = st_p[0]
    if j < st_p[1] and i == st_p[0]:
        j = st_p[1]
    if k < st_p[2] and i == st_p[0] and j == st_p[1]:
        k = st_p[2]
    if result_file_output.counter > 0:
        trunc_lines("punkty_kontrolne")
    with open("../../punkty_kontrolne.txt", 'a', encoding='utf-8') as result_file:
        output = '{}. Pobrano dane w liczbie {} od/do: (wojew|miasto|nr_bankom) = |{}|{}|{}| / |{}|{}|{}|\n'.format(
            code, data_count,
            st_p[0], st_p[1],
            st_p[2], i, j, k)
        if code in (code_blocked, code_retry, tor_ip.code_check_ip_blocked, tor_ip.code_check_ip_retry, code_privoxy):
            sound_notif(0)
            print(output)
        elif code in code_succ:
            sound_notif(1)
            print(output)
        result_file.write(output)
    result_file_output.counter += 1


def trunc_lines(filename):
    with open("../../{}.txt".format(filename), 'r', encoding='utf-8') as result_file:
        lines = result_file.readlines()[:-1]
    with open("../../{}.txt".format(filename), 'w', encoding='utf-8') as result_file:
        result_file.writelines(lines)


result_file_output.counter = 0
print("""Program pobiera dane bankomatow ze strony karty.pl. Nalezy podac punkt startowy w postaci:
a,b,c
,gdzie 'a,b,c' to liczby oznaczajace indeks wojewodztwa(a), miasta(b) i bankomatu(c), 
od ktorego ma sie rozpoczac pobieranie danych. Indeksy wojewodztw sa podane alfabetycznie tj.:

0	dolnoslaskie
1	kujawsko-pomorskie
2	lubelskie
3	lubuskie
4	lodzkie
5	malopolskie
6	mazowieckie
7	opolskie
8	podkarpackie
9	podlaskie
10	pomorskie
11	slaskie
12	swietokrzyskie
13	warminsko-mazurskie
14	wielkopolskie
15	zachodniopomorskie

Indeksy miast i bankomatow nie sa z gory znane i program musi pobierac je na biezaco ze strony.
Lepiej zostawic je na 0,0 dopoki nie uzyska sie punktu kontrolnego (patrz dalej).
    Przykladowo rozpoczecie od poczatku wojewodztwa dolnoslaskiego to podanie: 0,0,0
Program pobiera dane dla wojewodztw dopoki nie zostanie zablokowane IP, co jest sygnalizowane dzwiekowo. 
Wtedy nalezy zmienic IP poza programem. Następnie mozna wpisac "p" co spowoduje kontynuowanie
pobierania od miejsca przerwania.
    Program zapisuje wyniki w pliku tekstowym "bankomaty_dane.txt" w postaci:
wojewodztwo|miasto|lokalizacja|wlasciciel|dostepnosc|nr_bankomatu|funkcje_depozytowe|producent
W pliku "punkty_kontrolne.txt" znajduja sie punkty w ktorych zaczynalo i konczylo sie pobieranie.
""")
while 1:
    print('Podaj po przecinku startowe: wojewodztwo(0-15), miasto(liczba), bankomat(liczba). '
          'Wpisz "p", aby zaczac od miejsca gdzie skonczono:')
    inp = input()
    if inp == 'p':
        with open("../../punkty_kontrolne.txt", 'r') as in_file:
            lines = in_file.readlines()
            last_line = lines[-1]
            last_line_elems = last_line.split('|')
            str_st = last_line_elems[-4:-1]
            try:
                st = (int(str_st[0]), int(str_st[1]), int(str_st[2]))
                end = 16  # int(st[0]) + 1
                get_all_atms_data_rec(st, end)
            except IndexError:
                print("Nie odczytano punktu startowego z pliku punkty_kontrolne.txt.")
    else:
        st = inp.split(',')
        end = 16  # int(st[0]) + 1
        try:
            get_all_atms_data_rec((int(st[0]), int(st[1]), int(st[2])), end)
        except:
            print("Nieprawidlowe dane. Wpisz 3 liczby oddzielone przecinkami.")

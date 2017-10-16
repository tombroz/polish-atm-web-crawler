import random
import re
import time
import bs4
import tor_ip
from sounds import sound_notif

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
sleep_min = 100
sleep_max = 200
sleep_coeff = 0.01
requests_limit = 49
unique_ips = 20


def get_region_cities(region_url):
    region_cities = []
    # prepare html data from url
    response = tor_ip.get_url(region_url)
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
    response = tor_ip.get_url(city_url)
    html = response.text
    soup = bs4.BeautifulSoup(html, "html.parser")
    if soup.find('title', string="503 Service Unavailable"):
        return None
    content = soup.find_all('dd')
    for element in content:
        city_atms_numbers.append(element.find('a').get('href')[10:])
    return city_atms_numbers


def get_atm_data(atm_url, region_id):
    atm_data = []
    # prepare html data from url
    response = tor_ip.get_url(atm_url)
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
    count = 0

    def check_change_ip(cou, req_limit, uniq_ips):
        if cou > req_limit:
            tor_ip.change_ip(uniq_ips)

    i, j, k = 0, 0, 0
    for i in range(len(region_urls)):
        count+=1
        check_change_ip(count, requests_limit, unique_ips)
        if i < st_p[0]:
            continue
        elif i >= end_p:
            break
        print("Pobieranie dla: wojew_{} = {}".format(i, region_urls[i][46:]))
        region_cities = get_region_cities(region_urls[i])
        if region_cities is None:
            return result_file_output(st_p, i, j, k, True)
        time.sleep(float(random.randint(sleep_min, sleep_max)) * sleep_coeff)
        for j in range(len(region_cities)):
            count += 1
            check_change_ip(count, requests_limit, unique_ips)
            if j < st_p[1] and i == st_p[0]:
                continue
            print("Pobieranie dla: wojew_{} = {}\t| miasto_{} = {}"
                  .format(i, region_urls[i][46:], j, region_cities[j]))
            city_atms_numbers = get_city_atms_numbers(base_city_url + region_cities[j])
            if city_atms_numbers is None:
                return result_file_output(st_p, i, j, k, True)
            time.sleep(float(random.randint(sleep_min, sleep_max)) * sleep_coeff)
            for k in range(len(city_atms_numbers)):
                count += 1
                check_change_ip(count, requests_limit, unique_ips)
                if k < st_p[2] and j == st_p[1]:
                    continue
                print("Pobieranie dla: wojew_{} = {}\t| miasto_{} = {}\t| nr_bankom_{} = {}"
                      .format(i, region_urls[i][46:], j, region_cities[j], k, city_atms_numbers[k]))
                atm_data = get_atm_data(base_atm_url + city_atms_numbers[k], i)
                if atm_data is None:
                    return result_file_output(st_p, i, j, k, True)
                with open("../../bankomaty_dane.txt", 'a', encoding='utf-8') as atms_data_file:
                    for x in range(len(atm_data)):
                        atms_data_file.write(atm_data[x])
                        if x != len(atm_data) - 1:
                            atms_data_file.write("|")
                    atms_data_file.write("\n")
                time.sleep(float(random.randint(sleep_min, sleep_max)) * sleep_coeff)
    return result_file_output(st_p, i, j, k, False)


def result_file_output(st_p, i, j, k, user_blocked):
    if i < st_p[0]:
        i = st_p[0]
    if j < st_p[1] and i == st_p[0]:
        j = st_p[1]
    if k < st_p[2] and i == st_p[0]:
        k = st_p[2]
    with open("../../punkty_kontrolne.txt", 'a', encoding='utf-8') as result_file:
        if user_blocked:
            output = 'Zablokowano IP. Pobrano dane od/do: (wojew|miasto|nr_bankom) = |{}|{}|{}| / |{}|{}|{}|\n'.format(
                st_p[0], st_p[1], st_p[2], i, j,
                k)
            sound_notif(0)
        else:
            output = 'Zakonczono pobieranie. Pobrano dane od/do: (wojew|miasto|nr_bankom) = |{}|{}|{}| / |{}|{}|{}|\n'.format(
                st_p[0], st_p[1], st_p[2], i,
                j, k)
            sound_notif(1)
        result_file.write(output)
        print(output)


# st = starting region,city, atm. This should be the same as region,city,atm
#      from last failed request.
# end = end region id. Alphabetically. Example: dolnoslaskie = 0,...
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
            str_st = in_file.readlines()[-1].split('|')[-4:-1]
            try:
                st = (int(str_st[0]), int(str_st[1]), int(str_st[2]))
                end = 15  # st[0] + 1
                get_all_atms_data_rec(st, end)
            except IndexError:
                print("Nie odczytano punktu startowego z pliku punkty_kontrolne.txt.")
    else:
        st = inp.split(',')
        end = 15  # int(st[0]) + 1
        try:
            get_all_atms_data_rec((int(st[0]), int(st[1]), int(st[2])), end)
        except:
            print("Nieprawidlowe dane. Wpisz 3 liczby oddzielone przecinkami.")

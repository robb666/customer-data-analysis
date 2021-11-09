from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from datetime import date, timedelta
import base64
import re
import phonenumbers
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from typing import NamedTuple, Union
from itertools import chain


SCOPES = ['https://www.googleapis.com/auth/gmail.modify']


def ldi_label():
    """Bada"""
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server()

        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('gmail', 'v1', credentials=creds)

    today = date.today()
    after = (today - timedelta(365)).strftime('%Y/%m/%d')
    before = (today - timedelta(1)).strftime('%Y/%m/%d')

    query = f'after:{after} before:{before}'

    results = service.users().messages().list(userId='me', labelIds=['Label_2190344206317955071'], q=query).execute()
    messages = results.get('messages', [])

    subjects = []
    for message in messages:
        form = {}
        msg = service.users().messages().get(userId='me', id=message['id'], format='full').execute()
        dane_body = base64.urlsafe_b64decode(msg.get("payload").get("body").get("data").encode("ASCII")).decode("utf-8")

        form['service'] = service
        form['message id'] = message['id']
        form['imię'] = re.search('Imię:\s(\w+)', dane_body).group(1) if re.search('Imię:\s(\w+)',
                                                                                       dane_body) else ''
        form['nazwisko'] = dane_body.split('<br>')[1].rstrip().split(' ')[-1]
        if form['nazwisko'] == 'Nazwisko:':
            form['nazwisko'] = ''
        form['nr_rej'] = re.search('Nr. rej.:\s([\w\d]+)', dane_body).group(1) if \
            re.search('Nr. rej.:\s([\w\d]+)', dane_body) else ''
        form['nr_pesel'] = re.search('Pesel:\s(\w+)', dane_body).group(1) if \
            re.search('Pesel:\s(\w+)', dane_body) else ''
        form['nr_regon'] = re.search('Regon:\s(\w+)', dane_body).group(1) if \
            re.search('Regon:\s(\w+)', dane_body) else ''
        form['adres_email'] = re.search('E-mail:\s(.*)\s?<br>Kod', dane_body).group(1) if \
            re.search('E-mail:\s([\w])\s?', dane_body) else ''
        form['kod_poczt'] = re.search('Kod pocztowy:\s([\d-]+)', dane_body).group(1) if \
            re.search('Kod pocztowy:\s([\d-]+)', dane_body) else ''
        form['nr_telefonu'] = re.search('Telefon:\s(\d{8,13})', dane_body).group(1) if \
            re.search('Telefon:\s(\d{8,13})', dane_body) else ''
        if form['nr_telefonu'] != '':
            validate_phone = phonenumbers.parse(form['nr_telefonu'], 'PL')
            form['nr_telefonu'] = '+' + str(validate_phone.country_code) + str(validate_phone.national_number)

        form['2_raty'] = True if re.search('Raty:\s(\w+)', dane_body) and \
                                      re.search('Raty:\s(\w+)', dane_body).group(1) == 'true' else False

        form['jezyk'] = re.search('Język:\s(\w+)', dane_body).group(1) if re.search('Język:\s(\w+)',
                                                                                         dane_body) else ''
        if not form['jezyk']:
            form['jezyk'] = 'PL'

        subjects.append(form)
    return subjects


def pesel_checksum(p):
    """Suma kontrolna nr pesel."""
    if p and len(p) == 11:
        weights = [1, 3, 7, 9, 1, 3, 7, 9, 1, 3, 1]
        control_n = p[-1]
        sum = 0
        for i in range(len(weights)):
            sum += int(p[i]) * int(weights[i])
        sum = sum % 10
        control = 10 - sum
        if control == 10 or control_n == control:
            return True
        else:
            return False


def pesel_birth(p):
    if pesel_checksum(p):
        year, month, day = int(p[:2]), int(p[2:4]), int(p[4:6])
        if month >= 20:
            month = month - 20
        if year < 10:
            year = str(year).zfill(2)
        try:
            p = str(year) + str(month) + str(day)
            dt = datetime.strptime(p[:6], '%y%m%d')
            if dt > datetime.now() and not str(dt).startswith('0'):
                dt -= relativedelta(years=100)
                return dt.year
            return dt.year
        except ValueError as e:
            return f'Pesel date not valid. -> {e}'


def pesel_gender(p):
    if pesel_checksum(p):
        if int(p[-2]) % 2 == 1:
            return 'M'
        return 'K'


def uniqe_values():
    subjects = ldi_label()
    return {v['nr_pesel']: v for v in subjects}.values()


class Districts(NamedTuple):
    """Postal Address Numbers 0-9."""
    district: str
    district_code: int


class Cities(NamedTuple):
    city: str
    city_range: Union[range, chain]


warszawski = Districts('warszawski', 0)
olsztynski = Districts('olsztyński i białostocki', 1)
lubelski = Districts('lubelski i kielecki', 2)
krakowski = Districts('krakowski i rzeszowski', 3)
katowicki = Districts('katowicki i opolski', 4)
wrocławski = Districts('wrocławski', 5)
poznański = Districts('poznański i zielonogórski', 6)
szczeciński = Districts('szczeciński i koszaliński', 7)
gdański = Districts('gdański i bydgoski', 8)
łódzki = Districts('łódzki', 9)


all_dist = [warszawski, olsztynski, lubelski, krakowski, katowicki, wrocławski, poznański, szczeciński, gdański, łódzki]


Warszawa = Cities('Warszawa', range(0, 5))
Olsztyn = Cities('Olsztyn', range(10, 11))
Białystok = Cities('Białystok', range(15, 16))
Lublin = Cities('Lublin', range(20, 21))
Kielce = Cities('Kielce', range(25, 26))
Kraków = Cities('Krakow', range(30, 32))
Rzeszów = Cities('Rzeszów', range(35, 36))
Katowice = Cities('Katowice', range(40, 41))
Opole = Cities('Opole', range(45, 46))
Wrocław = Cities('Wroclaw', range(50, 55))
Poznań = Cities('Poznan', range(60, 62))
Zielona_Góra = Cities('Zielona Góra', range(65, 66))
Szczecin = Cities('Szczecin', range(70, 72))
Koszalin = Cities('Koszalin', range(75, 76))
Trójmiasto = Cities('Trójmiasto', chain(range(80, 85), range(86, 89)))
Bydgoszcz = Cities('Bydgoszcz', range(85, 86))
Łódź = Cities('Łódź', range(90, 95))

cities = [Warszawa, Olsztyn, Białystok, Lublin, Kielce, Kraków, Rzeszów, Katowice, Opole,
          Wrocław, Poznań, Zielona_Góra, Szczecin, Koszalin, Trójmiasto, Bydgoszcz, Łódź]


def desdfg(all_dist):
    counts = {}
    for data in uniqe_values():
        for dist in all_dist:
            if data['kod_poczt'] and int(data['kod_poczt'][0]) == dist.code_district:
                if dist.district not in counts:
                    counts[dist.district] = 0
                counts[dist.district] += 1
            if data['kod_poczt'] and int(data['kod_poczt'][:2]) in dist.city_range:
                if dist.city not in counts:
                    counts[dist.city] = 0
                counts[dist.city] += 1





            # print(data['kod_poczt'])
            # if data['kod_poczt'] != '':
            #     if int(data['kod_poczt'][0]) == warszawski.code_district:
            #         if warszawski.district not in counts:
            #             counts[warszawski.district] = 0
            #         counts[warszawski.district] += 1
            #         if int(data['kod_poczt'][:2]) in warszawski.city_range and warszawski.city not in counts:
            #             counts[warszawski.city] = 0
            #         counts[warszawski.city] += 1
            #         # TODO --> z warszawaskiego:..., w tym z Warszawy:...
            #
            #     if int(data['kod_poczt'][0]) == lodzki.code_district:
            #         if lodzki.district not in counts:
            #             counts[lodzki.district] = 0
            #         counts[lodzki.district] += 1
            #         if lodzki.city not in counts:
            #             counts[lodzki.city] = 0
            #         counts[lodzki.city] += 1

    return counts

print(desdfg(all_dist))


def age(): pass


def class_counts(rows):
    """Counts the number of each type of example in a dataset."""
    counts = {}  # a dictionary of label -> count.
    for row in rows:
        # in our dataset format, the label is always the last column
        label = row[-1]
        if label not in counts:
            counts[label] = 0
        counts[label] += 1
    return counts





# for data in uniqe_values():
#     # print(data)
#     birth_date = pesel_birth(data['nr_pesel'])
#     gender = pesel_gender(data['nr_pesel'])
#     print(data['kod_poczt'], birth_date, gender, data['nazwisko'])
























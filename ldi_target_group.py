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
from pprint import pprint


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
            return 'Mężczyzn'
        return 'Kobiet'


def email_values():
    subjects = ldi_label()
    return {v['nr_pesel']: v for v in subjects}.values()


class Districts(NamedTuple):
    """Districts ZIP codes 0-9."""
    name: str
    code: int


class Cities(NamedTuple):
    """Citie codes 00-94."""
    name: str
    code_range: Union[range, chain]


all_districts = [Districts('Okręg warszawski', 0),
                 Districts('Okręg olsztyński i białostocki', 1),
                 Districts('Okręg lubelski i kielecki', 2),
                 Districts('Okręg krakowski i rzeszowski', 3),
                 Districts('Okręg katowicki i opolski', 4),
                 Districts('Okręg wrocławski', 5),
                 Districts('Okręg poznański i zielonogórski', 6),
                 Districts('Okręg szczeciński i koszaliński', 7),
                 Districts('Okręg gdański i bydgoski', 8),
                 Districts('Okręg łódzki', 9)]


largest_cities = [Cities('Warszawa', range(0, 5)),
                  Cities('Olsztyn', range(10, 11)),
                  Cities('Białystok', range(15, 16)),
                  Cities('Lublin', range(20, 21)),
                  Cities('Kielce', range(25, 26)),
                  Cities('Krakow', range(30, 32)),
                  Cities('Rzeszów', range(35, 36)),
                  Cities('Katowice', range(40, 41)),
                  Cities('Opole', range(45, 46)),
                  Cities('Wrocław', range(50, 55)),
                  Cities('Poznań', range(60, 62)),
                  Cities('Zielona Góra', range(65, 66)),
                  Cities('Szczecin', range(70, 72)),
                  Cities('Koszalin', range(75, 76)),
                  Cities('Trójmiasto', chain(range(80, 85),
                                             range(86, 89))),
                  Cities('Bydgoszcz', range(85, 86)),
                  Cities('Łódź', range(90, 95))]


def count_district(forms_data, all_districts):
    district_counts = {}
    for data in forms_data:
        for district in all_districts:
            if data['kod_poczt'] and int(data['kod_poczt'][0]) == district.code:
                if district.name not in district_counts:
                    district_counts[district.name] = 0
                district_counts[district.name] += 1
    return district_counts


def count_city(forms_data, largest_cities):
    city_counts = {}
    for data in forms_data:
        for city in largest_cities:
            if data['kod_poczt'] and int(data['kod_poczt'][:2]) in city.code_range:
                if city.name not in city_counts:
                    city_counts[city.name] = 0
                city_counts[city.name] += 1
    return city_counts


def count_age(forms_data):
    age_counts = {}
    for data in forms_data:
        pesel = data['nr_pesel']
        if age := pesel_birth(pesel):
            if age not in age_counts:
                age_counts[age] = 0
            age_counts[age] += 1
    return age_counts


def count_gender(forms_data):
    gender_counts = {}
    for data in forms_data:
        pesel = data['nr_pesel']
        if gender := pesel_gender(pesel):
            if gender not in gender_counts:
                gender_counts[gender] = 0
            gender_counts[gender] += 1
    return gender_counts


forms_data = email_values()
pprint(count_district(forms_data, all_districts))
pprint(count_city(forms_data, largest_cities))
pprint(count_age(forms_data))
pprint(count_gender(forms_data))








def class_counts(rows):
    """Counts the number of each type of example in a dataset."""
    counts = {}  # a dictionary of label -> count.
    for row in rows:
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
























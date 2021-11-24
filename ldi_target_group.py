from __future__ import print_function
import pickle
import os.path
import time
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from datetime import date, timedelta
import base64
import re
import numpy as np
import phonenumbers
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from typing import NamedTuple, Union
from itertools import chain
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from pprint import pprint

pd.options.display.max_rows = 999
pd.set_option('display.max_columns', 40)
pd.set_option('max_colwidth', 1000)
pd.set_option('display.width', 1000)


SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


def _add(ids, msg, err):
    form, query_date = {}, ''
    for item in msg['payload']['headers']:
        if item.get('name') == 'Date':
            query_date = datetime.strptime(item['value'], '%a, %d %b %Y %H:%M:%S %z')

    body = base64.urlsafe_b64decode(msg.get("payload").get("body").get("data").encode("ASCII")).decode("utf-8")

    form['message id'] = msg['id']
    form['data'] = query_date.date().strftime('%Y.%m.%d')
    form['dzień'] = query_date.strftime('%A')
    form['godzina'] = query_date.time().strftime('%H:%M')
    form['imię'] = re.search('Imię:\s(\w+)', body).group(1) if re.search('Imię:\s(\w+)',
                                                                                   body) else ''
    form['nazwisko'] = body.split('<br>')[1].rstrip().split(' ')[-1]
    if form['nazwisko'] == 'Nazwisko:':
                        form['nazwisko'] = ''
    form['nr_rej'] = re.search('Nr. rej.:\s([\w\d]+)', body).group(1) if \
                        re.search('Nr. rej.:\s([\w\d]+)', body) else ''
    form['nr_pesel'] = re.search('Pesel:\s(\w+)', body).group(1) if \
                        re.search('Pesel:\s(\w+)', body) else ''
    form['nr_regon'] = re.search('Regon:\s(\w+)', body).group(1) if \
                        re.search('Regon:\s(\w+)', body) else ''
    form['adres_email'] = re.search('E-mail:\s(.*)\s?<br>Kod', body).group(1) if \
                        re.search('E-mail:\s([\w])\s?', body) else ''
    form['kod_poczt'] = re.search('Kod pocztowy:\s([\d-]+)', body).group(1) if \
                        re.search('Kod pocztowy:\s([\d-]+)', body) else ''
    form['nr_telefonu'] = re.search('Telefon:\s(\d{8,13})', body).group(1) if \
                        re.search('Telefon:\s(\d{8,13})', body) else ''
    if form['nr_telefonu'] != '':
        validate_phone = phonenumbers.parse(form['nr_telefonu'], 'PL')
        form['nr_telefonu'] = '+' + str(validate_phone.country_code) + str(validate_phone.national_number)

    form['2_raty'] = True if re.search('Raty:\s(\w+)', body) and \
                                re.search('Raty:\s(\w+)', body).group(1) == 'true' else False
    form['jezyk'] = re.search('Język:\s(\w+)', body).group(1) if re.search('Język:\s(\w+)',
                                                                                     body) else ''
    if not form['jezyk']:
        form['jezyk'] = 'PL'

    subjects.append(form)


def _retrive(service, query, pageToken=None):
    results = service.users().messages().list(userId='me',
                                              labelIds=['Label_2190344206317955071'],
                                              maxResults=100,
                                              pageToken=pageToken,
                                              q=query).execute()
    return results, results.get('nextPageToken')


def authentication():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server()

        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return build('gmail', 'v1', credentials=creds)


def batch_request(service):
    """Batch request to Gmail API."""
    today = date.today()
    after = (today - timedelta(400)).strftime('%Y/%m/%d')
    before = (today - timedelta(0)).strftime('%Y/%m/%d')

    query = f'after:{after} before:{before}'

    page_token = None
    while True:
        batch = service.new_batch_http_request()
        results, page_token = _retrive(service, query, page_token)
        messages = results.get('messages', [])

        for message in messages:
            msg = service.users().messages().get(userId='me',
                                                 id=message['id'],
                                                 format='full')
            batch.add(msg, callback=_add)
        batch.execute()
        if page_token is None:
            break


def pesel_checksum(p):
    """Pesel checksum."""
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
            return f'Pesel birth date error. -> {e}'


def pesel_gender(p):
    if pesel_birth(p):
        if int(p[-2]) % 2 == 1:
            return 'Males'
        return 'Females'


def eliminate_duplicates(subjects):
    return list({v['nr_pesel']: v for v in subjects}.values())


def eliminate_falsyficates(subjects):
    false = ['00000000000', '10101011111', '22222222222', '44444444444', '66666666666', '88888888888']
    for item in subjects:
        if item['nr_pesel'] in false or \
                len(item['nr_pesel']) != 11 and \
                not item['nr_regon'] or \
                re.search('[0-9]', item['imię']):
            subjects.remove(item)
    return subjects


class Districts(NamedTuple):
    """Districts ZIP codes 0-9."""
    name: str
    code: int


class Cities(NamedTuple):
    """Cities postal codes range 00-94."""
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


def pandas_frame(api_data):
    return pd.DataFrame(api_data, dtype=object)


def insert_district(forms_data, all_districts):
    for data in forms_data:
        for district in all_districts:
            if data['kod_poczt'] and int(data['kod_poczt'][0]) == district.code:
                data['okreg'] = district.name
    return forms_data


def insert_city(forms_data, largest_cities):
    for data in forms_data:
        for city in largest_cities:
            if data['kod_poczt'] and int(data['kod_poczt'][:2]) in city.code_range:
                data['miasto'] = city.name
    return forms_data


def insert_age(forms_data):
    for data in forms_data:
        pesel = data['nr_pesel']
        if age := pesel_birth(pesel):
            print(age)
            if isinstance(age, str):
                continue
            data['rocznik'] = round(age)
    return forms_data


def insert_gender(forms_data):
    for data in forms_data:
        pesel = data['nr_pesel']
        if gender := pesel_gender(pesel):
            data['plec'] = gender
    return forms_data


def count_district(forms_data, all_districts):
    district_counts = {}
    for data in forms_data:
        for district in all_districts:
            if data['kod_poczt'] and int(data['kod_poczt'][0]) == district.code:
                if district.name not in district_counts:
                    district_counts[district.name] = 0
                district_counts[district.name] += 1
                # if 'all clients' not in district_counts:
                #     district_counts['all clients'] = 0
                # district_counts['all clients'] += 1
    return district_counts


def percentage(counts: dict) -> list:
    counts_to_perc = {}
    all_dist = sum(counts.values())
    for item in counts:
        counts_to_perc[item] = round((counts[item] / all_dist) * 100, 1)
    return sort_dict(counts_to_perc)


def sort_dict(di: dict) -> list:
    if isinstance(list(di.keys())[0], int):
        return sorted(di.items(), key=lambda x: x[0])
    return sorted(di.items(), key=lambda x: x[1], reverse=True)


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
            if isinstance(age, str):
                continue
            elif age not in age_counts:
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


def count_language(forms_data):
    language_counts = {'PL': 0,
                       'EN': 0}
    for data in forms_data:
        lang = data['jezyk']
        if lang == 'PL':
            language_counts['PL'] += 1
        else:
            language_counts['EN'] += 1
    return language_counts


def plot_percentage(di):
    df_local = pd.DataFrame({'Okręgi':  [x[0] for x in di['okręgi']],
                             'Okręg %': [y[1] for y in di['okręgi']],
                             'Miasta':  [x[0] for x in di['miasta']],
                             'Miasto %':[y[1] for y in di['miasta']]})

    df_gen = pd.DataFrame({'Płeć':  [x[0] for x in di['płcie']],
                           'Płeć %':[y[1] for y in di['płcie']]})

    df_age = pd.DataFrame({'Rocznik':  [x[0] for x in di['roczniki']],
                           'Rocznik %':[y[1] for y in di['roczniki']]})

    sns.set(rc={'figure.figsize': (8, 8)}); fig, ax = plt.subplots(); fig.autofmt_xdate()
    ax = sns.barplot(x='Okręgi', y='Okręg %', data=df_local)
    ax.set_title('Z których okręgow spływaja zapytania.')
    plt.show()

    sns.set(rc={'figure.figsize': (8, 8)}); fig, ax = plt.subplots(); fig.autofmt_xdate()
    ax = sns.barplot(x='Miasta', y='Miasto %', data=df_local)
    ax.set_title('Miasta z których spływaja zapytania.')
    plt.show()

    sns.set(rc={'figure.figsize': (18, 6)}); fig, ax = plt.subplots(); fig.autofmt_xdate()
    ax = sns.barplot(x='Rocznik', y='Rocznik %', data=df_age)
    ax.set_title('Rocznik osób składających zapytania.')
    plt.show()

    sns.set(rc={'figure.figsize': (6, 6)}); fig, ax = plt.subplots(); fig.autofmt_xdate()
    ax = sns.barplot(x='Płeć', y='Płeć %', data=df_gen)
    ax.set_title('Płeć osób skladajcych zapytania.')
    plt.show()


subjects = []
service = authentication()
batch_request(service)

forms_data = eliminate_duplicates(subjects)
forms_data = eliminate_falsyficates(forms_data)


district_counts = count_district(forms_data, all_districts)
city_counts = count_city(forms_data, largest_cities)
gender_counts = count_gender(forms_data)
lang_counts = count_language(forms_data)
age_counts = count_age(forms_data)


# districts_arr = percentage(district_counts)
# cities_arr = percentage(city_counts)
# gender_arr = percentage(gender_counts)
# age_arr = percentage(age_counts)

# di = {}
# di['okręgi'], di['miasta'], di['płcie'], di['roczniki'] = districts_arr, cities_arr, gender_arr, age_arr
# plot_percentage(di)

# print(districts_arr)
# print(district_counts)
# print(cities_arr)
# print(gender_arr)
# print(age_arr)


insert_district(forms_data, all_districts)
insert_city(forms_data, largest_cities)
insert_age(forms_data)
insert_gender(forms_data)

# print(district_counts)
# print(forms_data)

print(pandas_frame(forms_data))
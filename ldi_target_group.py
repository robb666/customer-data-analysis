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
import phonenumbers
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from typing import NamedTuple, Union
from itertools import chain
from pprint import pprint


SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


def _add(ids, msg, err):
    form = {}
    body = base64.urlsafe_b64decode(msg.get("payload").get("body").get("data").encode("ASCII")).decode("utf-8")
    form['message id'] = msg['id']
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
    return {v['nr_pesel']: v for v in subjects}.values()


def eliminate_falsyficates(subjects):
    false = ['00000000000', '10101011111', '22222222222', '44444444444', '66666666666', '88888888888']
    for item in subjects:
        if item['nr_pesel'] in false or len(item['nr_pesel']) != 11 and not item['nr_regon']:
            item['nr_pesel'] = ''
        if re.search('[0-9]', item['imię']):
            item['nr_pesel'] = ''
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


def count_district(forms_data, all_districts):
    district_counts = {}
    for data in forms_data:
        for district in all_districts:
            if data['kod_poczt'] and int(data['kod_poczt'][0]) == district.code:
                if district.name not in district_counts:
                    district_counts[district.name] = 0
                district_counts[district.name] += 1
                if 'all clients' not in district_counts:
                    district_counts['all clients'] = 0
                district_counts['all clients'] += 1
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


def gender_percentage(gender_counts):
    female = gender_counts['Females']
    male = gender_counts['Males']
    gender_counts['Females'] = str(round(female / (female + male) * 100)) + ' %'
    gender_counts['Males'] = str(round(male / (female + male) * 100)) + ' %'
    return gender_counts


def language(forms_data):
    language_counts = {'PL': 0,
                       'EN': 0}
    for data in forms_data:
        lang = data['jezyk']
        if lang == 'PL':
            language_counts['PL'] += 1
        else:
            language_counts['EN'] += 1
    return language_counts


def language_percentage(lang_counts):
    pl = lang_counts['PL']
    en = lang_counts['EN']
    lang_counts['PL'] = str(round(pl / (pl + en) * 100)) + ' %'
    lang_counts['EN'] = str(round(en / (pl + en) * 100)) + ' %'
    return lang_counts



subjects = []
service = authentication()
batch_request(service)

forms_data = eliminate_duplicates(subjects)
forms_data = eliminate_falsyficates(forms_data)

gender_counts = count_gender(forms_data)
lang_counts = language(forms_data)

pprint(count_district(forms_data, all_districts))
pprint(count_city(forms_data, largest_cities))
pprint(count_age(forms_data))
pprint(count_gender(forms_data))
pprint(gender_percentage(gender_counts))
pprint(language(forms_data))
pprint(language_percentage(lang_counts))


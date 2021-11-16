from __future__ import print_function
import concurrent.futures
import time
import traceback
from io import StringIO
import logging
import os
import sys
# import do_loginmotru
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
import re
import phonenumbers
from typing import NamedTuple, Union
from itertools import chain
import matplotlib.pyplot as plt
import seaborn as sns
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



def plot(arr):
    names, values = [x[0] for x in arr], [y[1] for y in arr]
    plt.style.use('ggplot')
    sns.histplot(names, bins=range(min(names), max(names) + 1), stat='percent',  kde=True)
    plt.show()


arr = [(1941, 0.6),
       (1950, 0.6),
       (1951, 1.2),
       (1953, 0.6),
       (1954, 0.6),
       (1955, 1.2),
       (1957, 1.2),
       (1959, 1.2),
       (1962, 1.2),
       (1963, 1.2),
       (1966, 0.6),
       (1969, 1.2),
       (1970, 2.4),
       (1971, 0.6),
       (1973, 0.6),
       (1974, 2.4),
       (1975, 1.8),
       (1976, 1.2),
       (1977, 2.4),
       (1978, 2.4),
       (1979, 1.2),
       (1980, 1.2),
       (1981, 3.6),
       (1982, 1.8),
       (1983, 2.4),
       (1984, 5.4),
       (1985, 2.4),
       (1986, 5.4),
       (1987, 1.2),
       (1988, 2.4),
       (1989, 3.0),
       (1990, 3.6),
       (1991, 4.8),
       (1992, 4.2),
       (1993, 4.2),
       (1994, 4.2),
       (1995, 4.2),
       (1996, 5.4),
       (1997, 3.6),
       (1998, 4.2),
       (1999, 3.0),
       (2000, 1.8),
       (2001, 0.6),
       (2002, 0.6),
       (2003, 0.6)]

plot(arr)


















# SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


# def _add(id, msg, err):
#
#     body = base64.urlsafe_b64decode(msg.get("payload").get("body").get("data").encode("ASCII")).decode("utf-8")
#
#     form = {}
#     form['message id'] = msg['id']
#     form['imię'] = re.search('Imię:\s(\w+)', body).group(1) if re.search('Imię:\s(\w+)',
#                                                                                    body) else ''
#     form['nazwisko'] = body.split('<br>')[1].rstrip().split(' ')[-1]
#     if form['nazwisko'] == 'Nazwisko:':
#                         form['nazwisko'] = ''
#     form['nr_rej'] = re.search('Nr. rej.:\s([\w\d]+)', body).group(1) if \
#                         re.search('Nr. rej.:\s([\w\d]+)', body) else ''
#     form['nr_pesel'] = re.search('Pesel:\s(\w+)', body).group(1) if \
#                         re.search('Pesel:\s(\w+)', body) else ''
#     form['nr_regon'] = re.search('Regon:\s(\w+)', body).group(1) if \
#                         re.search('Regon:\s(\w+)', body) else ''
#     form['adres_email'] = re.search('E-mail:\s(.*)\s?<br>Kod', body).group(1) if \
#                         re.search('E-mail:\s([\w])\s?', body) else ''
#     form['kod_poczt'] = re.search('Kod pocztowy:\s([\d-]+)', body).group(1) if \
#                         re.search('Kod pocztowy:\s([\d-]+)', body) else ''
#     form['nr_telefonu'] = re.search('Telefon:\s(\d{8,13})', body).group(1) if \
#                         re.search('Telefon:\s(\d{8,13})', body) else ''
#     if form['nr_telefonu'] != '':
#         validate_phone = phonenumbers.parse(form['nr_telefonu'], 'PL')
#         form['nr_telefonu'] = '+' + str(validate_phone.country_code) + str(validate_phone.national_number)
#
#     form['2_raty'] = True if re.search('Raty:\s(\w+)', body) and \
#                                 re.search('Raty:\s(\w+)', body).group(1) == 'true' else False
#
#     form['jezyk'] = re.search('Język:\s(\w+)', body).group(1) if re.search('Język:\s(\w+)',
#                                                                                      body) else ''
#     if not form['jezyk']:
#         form['jezyk'] = 'PL'
#
#     subjects.append(form)
#
#
# def _retrive(service, query, pageToken=None):
#     results = service.users().messages().list(userId='me',
#                                               labelIds=['Label_2190344206317955071'],
#                                               maxResults=100,
#                                               pageToken=pageToken,
#                                               q=query).execute()
#     return results, results.get('nextPageToken')
#
#
# def ldi_label():
#     """Bada"""
#     creds = None
#
#     if os.path.exists('token.pickle'):
#         with open('token.pickle', 'rb') as token:
#             creds = pickle.load(token)
#
#     if not creds or not creds.valid:
#         if creds and creds.expired and creds.refresh_token:
#             creds.refresh(Request())
#         else:
#             flow = InstalledAppFlow.from_client_secrets_file(
#                 'credentials.json', SCOPES)
#             creds = flow.run_local_server()
#
#         with open('token.pickle', 'wb') as token:
#             pickle.dump(creds, token)
#
#     service = build('gmail', 'v1', credentials=creds)
#
#     today = date.today()
#     after = (today - timedelta(400)).strftime('%Y/%m/%d')
#     before = (today - timedelta(0)).strftime('%Y/%m/%d')
#
#     query = f'after:{after} before:{before}'
#
#     page_token = None
#     while True:
#         batch = service.new_batch_http_request()
#         results, page_token = _retrive(service, query, page_token)
#         messages = results.get('messages', [])
#
#         for message in messages:
#             msg = service.users().messages().get(userId='me',
#                                                  id=message['id'],
#                                                  format='full')
#             batch.add(msg, callback=_add)
#         batch.execute()
#         if page_token is None:
#             break
#
#
# subjects = []
# ldi_label()
# print(subjects)






















# # Create a range that does not contain 50
# for i in [x for x in range(100) if x != 50]:
#     print(i)

# Create 2 ranges [0,49] and [51, 100]
# from itertools import chain
# concatenated = chain(range(50), range(51, 100))
# for i in concatenated:
#     print(i)



# class Cities(NamedTuple):
#     city: str
#     city_range: Union[range, chain]
#
#
# Trójmiasto = Cities('Trójmiasto', chain(range(80, 85), range(86, 89)))
#
#
# for i in Trójmiasto.city_range:
#     print(i)


# # Create a iterator and skip 50
# xr = iter(range(100))
# for i in xr:
#     print(i)
#     if i == 49:
#         next(xr)

# # Simply continue in the loop if the number is 50
# for i in range(100):
#     if i == 50:
#         continue
#     print(i)














# dane_body = 'Imię: Rui Ramos<br>Nazwisko: Rui Ramos<br>Nr. rej.: PKR16531<br>Pesel: 78082119653<br>Regon: <br>' \
#        'E-mail: ruimailramos@gmail.com<br>Kod pocztowy: 96-325<br>Telefon: 669155117<br>Raty: true<br>Język: EN'

# dane_body = 'Imię: Pawel<br>Nazwisko: Jan<br>Nr. rej.: Ptu2641f<br>Pesel: 81010200141<br>Regon: <br>' \
#        'E-mail: Mocarmen3321@gmail.com<br>Kod pocztowy: 00-001<br>Telefon: <br>Raty: true<br>Język: EN'

# dane_body = 'Imię: david<br>Nazwisko: hoyland<br>Nr. rej.: elc51438<br>Pesel: 70062017694<br>Regon: <br>' \
#             'E-mail: david.hoyland@halocreativedesign.com<br>Kod pocztowy: 99-423<br>Telefon: 0789324027<br>Raty: false<br>Język: EN'

# dane_body = 'Imię: robert<br>Nazwisko: grzelak<br>Nr. rej.: el4c079<br>Pesel: 82082407038<br>Regon: <br>' \
#             'E-mail: robert.patryk.grzelak@gmail.com<br>Kod pocztowy: 90-441<br>Telefon: <br>Raty: false<br>Język: EN'


# print(dane_body)
# print()
#
# dane = [i.split()[-1] for i in dane_body.split('<br>')]
#
# print(dane)
# print()


# formularz = {}
#
#
# formularz['imię'] = re.search('Imię:\s(\w+)', dane_body).group(1)
# formularz['nazwisko'] = dane_body.split('<br>')[1].rstrip().split(' ')[-1]
# formularz['nr_rej'] = dane[2] if 2 < len(dane[2]) <= 8 else ''
# # formularz['anglik'] = True if dane[4] == 'prawa' else False
# formularz['nr_pesel'] = dane[3] if re.search('^\d{11}$', dane[3]) else ''
# formularz['nr_regon'] = dane[4] if re.search('^\d{9}$', dane[4]) else ''
# formularz['adres_email'] = dane[5].rstrip()
# formularz['kod_poczt'] = dane[6] if re.search('^\d{2}-\d{3}$', dane[6]) else ''
# formularz['nr_telefonu'] = dane[7] if re.search('\d{9}', dane[7]) else ''
# if formularz['nr_telefonu'] != '':
#     validate_phone = phonenumbers.parse(formularz['nr_telefonu'], 'PL')
#     formularz['nr_telefonu']= '+' + str(validate_phone.country_code) + str(validate_phone.national_number)
#
# formularz['2_raty'] = True if dane[8] == 'true' else False
# formularz['jezyk'] = dane[-1]
#
#
#
# print(formularz)







# my_model = ['X5 3.0D', '']
# li = any([X in model for X in ('X3', 'X5') for model in my_model[0].split()])
# print(li)

# # '82082407038'
# # '00213103073'
# # pesel = '00213103073'
# # pesel = '02302710110'
# pesel = '02302710110'
# # pesel = '82082407038'
#
# if pesel.startswith('0') and pesel[2] in ['2', '3']:
#     year, month, day = pesel[:2], str(int(pesel[2:4]) - 20).zfill(2), pesel[4:]
#     pesel = year + month + day
#     print(id(pesel))
# print(id(pesel))
# dt = datetime.strptime(pesel[:6], '%y%m%d')
# if dt > datetime.now() and not str(dt).startswith('0'):
#     dt -= relativedelta(years=100)
# my_license = (dt + relativedelta(years=19)).strftime('%d.%m.%Y')
#
# print(my_license)














# di = {   'DMC': '1560',
#          'Data pierwszej rejestracji': '21.06.2002',
#          'Import': 'tak',
#          'Kierownica po prawej stronie': 'NIE',
#          'Liczba miejsc': '5',
#          'Liczba współwłaścicieli': '1',
#          'Marka': 'MERCEDES-BENZ',
#          'Masa pojazdu': '1175',
#          'Moc': '70 kW',
#          'Model': 'A 170',
#          'Numer VIN': 'WDB1680091J630375',
#          'Numer rejestracyjny': 'RPZ32556',
#          'Paliwo': 'Olej napędowy',
#          'Pierwsza rejestracja w Polsce': '29.06.2017',
#          'Podrodzaj': 'hatchback',
#          'Pojazd wyposażony w instalację LPG': 'NIE',
#          'Pojemność': '1689 cm3',
#          'Przebieg': '326062',
#          'Rodzaj pojazdu': 'Samochód osobowy',
#          'Rok produkcji': '2001',
#          'Specjalne użytkowanie': '-',
#          'Termin następnego bad. tech.': '19.09.2019',
#          'Ważność OC': 'Brak info',
#          'Właściciel nr': '1',
#          'Ładowność pojazdu': '385'}
#
#
#
#
# print(int(di['Przebieg'][:2]) + int(di['Przebieg'][:2]))








"""LOG"""
# os.chdir('/home/robb/Desktop/PROJEKTY/ldi/ldi2')
#
#
# logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)
# formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(module)s:%(funcName)s:line %(lineno)d:%(message)s')
# file_handler = logging.FileHandler('log/practice.log')
# file_handler.setFormatter(formatter)
# logger.addHandler(file_handler)
#
#
# do_loginmotru.zero()
#
#
#
# # try:
# def one():
#     time.sleep(.9)
#     logging.info('First')
#     return False
#
#
# def two():
#     try:
#         # time.sleep(.4) + n
#         logger.info('two')
#     except:
#         logger.critical(sys.exc_info())
#     return True
#
#
# def three():
#     time.sleep(1.1)
#     logger.info('Third')
#     return False
#
# tasks = [one, two, three]
# executor = concurrent.futures.ThreadPoolExecutor()
# futures = [executor.submit(t) for t in tasks]
# for t in concurrent.futures.as_completed(futures):
#     if t.result():
#         break
#
#
# # with open('log', 'w+') as file:
# #     file.write(traceback.print_exc())
#
# logger.info("Just an information")




















# import trace
# tracer = trace.Trace()
# # for task in tasks:
# tracer.run('two()')
#
# r = tracer.results()
#
# r.write_results(show_missing=True, coverdir=os.getcwd())






# def one():
#     print('Start 1')
#     time.sleep(1)
#     print('Pierwsza')
#     return True
#
# d = threading.Thread(name='one', target=one)
# d.setDaemon(True)
#
# def two():
#     print('Start 2')
#     time.sleep(3)
#     print('Druga')
#     return False
#
#
# t = threading.Thread(name='two', target=two)
#
# d.start()
# t.start()
#
# d.join()
# t.join()












import requests
import json
import time

HEADERS_UserAgent = {'user-agent': 'HH-User-Agent'} # for query
FIRST_PART_TO_CREATE_URL = 'https://api.hh.ru/' # for create query

start_url_areas = 'https://api.hh.ru/areas'
start_url_specializations = 'https://api.hh.ru/specializations'


# query url
def putData(url):
    return requests.get(url, HEADERS_UserAgent).text


def get_cities(area_id): # area = state
    url_for_query = start_url_areas + f'/{area_id}'
    return requests.get(url_for_query, HEADERS_UserAgent).text

# get count/number of vacancies (return velue of "found" string)
def get_vacanciesF(area_id, specialization_id):
    params_for_create_new_url = {
            'only_with_salary=true', 
            f'area={area_id}', # область
            f'specialization={specialization_id}', # специализация
            'per_page=1', # 1 вакансий на запрашиваемой страничке, не обязательно просм все стр
        }
    url_for_query = FIRST_PART_TO_CREATE_URL + 'vacancies?' + '&' .join(params_for_create_new_url)
    resp = requests.get(url_for_query + f'&page={1}', HEADERS_UserAgent).text
    data = json.loads(resp)
    # print(data)
    for value in data:
        if value == "found":
            return data[value]

# get vacancies
def get_vacancies(page, area_id, specialization_id):
    params_for_create_new_url = {
        'only_with_salary=true', # только те у которых указана зарплата
        f'area={area_id}', # область
        f'specialization={specialization_id}', # специализация
        'per_page=100', # 100 вакансий на запрашиваемой страничке
    }
    url_for_query = FIRST_PART_TO_CREATE_URL + 'vacancies?' + '&' .join(params_for_create_new_url)
    resp = requests.get(url_for_query + f'&page={page}', HEADERS_UserAgent)
    time.sleep(0.2)
    return resp.text

# get currency
def get_currency_rates():
    currencies = requests.get(FIRST_PART_TO_CREATE_URL + 'dictionaries').json()['currency']
    rates = {}
    for currency in currencies:
        rates.update({currency['code']: currency['rate']})
    return rates
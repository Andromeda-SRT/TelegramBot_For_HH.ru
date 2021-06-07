from types import TracebackType
import requests
import time
import json
import sqlite3
import math
import telebot
import tcn

from hhFunctions import putData, get_cities, get_vacanciesF, get_vacancies, get_currency_rates, start_url_areas, start_url_specializations

from fuzzywuzzy import process
from telebot import types

bot = telebot.TeleBot(tcn.TOKEN)


# Part I, Run Bot. Loading of actual reference books
print("\nПодготовка к запуску бота. Заполнение справочников")
mb_city = {} # possible options
mb_spec = {} # possible options
cities = {} # city : id
cities_name = [] # array of cities name
specializations = {} # specialization : id
specializations_name = [] # array of specializations

city_id = "" # choised city
city_str = ""
flag_city = 0
s_id = "" # choised specialization
s_str = ""
flag_spec = 0

# Получение справочника регионов (area)
try:
    print("Получение справочника регионов!")
    data_area = json.loads(putData(start_url_areas))
    areas = {}
    areas_name = [] # array of cities
    #Добавляем их в словарь 
    for area in data_area:
        if (area['parent_id'] == None) and (area['id'] == '113'):
            areas.update({area['name']: area['id']})
            areas_name.append(area['name'])
            for subarea in area['areas']:
                areas.update({subarea['name']: subarea['id']})
                areas_name.append(subarea['name'])
            print(f"Справочник регионов. Было получено: {len(areas)} шт. \r", end="")
        # print(areas)
except requests.RequestException as error:
    print("Справочник регионов не получен. Причина: ", error)
    exit()

# Получение id абсолютно всех городов из справочника регионов
print("\nИзвлечение всех городов России из справочника регионов!")
for key in areas:
    try:
        area_id = areas[key]
        if area_id != "113": # 113 - Россия, пропускаем, нужны только регионы
            data_сity = json.loads(get_cities(area_id)) #/api.hh.ru/areas/parent_id
            for city in data_сity['areas']:
                if city['id'] != area_id and city['parent_id'] != 113:
                    cities.update({city['name']: city['id']})
                    cities_name.append(city['name'])
                print(f"Справочник городов. Было получено: {len(cities)} шт. \r", end="")
        else:
            cities.update({"Москва": "1"})
            cities_name.append("Москва")
            continue
    except requests.RequestException as error:
        print("\nСправочник городов не получен. Причина: ", error)
        exit()

# Получение справочника специализаций
try:
    print("\nПолучение справочника специализаций!")
    data_spec = json.loads(putData(start_url_specializations))
    # Создаём "свой" словарь специализаций, с данными которые мы хотим хранить
    for spec in data_spec:
        specializations.update({spec['name']: spec['id']})
        specializations_name.append(spec['name'])
        for subspec in spec['specializations']:
            specializations.update({subspec['name']: subspec['id']})
            specializations_name.append(subspec['name'])
        print(f"Справочник специализаций. Было получено {len(specializations)} шт. \r", end="")
except requests.RequestException as error:
    print("\nСправочник специализаций не получен. Причина: ", error)
    exit()

print("\nПодготовка к запуску бота. Все нужные справочники были получены!")



# Part II, Connection our DataBase
# create file for main database [city_id, spec_id, max, min, avg]
print("\nПодготовка к запуску бота. Подключение актуальной БД!")
db_file = open(r'C:\Users\Andromeda\PycharmProjects\LR5_OOP\.vs\MainDataBase.db', 'a')
db_file.close()

dbMain = sqlite3.connect(r"C:\Users\Andromeda\PycharmProjects\LR5_OOP\.vs\MainDataBase.db", check_same_thread=False)

curMain = dbMain.cursor()
curMain.execute("""CREATE TABLE IF NOT EXISTS vacanciesRes(
        city_id TEXT,
        spec_id TEXT,
        max INT,
        min INT,
        avg INT);
    """)
dbMain.commit()
print("Подготовка к запуску бота. Актуальная БД подключена!")


# Part III, Run Bot
print("\n >> Запуск бота")
keyboard_txt = types.ReplyKeyboardMarkup(resize_keyboard=True) # объявление клавиатуры для кнопок под полем ввода сообщения
btn1 = types.KeyboardButton('Статистика по вакансиям hh.ru')
btn2 = types.KeyboardButton('Помощь')
keyboard_txt.add(btn1, btn2) # добавление кнопок в клавиатуру


keyboard_message_result = types.InlineKeyboardMarkup(row_width = 3) # объявление клавиатуры в сообщении
xMax= types.InlineKeyboardButton(text="MAX", callback_data="RESMAX")
xMin = types.InlineKeyboardButton(text="MIN", callback_data="RESMIN")
xAvg = types.InlineKeyboardButton(text="AVG", callback_data="RESAVG")
# xAll = types.InlineKeyboardButton(text="OutPutAllInformation", callback_data="RESALL")
keyboard_message_result.add(xMax, xMin, xAvg)



@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, "Привет {0.first_name}! \nЯ, {1.first_name} - бот способный выводить макс. мин и среднее значение ЗП по конкретной специализации и региону.\n Для получения инструкции введи /help или нажми на кнопку 'Помощь', расположенной под строкой ввода сообщения".format(message.from_user, bot.get_me()), reply_markup=keyboard_txt)

@bot.message_handler(commands=['help'])
def help_message(message):
    bot.send_message(message.chat.id, "Как мной пользоваться?\n 1.\tНажми на кнопку «Статистика по вакансиям hh.ru», расположенную под строкой ввода сообщения\n\t2. Введи город,пользуясь подсказками, которые я тебе отправил\n\t3. Выбери специализацию\n\t4. Получи актуальные данные")

@bot.message_handler(content_types=['text'])
def send_messages(message):
    if message.text == 'Статистика по вакансиям hh.ru':
        msg = bot.send_message(message.chat.id, "Введите город")
        bot.register_next_step_handler(msg, choise_city)

    elif message.text == 'Помощь':
        help_message(message)

    elif message.text.lower() == "help":
        help_message(message)

    elif message.text.lower() == "start":
        start_message(message)

    else:
        bot.send_message(message.chat.id, "Я тебя не понимаю. Напиши /help.")

def choise_city(strMessage):
    # Input City
    flag_city = 0
    query_city = strMessage.text
    for key in cities:
        if key == query_city:
            global city_id
            city_id = cities[key]
            global city_str
            city_str = key
            flag_city = 1
    if (flag_city != 1):
        mb_city = process.extract(query_city, cities_name, limit=5)
        # print(mb_city)
        # bot.send_message(strMessage.from_user.id, text=f"Совпадений не найдено! Возможно вы имели ввиду: {mb_city}\nПожалуйста повторите запрос сначала")
        i = 0
        keyboard_message_city = types.InlineKeyboardMarkup(row_width = 1) # объявление клавиатуры в сообщении
        for key, value in mb_city:
            # print(key)
            # Currency = types.InlineKeyboardButton(text=key, callback_data=key)
            globals()['x' + str(i)] = types.InlineKeyboardButton(text=key, callback_data=key)
            i += 1
            if (i == 5): #Самый большой КОСТЫЛЬ в мире
                keyboard_message_city.add(x0, x1, x2, x3, x4)

        bot.send_message(strMessage.from_user.id, text="Совпадений не найдено!\n ->!Пожалуйста начните запрос заново или выберете один из возможных вариантов ниже!<-", reply_markup=keyboard_message_city)
            
    elif (flag_city == 1):
        msg2 = bot.send_message(strMessage.chat.id, "Введите специализацию")
        bot.register_next_step_handler(msg2, choise_spec)
        
    return
        
def choise_spec(strMessage):
    # Input Specialization
    flag_spec = 0
    query_spec = strMessage.text
    for key in specializations:
        if key == query_spec:
            global s_id
            s_id = specializations[key]
            global s_str
            s_str = key
            flag_spec = 1
    if (flag_spec != 1):
        mb_spec = process.extract(query_spec, specializations_name, limit=5)
        # print(mb_city)
        # bot.send_message(strMessage.from_user.id, text=f"Совпадений не найдено! Возможно вы имели ввиду: {mb_city}\nПожалуйста повторите запрос сначала")
        i = 0
        keyboard_message_spec = types.InlineKeyboardMarkup(row_width = 1) # объявление клавиатуры в сообщении
        for key, value in mb_spec:
            # Currency = types.InlineKeyboardButton(text=key, callback_data=key)
            globals()['x' + str(i)] = types.InlineKeyboardButton(text=key, callback_data=key)
            i += 1
            if (i == 5): #Самый большой КОСТЫЛЬ в мире
                keyboard_message_spec.add(x0, x1, x2, x3, x4)

        bot.send_message(strMessage.from_user.id, text="Совпадений не найдено!\n ->!Пожалуйста начните запрос заново или выберете один из возможных вариантов ниже!<-", reply_markup=keyboard_message_spec)   
    elif (flag_spec == 1):
        bot.send_message(strMessage.from_user.id, text="Какие данные вас интересуют?", reply_markup=keyboard_message_result)
        # bot.register_next_step_handler(msg3, output_data)
        print(f"Name: {city_str}, id: {city_id}")
        print(f"Name: {s_str}, id: {s_id}")
    return

@bot.callback_query_handler(func=lambda call: True) # декоратор для обработки выбранного пункта меню в сообщении
def callback_worker(call):
    # print(call)
    query = call.data
    
    # print(query)
    for key in cities:
        if key == query:
            global city_id
            city_id = cities[key]
            global city_str
            city_str = key
            global flag_city
            flag_city = 1
            msg2 = bot.send_message(call.from_user.id, "Введите специализацию")
            bot.register_next_step_handler(msg2, choise_spec)

    for key in specializations:
        if key == query:
            global s_id
            s_id = specializations[key]
            global s_str
            s_str = key
            global flag_spec
            flag_spec = 1
            bot.send_message(call.from_user.id, text="Какие данные вас интересуют?", reply_markup=keyboard_message_result)
            

    if query == "RESMAX" or query == "RESMIN" or query == "RESAVG" or query == "RESMIN" or query == "RESALL":
        print(f"Name: {city_str}, id: {city_id}")
        print(f"Name: {s_str}, id: {s_id}")

        curMain.execute(f"SELECT max, min, avg FROM vacanciesRes WHERE city_id = {city_id} AND spec_id = {s_id};")
        res = curMain.fetchone()
        print(res)
        if res != None:
            if query == "RESMAX":
                curMain.execute(f"SELECT max from vacanciesRes WHERE city_id = {city_id} AND spec_id = {s_id}")
                res = curMain.fetchone()
                print(res)
                bot.send_message(call.from_user.id, f"Максимальная зарплата по специализации {s_str} в городе {city_str} составляет {res} rub")
            if query == "RESMIN":
                curMain.execute(f"SELECT min from vacanciesRes WHERE city_id = {city_id} AND spec_id = {s_id}")
                res = curMain.fetchone()
                print(res)
                bot.send_message(call.from_user.id, f"Минимальная зарплата по специализации {s_str} в городе {city_str} составляет {res} rub")
            if query == "RESAVG":
                curMain.execute(f"SELECT avg from vacanciesRes WHERE city_id = {city_id} AND spec_id = {s_id}")
                res = curMain.fetchone()
                print(res)
                bot.send_message(call.from_user.id, f"Средняя зарплата по специализации {s_str} в городе {city_str} составляет {res} rub")
        elif res == None:
            bot.send_message(call.from_user.id, f"Подождите произвожу расчёты!")
            # create file for data base
            db_file = open(r'C:\Users\Andromeda\PycharmProjects\LR5_OOP\.vs\SubDataBase.db', 'w')
            db_file.close()

            dbQuerys = sqlite3.connect(r"C:\Users\Andromeda\PycharmProjects\LR5_OOP\.vs\SubDataBase.db")

            cur = dbQuerys.cursor()
            cur.execute("""CREATE TABLE IF NOT EXISTS vacancies(
                    Зарплата TEXT,
                    id TEXT);
                """)
            dbQuerys.commit()


            r = get_vacanciesF(city_id, s_id)
            try:
                print("Начинаю заполнение базы данных")

                rates = get_currency_rates()

                page = 0
                item_id = 0

                while True:
                    vac = json.loads(get_vacancies(page, city_id, s_id))
                    pages = vac['pages']
                    found =  r if r<=2000 else 2000

                    for item in vac['items']:
                        if item['salary']['to']:
                            salary = item['salary']['to']
                        else:
                            salary = item['salary']['from']

                        salary /= rates[item['salary']['currency']]
                        salary = math.trunc(salary)

                        vacancy = (salary, item['id'])
                        cur.execute("INSERT INTO vacancies VALUES(?, ?);", vacancy)
                        # db.commit()
                        item_id += 1

                    print(f"Было записанно {item_id} вакансий из {r}(максимально возможных записей {found}). Страницы {page+1} \r", end="")
                    page += 1
                    if page == pages:
                        dbQuerys.commit()
                        break
                    # if page == math.trunc(found/100):
                    #     break

            except requests.RequestException as error:
                print("Неудача в заполнении временной таблицы. Причина: ", error)
                exit()

            print("\nВакансии были загруженны!")

            cur.execute("SELECT max(Зарплата), min(Зарплата), avg(Зарплата) FROM vacancies")
            res = cur.fetchone()

            curMain.execute(f"INSERT INTO vacanciesRes VALUES({city_id}, {s_id}, ?, ?, ?)", res)
            dbMain.commit()

            if query == "RESMAX":
                cur.execute("SELECT max(Зарплата) from vacancies")
                res = cur.fetchone()
                print(res)
                bot.send_message(call.from_user.id, f"Максимальная зарплата по специализации {s_str} в городе {city_str} составляет {res} rub")
            if query == "RESMIN":
                cur.execute("SELECT min(Зарплата) from vacancies")
                res = cur.fetchone()
                print(res)
                bot.send_message(call.from_user.id, f"Минимальная зарплата по специализации {s_str} в городе {city_str} составляет {res} rub")
            if query == "RESAVG":
                cur.execute("SELECT avg(Зарплата) from vacancies")
                res = cur.fetchone()
                print(res)
                bot.send_message(call.from_user.id, f"Средняя зарплата по специализации {s_str} в городе {city_str} составляет {res} rub")

bot.polling(none_stop=False, interval=0)

















# # create file for data base
# db_file = open(r'C:\Users\Andromeda\PycharmProjects\LR5_OOP\.vs\dataBase.db', 'w')
# db_file.close()

# dbQuerys = sqlite3.connect(r"C:\Users\Andromeda\PycharmProjects\LR5_OOP\.vs\dataBase.db")

# cur = dbQuerys.cursor()
# cur.execute("""CREATE TABLE IF NOT EXISTS vacancies(
#         Зарплата TEXT,
#         id TEXT);
#     """)
# dbQuerys.commit()


# if __name__ == '__main__':
#     # Получение справочника регионов (area)
#     try:
#         print("Получение справочника регионов!")
#         data_area = json.loads(putData(start_url_areas))
#         areas = {}
#         areas_name = [] # array of cities
#         #Добавляем их в словарь 
#         for area in data_area:
#             if (area['parent_id'] == None) and (area['id'] == '113'):
#                 areas.update({area['name']: area['id']})
#                 areas_name.append(area['name'])
#                 for subarea in area['areas']:
#                     areas.update({subarea['name']: subarea['id']})
#                     areas_name.append(subarea['name'])
                    
#                 print(f"Справочник регионов. Было получено: {len(areas)} шт. \r", end="")
#                     # time.sleep(0.0001)
#         print("\n")
#         # print(areas)
#     except requests.RequestException as error:
#         print("Справочник регионов не получен. Причина: ", error)
#         exit()

#     # Получение id абсолютно всех городов из справочника регионов
#     cities = {}
#     cities_name = [] # array of cities
#     print(f"Получение справочника городов России!")
#     for key in areas:
#         try:
#             area_id = areas[key]
#             if area_id != "113": # 113 - Россия, пропускаем, нужны только регионы
#                 # print(area_id)
#                 data_сity = json.loads(get_cities(area_id)) #/api.hh.ru/areas/parent_id
#                 for city in data_сity['areas']:
#                     if city['id'] != area_id and city['parent_id'] != 113:
#                         cities.update({city['name']: city['id']})
#                         cities_name.append(city['name'])
#                         # print(cities)
#                         print(f"Справочник городов. Было получено: {len(cities)} наименований городов.\r", end="")
#                         # time.sleep(0.0001)
#             else:
#                 cities.update({"Москва": "1"})
#                 cities_name.append("Москва")
#                 continue
#         except requests.RequestException as error:
#             print("\nСправочник городов не получен. Причина: ", error)
#             exit()

#     # Получение справочника специализаций
#     try:
#         print("\nПолучение справочника специализаций!")
#         data_spec = json.loads(putData(start_url_specializations))
#         specializations = {}
#         specializations_name = [] # array of specializations
#         #Создаём "свой" словарь специализаций, с данными которые мы хотим хранить
#         for spec in data_spec:
#             specializations.update({spec['name']: spec['id']})
#             specializations_name.append(spec['name'])
#             for subspec in spec['specializations']:
#                 specializations.update({subspec['name']: subspec['id']})
#                 specializations_name.append(subspec['name'])
#                 print(f"Справочник специализаций. Было получено: {len(specializations)} шт. \r", end="")
#                 # time.sleep(0.0001)
#     except requests.RequestException as error:
#         print("\nСправочник специализаций не получен. Причина: ", error)
#         exit()


#     # Input City
#     flag_city = 0
#     while (flag_city != 1):
#         print(f'\nВведите город')
#         query_city = input()
#         for key in cities:
#             if key == query_city:
#                 city_id = cities[key]
#                 city_str = key
#                 flag_city = 1
#         if (flag_city != 1):
#             print("Совпадений не найдено! Возможно вы имели ввиду:")
#             mb_city = {}
#             mb_city = process.extract(query_city, cities_name, limit=7)
#             print(mb_city)
    
#     print(f"Name: {city_str}, id: {city_id}")

#     # Input Specialization
#     flag_spec = 0
#     while (flag_spec != 1):
#         print(f'\nВведите специализацию')
#         query_spec = input()
#         for key in specializations:
#             if key == query_spec:
#                 s_id = specializations[key]
#                 s_str = key
#                 flag_spec = 1
#         if (flag_spec != 1):
#             print("Совпадений не найдено! Возможно вы имели ввиду:")
#             mb_spec = {}
#             mb_spec = process.extract(query_spec, specializations_name, limit=7)
#             print(mb_spec)
    
#     print(f"Name: {s_str}, id: {s_id}")

#     r = get_vacanciesF(city_id, s_id)
#     print(f"Найдено {r} вакансий\n Вывести их в:\n\t1. Консоль, \n\t2. Базу данных")
#     ch = input()

#     if ch == '1':
#         print("Для выхода введите q")
#     # if r >= 2000:
#     #     print(f"Будет выведенно 2000 вакансий из {r}")
        
#     #     for i in 20:
#     #         vacan = json.loads(get_vacancies(i, city_id, s_id))

#     # elif r<2000:
#     #     print(f"Будет выведенно {r} вакансий")
#     elif ch=='2':
#         try:
#             print("Начинаю заполнение базы данных")

#             rates = get_currency_rates()

#             page = 0
#             item_id = 0

#             while True:
#                 vac = json.loads(get_vacancies(page, city_id, s_id))
#                 pages = vac['pages']
#                 found =  r if r<=2000 else 2000

#                 for item in vac['items']:
#                     if item['salary']['to']:
#                         salary = item['salary']['to']
#                     else:
#                         salary = item['salary']['from']

#                     salary /= rates[item['salary']['currency']]
#                     salary = math.trunc(salary)

#                     vacancy = (salary, item['id'])
#                     cur.execute("INSERT INTO vacancies VALUES(?, ?);", vacancy)
#                     # db.commit()
#                     item_id += 1

#                 print(f"Было записанно {item_id} вакансий из {r}(максимально возможных записей {found}). Страницы {page+1} \r", end="")
#                 page += 1
#                 if page == pages:
#                     dbQuerys.commit()
#                     break
#                 # if page == math.trunc(found/100):
#                 #     break

#         except requests.RequestException as error:
#             print("Справочник городов не получен. Причина: ", error)
#             exit()

#         print("\nВакансии были загруженны!")
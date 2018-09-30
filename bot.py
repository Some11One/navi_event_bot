import ast
import os

import telebot
from telebot import types

from settings import *
from utils import *

start_count = 0  # count telegram bot users
navi_token = get_token(email, password)  # naviaddress session token
bot = telebot.TeleBot(token)  # telegram bot


@bot.message_handler(commands=["start"])
def start(message):
    global user_state, start_count
    user_state = None
    bot.send_message(message.chat.id, "Добро пожаловать в Navi Event Bot!")
    start_count += 1
    print(start_count)
    menu(message)


@bot.message_handler(commands=["menu"])
def menu(message):
    keyboard_menu = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    keyboard_menu.row('Новое мероприятие', 'Поиск мероприятия')
    keyboard_menu.row('Мои мероприятия', 'Обратная связь')
    bot.send_message(message.chat.id, "Выберите пункт меню:", reply_markup=keyboard_menu)


@bot.message_handler(func=lambda message: message.text == "Поиск мероприятия")
def search_event(m):
    global user_state
    keyboard_hider = types.ReplyKeyboardRemove()
    user_state = 'searching_navi_address'
    bot.send_message(m.chat.id, "Введите NaviAddress:",
                     reply_markup=keyboard_hider)


@bot.message_handler(func=lambda message: user_state == 'searching_navi_address')
def searching_navi_address(m):
    global user_state, navi_container, navi_naviaddress
    user_state = 'searched_address'
    navi_container, navi_naviaddress = m.text.split('_')[0], m.text.split('_')[1]

    navi_route = json.loads(get_naviadress(token, navi_container, navi_naviaddress))

    navi_name = navi_route.get('result').get('name')
    navi_desc = navi_route.get('result').get('description')
    bot.send_message(m.chat.id, "Название: %s" % navi_name)
    if navi_desc != '' and navi_desc is not None:
        navi_desc = ast.literal_eval(navi_desc)
        bot.send_message(m.chat.id, "Ссылка: %s" % navi_desc.get('event_link'))

    navi_steps = navi_route.get('result').get('last_mile')
    if navi_steps is not None:
        navi_steps = navi_steps.get('steps')
        for i, navi_step in enumerate(navi_steps):
            step_text = navi_step.get('text')
            step_image = navi_step.get('image')

            bot.send_message(m.chat.id, 'Шаг %s: %s' % (str(i + 1), step_text))
            bot.send_photo(m.chat.id,
                           photo=open('data/photos/%s/%s' % (navi_container + '_' + navi_naviaddress, step_image),
                                      'rb'))

    keyboard_menu = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    keyboard_menu.row('Регистрация', 'К меню')
    bot.send_message(m.chat.id, "Выберите действие:", reply_markup=keyboard_menu)


@bot.message_handler(func=lambda message: message.text == 'К меню')
def to_menu(m):
    menu(m)


@bot.message_handler(func=lambda message: message.text == 'Регистрация')
def register(m):
    global user_state, navi_container, navi_naviaddress
    keyboard_hider = types.ReplyKeyboardRemove()
    navi_route = json.loads(get_naviadress(token, navi_container, navi_naviaddress))
    navi_desc = navi_route.get('result').get('description')
    if navi_desc != '' and navi_desc is not None:
        navi_desc = ast.literal_eval(navi_desc)
        money = navi_desc.get('event_money')

        if money != "" and int(money) != 0:
            bot.send_message(m.chat.id, 'Оплата за регистрацию', reply_markup=keyboard_hider)
            bot.send_invoice(m.chat.id, 'Билет на мероприятие',
                             'Посещение данного мероприятия платно. Пожалуйтса, оплатите билет.',
                             '67192', payment_token, 'RUB',
                             [types.LabeledPrice(label='Регистрация', amount=int(money))], 'tme')

        else:
            user_state = 'registering'
            bot.send_message(m.chat.id, "Введите имя:", reply_markup=keyboard_hider)

    else:
        user_state = 'registering'
        bot.send_message(m.chat.id, "Введите имя:", reply_markup=keyboard_hider)


@bot.shipping_query_handler(func=lambda query: True)
def shipping(shipping_query):
    print(shipping_query)
    bot.answer_shipping_query(shipping_query.id, ok=True, shipping_options=shipping_options,
                              error_message='Что-то пошло не так. Пожалуйста, попробуйте снова!')


@bot.pre_checkout_query_handler(func=lambda query: True)
def checkout(pre_checkout_query):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True,
                                  error_message="Была произведена защита CVV"
                                                " попробуйте повторно оплатить через несколько минут.")


@bot.message_handler(content_types=['successful_payment'])
def got_payment(m):
    global user_state
    user_state = 'registering'
    bot.send_message(m.chat.id, "Введите имя:")


@bot.message_handler(func=lambda message: user_state == 'registering')
def registering(m):
    global user_name, user_state
    user_name = m.text
    user_state = 'registering_mail'
    bot.send_message(m.chat.id, 'Введите e-mail')


@bot.message_handler(func=lambda message: user_state == 'registering_mail')
def registering_mail(m):
    global user_state, user_name, navi_container, navi_naviaddress, user_mail

    user_mail = m.text
    new_user = "{'user_name':'%s', 'user_mail':'%s'}" % (user_name, user_mail)

    bot.send_message(m.chat.id, "Спасибо за регистрацию!")

    navi_route = json.loads(get_naviadress(token, navi_container, navi_naviaddress))
    result = navi_route.get('result')
    last_mile = result.get('last_mile')
    old_users = last_mile.get('text')

    if old_users is None or old_users == '':
        all_users = "[" + new_user + "]"
    else:
        all_users = ast.literal_eval(old_users)
        all_users.append(new_user)
        all_users = str(all_users)

    last_mile.update({'text': all_users})
    result.update({'last_mile': last_mile})
    navi_route.update({'result': result})

    put_naviadress(navi_token, navi_container, navi_naviaddress, navi_route.get('result'))
    menu(m)


@bot.message_handler(func=lambda message: message.text == 'Оставить комментарий')
def leave_feedback(m):
    global user_state
    keyboard_hider = types.ReplyKeyboardRemove()
    user_state = 'leaving_feedback'
    bot.send_message(m.chat.id, "Введите комментарий:",
                     reply_markup=keyboard_hider)


@bot.message_handler(func=lambda message: user_state == 'leaving_feedback')
def leaving_feedback(m):
    global user_state, navi_container, navi_naviaddress

    feedback = m.text
    user_state = 'leaved_feedback'
    navi_route = json.loads(get_naviadress(token, navi_container, navi_naviaddress))
    result = navi_route.get('result')
    last_mile = result.get('last_mile')
    old_feedback = last_mile.get('text')

    if old_feedback is None or old_feedback == '':
        new_feedback = feedback
    else:
        new_feedback = '\t'.join([old_feedback, feedback])

    last_mile.update({'text': new_feedback})
    result.update({'last_mile': last_mile})
    navi_route.update({'result': result})

    put_naviadress(navi_token, navi_container, navi_naviaddress, navi_route.get('result'))
    menu(m)


@bot.message_handler(func=lambda message: message.text == "Новое мероприятие")
def create_event(m):
    keyboard_hider = types.ReplyKeyboardRemove()
    global user_state, weights
    user_state = 'create_event_name'
    bot.send_message(m.chat.id, "Введите названиие мероприятия",
                     reply_markup=keyboard_hider)


@bot.message_handler(func=lambda message: user_state == 'create_event_name')
def create_event_name(m):
    global user_state, event_name

    event_name = m.text
    print('event_name:', event_name)

    user_state = 'add_event_link'
    bot.send_message(m.chat.id, "Введите ссылку на мероприятие")


@bot.message_handler(func=lambda message: user_state == 'add_event_link')
def add_event_link(m):
    global user_state, event_name, event_link

    event_link = m.text
    print('event_link:', event_link)

    user_state = 'added_event_link'
    keyboard_menu = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    keyboard_menu.row('Да', 'Нет')
    bot.send_message(m.chat.id, "Сделать мероприятие платным?", reply_markup=keyboard_menu)


@bot.message_handler(func=lambda message: message.text == "Да")
def yes_money(m):
    global user_state
    keyboard_hider = types.ReplyKeyboardRemove()
    user_state = 'add_money'
    bot.send_message(m.chat.id, "Введите цену, в рублях", reply_markup=keyboard_hider)


@bot.message_handler(func=lambda message: user_state == 'add_money')
def add_money(m):
    global user_state, event_money
    event_money = str(int(m.text) * 100)
    user_state = "add_location"
    add_location(m)


@bot.message_handler(func=lambda message: message.text == "Нет")
def no_money(m):
    global user_state
    user_state = "add_location"
    add_location(m)


@bot.message_handler(func=lambda message: user_state == 'add_location')
def add_location(m):
    global user_state, event_name

    keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    button_geo = types.KeyboardButton(text="Отправить локацию", request_location=True)
    keyboard.add(button_geo)
    user_state = 'gives_state_location'
    bot.send_message(m.chat.id,
                     "Теперь укажите локацию мероприятия",
                     reply_markup=keyboard)


@bot.message_handler(content_types=['location'])
def def_request_location(m):
    global user_state, navi_container, navi_naviaddress, event_name, event_money, event_link
    user_state = 'step_description'

    bot.send_message(m.chat.id, "Создается NaviAddress. Пожалуйста, подождите.")

    navi_container, navi_naviaddress = create_naviaddress(navi_token, m.location.latitude, m.location.longitude)
    accept_naviaddress(navi_token, navi_container, navi_naviaddress)
    print('navi_container, navi_naviaddress:', navi_container, navi_naviaddress)
    params = {'name': event_name, 'description': "{'event_link':'%s', 'event_money':'%s'}" % (event_link, event_money)}
    put_naviadress(navi_token, navi_container, navi_naviaddress, params)

    keyboard_menu = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    keyboard_menu.row('Добавить шаг', 'Закончить')
    bot.send_message(m.chat.id, "Спасибо! Теперь создадим маршрут", reply_markup=keyboard_menu)


@bot.message_handler(func=lambda message: message.text == "Добавить шаг")
def add_route_step(m):
    keyboard_hider = types.ReplyKeyboardRemove()
    bot.send_message(m.chat.id, "Добавьте описание шага", reply_markup=keyboard_hider)
    global user_state, weights
    user_state = 'add_step_description'


@bot.message_handler(func=lambda message: user_state == 'add_step_description')
def create_event_name(m):
    global user_state, step_description

    user_state = 'step_description'
    step_description = m.text
    bot.send_message(m.chat.id, "Добавьте иллюстрацию шага")


@bot.message_handler(content_types=['photo'])
def handle_photo(m):
    global user_state, navi_container, navi_naviaddress, event_name, step_description, steps, image_counter, event_money, event_link

    fileID = m.photo[-1].file_id
    file = bot.get_file(fileID)
    downloaded_file = bot.download_file(file.file_path)
    navi_dir = 'data/photos/' + navi_container + '_' + navi_naviaddress
    if not os.path.exists(navi_dir):
        os.makedirs(navi_dir)
    with open(navi_dir + '/' + str(image_counter) + '.jpg', 'wb') as new_file:
        new_file.write(downloaded_file)

    step = {'text': step_description, 'image': str(image_counter) + '.jpg', 'image_uuid': str(image_counter)}
    image_counter += 1
    steps.append(step)
    params = {'name': event_name, 'description': "{'event_link':'%s', 'event_money':'%s'}" % (event_link, event_money),
              'last_mile': {'text': '', 'steps': steps}}
    put_naviadress(navi_token, navi_container, navi_naviaddress, params)

    bot.send_message(m.chat.id, "Шаг добавлен!")
    keyboard_menu = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    keyboard_menu.row('Добавить шаг', 'Закончить')
    bot.send_message(m.chat.id, "Добавить еще шаг?", reply_markup=keyboard_menu)


@bot.message_handler(func=lambda message: message.text == "Закончить")
def end_routing(m):
    global user_state, navi_container, navi_naviaddress, event_name, step_description, steps
    bot.send_message(m.chat.id, "Мероприятие создано! NaviAddress: %s" % navi_container + '_' + navi_naviaddress)
    menu(m)


@bot.message_handler(func=lambda message: message.text == "Мои мероприятия")
def event_info(m):
    global user_state
    keyboard_hider = types.ReplyKeyboardRemove()
    user_state = 'searching_event_info'
    bot.send_message(m.chat.id, "Введите NaviAddress:",
                     reply_markup=keyboard_hider)


@bot.message_handler(func=lambda message: user_state == 'searching_event_info')
def searching_event_info(m):
    global user_state, navi_container, navi_naviaddress
    user_state = 'searched_feedback'
    navi_container, navi_naviaddress = m.text.split('_')[0], m.text.split('_')[1]

    navi_route = json.loads(get_naviadress(token, navi_container, navi_naviaddress))

    navi_name = navi_route.get('result').get('name')
    bot.send_message(m.chat.id, "Название: %s" % navi_name)
    bot.send_message(m.chat.id, "Количество зарегистрированных пользователей: ")

    all_users = navi_route.get('result').get('last_mile')
    if all_users is not None:
        all_users = all_users.get('text')
        if all_users is not None:
            if all_users == "":
                bot.send_message(m.chat.id, '0')
            else:
                all_users = ast.literal_eval(all_users)
                all_users_len = len(all_users)
                bot.send_message(m.chat.id, str(all_users_len))

                bot.send_message(m.chat.id, 'Список участников:')
                for user_info in all_users:
                    bot.send_message(m.chat.id,
                                     'Имя: %s, E-mail: %s' % (user_info.get('user_name'), user_info.get('user_mail')))
                    bot.send_message(m.chat.id, '------------------------------------')

    else:
        bot.send_message(m.chat.id, '0')

    menu(m)


@bot.message_handler(func=lambda message: message.text == "Отзывы")
def search_feedback(m):
    global user_state
    keyboard_hider = types.ReplyKeyboardRemove()
    user_state = 'searching_feedback'
    bot.send_message(m.chat.id, "Введите NaviAddress:",
                     reply_markup=keyboard_hider)


@bot.message_handler(func=lambda message: user_state == 'searching_feedback')
def searching_feedback(m):
    global user_state, navi_container, navi_naviaddress
    user_state = 'searched_feedback'
    navi_container, navi_naviaddress = m.text.split('_')[0], m.text.split('_')[1]

    navi_route = json.loads(get_naviadress(token, navi_container, navi_naviaddress))

    navi_name = navi_route.get('result').get('name')
    bot.send_message(m.chat.id, "Название: %s" % navi_name)
    bot.send_message(m.chat.id, "Отзывы: ")

    feedback = navi_route.get('result').get('last_mile').get('text')
    if feedback is not None:
        feedback = feedback.split('\t')

        for f in feedback:
            bot.send_message(m.chat.id, "----------------------")
            bot.send_message(m.chat.id, f)
    else:
        bot.send_message(m.chat.id, 'Отзывов нет.')

    bot.send_message(m.chat.id, "----------------------")
    menu(m)


bot.skip_pending = True
bot.polling(none_stop=True)

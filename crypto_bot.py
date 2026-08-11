from telebot import *
import simple_db
import json 
import configparser
import requests 
import xml.etree.ElementTree as ET
import datetime
import pytz
import os
import sys
from time import sleep
from threading import Thread 
import matplotlib.pyplot as plt  
plt.switch_backend('Agg')
db = simple_db.Simple_DB('database/users.db')
db.create_table('users', 'id INTEGER; subscription BOOL; rang TEXT; activ INTEGER; data TEXT; StartBot TEXT; FIO TEXT; TIMEGMT TEXT')
now = datetime.datetime.now()
db2 = simple_db.Simple_DB('database/crypto_price_' + now.strftime("%Y-%m-%d")+'.db') #
def create_db_prices():
    create_table_request="symbol TEXT; "
    for i in range(1,1728+1,1):
        if i<=1728-1:
            create_table_request+="price"+str(i)+" TEXT DEFAULT \"0\"; "
        if i==1728:
            create_table_request+="price"+str(i)+" TEXT DEFAULT \"0\""
    return create_table_request
db2.create_table('history', create_db_prices()) #
config = configparser.ConfigParser() 
config.read("settings.ini")

bot_api = config["telegram"]["bot_api"]
bot_id = int(config["telegram"]["bot_id"])
group_id = int(config["telegram"]["group_id"])
base_group_id = int(config["telegram"]["base_group_id"])

triger_crypto_signal = int(config["crypto_parser"]["triger_crypto_signal"])
triger_delay_crypto = int(config["crypto_parser"]["triger_delay_crypto"])
delay_commands = float(config["crypto_parser"]["delay_commands"])
crypto_key = config["crypto_parser"]["crypto_key"]
crypto_valutes = config["crypto_parser"]["crypto_valutes"].split(",")
char_code_currency=config["crypto_parser"]["char_code_currency"]
name_file=config["crypto_parser"]["name_file"]

log_error = "" 
crypto_currency = 0 
len_crypto_currency = 0
smile_crypto = ["💰","🎁","🚗","💳","💎","💸","🎯","💻","💼"] 

bot = telebot.TeleBot(bot_api)

with open("database/currency.txt") as file:
    crypto_currency = [row.strip() for row in file]
    len_crypto_currency = len(crypto_currency)


top = types.KeyboardButton('🔥 Топ криптовалют') 
alerts = types.KeyboardButton('🚨 Алерты')   
statistic = types.KeyboardButton('Статистика📊') 
off_ad = types.KeyboardButton('❌ Отключить рассылку')
price = types.KeyboardButton('📈 Курсы валют') 
on_ad = types.KeyboardButton('✅ Включить рассылку')
on = types.ReplyKeyboardMarkup(resize_keyboard = True, row_width=2)
off = types.ReplyKeyboardMarkup(resize_keyboard = True, row_width=2)
group = types.ReplyKeyboardMarkup(resize_keyboard = True, row_width=2)
group.add(top, alerts, price, statistic)
on.add(off_ad,top,price,alerts, statistic)
off.add(on_ad,top,price,alerts, statistic)


delay = {}
statadelay = {}

def crypto_analysis():
    bot = telebot.TeleBot(bot_api)
    while True:
        for currency in crypto_currency:
            with requests.get(crypto_key+currency+"USDT") as response:
                if response.status_code == 200:
                    crypto_data = requests.get(crypto_key+currency+"USDT").json()
                    crypto = [crypto_data['symbol'], crypto_data['price']]    
                    search_crypto = db2.select('history; symbol=\"'+str(crypto[0])+'\"')
                    if search_crypto != []:
                        mask_request_start = "UPDATE history SET symbol=\""+crypto[0]+"\""
                        mask_request_end = " WHERE symbol=\"" + crypto[0] + "\""
                        request_db=""
                        if search_crypto[0][1728-1] != "0" and search_crypto[0][1728-1] != None:
                            db2.close()
                            db.close()
                            file=open('logs/errors.txt', 'a+')
                            file.write("database reset: " + str(search_crypto[0][1728-1]))
                            file.close()
                            os.system("pm2 restart "+name_file)
                        for i in range(1,1728,1):
                            if search_crypto[0][i] == "0":
                                request_db+=",price"+str(i+1)+"=\"0\""
                            else:
                                request_db+=",price"+str(i+1)+"=\""+str(search_crypto[0][i]).rstrip('0')+"\""
                        db2.request(mask_request_start+request_db+mask_request_end)
                        db2.commit()
                        db2.request(mask_request_start+",price1=\""+str(crypto[1]).rstrip('0')+"\""+mask_request_end)
                        db2.commit()
                    if search_crypto!=[]:
                        if float(str(crypto[1]).rstrip('0'))!=0 and search_crypto[0][6]!='0':
                            difference = round(100-float(str(search_crypto[0][6]).rstrip('0'))/float(str(crypto[1]).rstrip('0'))*100,2)
                            print(crypto[0]+" "+str(difference))
                            if difference>triger_crypto_signal or difference<(-triger_crypto_signal):
                                text_post = ["0","0","0"]
                                if difference>triger_crypto_signal:
                                    text_post=["📗","Покупку (Long)📈","выросла"]
                                if difference<(-triger_crypto_signal):
                                    text_post=["📕","Продажу (Short)📉","упала"]
                                    difference=-difference
                                with requests.get(crypto_key+crypto[0]) as response:
                                    if response.status_code == 200:
                                        crypto_data = requests.get(crypto_key+crypto[0]).json()
                                        crypto = [crypto_data['symbol'], crypto_data['price']]    
                                        if db2.select('history; symbol=\"'+crypto[0]+'\"')!=[]:
                                            data = db2.select('history; symbol=\"'+crypto[0]+'\"')[0][1:]
                                            len_data = 0
                                            for i in range(1, len(data)):
                                                if data[i] != '0':
                                                    len_data+=1
                                                else:
                                                    break
                                            price_gr = []
                                            for i in range(0,len_data):
                                                    price_gr.append(float(data[i]))
                                            x = []
                                            for i in range(0,len_data,1):
                                                x.append(i) 
                                            #plt.title(message.text.upper())
                                            plt.style.use('seaborn-v0_8-darkgrid')
                                            plt.plot(x, price_gr)
                                            plt.legend([crypto[0]], loc='best')
                                            plt.gca().invert_xaxis() #plt.yticks(np.arange(min(price_gr), max(price_gr)+float(crypto[1])/100, float(crypto[1])/100))
                                            ax = plt.gca()
                                            ax.axes.xaxis.set_visible(False)
                                            plt.savefig('temp/currency.png', dpi=400, bbox_inches = 'tight', facecolor='lightgrey')
                                            plt.clf()
                                            plt. close()
                                            photo = open('temp/currency.png', 'rb')
                                            bot.send_photo(group_id,photo,"<code>"+crypto[0]+"</code> "+str(text_post[0])+"\n-----------------------\nЦена данной-крипто-валюты " + text_post[2]+" на " +str(difference)+ "%\n\nСделки рассматриваются на <b>" +text_post[1]+ "</b>\n\n💸 Цена: <code>" + str(crypto[1]).rstrip('0')+"</code>$" + "\n\n🕗 1 час назад: <code>"+str(search_crypto[0][12]).rstrip('0')+"</code>$"+"\n🕗 4 часа назад: <code>"+str(search_crypto[0][48]).rstrip('0')+"</code>$"+"\n🕗 12 часов назад: <code>"+str(search_crypto[0][144]).rstrip('0')+"</code>$"+"\n🕗 24 часа назад: <code>"+str(search_crypto[0][228]).rstrip('0')+"</code>$", parse_mode="html")
                                        else:
                                            bot.send_message(group_id,"<code>"+crypto[0]+"</code> "+str(text_post[0])+"\n-----------------------\nЦена данной-крипто-валюты " + text_post[2]+" на " +str(difference)+ "%\n\nСделки рассматриваются на <b>" +text_post[1]+ "</b>\n\n💸 Цена: <code>" + str(crypto[1]).rstrip('0')+"</code>$" + "\n\n🕗 1 час назад: <code>"+str(search_crypto[0][12]).rstrip('0')+"</code>$"+"\n🕗 4 часа назад: <code>"+str(search_crypto[0][48]).rstrip('0')+"</code>$"+"\n🕗 12 часов назад: <code>"+str(search_crypto[0][144]).rstrip('0')+"</code>$"+"\n🕗 24 часа назад: <code>"+str(search_crypto[0][228]).rstrip('0')+"</code>$", parse_mode="html")
                                
                    else:
                        db2.insert('history; symbol,price1; \"'+crypto[0]+'\",\"'+str(crypto[1]).rstrip('0') + "\"")
                        db2.commit()
                        print("новая валюта " + crypto[0])
                else:
                    global log_error
                    print("ошибка! Её создала валюта: " + currency)
                    log_error+=currency+"\n"

                    
        print("задержка " + str(datetime.datetime.now()))
        file=open('logs/errors.txt', 'a+')
        file.write(log_error)
        file.close()
        sleep(triger_delay_crypto*60)
        

def bot():
    bot = telebot.TeleBot(bot_api)
    def after_text_2(message):
        if message.text in ["✅ Включить рассылку", "❌ Отключить рассылку", "📈 Курсы валют", "Статистика📊", "🚨 Алерты", "🔥 Топ криптовалют"] or message.content_type != 'text':
            bot.reply_to(message, "Отменяю...")
            return 0
        with requests.get(crypto_key+message.text.upper()) as response:
            if response.status_code == 200:
                crypto_data = requests.get(crypto_key+message.text.upper()).json()
                crypto = [crypto_data['symbol'], crypto_data['price']]    
                if db2.select('history; symbol=\"'+message.text.upper()+'\"')!=[]:
                    data = db2.select('history; symbol=\"'+message.text.upper()+'\"')[0][1:]
                    len_data = 0
                    for i in range(1, len(data)):
                        if data[i] != '0':
                            len_data+=1
                        else:
                            break
                    price_gr = []
                    for i in range(0,len_data):
                            price_gr.append(float(data[i]))
                    x = []
                    for i in range(0,len_data,1):
                        x.append(i) 
                    #plt.title(message.text.upper())
                    plt.style.use('seaborn-v0_8-darkgrid')
                    plt.plot(x, price_gr)
                    plt.legend([message.text.upper()], loc='best')
                    plt.gca().invert_xaxis() #plt.yticks(np.arange(min(price_gr), max(price_gr)+float(crypto[1])/100, float(crypto[1])/100))
                    ax = plt.gca()
                    ax.axes.xaxis.set_visible(False)
                    plt.savefig('temp/currency.png', dpi=400, bbox_inches = 'tight', facecolor='lightgrey')
                    plt.clf()
                    plt. close()
                    photo = open('temp/currency.png', 'rb')
                    bot.send_photo(message.chat.id,photo, "📒 Цена <code>" + crypto[0] + "</code> на текущий момент равна: <code>" + str(crypto[1]).rstrip('0') + "</code>$"+"\n\n🕗 1 час назад: <code>"+str(data[12]).rstrip('0')+"</code>$"+"\n🕗 4 часа назад: <code>"+str(data[48]).rstrip('0')+"</code>$"+"\n🕗 12 часов назад: <code>"+str(data[144]).rstrip('0')+"</code>$"+"\n🕗 24 часа назад: <code>"+str(data[288]).rstrip('0')+"</code>$", parse_mode="html")
                else:
                    bot.reply_to(message, "📒 Цена <code>" + crypto[0] + "</code> на текущий момент равна: <code>" + str(crypto[1]).rstrip('0') + "</code>$", parse_mode="html")
            else:
                bot.reply_to(message, "🤔 Не было найдено данной валютной пары, попробуйте еще раз")
            
    @bot.message_handler(commands=['start'])
    def handle_start(message):
        sleep(delay_commands)
        if db.select('users; id=\"'+str(message.from_user.id)+'\"') != []:
            if message.chat.id > 0:
                bot.reply_to(message, "*Добрый день, *" + message.from_user.first_name, reply_markup=on, parse_mode="Markdown")
                bot.send_message(message.chat.id, "Это телеграм бот, где ты можешь следить за миром криптовалют\nВыбери что конкретно тебя интересует...")
                db.request('UPDATE users SET StartBot = 1 WHERE id = \"'+str(message.from_user.id)+"\"")
                db.commit()

            else:
                bot.reply_to(message, "*Добрый день, *" + message.from_user.first_name,reply_markup=group, parse_mode="Markdown")
                bot.send_message(message.chat.id, "Это телеграм бот, где ты можешь следить за миром криптовалют\nВыбери что конкретно тебя интересует...")

        else:
            no_subscription_photo = open('images/no_subscription.jpg', 'rb')
            bot.send_photo(message.chat.id,no_subscription_photo, "Похоже, вы не участник крипто сообщества. Для работы с функционалом бота получите подписку у администратора: @frog773") 
    @bot.message_handler(func=lambda message: True, content_types=['text', 'photo', 'video'])
    def echo_all(message):
        sleep(delay_commands)
        if message.text == None:
            message.text = "ㅤ"
            print("без текста")
        else:
            if message.chat.id == group_id or message.chat.id == base_group_id:
                print(message.text)
            else:
                print("не в группе: "+message.text+" "+str(message.from_user.id))
        if db.select('users; id=\"'+str(message.from_user.id)+'\"') != []:
            if message.from_user.id > 0:
                if db.select('users; id=\"'+str(message.from_user.id)+'\"') != []:
                    if message.chat.id==group_id or message.chat.id==base_group_id:
                        db.request('UPDATE users SET activ = activ + 1 WHERE id = \"'+str(message.from_user.id)+"\"")
                        db.commit()
                if message.text == "❌ Отключить рассылку":
                    if message.chat.id > 0:
                        db.update('users; subscription; \"0\"; id=\"'+str(message.chat.id)+'\"')
                        db.commit()
                        bot.reply_to(message, "Вы отключили перессылку важных объявлений",reply_markup=off) 
                if message.text == "✅ Включить рассылку":
                    if message.chat.id > 0:  
                        db.update('users; subscription; \"1\"; id=\"'+str(message.chat.id)+'\"')
                        db.commit()
                        bot.reply_to(message, "Вы включили перессылку важных объявлений",reply_markup=on)
                if message.text.lower() in ["статистика📊","статистика","стата"]:
                    s_firstname = 0
                    s_id = 0
                    current_time = time.time()  
                    if message.from_user.id in statadelay:
                        elapsed_time = current_time - statadelay[message.from_user.id]
                        if elapsed_time < 2:  
                            remaining_time = 2 - elapsed_time
                            bot.send_message(message.chat.id, f"Подождите, перед выполнением команды.")
                            return
                        statadelay[message.from_user.id] = current_time
                    if message.reply_to_message:
                            if message.reply_to_message.from_user.id == bot_id:
                                s_firstname = str(message.from_user.first_name)
                                s_id = str(message.from_user.id)
                            else: 
                                s_firstname = str(message.reply_to_message.from_user.first_name)
                                s_id = str(message.reply_to_message.from_user.id)
                    else:
                        s_firstname = str(message.from_user.first_name)
                        s_id = str(message.from_user.id)
                    profile_photos = bot.get_user_profile_photos(s_id)
                    if profile_photos == None:
                        photo = None
                    else:
                        if profile_photos.total_count > 0:
                            photo = profile_photos.photos[0][-1].file_id
                        else:
                            photo = None
                    if db.select('users; id=\"'+str(s_id)+'\"') != []:
                        user = db.select('users; id=\"'+str(s_id)+'\"')[0]
                        people = db.request("SELECT COUNT(*) FROM users")[0][0]
                        statistic_photo=0
                        if photo == None:
                            statistic_photo = open('images/statistic.jpg', 'rb')
                        else:
                            statistic_photo = photo
                        bot.send_photo(message.chat.id,statistic_photo, "👤 " + s_firstname + "\n🆔 `@" + str(s_id) + "`\n📊 Активность: " + str(user[3]) + " (от _" +user[4]+ "_)\n\n🥇 *" + user[2] + "*\n\nВсего в клубе: " + str(people), parse_mode="Markdown")
                        statadelay[message.from_user.id] = current_time
                if message.text == "📈 Курсы валют" or message.text.lower() == "курс" or message.text.lower() == "курсы" or message.text.lower() == "графики":
                    msg = bot.send_message(message.chat.id, '💸 Напишите название криптовалютной пары \n*(Пример: BTCUSDT)* ', parse_mode="Markdown")
                    bot.register_next_step_handler(msg, after_text_2)
                if message.text.lower()[:7] == "+право ":
                    id=message.text.lower()[7:]
                    if db.select('users; id=\"'+str(message.from_user.id)+'\"')[0][2] == "Администратор":
                        if id!=None and id.isnumeric():
                            if db.select('users; id=\"'+id+'\"') == []:
                                current_date = datetime.datetime.now().strftime('%d.%m.%Y')
                                db.insert('users; id,subscription,rang,activ,data,StartBot; \"'+message.text.lower()[7:]+'\" 1\" Участник\" 0\" ' + current_date + "\"" + " 0\"")
                                db.commit()
                                bot.reply_to(message, "➕ Успешно добавлен участник") 
                        else:
                            bot.reply_to(message, "Укажите id пользователя") 
                    else:
                        bot.reply_to(message, "У вас недостаточно прав ❌")
                if message.text == "🚨 Алерты":
                    bot.send_message(message.chat.id,"👨‍💼 Я могу дать сигнал, когда цена инструмента достигнет заданного уровня. Такой сигнал называется \"алерт\"")
                    sleep(0.6)
                    bot.send_message(message.chat.id,"💤 Функция в разработке...")
                if message.text.lower()[:7] == "-право ":   
                    id=message.text.lower()[7:]
                    if db.select('users; id=\"'+str(message.from_user.id)+'\"')[0][2] == "Администратор":
                        if id!=None and id.isnumeric():
                            if db.select('users; id=\"'+id+'\"') != []:
                                if db.select('users; id=\"'+id+'\"') != "Администратор":
                                    db.delete('users; id=\"'+id+'\"')
                                    bot.reply_to(message, "Пользователь удален из участников")
                                else:
                                    bot.reply_to(message, "Участник является Администратором")
                            else:
                                bot.reply_to(message, "Этот пользователь не участник сообщества")
                    else:
                        bot.reply_to(message, "У вас недостаточно прав ❌")
                if message.text.lower() == "пинг":
                    bot.reply_to(message, "Понг 🏓", parse_mode='Markdown')
                if message.text.lower() in ["/id","айди","id"]:
                    m_id = 0
                    m_us = 0
                    if message.reply_to_message:
                        m_id = str(message.reply_to_message.from_user.id)
                        m_us = message.reply_to_message.from_user.username
                    else:
                        m_id = str(message.from_user.id)
                        m_us = message.from_user.username
                    if m_us == None:
                        m_us="Нету"
                    else:
                        m_us="@"+m_us
                    bot.reply_to(message, "👤 " + m_us +  "\n🆔 <code>" + m_id + "</code>\n\n💬 <b>Чат </b><code>" + str(message.chat.id) + "</code>" , parse_mode="HTML", disable_web_page_preview=True)
                if message.text.lower() == "!объявление":
                    if db.select('users; id=\"'+str(message.from_user.id)+'\"')[0][2] == "Администратор":
                        if message.reply_to_message:
                            reply_message = message.reply_to_message
                            if reply_message.text:
                                bot.send_message(group_id, reply_message.text)
                            elif reply_message.photo:
                                photo_id = reply_message.photo[-1].file_id
                                caption = reply_message.caption if reply_message.caption else ""
                                bot.send_photo(group_id, photo_id, caption=caption)
                            elif reply_message.video:
                                caption = reply_message.caption if reply_message.caption else ""
                                bot.send_video(group_id, reply_message.video.file_id, caption=caption)
                        else:
                            bot.reply_to(message, "Ответьте на сообщение, которое хотите опубликовать")


                if message.text.lower() in ["кто участник","!участники","!спуч","все"]:
                    if db.select('users; id=\"'+str(message.from_user.id)+'\"')[0][2] == "Администратор":
                        users = db.request("SELECT * FROM users")
                        people = db.request("SELECT COUNT(*) FROM users")[0][0]
                        users_text = '📕 Пользователи, которым предоставлен доступ к боту. Всего в клубе: '+str(people)+'\n\n'
                        for elem in users:
                            users_text += '👨 <a href="tg://user?id='+str(elem[0])+'">Перейти на пользователя</a>\n🆔 <code>'+str(elem[0])+'</code>\n📊 Активность: ' + str(elem[3]) + ' (от <i>' +elem[4]+ '</i>)\n🪪 Ранг: '+elem[2]+'\n\n'
                        bot.reply_to(message, users_text, parse_mode="HTML", disable_web_page_preview=True)
                    else:
                        bot.reply_to(message, "У вас недостаточно прав ❌")


                if message.text.lower() == "!опубликовать":
                    if db.select('users; id=\"'+str(message.from_user.id)+'\"')[0][2] == "Администратор":
                        if message.reply_to_message:
                            usdb = db.request('select id from users')
                        else:
                            bot.reply_to(message, "У вас недостаточно прав ❌")
                                
                            reply_message = message.reply_to_message
                            for i in usdb:
                                try:
                                    if db.select('users; id=\"'+str(i[0])+'\"')[0][1] == 1 and db.select('users; id=\"'+str(i[0])+'\"')[0][5] == 1:
                                        if reply_message.text:
                                            bot.send_message(i[0], reply_message.text)
                                        elif reply_message.photo:
                                            photo_id = reply_message.photo[-1].file_id
                                            caption = reply_message.caption if reply_message.caption else ""
                                            bot.send_photo(i[0], photo_id, caption=caption)
                                        elif reply_message.video:
                                            caption = reply_message.caption if reply_message.caption else ""
                                            bot.send_video(i[0], reply_message.video.file_id, caption=caption)
                                    
                                except Exception as e:
                                    bot.reply_to(message, "Не удалось отправить сообщение для: " + str(i[0]))
                    else:
                        bot.reply_to(message, "У вас недостаточно прав ❌")
                
                if message.text == "🔥 Топ криптовалют" or message.text.lower() == "!ткп":
                    current_time = time.time()  
                    if message.from_user.id in delay:
                        elapsed_time = current_time - delay[message.from_user.id]
                        if elapsed_time < 5:  
                            remaining_time = 5 - elapsed_time
                            bot.send_message(message.chat.id, f"Подождите, перед выполнением команды.")
                            return
                        delay[message.from_user.id] = current_time
                    msg = bot.send_message(message.chat.id, "ℹ Ожидайте. Операция выполняется", parse_mode="HTML")
                    delay[message.from_user.id] = current_time
                    answer_text = "🔥 <b>Топ популярных крипто-валют:</b>\n\n"
                    for i in range(0,len(crypto_valutes),1):
                        with requests.get(crypto_key+crypto_valutes[i]) as response:
                            if response.status_code == 200:
                                crypto_data = requests.get(crypto_key+crypto_valutes[i]).json()
                                crypto = [crypto_data['symbol'], crypto_data['price']]    
                                answer_text +=smile_crypto[i] +" "+ "<code>"+crypto[0]+"</code> — Цена: <code>"+ str(crypto[1]).rstrip('0')+"</code>$\n\n"
                            else:
                                bot.edit_message_text("Произошла ошибка!", message.chat.id, message_id=msg.message_id, parse_mode="HTML")

                    MSK_time = datetime.datetime.now(pytz.utc).astimezone(pytz.timezone('Europe/Moscow')).strftime('%H:%M:%S')
                    currency=ET.fromstring(requests.get('https://www.cbr.ru/scripts/XML_daily.asp').text).find('./Valute[CharCode="USD"]/Value').text.replace(',', '.')
                    answer_text+="💼 <code>USDRUB</code> — Цена: <code>"+currency+"</code>₽\n\n• "+str(MSK_time)+" - последние обновление"
                    update = types.InlineKeyboardMarkup()
                    updatebutton = types.InlineKeyboardButton(text="Обновить данные ✅", callback_data='upd')
                    update.add(updatebutton)
                    bot.edit_message_text(answer_text, message.chat.id, message_id=msg.message_id, parse_mode="HTML",reply_markup=update)
                    delay[message.from_user.id] = current_time
    @bot.callback_query_handler(func=lambda call: True)
    def callback_query(call):
        if call.data == 'upd':
            update = types.InlineKeyboardMarkup()
            updatebutton = types.InlineKeyboardButton(text="Обновить данные ✅", callback_data='upd')
            update.add(updatebutton)
            answer_text = "🔥 <b>Топ популярных крипто-валют:</b>\n\n"
            for i in range(0,len(crypto_valutes),1):
                with requests.get(crypto_key+crypto_valutes[i]) as response:
                    if response.status_code == 200:
                        crypto_data = requests.get(crypto_key+crypto_valutes[i]).json()
                        crypto = [crypto_data['symbol'], crypto_data['price']]    
                        answer_text +=smile_crypto[i] +" "+ "<code>"+crypto[0]+"</code> — Цена: <code>"+ str(crypto[1]).rstrip('0')+"</code>$\n\n"
                    else:
                        bot.answer_callback_query(call.id, show_alert=True, text="Произошла ошибка!")
            MSK_time = datetime.datetime.now(pytz.utc).astimezone(pytz.timezone('Europe/Moscow')).strftime('%H:%M:%S')
            currency=ET.fromstring(requests.get('https://www.cbr.ru/scripts/XML_daily.asp').text).find('./Valute[CharCode="USD"]/Value').text.replace(',', '.')
            answer_text+="💼 <code>USDRUB</code> — Цена: <code>"+currency+"</code>₽\n\n• "+str(MSK_time)+" - последние обновление"
            bot.edit_message_text(answer_text, chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=update)



    bot.polling(none_stop=True)

t1 = Thread(target=crypto_analysis)
t2 = Thread(target=bot)


def restart_on_error():
    global t1,t2
    while True:
        if not t1.is_alive():
            print("error! T1 is die, restarting")
            t1 = Thread(target=crypto_analysis)
            t1.start()
        if not t2.is_alive():
            print("error! T2 is die, restarting")
            t2 = Thread(target=bot)
            t2.start()
        sleep(5)
t3 = Thread(target=restart_on_error)

t1.start()
t2.start()
t3.start()
t2.join()

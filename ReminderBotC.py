import sys
import threading

import time

import ReminderBotCHTTP
import ReminderBotCSQL
import ReminderBotCRE
from datetime import (datetime, timedelta)


# ***************************************************************
# ***************************************************************
# THREADS

# CYCLE THREAD
def CycleThread():
    """Thread for the main cycle of bot work"""
    global stop_cycle, cycle_period
    while not stop_cycle:
        if RunCycleTimerAction() != 0:
            stop_cycle = True
            print('\n->  Main cycle is stopped.')
            return 1

        time.sleep(cycle_period)

    print('\n->  Main cycle is stopped.')
    return 0

# ***************************************************************
# ***************************************************************
# FUNCTIONS


# STOP CYCLE
def StopCycle(error_text='->  Error. Stoping cycle.', db_connection=None ):
    """Stopping main cycle with bot work"""
    global stop_cycle
    SaveTokenAndUpdateNum()
    print(error_text)
    stop_cycle = True
    if db_connection is not None:
        db_connection.close()
    return 0


# READ TOKEN AND LAST UPDATE FROM FILE
def ReadTokenAndUpdateNum():
    """Reading bot token and last update number from bot.info file"""
    global bot_token, curr_update_num
    with open('bot.info', 'r') as bot_info_file:
        bot_token = bot_info_file.readline().strip()
        curr_update_num = int(bot_info_file.readline().strip())

    return 0


# SAVE TOKEN AND LAST UPDATE TO FILE
def SaveTokenAndUpdateNum():
    """Saving bot token and last update number to bot.info file"""
    global bot_token, curr_update_num
    with open('bot.info', 'r') as bot_info_file:
        bot_token = bot_info_file.readline().strip()
    with open('bot.info', 'w') as bot_info_file:
        bot_info_file.write(bot_token + '\n')
        bot_info_file.write(str(curr_update_num))

    return 0


# CHECK TOKEN BY SENDING SPECIAL REQUEST
def TestBotToken():
    """Sending a request to test the token to be valid"""
    global bot_token, curr_update_num
    print('\n->  Sending "getMe" request with current token.')
    if len(bot_token) == 0:
        print("""->  Error: can't send "getMe" request as current token is empty.""")

    else:
        print("->  The answer:")
        [result, decoded_answer] = ReminderBotCHTTP.GetMeRequest(bot_start_URL, bot_token)
        if result == 1:     # EXCEPTION OCCURED
            print('->  An error has occurred during "getMe" request: ' + decoded_answer)
        else:               # NO EXCEPTIONS
            print(str(decoded_answer))
            if decoded_answer['ok'] is True:
                print("\n->  Result: check is complete successful.")


# SEND MESSAGE TO CHAT
def SendMessageToChatOrStop(chat_id, text, db_connection=None, parse_mode='HTML', startURL=None, token=None):
    """Sending message to chat with logging of process"""
    global bot_start_URL, bot_token
    if startURL is None:
        startURL = bot_start_URL

    if token is None:
        token = bot_token

    while True:
        [result, decoded_answer, error_code] = ReminderBotCHTTP.SendMessageToChat(chat_id, text, parse_mode, startURL, token)
        if result == 1:
            if error_code[0] != '5':
                StopCycle('->  An error has occurred during "sendMessage" request: ' + decoded_answer, db_connection)
                return 1
            else:
                print('->  Server error while sending message: ' + decoded_answer +
                      '\nTrying to reconnect in 10 seconds.')
                time.sleep(10)
                continue

        else:
            return 0


# CHANGE THE STATE OF THE SOURCE
def ChangeSourceStateOrStop(source_id, db_connection, new_state):
    """Changing the source <source_id> state to <new_state> through <db_connection>"""
    if ReminderBotCSQL.ChangeSourceState(source_id, db_connection, new_state) != 0:
        StopCycle("->  Error changing source " + str(source_id) + " state to " + str(new_state) +
                  " through DB connection.", db_connection)
        return 1

    return 0


# GET LAST REMINDED NOTE OF THE SOURCE
def GetLastRemindedNoteOrStop(update_source_id, db_conn, db_connection=None):
    """Getting last note of the source that was reminded in last 30 minutes"""
    note = ReminderBotCSQL.GetLastRemindedNoteOfSource(update_source_id, db_conn)
    if note == -1:
        StopCycle('->  Error getting last reminded note from DB.', db_connection)
        return -1

    if note == -2:
        return 0

    return note


# SHOW ALL SOURCES
def ShowAllSource():
    """Getting all registered in BD sources and printing them"""
    sources = ReminderBotCSQL.GetAllSources(db_filename)
    if sources == -1:
        print('->  Error while printing current content of Sources table. Details see above.')
        return -1

    else:
        print('\n->  Current Sources table content:'
              '\nID, TYPE (1 - chat, 2 - channel), SOURCE (ID), STATE (1 - after /save, 2 - after /delay, '
              '3 - after /remind) LANG (language):')
        for source in sources:
            print(str(source[0]) + '  ' + str(source[1]) + '  ' + str(source[2]) + '  ' + str(source[3]) + '  '
                  + str(source[4]))

        return 0


# SHOW ALL NOTES
def ShowAllNotes():
    """Getting all registered in DB notes and printing them"""
    notes = ReminderBotCSQL.GetAllNotes(db_filename)
    if notes == -1:
        print('->  Error while printing current content of Notes table. Details see above.')
        return 1
    else:
        print('\n->  Current Notes table content:'
              '\nID, SOURCE (ID), YEAR.MONTH.DAY HOUR:MINUTE, TEXT, REMINDED (0 - no, 1 - yes):')
        for note in notes:
            print(str(note[0]) + '  ' + str(note[1]) + '  ' + str(note[2]) + '.' + str(note[3]) + '.'
                  + str(note[4]) + ' ' + str(note[5]) + ':' + str(note[6]) + '  ' + str(note[7]) + '  '
                  + str(note[8]))
        return 0


# SHOW STATISTICS
def ShowStats():
    """Getting statistics from DB table with same name and printing it"""
    stats = ReminderBotCSQL.GetStats(db_filename)
    if stats == -1:
        print('->  Error while printing statistics. Details see above.')
        return 1

    else:
        print('\n->  Current statistics.'
              '\n- total amount of registered chats: ' + str(stats[0][1]) +
              '\n- total amount of registered notes: ' + str(stats[0][2]))
        return 0


# CLEAR SOURCES TABLE
def ClearSourcesTable():
    """Clearing table, containing sources data"""
    if ReminderBotCSQL.ClearSourcesTable(db_filename) != 0:
        print('->  Error while erasing Sources table.')
        return 1

    else:
        print('\n->  Sources table erased successfully.')
        return 0


# CLEAR NOTES TABLE
def ClearNotesTable():
    """Clearing table, containing notes data"""
    if ReminderBotCSQL.ClearNotesTable(db_filename) != 0:
        print('->  Error while erasing Notes table.')
        return 1

    else:
        print('\n->  Notes table erased successfully.')
        return 0


# SAVE TEXT TO CERTAIN LOG FILE
def SaveToLog(text, log_file_name):
    """Appending text to the certain log file"""
    with open(log_file_name, 'a') as log_file:
        log_file.write('\n' + text)
    return 0


# ***************************************************************
# ***************************************************************
# EVENTS


# THE RUN CYCLE TIMER ACTION
def RunCycleTimerAction():
    """The action of main run cycle timer with bot work"""
    global bot_token, curr_update_num
    # CALCULATING SERVER UTC OFFSET
    ts = time.time()
    utc_offset = str(round((datetime.fromtimestamp(ts) -
                  datetime.utcfromtimestamp(ts)).total_seconds()/3600))
    if utc_offset[0] != '-':
        utc_offset = '+' + utc_offset

    # REQUESTING UPDATES
    if len(bot_token) == 0:
        StopCycle("""\n->  Can't send "getUpdate" request as current token is empty.""")
        return 1

    while True:
        [result, decoded_answer, error_code] = ReminderBotCHTTP.SendGetUpdatesRequest(curr_update_num + 1, 100, 2, bot_token)
        if result == 1:         # IF AN EXCEPTION OCCURED
            if error_code[0] != '5':
                StopCycle('->  An error has occurred during "getUpdates" request: ' + decoded_answer)
                return 1

            else:
                print('->  Server error while sending message: ' + decoded_answer +
                      '\nTrying to reconnect in 10 seconds.')
                time.sleep(10)
                continue

        else:
            break

    # IF NO EXCEPTIONS
    db_connection = ReminderBotCSQL.ConnectToDB(db_filename, None)
    # PREPARING MESSAGES ON TWO LANGUAGES
    help_message = ('Hi, I am the <b>reminder bot</b>! And I am at your service. Note, that '
                    'my UTC time offset is ' + utc_offset + '\n'
                    'You can send me next commands:\n'
                    '/help - for getting this help message,\n'
                    '/show - to see all your notes I still remember,\n'
                    '/remind - to save a note that I will remind after entered period of time,\n'
                    '/save - to save a note that I will remind you at specified time (take into '
                    'account my time offset),\n'
                    '/delay - to delay last note reminded by me not longer ago then 30 min.\n'
                    'You can type that commands manually without "/" symbol.',
                    'Привет, я - <b>reminder bot</b> (бот для напоминаний)! И я к Вашим услугам.\n'
                    'Обратите внимание, что мой часовой пояс ' + utc_offset + '\n'
                    'Вы можете использовать следующие комманды:\n'
                    '/help - чтобы получить данное информационное сообщение,\n'
                    '/show - чтобы увидеть, какие Ваши памятки я еще помню,\n'
                    '/remind - чтобы сохранить памятку, которую я напомню через заданное время,\n'
                    '/save - чтобы сохранить памятку, которую я напомню в определенное время ('
                    'учтите мой часовой пояс),\n'
                    '/delay - чтобы отложить памятку, которую я напомнил не далее, чем 30 минут назад.\n'
                    'Вы также можете ввести эти команды вручную без символа "/".')

    show_nosaved_message = ('You have no saved not-reminded notes to show. '
                            'Use /help to get help with list of all commands.',
                            'У Вас нет сохраненных памяток. Используйте /help для '
                            'получения списка доступных комманд')

    show_saved_message = ('Your saved notes are:', 'Ваши сохраненные памятки:')

    show_reminded_message = (' (reminded)', ' (уже напомненное)')

    remind_message = ('Enter the note to remind in format:\n<i>minutes hours days months years note_text</i>\n'
                      'where minutes, hour and up to year - are number parameters (1-2 digits), that can be '
                      'ommited from the end to start except minutes,\n'
                      'text length must be at least 3 characters.\n'
                      'Example: "15 2 Call mom" - will remind to call mom in 2 hours and 15 minute,\n'
                      'Example: "0 0 0 1 1 Change driver licence" - will remind to change driver '
                      'licence after 1 year and 1 month.',
                      'Введите памятку для напоминания в формате:\n'
                      '<i>минуты часы дни месяцы годы текст_памятки</i>\n'
                      'где минуты, часы и так до годов - числовые параметры (1-2 цифры), которые могут быть '
                      'опущены начиная с конца, кроме минут,\n'
                      'длинна текста должна быть не менее 3 символов.\n'
                      'Пример: "15 2 Позвонить маме" - напомнит Вам позвонить маме через 2 часа и 15 минут,\n'
                      'Пример: "0 0 0 1 1 Заменить права" - напомнит Вам заменить права через 1 год и 1 месяц.')

    remind_invalid_message = ('The entered note does not match the format: <i>m h D M Y note_text</i>\nPlease,'
                              'try again. You can use /remind to see the description of format or /help for help.',
                              'Введенная памятка не соответствует формату: <i>м ч Д М Г текст_памятки</i>\nПожалуйста, '
                              'попробуйте еще раз. Вы можете использовать команду /remind для получения описания '
                              'формата или /help для получения списка доступных команд.')

    remind_success_message = ('Your note has been saved. I will kindly remind it to you on ',
                              'Выша памятка сохранена. И напомню ее вам ')

    save_message = ('Enter the note to remind in format: <i>YYYY.MM.DD hh:mm note_text</i>\n'
                    'or <i>hh:mm note_text</i>\n'
                    'where YYYY.MM.DD hh:mm - date and time to remind the text (without date - today time):\n'
                    'YYYY - 4 digits of the year\n'
                    'MM - 2 digits of the month\n'
                    'DD - 2 digits of the day\n'
                    'hh - 2 digits of the hour\n'
                    'mm - 2 digits of the minutes.\n'
                    'Text length must be at least 3 characters.\n'
                    'Example: "2018.08.16 15:20 Final game"',
                    'Введите памятку для напоминания в формате: <i>ГГГГ.ММ.ДД чч:мм текст_памятки</i>\n'
                    'или <i>чч:мм текст_памятки</i>\n'
                    'где ГГГГ.ММ.ДД чч:мм - дата и время, когда нужно напомнить памятку (не указанная дата принимается '
                    'сегодняшним днем):\n'
                    'ГГГГ - 4 цифры года\n'
                    'ММ - 2 цифры месяца\n'
                    'ДД - 2 цифры дня\n'
                    'чч - 2 цифры часа\n'
                    'мм - 2 цифры минут.\n'
                    'Длинна текста должна быть не менее 3 символов.\n'
                    'Пример: "2018.08.16 15:20 Финальная игра"')

    save_invalid_message = ('The entered note does not match the format: <i>YYYY.MM.DD hh:mm note_text</i> or <i>hh:mm '
                            'note_text</i>.\nPlease,'
                            'try again. You can use /save to see the description of format or /help for help.',
                            'Введенная памятка не соответствует формату: <i>ГГГГ.ММ.ДД чч:мм текст_памятки</i> или '
                            '<i>чч:мм текст_памятки</i>.\nПожалуйста, попробуйте еще раз. Вы можете использовать '
                            'команду '
                            '/save для получения описания формата или /help для получения списка доступных команд.')

    save_success_message = ('Your note has been saved. I will kindly remind it to you on time. Use /help for help.',
                            'Ваша памятка сохранена. Я любезно напомню ее Вам, когда придет время. Используйте '
                            '/help для получения списка доступных команд.')

    save_shorttext_message = ('Your note text is too short (less then 3 symbols). Please,'
                              'try again. You can use /save to see the description of format or /help for help.',
                              'Текст Вашей памятки слишком коротки (меньше 3 символов). Пожалуйста, '
                              'попробуйте еще раз. Вы можете использовать команду /save для получения описания формата '
                              'или /help для получения списка доступных команд.')

    delay_norecent_message = ('You have no recently reminded note to delay (no notes where reminded last 30 minutes). '
                              'Use /save command first to save a note or /help for help.',
                              'К сожалению, я Вам ничего недавно не напоминал (нет напомненных памяток за '
                              'последние 30 минут. Используйте сначала команду /save для сохранения памяток '
                              'или /help для получения списка доступных команд.')

    delay_message = ('Enter the delay period in format:\n' 
                     '<i>YYYY.MM.DD hh:mm</i> (date and time to remind again) or <i>hh:mm</i> '
                     '(time gap to delay from current moment)\nwhere:\n'
                     'YYYY - 4 digits of the year\n'
                     'MM - 2 digits of the month\n'
                     'DD - 2 digits of the day\n'
                     'hh - 2 digits of the hour\n'
                     'mm - 2 digits of the minutes.\n'
                     'Example: "2018.09.22 15:40" or "02:30".\n'
                     'Next message will be delayed:\n"',
                     'Введите период, на который Вы хотите отложить памятку, в формате:\n'
                     '<i>ГГГГ.ММ.ДД чч:мм</i> (дата и время для повторного напоминания) или <i>чч:мм</i> '
                     '(отсрочка повторного напоминания от текущего момента)\n'
                     'где:'
                     'ГГГГ - 4 цифры года\n'
                     'ММ - 2 цифры месяца\n'
                     'ДД - 2 цифры дня\n'
                     'чч - 2 цифры часа\n'
                     'мм - 2 цифры минут.\n'
                     'Пример: "2018.09.22 15:40" или "02:30".\n'
                     'Будет повторно напомнена следующая памятка:\n"')

    delay_invalid_message = ('The entered delay does not match the format:\n'
                             '<i>YYYY.MM.DD hh:mm</i> or <i>hh:mm</i>\n'
                             'Please, try again. You can use /delay to see the description of format or /help for help.',
                             'Введенный период отсрочки не соответствует формату:\n'
                             '<i>ГГГГ.ММ.ДД чч:мм</i> или <i>чч:мм</i>\n'
                             'Пожалуйста, попробуйте еще раз. Вы можете использовать команду /delay для получения '
                             'описания формата или /help для получения списка доступных команд.')

    delay_notavailable_message = ('Your last note is no longer available to delay. You can delay a note not' 
                                  'longer then next 30 minutes after it has been reminded. Use /help for help.',
                                  'Ваша последняя памятка более недоступна для отсрочки. Вы можете отсрочить '
                                  'памятку, которую я напомнил не более 30 минут назад. Используйте /help для '
                                  'получения списка доступных команд.')

    delay_success_message1 = ('Your note\n"', 'Ваша памятка\n"')

    delay_success_message2 = ('"\nhas been delayed. Use /help for help.',
                              '"\nотложена. Используйте /help для получения списка доступных команд.')

    time_message = ('Server time is: ', 'Серверное время: ')

    author_message = ('Developed by Mikhail BRUNMAN -Taimish- (C) 2018', 'Разработал: Брунман Михаил -Taimish- (C) 2018')

    ending_message = ('\nUse /help for help.', '\nИспользуйте /help для получения списка доступных команд.')

    reminding_message = ('Kindly reminding:\n', 'Любезно напоминаю:\n')

    statistics_message = ('Current statistics:\n- total users registered: %s\n- total notes registered: %s',
                          'Текущая статистика:\n- всего пользователей зарегистрировано: %s\n'
                          '- всего памяток зарегистрировано: %s')

    language = 0

    # CHECKING THE ANSWER
    if len(decoded_answer['result']) == 0:
        pass
    else:
        print('->  Received ' + str(len(decoded_answer['result'])) + ' updates.\n')
        # GETTING ACTUAL UPDATE NUMBER AND REWRITING BOT.INFO FILE WITH TOKEN AND UPDATE NUMBER
        curr_update_num = decoded_answer['result'][-1]['update_id']
        SaveTokenAndUpdateNum()
        SaveToLog(str(decoded_answer), 'answer.log')

        # PROCESSING UPDATES
        for update in decoded_answer['result']:
            # GETTING PARAMETERS FROM UPDATE OBJECT
            source_id = update['message']['chat']['id']
            message = str(update['message']['text']).strip()
            is_user = True
            is_bot = update['message']['from']['is_bot']
            user_language = update['message']['from']['language_code']
            if str(user_language).lower() == 'ru-ru':
                language = 1

            # NO BUSINESS WITH OTHER BOTS
            if is_bot == 'false':
                continue

            # GETTING CURRENT SOURCE STATE
            source_state = ReminderBotCSQL.CheckSourceState(source_id, db_connection)
            if source_state == -1:
                StopCycle('->  Error checking source state: error executing through DB connection.')
                return 1
            if source_state == -3:
                StopCycle('->  Error checking source state: more than one example of the source in DB.')
                return 1
            if source_state == -2:
                # ADDING SOURCE TO BD IF IT IS NEW
                if ReminderBotCSQL.AddSource(source_id, db_connection, is_user, user_language) == 1:
                    StopCycle('->  Error adding a source to the DB.', db_connection)
                    return 1

                SaveToLog('\n->  A source is added to DB: ' + str(source_id) + ', is a user: ' + str(is_user) +
                          ', language: ' + user_language, 'sources.log')

            # LOGIC OF STATE AND MESSAGE

            # HELP COMMAND
            if message.lower() in ('/help', 'help', '/start', 'start'):
                answer_to_source = help_message[language]
                if SendMessageToChatOrStop(source_id, answer_to_source, db_connection) != 0:
                    return 1

                # CHANGING SOURCE STATE TO 0 - DEFAULT
                if ChangeSourceStateOrStop(source_id, db_connection, 0) != 0:
                    return 1

                continue

            # SHOW COMMAND
            if message.lower() in ('/show', 'show'):
                # GETTING NOTES OF CURRENT SOURCE
                notes = ReminderBotCSQL.GetAllNotesOfSource(source_id, db_connection)
                if notes == -1:
                    StopCycle('->  Error getting notes from DB.', db_connection)
                    return 1

                if notes is None or len(notes) == 0:
                    answer_to_source = show_nosaved_message[language]
                else:
                    # ADDING FOUND NOTES TO THE ANSWER
                    answer_to_source = show_saved_message[language]
                    for note in notes:
                        answer_to_source += ('\n' + str(note[0]) + '.' + str(note[1]) + '.' + str(note[2]) + ' '
                                             + str(note[3]) + ':' + str(note[4]) + '\n"' + note[5]) + '"'
                        if note[6] == 1:
                            answer_to_source += show_reminded_message[language]

                    answer_to_source += ending_message[language]

                if SendMessageToChatOrStop(source_id, answer_to_source, db_connection) != 0:
                    return 1

                # CHANGING SOURCE STATE TO 0 - DEFAULT
                if ChangeSourceStateOrStop(source_id, db_connection, 0) != 0:
                    return 1

                continue

            # REMIND COMMAND
            if message.lower() in ('/remind', 'remind'):
                answer_to_source = remind_message[language]
                if SendMessageToChatOrStop(source_id, answer_to_source, db_connection) != 0:
                    return 1

                # CHANGING SOURCE STATE TO 3 - WAITING FOR MESSAGE IN FORMAT TO REMIND
                if ChangeSourceStateOrStop(source_id, db_connection, 3) != 0:
                    return 1

                continue

            # SAVE COMMAND
            if message.lower() in ('/save', 'save'):
                answer_to_source = save_message[language]
                if SendMessageToChatOrStop(source_id, answer_to_source, db_connection) != 0:
                    return 1

                # CHANGING SOURCE STATE TO 1 - WAITING FOR MESSAGE IN FORMAT TO REMIND
                if ChangeSourceStateOrStop(source_id, db_connection, 1) != 0:
                    return 1

                continue

            # DELAY COMMAND
            if message.lower() in ('/delay', 'delay'):
                # GETTING LAST REMINDED NOTE IN PAST 30 MINUTES OF CURRENT SOURCE
                note = GetLastRemindedNoteOrStop(source_id, db_connection, db_connection)
                if note == -1:
                    return 1

                if note == 0:
                    answer_to_source = delay_norecent_message[language]
                    if SendMessageToChatOrStop(source_id, answer_to_source, db_connection) != 0:
                        return 1

                    # CHANGING SOURCE STATE TO 0 - DEFAULT
                    if ChangeSourceStateOrStop(source_id, db_connection, 0) != 0:
                        return 1

                    continue

                else:
                    answer_to_source = delay_message[language] + str(note[6]) + '"'
                    if SendMessageToChatOrStop(source_id, answer_to_source, db_connection) != 0:
                        return 1

                    # CHANGING SOURCE STATE TO 2 - WAITING FOR MESSAGE IN FORMAT TO DELAY
                    if ChangeSourceStateOrStop(source_id, db_connection, 2) != 0:
                        return 1

                    continue

            # TIME COMMAND
            if message.lower() in ('/time', 'time'):
                answer_to_source = time_message[language] + str(datetime.now())
                if SendMessageToChatOrStop(source_id, answer_to_source, db_connection) != 0:
                    return 1

                # CHANGING SOURCE STATE TO 0 - DEFAULT
                if ChangeSourceStateOrStop(source_id, db_connection, 0) != 0:
                    return 1

                continue

            # AUTHOR COMMAND
            if message.lower() in ('/auth', 'auth'):
                answer_to_source = author_message[language]
                if SendMessageToChatOrStop(source_id, answer_to_source, db_connection) != 0:
                    return 1

                # CHANGING SOURCE STATE TO 0 - DEFAULT
                if ChangeSourceStateOrStop(source_id, db_connection, 0) != 0:
                    return 1

                continue

            #ROOTSTAT COMMAND
            if message.lower() in ('/rootstat', 'rootstat'):
                stats = ReminderBotCSQL.GetStats(db_filename)
                if stats == -1:
                    StopCycle('->  Error while printing statistics. Details see above.')
                    return 1

                stat_info = (str(stats[0][1]), str(stats[0][2]))
                answer_to_source = statistics_message[language] % stat_info
                if SendMessageToChatOrStop(source_id, answer_to_source, db_connection) != 0:
                    return 1

                # CHANGING SOURCE STATE TO 0 - DEFAULT
                if ChangeSourceStateOrStop(source_id, db_connection, 0) != 0:
                    return 1

                continue

            # MESSAGE WITHOUT A COMMAND

            # AFTER SAVE COMMAND
            if source_state == 1:
                # CHECKING THE UPDATE MESSAGE TO HAVE THE FORMAT "DATE TIME TEXT"
                check_result = ReminderBotCRE.CheckForDateTimeText(message)
                if check_result == 0:
                    # THE UPDATE MESSAGE WAS INCORRECT
                    answer_to_source = save_invalid_message[language]

                else:
                    answer_to_source = save_success_message[language]

                # GETTING DATETIME FOR DATE TIME TEXT FORMAT
                if check_result == 1:
                    year = int(message[0:4])
                    month = int(message[5:7])
                    day = int(message[8:10])
                    message = message[10:].lstrip()
                    hour = int(message[0:2])
                    minute = int(message[3:5])
                    text = message[5:].lstrip()

                # GETTING DATETIME FOR TIME TEXT FORMAT
                if check_result == 2:
                    current_day = datetime.now()
                    year = current_day.year
                    month = current_day.month
                    day = current_day.day
                    hour = int(message[0:2])
                    minute = int(message[3:5])
                    text = message[5:].lstrip()

                if check_result > 0:
                    if len(text) < 3:
                        answer_to_source = save_shorttext_message[language]

                    else:
                        # THE UPDATE MESSAGE IS CORRECT - SAVING NOTE TO DB
                        if ReminderBotCSQL.AddNote(source_id, db_connection, year, month, day, hour, minute, text) != 0:
                            StopCycle('->  Error adding a note through DB connection.', db_connection)
                            return 1

                        # CHANGING SOURCE STATE TO 0 - DEFAULT
                        if ChangeSourceStateOrStop(source_id, db_connection, 0) != 0:
                            return 1

                if SendMessageToChatOrStop(source_id, answer_to_source, db_connection) != 0:
                    return 1

                continue

            # AFTER DELAY COMMAND
            if source_state == 2:
                # CHECKING THE UPDATE MESSAGE TO HAVE THE FORMAT "DATE TIME" OR "TIME"
                check_result = ReminderBotCRE.CheckForDateTimeOrTime(message)
                if check_result == 0:
                    # THE UPDATE MESSAGE WAS INCORRECT
                    answer_to_source = delay_invalid_message[language]
                else:
                    # MESSAGE CORRECT - GETTING LAST REMINDED NOTE NOT OLDER THEN 30 MINUTES
                    note = GetLastRemindedNoteOrStop(source_id, db_connection, db_connection)
                    if note == -1:
                        return 1

                    if note == 0:
                        answer_to_source = delay_notavailable_message[language]
                    else:
                        answer_to_source = delay_success_message1[language] + note[6] + delay_success_message2[language]

                # ACQUIRING NEW TIME FOR THE NOTE TO REMIND
                if check_result == 1:
                    # THE UPDATE MESSAGE IS CORRECT AND HOLD NEW DATE TIME
                    year = int(message[0:4])
                    month = int(message[5:7])
                    day = int(message[8:10])
                    message = message[10:].lstrip()
                    hour = int(message[0:2])
                    minute = int(message[3:5])

                if check_result == 2:
                    # THE UPDATE MESSAGE IS CORRECT AND HOLD DELAY TIME
                    hour = int(message[0:2])
                    minute = int(message[3:5])
                    new_datetime = datetime.now() + timedelta(0, 0, 0, 0, minute, hour)
                    year = new_datetime.year
                    month = new_datetime.month
                    day = new_datetime.day
                    hour = new_datetime.hour
                    minute = new_datetime.minute

                if check_result > 0 and note != 0 and note != -1:
                    # UPDATING NOTE DATA AND REMINDED STATUS
                    if ReminderBotCSQL.DelayNote(note[0], db_connection, year, month, day, hour, minute) != 0:
                        StopCycle('->  Error delaying note ID: ' + str(note[0]) + ' .', db_connection)

                    # CHANGING SOURCE STATE TO 0 - DEFAULT
                    if ChangeSourceStateOrStop(source_id, db_connection, 0) != 0:
                        return 1

                if SendMessageToChatOrStop(source_id, answer_to_source, db_connection) != 0:
                    return 1

                continue

            # AFTER REMIND COMMAND
            if source_state == 3:
                # CHECKING THE UPDATE MESSAGE TO HAVE THE FORMAT "M H D M Y TEXT"
                check_result = ReminderBotCRE.CheckForRemindFormat(message)

                if check_result == 0:
                    answer_to_source = remind_invalid_message[language]

                else:
                    minute = message.strip()[0:message.index(' ')]
                    message = message[len(minute):].strip()
                    minute = int(minute)
                    if check_result > 1:
                        hour = message[0:message.index(' ')]
                        message = message[len(hour):].strip()
                        hour = int(hour)
                        if check_result > 2:
                            day = message.strip()[0:message.index(' ')]
                            message = message[len(day):].strip()
                            day = int(day)
                            if check_result > 3:
                                month = message.strip()[0:message.index(' ')]
                                message = message[len(month):].strip()
                                month = int(month)
                                if check_result > 4:
                                    year = message.strip()[0:message.index(' ')]
                                    message = message[len(year):].strip()
                                    year = int(year)

                                else:
                                    year = 0

                            else:
                                month, year = 0, 0

                        else:
                            day, month, year = 0, 0, 0

                    else:
                        hour, day, month, year = 0, 0, 0, 0

                    text = message
                    remind_datetime = datetime.now() + timedelta(days=(year*365 + month*30), hours=hour, minutes=minute)
                    rd_str = str(remind_datetime)
                    rd_str = rd_str[0:rd_str.rindex('.')]
                    answer_to_source = (remind_success_message[language] + rd_str + ending_message[language])
                    # THE UPDATE MESSAGE IS CORRECT - SAVING NOTE TO DB
                    if ReminderBotCSQL.AddNote(source_id, db_connection, remind_datetime.year, remind_datetime.month,
                                               remind_datetime.day, remind_datetime.hour,
                                               remind_datetime.minute, text) != 0:
                        StopCycle('->  Error adding a note through DB connection.', db_connection)
                        return 1

                    SaveToLog('->  A note has been added.', 'notes.log')
                    # CHANGING SOURCE STATE TO 0 - DEFAULT
                    if ChangeSourceStateOrStop(source_id, db_connection, 0) != 0:
                        return 1

                if SendMessageToChatOrStop(source_id, answer_to_source, db_connection) != 0:
                    return 1

                continue

            # IF MESSAGE CONTAINS NO COMMAND AND NO CERTAIN DATA REQUIRED FROM SOURCE (STATE = 0)
            answer_to_source = help_message[language]
            if SendMessageToChatOrStop(source_id, answer_to_source, db_connection) != 0:
                return 1

            # END OF FOR LOOP OF UPDATES

    # REMINDING ALL NOTES WITH PASSED DATETIME AND REMINDED = 0
    notes = ReminderBotCSQL.GetNotesToRemind(db_connection)
    if notes == -1:
        StopCycle('->  Error getting notes to remind from DB.')
        return 1

    if notes != -2:
        sent_notes_id = ''
        for note in notes:
            source_id = note[1]
            # GETTING SOURCE LANGUAGE
            source_language = ReminderBotCSQL.GetSourceLanguage(source_id, db_connection)
            if source_language == -1:
                StopCycle('->  Error checking source language: error executing through DB connection.')
                return 1

            if source_language == -2:
                StopCycle('->  Error checking source language: no source with ID ' + source_id + ' found in DB.')
                return 1

            if source_language == -3:
                StopCycle('->  Error checking source language: more than one example of the source in DB.')
                return 1

            if str(source_language).lower() == 'ru-ru':
                language = 1

            remind_datetime = datetime(note[2], note[3], note[4], note[5], note[6])
            if (datetime.now() - remind_datetime).total_seconds() > 0:
                message_to_source = reminding_message[language] + str(remind_datetime) + '\n' + note[7]
                if SendMessageToChatOrStop(source_id, message_to_source, db_connection) != 0:
                    return 1

                sent_notes_id += str(note[0]) + ', '

        # CHANGING PREVIOUSLY PROCESSED NOTES REMINDED TO 1
        if len(sent_notes_id) > 0:
            sent_notes_id = sent_notes_id[0:-2]
            if ReminderBotCSQL.ChangeNotesToReminded(db_connection, sent_notes_id) != 0:
                StopCycle('->  Error changing notes to reminded in DB.', db_connection)
                return 1

    # REMOVING ALL OLD NOTES
    count = ReminderBotCSQL.RemoveOldRemindedNotes(db_connection)
    if count == -1:
        StopCycle('->  Error removing old reminded notes from DB.', db_connection)
        return 1

    elif count > 0:
        SaveToLog('->  Removing old notes: ' + str(count) + ' entries proceeded.', 'notes.log')

    db_connection.close()

    return 0


# ***************************************************************
# ***************************************************************
# MAIN PROGRAM RUN

if __name__ == '__main__':
    # START VARIABLES
    bot_start_URL = r'https://api.telegram.org/bot'
    db_filename = 'SourcesAndNotes.db'
    bot_token = ''
    curr_update_num = 0
    # CYCLE VARIABLES
    cycle_period = 3
    stop_cycle = False

    # CHECKING TERMINAL ARGUMENTS
    if len(sys.argv) > 1:
        if str(sys.argv[1]).lower() in ('help', '-help', '--help', 'man', '-man', '--man'):
            print('ReminderBotC can be started without arguments as daemon or with 1 parameter (argument):\n'
                  '-help    -  provides this help message,\n'
                  '-shows   -  prints the current content of Sources table of "' + db_filename + '" database,\n'
                  '-shown   -  prints the current content of Notes table of "' + db_filename + '" database,\n'
                  '-stat    -  prints statistics on total sources and notes ever registered.\n')
        elif str(sys.argv[1]).lower() in ('-shows', 'shows'):
            ShowAllSource()

        elif str(sys.argv[1]).lower() in ('-shown', 'shown'):
            ShowAllNotes()

        elif str(sys.argv[1]).lower() in ('-stat', 'stat'):
            ShowStats()

        else:
            print('Unknown argument, try -help for help.')

    else:
        # READING BOT TOKEN AND LAST UPDATE NUMBER FROM FILE
        ReadTokenAndUpdateNum()
        # STARTING THREAD
        print('\n->  Starting bot.')
        main_cycle = threading.Thread(target=CycleThread, name='MainCycle')
        main_cycle.start()
        # INPUT LOOP
        while True:
            print('\n->  Enter the command. Available:\n'
                  '-shows       -  prints the current content of Sources table of "' + db_filename + '" database,\n'
                  '-shown       -  prints the current content of Notes table of "' + db_filename + '" database,\n'
                  '-stat        -  prints statistics on total sources and notes ever registered,\n'
                  '-test        -  test the bot token to be valid,\n'
                  '-delay <num> -  set main cycle delay equal to <num> seconds, where <num> must be positive int,\n'
                  '-exit    -  stops the bot and exit the application.\n\n')
            command = input()
            if command.lower() in ('-shows', 'shows'):
                ShowAllSource()

            elif command.lower() in ('-shown', 'shown'):
                ShowAllNotes()

            elif command.lower() in ('-stat', 'stat'):
                ShowStats()

            elif command.lower() in ('-test', 'test'):
                TestBotToken()

            elif command.lower()[0: command.index(' ')] in ('-delay', 'delay'):
                if command[command.rindex(' ') + 1] == '-':
                    print('->  Error in entered cycle period - negative value.')
                    continue
                try:
                    cycle_period = int(command[command.rindex(' ') + 1:])
                except:
                    print('->  Error converting entered number to cycle period.')
                    continue

            elif command.lower() in ('-exit', 'exit', '-quit', 'quit') or stop_cycle:
                if main_cycle.is_alive():
                    print('\n->  Stopping main cycle...')
                    stop_cycle = True
                    main_cycle.join()
                break

        print('->  See ya.')

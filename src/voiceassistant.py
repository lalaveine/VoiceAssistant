# Text-to-Speech
from gtts import gTTS
from io import BytesIO
from pydub import AudioSegment
from pydub.playback import play

# Speech recognition
import speech_recognition as sr

# Hotword detection
import snowboy.snowboydecoder as snowboydecoder
from definitions import SNOWBOY_MODEL_PATH
import threading

# Fuzzy logic
from rapidfuzz import fuzz

# DBus
from pydbus import SessionBus
from gi.repository import GLib

# Model
from src.model.datamanager import Command
from src.model.datamanager import Contacts

# GMail
from src.functions.googlemail import VAMailGoogle

# Google Calendar
from src.functions.googlecalendar import VACalendarGoogle

# Weather
from src.functions.weather import VAWeather

# Time related functions
import datetime
import time

# Misc.
import random

class DBusService(object):
    """
        <node>
            <interface name='org.LinuxAssistantServer'>
                <method name='client_init'>
                    <arg type='b' name='response' direction='out'/>
                </method>
                <method name='wakeup_call'>
                </method>
                <method name='echo_string'>
                    <arg type='s' name='a' direction='in'/>
                    <arg type='s' name='response' direction='out'/>
                </method>
                <method name='quit'/>
            </interface>
        </node>
    """
    def client_init(self):
        return True

    def wakeup_call(self):
        if VoiceAssistant.assistant_is_busy is False:
            VoiceAssistant.wakeup_response()
        else:
            print("assistant is busy")

    def echo_string(self, s):
        """returns whatever is passed to it"""
        print(s)
        return s


class VoiceAssistant(object):
    assistant_is_busy = False

    @staticmethod
    def say(text, lang='ru', client=None):
        mp3_fp = BytesIO()
        tts = gTTS(text, lang)
        tts.write_to_fp(mp3_fp)
        text_audio = AudioSegment.from_file(BytesIO(mp3_fp.getvalue()), format="mp3")

        if client is not None:
            client.print_text(text, False)

        play(text_audio)

    @staticmethod
    def recognize(lang='ru-RU', client=None):
        recognizer = sr.Recognizer()
        mic = sr.Microphone()
        with mic as source:
            recognizer.dynamic_energy_threshold = True
            recognizer.adjust_for_ambient_noise(source, duration=2)
            if client is not None:
                client.print_text("Говорите...", False)
            print("Говорите...")
            audio = recognizer.listen(source)

        if client is not None:
            client.print_text("Распознаю...", False)

        print("Распознаю...")
        query = recognizer.recognize_google(audio, language=lang)

        if client is not None:
            client.print_text(query, True)

        return query

    @staticmethod
    def identify_command(cmd_text):
        identified_command = {'cmd': '', 'percent': 0}
        commands = Command.get_commands()

        for identifier, triggers_vector in commands:
            for string in triggers_vector:
                fuzzy_ratio = fuzz.ratio(cmd_text, string, score_cutoff=identified_command['percent'])
                if fuzzy_ratio:
                    identified_command['cmd'] = identifier
                    identified_command['percent'] = fuzzy_ratio

        return identified_command['cmd']

    @staticmethod
    def identify_date(voice_input):
        if voice_input == 'сегодня':
            today = datetime.datetime.now().date()
            return {
                'day': today.day,
                'month': today.month,
                'year': today.year
            }
        else:
            print(voice_input)
            voice_input = voice_input.split()
            months = ['январь', 'февраль', 'март', 'аплель', 'май', 'июнь', 'июль', 'август', 'сентябрь', 'октябрь', 'ноябрь', 'декабрь']
            identified_month = {'month': '', 'percent': 0}
            for month in months:
                fuzzy_ratio = fuzz.ratio(voice_input[1], month)
                if fuzzy_ratio > identified_month['percent']:
                    identified_month['percent'] = fuzzy_ratio
                    identified_month['month'] = month

            day = voice_input[0]
            month = str(months.index(identified_month['month']) + 1)
            year = voice_input[2]

            return {
                'day': day,
                'month': month,
                'year': year
            }

    @staticmethod
    def ask_event_info(dbus_client=None):
        VoiceAssistant.say("Укажите дату вашей встречи, в формате число месяц год.", client=dbus_client)
        voice_str = VoiceAssistant.recognize(client=dbus_client)
        event_day = VoiceAssistant.identify_date(voice_str)
        VoiceAssistant.say("Укажите время встречи.", client=dbus_client)
        event_time = VoiceAssistant.recognize(client=dbus_client)

        start_time = f'{event_day["year"]}-{event_day["month"]}-{event_day["day"]}T{event_time}'
        start_time = datetime.datetime.strptime(start_time, "%Y-%m-%dT%H:%M")


        VoiceAssistant.say("Сколько продлится встреча?", client=dbus_client)
        event_duration = VoiceAssistant.recognize(client=dbus_client)
        event_duration = datetime.datetime.strptime(event_duration, "%H:%M").time()
        duration = datetime.timedelta(hours=event_duration.hour, minutes=event_duration.minute)

        end_time = start_time + duration
        start_time = str(start_time) + ':00+03:00'
        end_time = str(end_time) + ':00+03:00'

        VoiceAssistant.say("Как мне назвать встречу.", client=dbus_client)
        event_name = VoiceAssistant.recognize(client=dbus_client)
        add_description = VoiceAssistant.ask("Добавить ли описание?", client=dbus_client)
        event_description = None
        if add_description is True:
            VoiceAssistant.say("Что добавить в описание встречи?", client=dbus_client)
            event_description = VoiceAssistant.recognize(client=dbus_client)

        add_attendees = VoiceAssistant.ask("Пригласить ли других участников?", client=dbus_client)
        attendees = []
        while add_attendees is True:
            VoiceAssistant.say("Кого мне добавить к этой встрече?", client=dbus_client)
            voice_str = VoiceAssistant.recognize(client=dbus_client)
            contact_info = VoiceAssistant.identify_contact(voice_str)
            attendees.append({
                'email': contact_info['email']
            })
            add_attendees = VoiceAssistant.ask("Пригласить ли других участников?", client=dbus_client)

        return {
            'summary': event_name,
            'start_time': str(start_time),
            'end_time': str(end_time),
            'description': event_description,
            'attendees': attendees
        }

    @staticmethod
    def ask_email_info(dbus_client=None):
        VoiceAssistant.say("Кому отправить письмо?", client=dbus_client)
        voice_input = VoiceAssistant.recognize(client=dbus_client)

        contact = VoiceAssistant.identify_contact(voice_input)

        VoiceAssistant.say("Какая тема письма?", client=dbus_client)
        subject = VoiceAssistant.recognize(client=dbus_client)

        VoiceAssistant.say("Содержание письма?",client=dbus_client)
        message = VoiceAssistant.recognize(client=dbus_client)
        return contact['name'], contact['email'], subject, message

    @staticmethod
    def ask(question, client=None):
        VoiceAssistant.say(question, client=client)
        while True:
            response = VoiceAssistant.recognize(client=client).lower()
            print(f'response: {response}')
            if response == "да":
                return True
            elif response == "нет":
                return False
            else:
                VoiceAssistant.say("Прошу прощения, но я вас не расслышала, не могли бы повторить?", client=client)

    @staticmethod
    def identify_contact(input_str):
        identified_contact = {'name': '', 'percent': 0}
        contacts = Contacts.get_contacts()
        for name in contacts:
            fuzzy_ratio = fuzz.ratio(name, input_str)
            if fuzzy_ratio > identified_contact['percent']:
                identified_contact['name'] = name
                identified_contact['percent'] = fuzzy_ratio
        name = identified_contact['name']
        email = contacts[name]

        return {
            'name': name,
            'email': email
        }

    @staticmethod
    def execute_command(cmd_str, dbus_client=None):
        if cmd_str == 'unread_email':
            gmail = VAMailGoogle()
            messages = gmail.get_unread('in:inbox is:unread')

            VoiceAssistant.say(f"У вас {len(messages)} непрочитанных сообщений", client=dbus_client)

            # response = None
            # if dbus_client is not None:
            response = VoiceAssistant.ask("Хотите, чтобы я прочитала от кого они и темы писем?", client=dbus_client)
            # else:
            #     response = VoiceAssistant.ask("Хотите, чтобы я прочитала от кого они и темы писем?")

            if response is True:
                for message in messages:
                    date = message['Date']
                    date = utc_to_local(datetime.datetime.strptime(date, '%d %b %Y %X %z'))
                    date_str = '{:"%d/%m/%Y"}'.format(date)

                    VoiceAssistant.say(f"{date_str} в {date.time()} вам прикло письмо от {message['From']} с темой {message['Subject']}")
            elif response is False:
                if dbus_client is not None:
                    VoiceAssistant.say("Хорошо.", client=dbus_client)
                else:
                    VoiceAssistant.say("Хорошо.")


        if cmd_str == 'send_email':
            gmail = VAMailGoogle()
            name, email_address, subject, message = VoiceAssistant.ask_email_info(dbus_client=dbus_client)
            print(email_address, subject, message)
            VoiceAssistant.say(f'Вы хотите отправить письмо контакту {name}, с темой {subject}, и содержанием {message}.Все верно?', client=dbus_client)
            resp = VoiceAssistant.recognize(client=dbus_client)
            if resp == "да":
                raw_email = gmail.create_email(email_address, subject, message)
                gmail.send_email(raw_email)
                dbus_client.print_text("Письмо было отправлено", False)
                print("Email has been sent.")
            else:
                dbus_client.print_text("Письмо не было отправлено", False)
                print("Email has not been sent")

        if cmd_str == 'events_day':
            gcal = VACalendarGoogle()
            today = datetime.date.today()
            events = gcal.get_events_on_a_day(today)
            if events != []:
                VoiceAssistant.say(f"На сегодня у вас запланировано {len(events)} событий.", client=dbus_client)
                for event in events:
                    event_date_info = event["Start"]["dateTime"]
                    event_date_info = event_date_info[:event_date_info.index('+')]
                    event_time = datetime.datetime.strptime(event_date_info, "%Y-%m-%dT%H:%M:%S").time()
                    VoiceAssistant.say(f"В {event_time} у вас {event['Summary']}", client=dbus_client)

        if cmd_str == 'add_event':
            gcal = VACalendarGoogle()
            data = VoiceAssistant.ask_event_info(dbus_client=dbus_client)
            send_invites = 'none'
            if data['attendees'] != []:
                send_invites = 'all'

            VoiceAssistant.say(f'Вы хотите добавить событие с названием {data["summary"]}. Верно?', client=dbus_client)
            resp = VoiceAssistant.recognize(client=dbus_client)
            if resp == "да":
                gcal.add_event(data['summary'], data['start_time'], data['end_time'], send_invites,
                               description=data['description'], attendees=data['attendees'])
                dbus_client.print_text("Встреча была создана", False)
                print("Event has been created.")
            else:
                dbus_client.print_text("Создание встречи отменено", False)
                print("Event has not been created")



        if cmd_str == 'time':
            now = datetime.datetime.now()
            if dbus_client is not None:
                VoiceAssistant.say(f'Сейчас {now.strftime("%H")}:{now.strftime("%M")}', client=dbus_client)
            else:
                VoiceAssistant.say(f'Сейчас {now.hour}:{now.minute}')

        if cmd_str == 'weather':
            weather = VAWeather()
            if dbus_client is not None:
                VoiceAssistant.say(weather.get_weather(), client=dbus_client)
            else:
                VoiceAssistant.say(weather.get_weather())

        if cmd_str == 'help':
            if dbus_client is not None:
                VoiceAssistant.say("Я могу помочь вам узнать погоду и время."
                                   " Также я могу отправить сообщение по почте "
                                   "и создать событие в календаре", client=dbus_client)

    @staticmethod
    def greeter():
        greetings = [
            'Чем могу помочь?',
            'Я вас слушаю...'
        ]
        return random.choice(greetings)

    @staticmethod
    def wakeup_response():
        # Make threading safe
        lock = threading.Lock()
        lock.acquire()

        VoiceAssistant.assistant_is_busy = True

        dbus_client = None
        try:
            client_bus = SessionBus()
            dbus_client = client_bus.get("org.LinuxAssistantClient")
        except:
            print("[log] Can't connect to the client")

        VoiceAssistant.say(VoiceAssistant.greeter(), client=dbus_client)

        voice_cmd = None
        try:
            voice_cmd = VoiceAssistant.recognize(client=dbus_client)
        except sr.UnknownValueError:
            print("[log] Голос не распознан!")
        except sr.RequestError as e:
            print("[log] Неизвестная ошибка, проверьте интернет!")

        if voice_cmd is not None:
            print("[log] Распознано: " + voice_cmd)

            voice_cmd = voice_cmd.lower()

            for word in opts['alias']:
                voice_cmd = voice_cmd.replace(word, '').strip()

            for word in opts['tbr']:
                voice_cmd = voice_cmd.replace(word, '').strip()

            cmd = VoiceAssistant.identify_command(voice_cmd)

            VoiceAssistant.execute_command(cmd, dbus_client=dbus_client)

        lock.release()

        VoiceAssistant.assistant_is_busy = False


opts = {
        "alias": ('алиса', 'алисочка', 'леся'),
        "tbr": ('скажи', 'расскажи', 'покажи', 'сколько', 'произнеси')
}


def utc_to_local(utc):
    epoch = time.mktime(utc.timetuple())
    offset = datetime.datetime.fromtimestamp(epoch) - datetime.datetime.utcfromtimestamp(epoch)
    return utc + offset


def detected_callback():
    if VoiceAssistant.assistant_is_busy is False:
        VoiceAssistant.wakeup_response()
    else:
        print("assistant is busy")


if __name__ == '__main__':
    server_bus = SessionBus()
    server_bus.publish("org.LinuxAssistantServer", DBusService())
    loop = GLib.MainLoop()

    thread = threading.Thread(target=loop.run)
    thread.daemon = True
    thread.start()

    detector = snowboydecoder.HotwordDetector(SNOWBOY_MODEL_PATH, sensitivity=0.5, audio_gain=1)
    thread2 = threading.Thread(target=detector.start, kwargs=dict(detected_callback=detected_callback, recording_timeout=30))
    thread2.start()

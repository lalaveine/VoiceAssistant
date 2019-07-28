import pyaudio
import wit
import os
from pydub import AudioSegment
from pydub.playback import play
import io

# Audio info
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
RECORD_SECONDS = 5
ENDIAN = 'little'
CONTENT_TYPE = \
    'raw;encoding=signed-integer;bits=16;rate={0};endian={1}'.format(RATE, ENDIAN)

# будущий файл настроек
OWM_API_KEY = '01176a268541e281e6e830079b34bb86'
WIT_TOKEN = '7LD2YOP3PHNH2725ZRVV2MGDZ5VHK4LD'
MODEL = 'resources/Алиса.pmdl'

# Запускаемые приложения
appList = {
    'kodi': 'kodi',
    'браузер': 'x-www-browser',
    'firefox': 'firefox',
    'блокнот': 'gedit'
}

# Список слов, которые необходимо убрать из voice_input
CLEAN_LIST = [
    'може',  # Можешь/Можете
    'пожалуй',
    'как',
    'что'
]

RUN_APP_TRIGGERS_LIST = [
    'включ',
    'запус',
    'откр'
]

WEATHER_TRIGGERS_LIST = [
    'погод'
]

ADD_COMMAND_TRIGGERS_LIST = [
    'добав'
]

def record_and_stream():
    p = pyaudio.PyAudio()

    stream = p.open(
        format=FORMAT, channels=CHANNELS, rate=RATE,
        input=True, frames_per_buffer=CHUNK)

    play(ding_sound)
    print("* идет запись")

    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        yield stream.read(CHUNK)

    play(ding_sound)
    print("* запись завершена")

    stream.stop_stream()
    stream.close()
    p.terminate()



def cleanse_input(command):
    command = command.lower()
    word_list = command.split()

    for word in word_list:
        for word_to_remove in CLEAN_LIST:
            if word_to_remove in word:
                word_list.remove(word)

    return word_list


def check_for_command(input_list, TRIGGERS_LIST):
    is_included = False

    for word in input_list:
        for command in TRIGGERS_LIST:
            if command in word:
                is_included = True
                break
        else:
            continue
        break

    return is_included


def add_command():
    print()


def execute_command():
    voice_input = w.post_speech(record_and_stream(), content_type=CONTENT_TYPE)['_text']

    print(voice_input)

    input_list = cleanse_input(voice_input)

    print(input_list)

    if check_for_command(input_list, RUN_APP_TRIGGERS_LIST):
        for i in range(0, len(input_list) - 1):
            if input_list[i + 1] in appList:
                os.system(appList[input_list[i + 1]])
                break
            else:
                print("Я не знаю такого приложения, вы сказали - " + voice_input)

    # elif check_for_command(input_list, WEATHER_TRIGGERS_LIST):
    #     get_forecast(input_list)
    # add music control with mpd and mpc
    # elif '' in voice_input:
    #     print('')
    else:
        print("Такой комманды нет, вы сказали - " + voice_input)


# snowboy callbacks
interrupted = False


def signal_handler(signal, frame):
    global interrupted
    interrupted = True


def interrupt_callback():
    global interrupted
    return interrupted


if __name__ == '__main__':

    w = wit.Wit(WIT_TOKEN)

    with open('resources/ding.wav', 'rb') as fd:
        ding_fp = fd.read()

    # with open('resources/dong.wav', 'rb') as fd:
    #     dong_fp = fd.read()

    ding_sound = AudioSegment.from_file(io.BytesIO(ding_fp), format="wav")
    # dong_sound = AudioSegment.from_file(io.BytesIO(dong_fp), format="wav")

    execute_command()
    # # capture SIGINT signal, e.g., Ctrl+C
    # signal.signal(signal.SIGINT, signal_handler)
    #
    # detector = snowboydecoder.HotwordDetector(MODEL, sensitivity=0.5)
    # print('Listening... Press Ctrl+C to exit')
    #
    # # main loop
    # detector.start(detected_callback=execute_command,
    #                interrupt_check=interrupt_callback,
    #                sleep_time=0.03)
    #
    # detector.terminate()



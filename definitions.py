import os

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.join(ROOT_DIR, 'config')
#POCKET_SPHINX_RUSSIAN_MODEL_PATH = os.path.join(ROOT_DIR, 'venv/lib/python3.7/site-packages/speech_recognition/pocketsphinx-data/ru-RU')

CONFIG_PATH = os.path.join(ROOT_DIR, 'config/config.json')
DATABASE_PATH = os.path.join(ROOT_DIR, 'database.db')
SNOWBOY_MODEL_PATH = os.path.join(ROOT_DIR, 'snowboy/resources/Алиса.pmdl')


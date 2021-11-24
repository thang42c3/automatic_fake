import json
import logging
import os
logging.basicConfig(level=logging.INFO)
basedir = os.path.abspath(os.path.dirname(__file__))
def configs(link = './config/config.json'):
    with open(link, 'r') as f:  # ./config/
        config = json.load(f)
    f.close()
    return config

class Config(object):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, '../app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = 'file_csv'
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'





import os

class Config:
    SECRET_KEY = os.environ.get('123456') 
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///digital_bridge.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
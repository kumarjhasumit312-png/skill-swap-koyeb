import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'skillswap-secret-key-2026')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///skillswap.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = True
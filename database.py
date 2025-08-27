from flask_sqlalchemy import SQLAlchemy
import os
from dotenv import load_dotenv
from urllib.parse import quote_plus

load_dotenv()

db = SQLAlchemy()


def init_db(app):
    # Получаем параметры из .env
    db_name = os.getenv('DB_NAME')
    db_user = os.getenv('DB_USER')
    db_password = os.getenv('DB_PASSWORD')
    db_host = os.getenv('DB_HOST')
    db_port = os.getenv('DB_PORT')

    # Кодируем пароль для безопасного использования в URI
    encoded_password = quote_plus(db_password)

    # Формируем URI для PostgreSQL с явным указанием кодировки UTF-8
    db_uri = f"postgresql://{db_user}:{encoded_password}@{db_host}:{db_port}/{db_name}?client_encoding=utf8"

    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_recycle': 300,
        'pool_pre_ping': True,
        'connect_args': {
            'options': '-c client_encoding=utf8'
        }
    }
    app.config['JSON_AS_ASCII'] = False  # Для русского языка в JSON

    db.init_app(app)

    try:
        with app.app_context():
            db.create_all()
        print("✅ Database initialized successfully with PostgreSQL")
        print(f"✅ Database URI: postgresql://{db_user}:******@{db_host}:{db_port}/{db_name}")
        print("✅ Client encoding set to UTF-8")
    except Exception as e:
        print(f"❌ Database initialization error: {e}")
        print("Убедитесь, что:")
        print("1. PostgreSQL запущен")
        print("2. База данных 'advertisements_db' существует")
        print("3. Параметры в .env файле корректны")
        print("4. База данных создана с кодировкой UTF-8")
        print("\nДля создания базы данных выполните:")
        print("   createdb -U postgres -E UTF8 advertisements_db")
        print("\nИли в psql:")
        print("   CREATE DATABASE advertisements_db WITH ENCODING = 'UTF8';")
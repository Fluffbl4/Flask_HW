from flask import request, jsonify, g
from functools import wraps
from models import User
import base64


def basic_auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')

        if not auth_header or not auth_header.startswith('Basic '):
            return jsonify({'error': 'Authorization required'}), 401

        try:
            # Декодируем Basic Auth
            encoded_credentials = auth_header.split(' ')[1]
            decoded_credentials = base64.b64decode(encoded_credentials).decode('utf-8')
            email, password = decoded_credentials.split(':', 1)

            # Проверяем пользователя
            user = User.query.filter_by(email=email).first()
            if not user or not user.check_password(password):
                return jsonify({'error': 'Invalid credentials'}), 401

            # Сохраняем пользователя в контексте приложения
            g.current_user = user

        except (ValueError, IndexError, UnicodeDecodeError):
            return jsonify({'error': 'Invalid authorization header'}), 401

        return f(*args, **kwargs)

    return decorated


def get_current_user():
    return getattr(g, 'current_user', None)
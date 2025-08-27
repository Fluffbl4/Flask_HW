from flask import Flask, request, jsonify, g, make_response
from flask.views import MethodView
from models import Advertisement, User
from database import db, init_db
from validators import AdvertisementCreateValidator, AdvertisementUpdateValidator, UserCreateValidator
from auth import basic_auth_required, get_current_user
from pydantic import ValidationError
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Настройки кодировки
app.config['JSON_AS_ASCII'] = False  # Важно для русского языка
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

# Инициализация базы данных
init_db(app)


class HttpError(Exception):
    def __init__(self, status_code: int, message: str | dict | list):
        self.status_code = status_code
        self.message = message


@app.errorhandler(HttpError)
def error_handler(error: HttpError):
    response = make_response(jsonify({'status': 'error', 'message': error.message}))
    response.status_code = error.status_code
    response.headers['Content-Type'] = 'application/json; charset=utf-8'
    return response


def validate_data(data: dict, validator_class):
    try:
        return validator_class(**data).model_dump(exclude_none=True)
    except ValidationError as error:
        raise HttpError(400, error.errors())


def create_json_response(data, status_code=200):
    """Создает JSON response с правильной кодировкой"""
    response = make_response(jsonify(data))
    response.status_code = status_code
    response.headers['Content-Type'] = 'application/json; charset=utf-8'
    return response


class AdvertisementView(MethodView):

    def get(self, ad_id=None):
        if ad_id:
            advertisement = Advertisement.query.get(ad_id)
            if not advertisement:
                raise HttpError(404, 'Advertisement not found')
            return create_json_response(advertisement.to_dict())
        else:
            advertisements = Advertisement.query.all()
            return create_json_response([ad.to_dict() for ad in advertisements])

    @basic_auth_required
    def post(self):
        current_user = get_current_user()
        if not current_user:
            raise HttpError(401, 'User not authenticated')

        validated_data = validate_data(request.json, AdvertisementCreateValidator)

        advertisement = Advertisement(
            title=validated_data['title'],
            description=validated_data['description'],
            owner_id=current_user.id
        )

        db.session.add(advertisement)
        db.session.commit()

        return create_json_response(advertisement.to_dict(), 201)

    @basic_auth_required
    def patch(self, ad_id):
        current_user = get_current_user()
        if not current_user:
            raise HttpError(401, 'User not authenticated')

        advertisement = Advertisement.query.get(ad_id)
        if not advertisement:
            raise HttpError(404, 'Advertisement not found')

        if advertisement.owner_id != current_user.id:
            raise HttpError(403, 'You can only edit your own advertisements')

        validated_data = validate_data(request.json, AdvertisementUpdateValidator)

        if 'title' in validated_data:
            advertisement.title = validated_data['title']
        if 'description' in validated_data:
            advertisement.description = validated_data['description']

        db.session.commit()

        return create_json_response(advertisement.to_dict())

    @basic_auth_required
    def delete(self, ad_id):
        current_user = get_current_user()
        if not current_user:
            raise HttpError(401, 'User not authenticated')

        advertisement = Advertisement.query.get(ad_id)
        if not advertisement:
            raise HttpError(404, 'Advertisement not found')

        if advertisement.owner_id != current_user.id:
            raise HttpError(403, 'You can only delete your own advertisements')

        db.session.delete(advertisement)
        db.session.commit()

        return create_json_response({'message': 'Advertisement deleted successfully'})


class UserView(MethodView):

    def post(self):
        validated_data = validate_data(request.json, UserCreateValidator)

        if User.query.filter_by(email=validated_data['email']).first():
            raise HttpError(400, 'User with this email already exists')

        user = User(email=validated_data['email'])
        user.set_password(validated_data['password'])

        db.session.add(user)
        db.session.commit()

        return create_json_response({
            'message': 'User created successfully',
            'user_id': user.id
        }, 201)


# Регистрация роутов
app.add_url_rule('/ads/', view_func=AdvertisementView.as_view('ads'), methods=['GET', 'POST'])
app.add_url_rule('/ads/<int:ad_id>/', view_func=AdvertisementView.as_view('ad_detail'),
                 methods=['GET', 'PATCH', 'DELETE'])
app.add_url_rule('/register/', view_func=UserView.as_view('register'), methods=['POST'])


@app.after_request
def after_request(response):
    """Добавляем заголовки кодировки ко всем ответам"""
    if response.content_type.startswith('application/json'):
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
    return response


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
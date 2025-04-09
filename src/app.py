"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, Character, Planet, Favorite

app = Flask(__name__)
app.url_map.strict_slashes = False

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Error handler
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# Sitemap
@app.route('/')
def sitemap():
    return generate_sitemap(app)

# GET /users
@app.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    user_serialize = [user.serialize() for user in users if user.is_active]
    return jsonify(user_serialize), 200

# GET /people
@app.route('/people', methods=['GET'])
def get_people():
    characters = Character.query.all()
    serialized_characters = [char.serialize() for char in characters]
    return jsonify(serialized_characters), 200

# GET /people/<id>
@app.route('/people/<int:id>', methods=['GET'])
def get_single_character(id):
    character = Character.query.get(id)
    if not character:
        return jsonify({"message": "not found"}), 404
    return jsonify(character.serialize()), 200

# POST /favorite/people/<id>
@app.route('/favorite/people/<int:id>', methods=['POST'])
def add_favorite_people(id):
    exist = Favorite.query.filter_by(character_id=id, user_id=1).first()
    if exist:
        return jsonify({"message": "Favorite already exists"}), 400

    favorite = Favorite(character_id=id, user_id=1, planet_id=None)
    db.session.add(favorite)
    db.session.commit()

    return jsonify(favorite.serialize()), 201

# GET /planets
@app.route('/planets', methods=['GET'])
def get_planets():
    planets = Planet.query.all()
    return jsonify([planet.serialize() for planet in planets]), 200

# GET /planets/<id>
@app.route('/planets/<int:id>', methods=['GET'])
def get_single_planet(id):
    planet = Planet.query.get(id)
    if not planet:
        return jsonify({"message": "not found"}), 404
    return jsonify(planet.serialize()), 200

# this only runs if `$ python src/app.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)

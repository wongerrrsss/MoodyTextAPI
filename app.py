from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_heroku import Heroku
from flask_marshmallow import Marshmallow
from flask_bcrypt import Bcrypt
import os

app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(basedir, "app.sqlite")

db = SQLAlchemy(app)
ma = Marshmallow(app)
bcrypt = Bcrypt(app)
heroku = Heroku(app)
CORS(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), nullable=False, unique=True)
    password = db.Column(db.String(), nullable=False)
    email = db.Column(db.String()) # Since we didn't add the nullable field, the user does NOT have to have an email

    def __init__(self, username, password, email):
        self.username = username
        self.password = password
        self.email = email

class UserSchema(ma.Schema):
    class Meta:
        fields = ("id", "username", "password", "email")

user_schema = UserSchema()
users_schema = UserSchema(many=True)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(), nullable=False)
    color = db.Column(db.String(), nullable=False)
    userID = db.Column(db.Integer, nullable=False)

    def __init__(self, content, color, userID):
        self.content = content
        self.color = color
        self.userID = userID

class PostSchema(ma.Schema):
    class Meta:
        fields = ("id", "content", "color", "userID")

post_schema = PostSchema()
posts_schema = PostSchema(many=True)

@app.route("/users/post", methods=["POST"])
def create_user():
    if request.content_type != "application/json":
        return jsonify("Error: Data must be sent as JSON.")

    post_data = request.get_json()
    username = post_data.get("username")
    password = post_data.get("password")
    email = post_data.get("email")

    encrypted_password = bcrypt.generate_password_hash(password).decode("utf8")

    record = User(username, encrypted_password, email)
    db.session.add(record)
    db.session.commit()

    return jsonify("User Created")

@app.route("/users/get", methods=["GET"])
def get_all_users():
    all_users = db.session.query(User).all()
    return jsonify(users_schema.dump(all_users))

@app.route("/users/get/by_id/<id>", methods=["GET"])
def get_user_by_id(id):
    user = db.session.query(User).filter(User.id == id).first()
    return jsonify(user_schema.dump(user))

@app.route("/users/get/by_username/<username>", methods=["GET"])
def get_user_by_username(username):
    user = db.session.query(User).filter(User.username == username).first()
    return jsonify(user_schema.dump(user))

@app.route("/users/verification", methods=["POST"])
def verify_user():
    if request.content_type != "application/json":
        return jsonify("Error: Data must be sent as JSON.")

    post_data = request.get_json()
    username = post_data.get("username")
    password = post_data.get("password")

    encrypted_password = db.session.query(User.password).filter(User.username == username).first()

    if encrypted_password is None:
        return jsonify("User NOT Verified: Username")

    password_check = bcrypt.check_password_hash(encrypted_password[0], password)

    if password_check == False:
        return jsonify("User NOT Verified: Password")

    return jsonify("User Verified")

@app.route("/users/posts/by_user_id/<user_id>", methods=["GET"])
def get_all_posts_by_user(user_id):
    all_posts = db.session.query(Post).filter(Post.userID == user_id).all()
    return jsonify(posts_schema.dump(all_posts))

@app.route("/users/posts/by_username/<username>", methods=["GET"])
def get_all_posts_by_user_with_username(username):
    user_id = db.session.query(User.id).filter(User.username == username).first()[0]

    all_posts = db.session.query(Post).filter(Post.userID == user_id).all()
    return jsonify(posts_schema.dump(all_posts))


@app.route("/posts/post", methods=["POST"])
def create_post():
    if request.content_type != "application/json":
        return jsonify("Error: Data must be sent as JSON.")

    post_data = request.get_json()
    content = post_data.get("content")
    color = post_data.get("color")
    userID = post_data.get("userID")

    record = Post(content, color, userID)
    db.session.add(record)
    db.session.commit()

    return jsonify("Post Created")

@app.route("/posts/get", methods=["GET"])
def get_all_posts():
    all_posts = db.session.query(Post).all()
    return jsonify(posts_schema.dump(all_posts))

@app.route("/posts/get/<id>", methods=["GET"])
def get_post_by_id(id):
    post = db.session.query(Post).filter(Post.id == id).first()
    return jsonify(post_schema.dump(post))

if __name__ == "__main__":
    app.debug = True
    app.run()
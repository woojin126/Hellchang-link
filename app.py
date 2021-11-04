import hashlib
import json
from datetime import datetime, timedelta
from bson.objectid import ObjectId
from bson.json_util import dumps
# from bson import json_util, ObjectId

import jwt
import pymongo
from flask import Flask, render_template, jsonify, request, redirect, url_for
from pymongo import MongoClient

app = Flask(__name__)

# JWT 매니저 활성화
# app.config.update(DEBUG=True, JWT_SECRET_KEY="thisissecertkey")
#
# jwt = JWTManager(app)
# app.config['JWT_COOKIE_SECURE'] = False  # https를 통해서만 cookie가 갈 수 있는지 (production 에선 True)
# app.config['JWT_TOKEN_LOCATION'] = ['cookies']
# app.config['JWT_ACCESS_COOKIE_PATH'] = '/'  # access cookie를 보관할 url (Frontend 기준)
# app.config['JWT_REFRESH_COOKIE_PATH'] = '/'  # refresh cookie를 보관할 url (Frontend 기준)
# # CSRF 토큰 역시 생성해서 쿠키에 저장할지
# # (이 경우엔 프론트에서 접근해야하기 때문에 httponly가 아님)
# app.config['JWT_COOKIE_CSRF_PROTECT'] = True

# client = MongoClient('mongodb://rladnwls:rladnwls@localhost', 27017)
client = MongoClient('mongodb://rladnwls:rladnwls@3.36.122.47', 27017 ,authSource="admin")
db = client.dbhellchang

@app.route('/')
def mainPage():
    return render_template('index.html')

@app.route('/category')
def categoryPage():
    return render_template('category.html', name="category")

@app.route('/details')
def DetailsPage():
    return render_template('details.html', name="details")

@app.route('/register')
def registerPage():
    return render_template('register.html', name="register")

@app.route("/login")
def loginPage():
    msg = request.args.get("msg")
    return render_template("login.html", msg=msg, name="login")


@app.route('/sign_up/save', methods=['POST'])
def sign_up():
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']
    email_receive = request.form['email_give']
    password_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    doc = {
        "username": username_receive,  # 아이디
        "password": password_hash,  # 비밀번호
        "profile_name": username_receive,
        "email": email_receive,  # 프로필 이름 기본값은 아이디
        "profile_pic": "",  # 프로필 사진 파일 이름
        "profile_pic_real": "profile_pics/profile_placeholder.png",  # 프로필 사진 기본 이미지
        "profile_info": ""  # 프로필 한 마디
    }
    db.users.insert_one(doc)
    return jsonify({'result': 'success'})


# @app.route("/api/sports/<data>", methods=['GET'])
# def sportsCategory(data):
#     if data == 'soccer':
#         result = db.sports.find({"key": data}, {"_id": False})
#         return jsonify({"result": result})
#     elif data == 'baseball':
#         result = db.sports.find({"key": data}, {"_id": False})
#         return jsonify({"result": result})
#     else:
#         result = db.sports.find({"key": data}, {"_id": False})
#         return jsonify({"result": result})

@app.route("/api/sports" , methods=['GET'])
def sportsCategory():
    category = request.args.get('category')
    print(category)
    result = list(db.sports.find({'key':category},{'_id': False}))
    return jsonify({"result": result ,"msg":"GET 성공!!"})


# 회원가입시, 아이디 중복검사 기능
@app.route('/sign_up/check_dup', methods=['POST'])
def check_dup():
    username_receive = request.form['username_give']
    exists = bool(db.users.find_one({"username": username_receive}))
    return jsonify({'result': 'success', 'exists': exists})


# 로그인 기능
SECRET_KEY = 'SPARTA'


@app.route('/api/login', methods=['POST'])
def login():
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']

    pw_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()

    result = db.users.find_one({'username': username_receive, 'password': pw_hash})

    if result is not None:
        payload = {
            'id': username_receive,
            'exp': datetime.utcnow() + timedelta(seconds=60 * 60 * 24)
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
        return jsonify({'result': 'success', 'token': token})
    else:
        return jsonify({'result': 'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.'})


@app.route("/api/profile")
def profile():
    token = request.cookies.get('token')

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        memberId = payload["id"]

        result = db.users.find_one({'username': memberId})
        return jsonify({"memberId": result['username']})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("login"))


@app.route("/api/comment", methods=['POST'])
def comment():
    token_receive = request.cookies.get('token')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        memberId = payload["id"]
        comment = request.form['comment']

        doc = {
            "username": memberId,
            "comment": comment
        }

        db.hellchangComment.insert_one(doc)
        return jsonify({"result": "success", 'msg': '댓글 달기 완료'})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("api/login"))


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)

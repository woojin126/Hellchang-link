import hashlib
import json
from datetime import datetime, timedelta
from bson.objectid import ObjectId
from bson.json_util import dumps

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

# client = MongoClient("localhost", 27017)
# client = MongoClient('mongodb://rladnwls:rladnwls@localhost', 27017)
client = MongoClient('mongodb://rladnwls:rladnwls@3.36.122.47', 27017, authSource="admin")
db = client.dbhellchang


@app.route('/')
def mainPage():
    return render_template('index.html',name="Main")


@app.route('/category/<keyword>')
def categoryPage(keyword):
    return render_template('category.html', name="category", word=keyword)


@app.route('/details/<id>')
def DetailsPage(id):
    return render_template('details.html', name="details", id=id)


@app.route('/register')
def registerPage():
    return render_template('register.html', name="register")


@app.route("/login")
def loginPage():
    msg = request.args.get("msg")
    return render_template("login.html", msg=msg, name="login")


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
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256').decode('UTF-8')

        return jsonify({'result': 'success', 'token': token})
    else:
        return jsonify({'result': 'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.'})


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


# 회원가입시, 아이디 중복검사 기능
@app.route('/sign_up/check_dup', methods=['POST'])
def check_dup():
    username_receive = request.form['username_give']
    exists = bool(db.users.find_one({"username": username_receive}))
    return jsonify({'result': 'success', 'exists': exists})


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
        replyBoardId = request.form['replyBoardId']

        doc = {
            "username": memberId,
            "comment": comment,
            "replyBoardId": replyBoardId
        }

        db.comments.insert_one(doc)
        return jsonify({"result": "success", 'msg': '댓글 달기 완료'})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("api/login"))


@app.route("/api/comments", methods=['GET'])
def comment_list():
    replyBoardId = request.args.get('replyBoardId')
    result = list(db.comments.find({'replyBoardId': replyBoardId}))
    for post in result:
        post['_id'] = str(post['_id'])
    return jsonify({"result": result})


# 좋아요 토글 기능
@app.route('/update_like', methods=['POST'])
def update_like():
    token_receive = request.cookies.get('token')
    try:
        # payload에 토큰 정보랑 KEY랑 알고리즘으로 저장 시키면 토큰 정보를 볼 수 있다.
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        # payload에서 id 정보만 가져와서 usernmae이랑 비교해본다.
        user_info = db.users.find_one({"username": payload["id"]})
        # 포스트 아이디를 가지고와야 하는지 저장해야한다.
        post_id_receive = request.form["post_id_give"]
        # 클라이언트에서 넘어오는 타입에 따라 db를 변경하기 위해
        type_receive = request.form["type_give"]
        # 좋아요지 싫어요인지 보내서 받아야한다.
        action_receive = request.form["action_give"]
        doc = {
            "post_id": post_id_receive,
            "username": user_info["username"],
            "type": type_receive
        }
        if action_receive == "like":
            db.likes.insert_one(doc)
        else:
            db.likes.delete_one(doc)
        count = db.likes.count_documents({"post_id": post_id_receive, "type": type_receive})
        return jsonify({"result": "success", 'msg': 'updated', "count": count})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for('mainPage'))


@app.route("/api/details", methods=['GET'])
def sportsDetails():
    token_receive = request.cookies.get('token')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        str_id = request.args.get('data_id')
        obj_id = ObjectId(str_id)
        result = db.sports.find_one({'_id': obj_id})
        result['_id'] = str(result['_id'])
        result["count_heart"] = db.likes.count_documents({"post_id": result["_id"], "type": "heart"})
        result["heart_by_me"] = bool(
            db.likes.find_one({"post_id": result["_id"], "type": "heart", "username": payload['id']}))
        return jsonify({"result": result})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for('mainPage'))


@app.route("/api/comments/delete", methods=['POST'])
def commentDelete():
    commentId = request.form['commentId']
    comments = request.form['comments']
    db.comments.delete_one({'_id': ObjectId(commentId)})

    return jsonify({"msg": "댓글삭제 완료"})


@app.route("/api/sports", methods=['GET'])
def sportsCategory():
    category = request.args.get('category')
    result = list(db.sports.find({'key': category}).sort('data', -1))
    for post in result:
        post['_id'] = str(post['_id'])
        post["count_heart"] = db.likes.count_documents({"post_id": post["_id"], "type": "heart"})
    return jsonify({"result": result})


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)

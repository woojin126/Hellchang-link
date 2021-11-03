import hashlib
from datetime import datetime, timedelta

import jwt
from flask import Flask, render_template, jsonify, request, redirect, url_for
from pymongo import MongoClient

app = Flask(__name__)
# client = MongoClient('mongodb://test:test@localhost', 27017)
client = MongoClient('localhost', 27017)
db = client.dbsparta


@app.route('/category')
def categoryPage():
    return render_template('category.html', name="category")


@app.route('/details')
def DetailsPage():
    return render_template('details.html', name="details")


@app.route('/')
def mainPage():
    return render_template('index.html')


# API
@app.route('/api/register', methods=['POST'])
def register():
    member_Id = request.form['me_id']
    member_Pw = request.form['me_pw']
    member_Email = request.form['me_email']
    member_Name = request.form['me_name']

    pw_hash = hashlib.sha256(member_Pw.encode('utf-8')).hexdigest()

    doc = {
        'id': member_Id,
        'pw': pw_hash,
        'email': member_Email,
        'name': member_Name
    }

    db.hellchangRegister.insert_one(doc)

    return jsonify({'msg': '회원가입이 되었습니다'})


# 회원가입시, 아이디 중복검사 기능
@app.route('/api/register/check_id_dup', methods=['POST'])
def check_id_dup():
    id_receive = request.form['me_id']
    exists = bool(db.hellchangRegister.find_one({"id": id_receive}))  # exists: True or False

    return jsonify({'exists': exists})


# 로그인 기능
SECRET_KEY = 'SPARTA'


@app.route('/api/login', methods=['POST'])
def login():
    member_Id = request.form['me_id']
    member_Pw = request.form['me_pw']

    pw_hash = hashlib.sha256(member_Pw.encode('utf-8')).hexdigest()

    result = db.hellchangRegister.find_one({'me_id': member_Id, 'me_pw': pw_hash})

    if result is not None:
        payload = {
            'id': member_Id,
            'exp': datetime.utcnow() + timedelta(seconds=60 * 60 * 24)
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
        return jsonify({'result': 'success', 'token': token})
    else:
        return jsonify({'result': 'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.'})


@app.route("/api/comment", methods=['POST'])
def comment():
    token_receive = request.cookies.get('token')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        me_id = payload["id"]
        comment = request.form['comment']

        doc = {
            "me_id": me_id,
            "comment": comment
        }

        db.hellchangComment.insert_one(doc)
        return jsonify({"result": "success", 'msg': '댓글 달기 완료'})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("api/login"))


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)

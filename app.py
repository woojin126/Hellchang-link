import hashlib
from datetime import datetime, timedelta

import jwt
from flask import Flask, render_template, jsonify, request
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
@app.route('/register', methods=['POST'])
def register():
    member_Id = request.form['me_id']
    member_Pw = request.form['me_pw']
    member_Email = request.form['me_email']
    member_Name = request.form['me_name']

    pw_hash = hashlib.sha256(member_Pw.encode('utf-8')).hexdigest()

    doc = {
        'me_id': member_Id,
        'me_pw': pw_hash,
        'me_email': member_Email,
        'member_name': member_Name
    }

    db.hellchangRegister.insert_one(doc)

    return jsonify({'msg': '회원가입이 되었습니다'})


# 로그인 기능
SECRET_KEY = 'SPARTA'
@app.route('/login', methods=['POST'])
def login2():
    id_receive = request.form['me_id']
    pw_receive = request.form['me_pw']

    # pw를 암호화
    pw_hash = hashlib.sha256(pw_receive.encode('utf-8')).hexdigest()

    # id, 암호화된 pw로 db에서 유저 찾기
    result = db.hellchangRegister.find_one({'me_id': id_receive, 'me_pw': pw_hash})

    # 결과값이 존재하면, 로그인 성공, JWT 토큰 발급 (payload, SECRET_KEY 필요!)
    if result is not None:
        # 토큰을 발급할 경로(id)와 만료기간(exp) 지정
        payload = {
            'id': id_receive,
            'exp': datetime.utcnow() + timedelta(seconds=60 * 60 * 24)  # 로그인 만료기간 (24시간)
        }
        # 토큰 발급
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
        print('token:' + token)

        # 토큰을 준다
        print('token 발급성공')
        return jsonify({'result': 'success', 'token': token})

        # 존재하지 않으면
    else:
        print('token 발급실패')
        return jsonify({'result': 'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.'})


# 회원가입시, 아이디 중복검사 기능
@app.route('/api/join/check_id_dup', methods=['POST'])
def check_id_dup():
    id_receive = request.form['me_id']
    exists = bool(db.hellchangRegister.find_one({"id": id_receive}))  # exists: True or False
    return jsonify({'exists': exists})

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)

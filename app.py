from flask import Flask, render_template, jsonify, request
from flask_jwt_extended import *

app = Flask(__name__)

from pymongo import MongoClient

# client = MongoClient('mongodb://test:test@localhost', 27017)
client = MongoClient('localhost', 27017)
db = client.dbsparta


@app.route('/api/member', methods=['GET'])
def mainPage():
    return render_template('index.html')


@app.route('/api/sign_up', methods=['POST'])
def register():
    member_Id = request.form['me_id']
    member_Pw = request.form['me_pw']
    member_Email = request.form['me_email']
    member_Name = request.form['me_name']

    doc = {
        'me_id': member_Id,
        'me_pw': member_Pw,
        'me_email': member_Email,
        'member_name': member_Name
    }

    db.hellchangRegister.insert_one(doc)

    return jsonify({'msg': '회원가입이 되었습니다'})


@app.route('/api/login', methods=['POST'])
def login():
    me_id = request.form['me_id']
    me_pw = request.form['me_pw']

    member = db.hellchangRegister.find_one({'me_id': me_id}, {'me_pw': me_pw})
    if member is None:
        return jsonify({'login': False})

    access_token = create_access_token(identity=me_id, expires_delta=False)
    refresh_token = create_refresh_token(identity=me_id)

    resp = jsonify({'login': True})

    set_access_cookies(access_token)
    set_refresh_cookies(refresh_token)

    return resp,200


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)

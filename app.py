from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

from pymongo import MongoClient

# client = MongoClient('mongodb://test:test@localhost', 27017)
client = MongoClient('localhost', 27017)
db = client.dbsparta


# @app.route('/api/member', methods=['GET'])
# def mainPage():
#     return render_template('index.html')


@app.route('/api/member')
def mainPage():
    if request.method == 'GET':
        return render_template('index.html')
    else:
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


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)

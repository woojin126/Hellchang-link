import hashlib
import json
from datetime import datetime, timedelta
from bson.objectid import ObjectId

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


# / 메인페이지 경로의 요청
@app.route('/')
def mainPage():
    # templates/index.html 으로 name = Main이라는 파라미터를 넘겨서 각페이지의 명을 jinja2 템플릿 {{}} 으로 이름적용
    return render_template('index.html', name="Main")


# /category/<파라미터> 농구,축구.야구 카테고리중 하나 클릭하면 keyword로 들어옴
@app.route('/category/<keyword>')
def categoryPage(keyword):
    # category.html에 name,word 파라미터 전송
    return render_template('category.html', name="category", word=keyword)


# 회원 페이지 요청
@app.route('/register')
def registerPage():
    return render_template('register.html', name="register")


# token 만들때 사용하는 키
SECRET_KEY = 'SPARTA'


# 회원가입 요청
@app.route('/sign_up/save', methods=['POST'])
def sign_up():
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']
    email_receive = request.form['email_give']

    # 비밀번호를 암호화해서 db에 삽입
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


# 로그인 폼 데이터 들어오는 router POST 방식은 request body 부분에 데이터가 담겨서 온다
@app.route('/api/login', methods=['POST'])
def login():
    # 작성한 이름, 비밀번호가 넘어오는것이고 request.form은 POST 데이터 받을때 사용
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']

    # 비밀번호 암호화
    pw_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()

    # 로그인폼에서 입력한 아이디와, 암호화한 비밀번호를 사용해서 디비에 있는지 조회
    result = db.users.find_one({'username': username_receive, 'password': pw_hash})

    # result에 값이 있으면 JWT의 payload 부분
    if result is not None:
        # payload는 토큰에서 사용할 정보의 조각들인 클레임(Claim) 토큰만료일자, 발급시간 등 정보를 담는곳
        payload = {
            'id': username_receive,
            'exp': datetime.utcnow() + timedelta(seconds=60 * 60 * 24)
        }

        # payload+비밀키+알고리즘 hs256암호화 로 토큰생성
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256').decode('UTF-8')

        # 성공시 토큰 리턴
        return jsonify({'result': 'success', 'token': token})
    else:
        # 실패시 실패 메시지
        return jsonify({'result': 'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.'})


# 각페이지 상단에 공통 프로필 정보
@app.route("/api/profile")
def profile():
    # 쿠키에있는 token을 꺼내와서
    token = request.cookies.get('token')
    try:
        # 토큰을 부호화해서 아이디값을 꺼냄
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        memberId = payload["id"]
        # 토큰에서 꺼낸 아이디값으로 db에 해당 컬럼을 찾음
        result = db.users.find_one({'username': memberId})
        # 해당컬럼을 반환해줌
        return jsonify({"memberId": result['username']})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        # 토큰 만료가되거나 부호화 문제생길시 다시 로그인페이지로
        return redirect(url_for("login"))


# 댓글 쓰는 api
@app.route("/api/comment", methods=['POST'])
def comment():
    # 어떤 사용자가 댓글을 다는지 알기위해 토큰을 가져옴
    token_receive = request.cookies.get('token')
    try:
        # 암호화된 토큰을 부호화로 풀어냄
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        memberId = payload["id"]
        comment = request.form['comment']
        replyBoardId = request.form['replyBoardId']
        # 어떤 사람이, 댓글을 , 어떤 게시판에 달았는지 알기위한 정보들 db 삽입
        doc = {
            "username": memberId,
            "comment": comment,
            "replyBoardId": replyBoardId
        }

        db.comments.insert_one(doc)
        return jsonify({"result": "success", 'msg': '댓글 달기 완료'})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("api/login"))


# 해당 게시물에 달린 댓글들을 조회하기위한 API
@app.route("/api/comments", methods=['GET'])
def comment_list():
    # 해당게시물 primary key
    replyBoardId = request.args.get('replyBoardId')
    # 해당게시물에 달린 댓글들을 모두조회
    result = list(db.comments.find({'replyBoardId': replyBoardId}))
    # mongodb id는 오브젝트 형태로 되있어서 str 형태로바꿔서 사용
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
        # payload에서 id 정보만 가져와서 username이랑 비교해본다.
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
        # like가 들어오면 좋아요 안누른상태 -> 누른상태
        if action_receive == "like":
            db.likes.insert_one(doc)
        else:
            db.likes.delete_one(doc)
            # 게시물 마다 좋아요 개수
        count = db.likes.count_documents({"post_id": post_id_receive, "type": type_receive})
        return jsonify({"result": "success", 'msg': 'updated', "count": count})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for('mainPage'))


# 카테고리 페이지(category.js)에서 게시물중 하나를 클릭하면 해당 아이디가 /detail/<id>에 바인딩되어 들어옴
@app.route('/details/<id>')
def DetailsPage(id):
    # detail.html에 name,카테고리 게시물 id 전달
    return render_template('details.html', name="details", id=id)

# 상세페이지 정보와 , 좋아요 기능
@app.route("/api/details", methods=['GET'])
def sportsDetails():
    token_receive = request.cookies.get('token')
    try:
        # 현재유저정보
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        # 상세정보 게시물 아이디
        str_id = request.args.get('data_id')
        # 상세정보 게시물 아이디 오브젝트화
        obj_id = ObjectId(str_id)
        # 상세정보 페이지 필드 조회
        result = db.sports.find_one({'_id': obj_id})
        result['_id'] = str(result['_id'])
        # 현재 상세 게시물에 좋아요 개수
        result["count_heart"] = db.likes.count_documents({"post_id": result["_id"], "type": "heart"})
        # 좋아요 눌렸는지 안눌렸는지 상태확인
        result["heart_by_me"] = bool(
            db.likes.find_one({"post_id": result["_id"], "type": "heart", "username": payload['id']}))
        return jsonify({"result": result})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for('mainPage'))


# 게시물 댓글 삭제
@app.route("/api/comments/delete", methods=['POST'])
def commentDelete():
    commentId = request.form['commentId']
    comments = request.form['comments']
    # 게시물삭제버튼 클릭하면 해당게시물 id 를가져와서 삭제
    db.comments.delete_one({'_id': ObjectId(commentId)})

    return jsonify({"msg": "댓글삭제 완료"})


# 경로 / 인 메인페이지에서 선택한 종목 (soccer,baseball,basketball) 변수가 아래 ('category')키값으로 들어온다.
@app.route("/api/sports", methods=['GET'])
def sportsCategory():
    category = request.args.get('category')
    result = list(db.sports.find({'key': category}).sort('data', -1))
    for post in result:
        post['_id'] = str(post['_id'])
        # 카테고리 페이지 좋아요수 표시
        post["count_heart"] = db.likes.count_documents({"post_id": post["_id"], "type": "heart"})
    return jsonify({"result": result})


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)

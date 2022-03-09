from pymongo import MongoClient
import jwt
import datetime
import hashlib
from flask import Flask, render_template, jsonify, request, redirect, url_for
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta

from pymongo import MongoClient
import certifi
ca= certifi.where()

client = MongoClient('mongodb+srv://test:sparta@cluster0.1jgyj.mongodb.net/Cluster0?retryWrites=true&w=majority',tlsCAFile=ca)
db = client.sparta
import requests
from bs4 import BeautifulSoup

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'}
data = requests.get(
    'https://weather.com/ko-KR/weather/today', headers=headers)

soup = BeautifulSoup(data.text, 'html.parser')



location = soup.select_one('#WxuCurrentConditions-main-b3094163-ef75-4558-8d9a-e35e6b9b1034 > div > section > div > div.CurrentConditions--header--27uOE > h1')
temperature= soup.select_one('#WxuCurrentConditions-main-b3094163-ef75-4558-8d9a-e35e6b9b1034 > div > section > div > div.CurrentConditions--body--8sQIV > div.CurrentConditions--columns--3KgfN > div.CurrentConditions--primary--2SVPh > span')
weather = soup.select_one('#WxuCurrentConditions-main-b3094163-ef75-4558-8d9a-e35e6b9b1034 > div > section > div > div.CurrentConditions--body--8sQIV > div.CurrentConditions--columns--3KgfN > div.CurrentConditions--primary--2SVPh > div.CurrentConditions--phraseValue--2Z18W')
image = soup.select_one('#WxuCurrentConditions-main-b3094163-ef75-4558-8d9a-e35e6b9b1034 > div > section > div > div.CurrentConditions--body--8sQIV > div.CurrentConditions--columns--3KgfN > div.CurrentConditions--secondary--2J2Cx > svg')
humidity = soup.select_one('#todayDetails > section > div.TodayDetailsCard--detailsContainer--16Hg0 > div:nth-child(3) > div.WeatherDetailsListItem--wxData--2s6HT > span')
wind = soup.select_one('#todayDetails > section > div.TodayDetailsCard--detailsContainer--16Hg0 > div:nth-child(2) > div.WeatherDetailsListItem--wxData--2s6HT > span')
print(location.text, temperature.text, weather.text, humidity.text, wind.text)

doc = {
    "location": location.text,
    "temperature": temperature.text,
    "weather": weather.text,
    "humidity": humidity.text,
    "wind": wind.text
}
db.weather1.insert_one(doc)


app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config['UPLOAD_FOLDER'] = "./static/profile_pics"

SECRET_KEY = 'SPARTA'

#몽고디비연결
# from pymongo import MongoClient
# import certifi
#
# ca= certifi.where()
#
# client = MongoClient('mongodb+srv://test:sparta@cluster0.1jgyj.mongodb.net/Cluster0?retryWrites=true&w=majority',tlsCAFile=ca)
# db = client.sparta


@app.route('/')
def home():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"username":payload["id"]})
        return render_template('index.html', user_info=user_info)
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))


@app.route('/login')
def login():
    msg = request.args.get("msg")
    return render_template('login.html', msg=msg)


@app.route('/user/<username>')
def user(username):
    # 각 사용자의 프로필과 글을 모아볼 수 있는 공간
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        status = (username == payload["id"])  # 내 프로필이면 True, 다른 사람 프로필 페이지면 False

        user_info = db.users.find_one({"username": username}, {"_id": False})
        return render_template('user.html', user_info=user_info, status=status)
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))


@app.route('/sign_in', methods=['POST'])
def sign_in():
    # 로그인
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']

    pw_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    result = db.users.find_one({'username': username_receive, 'password': pw_hash})

    if result is not None:
        payload = {
            'id': username_receive,
            'exp': datetime.utcnow() + timedelta(seconds=60 * 60 * 24)  # 로그인 24시간 유지
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

        return jsonify({'result': 'success', 'token': token})
    # 찾지 못하면
    else:
        return jsonify({'result': 'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.'})


@app.route('/sign_up/save', methods=['POST'])
def sign_up():
    realname_receive = request.form['realname_give']
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']
    password_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    doc = {
        "realname": realname_receive,  # 회원이름
        "username": username_receive,  # 아이디
        "password": password_hash,  # 비밀번호
        "profile_name": username_receive,  # 프로필 이름 기본값은 아이디
        "profile_pic": "",  # 프로필 사진 파일 이름
        "profile_pic_real": "profile_pics/profile_placeholder.png",  # 프로필 사진 기본 이미지
        "profile_info": ""  # 프로필 한 마디
    }
    db.users.insert_one(doc)
    return jsonify({'result': 'success'})


@app.route('/sign_up/check_dup', methods=['POST'])
def check_dup():
    username_receive = request.form['username_give']
    exists = bool(db.users.find_one({"username": username_receive}))
    return jsonify({'result': 'success', 'exists': exists})

@app.route("/weather", methods=["GET"])
def show_weather():
    weather_list = list(db.weather1.find({}, {'_id': False}))

    return jsonify({'weather': weather_list})



if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)

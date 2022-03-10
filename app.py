from pymongo import MongoClient
import jwt
import datetime
import hashlib
from flask import Flask, render_template, jsonify, request, redirect, url_for
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config['UPLOAD_FOLDER'] = "./static/profile_pics"

SECRET_KEY = 'SPARTA'

# 몽고디비연결
# 크롤링 세팅
from pymongo import MongoClient
import certifi

ca= certifi.where()

client = MongoClient('mongodb+srv://test:sparta@cluster0.1jgyj.mongodb.net/Cluster0?retryWrites=true&w=majority',tlsCAFile=ca)
db = client.sparta

# 타겟 URL을 읽어서 HTML를 받아오고,
# HTML을 BeautifulSoup이라는 라이브러리를 활용해 검색하기 용이한 상태로 만듦
# soup이라는 변수에 "파싱 용이해진 html"이 담긴 상태가 됨
# 이제 코딩을 통해 필요한 부분을 추출하면 된다.

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'}
movie_data = requests.get('https://movie.naver.com/movie/running/current.naver', headers=headers)
moviedata = BeautifulSoup(movie_data.text, 'html.parser')

# 공통 코드 추출




movies = moviedata.select('#content > div.article > div:nth-child(1) > div.lst_wrap > ul > li')
# 반복문 돌면서 아래 코드 실행
db.movieData.drop();
for movie in movies:
    title = movie.select_one('dl > dt > a').text
    if title is not None:

        movieName = title
        movieImage = movie.select_one('div > a > img')['src']
        movieScore = movie.select_one('dl > dd.star > dl.info_star > dd > div > a > span.num').text
        movieJenre = movie.select_one('dl > dd:nth-child(3) > dl > dd:nth-child(2) > span.link_txt > a:nth-child(1)').text
        movielink = movie.select_one('dl > dd.info_t1 > div > a')['href']


        doc = {
            'movieNm': movieName,
            'movieImg': movieImage,
            'movieScr': movieScore,
            'movieJnr': movieJenre,
            'movielink': movielink

        }
        db.movieData.insert_one(doc)



data = requests.get('https://search.naver.com/search.naver?where=nexearch&sm=top_hty&fbm=1&ie=utf8&query=%EB%82%A0%EC%94%A8',headers=headers)

soup = BeautifulSoup(data.text, 'html.parser')

location = soup.select_one('#main_pack > section.sc_new.cs_weather_new._cs_weather > div._tab_flicking > div.top_wrap > div.title_area._area_panel > h2.title')
temperature = soup.select_one('#main_pack > section.sc_new.cs_weather_new._cs_weather > div._tab_flicking > div.content_wrap > div.open > div:nth-child(1) > div > div.weather_info > div > div.weather_graphic > div.temperature_text')
image = soup.select_one('#main_pack > section.sc_new.cs_weather_new._cs_weather > div._tab_flicking > div.content_wrap > div.open > div:nth-child(1) > div > div.weather_info > div > div.weather_graphic > div.weather_main > i')
humidity = soup.select_one('#main_pack > section.sc_new.cs_weather_new._cs_weather > div._tab_flicking > div.content_wrap > div.open > div:nth-child(1) > div > div.weather_info > div > div.temperature_info > dl > dd:nth-child(4)')
wind = soup.select_one('#main_pack > section.sc_new.cs_weather_new._cs_weather > div._tab_flicking > div.content_wrap > div.open > div:nth-child(1) > div > div.weather_info > div > div.temperature_info > dl > dd:nth-child(6)')
weather = soup.select_one('#main_pack > section.sc_new.cs_weather_new._cs_weather > div._tab_flicking > div.content_wrap > div.open > div:nth-child(1) > div > div.weather_info > div > div.temperature_info > p > span.weather.before_slash')
# print('습도:', humidity.text ,image, '오늘의 날씨는?', weather.text , '기온:', temperature.text , '바람:',wind.text , location.text)

doc = {
    'weather': weather.text,
    'temperature': temperature.text,
    'humidity': humidity.text,
    'wind': wind.text,
    'location': location.text
}
db.weather.insert_one(doc)


app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config['UPLOAD_FOLDER'] = "./static/profile_pics"

SECRET_KEY = 'SPARTA'




@app.route('/')
def home():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"username": payload["id"]})
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
    username_receive = request.form['username_give']  # username_give로 받은 데이터를 username_receive에 저장
    password_receive = request.form['password_give']

    pw_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()  # password_receive에 있는 비밀번호를 암호화
    result = db.users.find_one({'username': username_receive, 'password': pw_hash})  # db에서 아이디와 암호화된 비밀번호가 있는지 찾기

    if result is not None:  # 결과가 있는 경우
        payload = {  # 페이로드에 아이디와 만료시간을 저장
            'id': username_receive,
            'exp': datetime.utcnow() + timedelta(seconds=60 * 60 * 24)  # 로그인 24시간 유지
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')  # 토큰에 페이로드/시크릿키를 담기

        return jsonify({'result': 'success', 'token': token})  # 토큰 전달
    # 찾지 못하면
    else:
        return jsonify({'result': 'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.'})


@app.route('/sign_up/save', methods=['POST'])
def sign_up():
    userRealName_receive = request.form['userRealName_give']
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']
    password_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    doc = {
        "userRealName": userRealName_receive,  # 회원이름
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



@app.route('/posting', methods=['POST'])
def posting():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        # 포스팅하기
        return jsonify({"result": "success", 'msg': '포스팅 성공'})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))


@app.route("/get_posts", methods=['GET'])
def get_posts():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        # 포스팅 목록 받아오기
        return jsonify({"result": "success", "msg": "포스팅을 가져왔습니다."})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))

@app.route("/weather", methods=['GET'])
def weather():
    weather_list = list(db.weather.find({}, {'_id': False}))
    return jsonify({'weather': weather_list})

# 영화 전체 데이터
@app.route("/movieData", methods=["GET"])
def movie_listing():
    movie_list = list(db.movieData.find({}, {'_id': False}))
    return jsonify({'movies': movie_list})

@app.route("/Sunmovie", methods=["GET"])
def movie_A():
    movie_list = list(db.movieData.find({}, {'_id': False}))
    return jsonify({'Sun': movie_list})





@app.route('/update_like', methods=['POST'])
def update_like():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        # 좋아요 수 변경
        return jsonify({"result": "success", 'msg': 'updated'})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)

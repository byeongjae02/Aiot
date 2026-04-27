from flask import Flask, request, render_template # flask 라이브러리에서 Flask, request, render_template 가져옴
from gpiozero import LED # gpiozero 라이브러리에서 LED 클래스 가져옴

app = Flask(__name__) # Flask 웹서버 객체 생성

red_led = LED(21) # LED를 GPIO 21번 핀에 연결하여 객체 생성

@app.route('/') # 기본 주소로 접속했을 때 실행되는 경로 설정
def home(): # home 함수 정의
   return render_template("index.html") # templates 폴더 안에 있는 index.html 파일을 웹페이지로 보여줌

@app.route('/data', methods = ['POST']) # /data 주소로 POST 방식 요청이 들어왔을 때 실행되는 경로 설정
def data(): # data 함수 정의
    data = request.form['led'] # 웹페이지에서 사용자가 누른 버튼 값을 led라는 이름으로 받아와 data 변수에 저장
    
    if(data == 'on'): # 받아온 값이 on이면 LED를 켜는 조건문
        red_led.on() # GPIO 21번 핀에 연결된 LED를 켬
        return home() # LED를 켠 뒤 다시 기본 웹페이지 화면을 보여줌

    elif(data == 'off'): # 받아온 값이 off이면 LED를 끄는 조건문
        red_led.off() # GPIO 21번 핀에 연결된 LED를 끔
        return home() # LED를 끈 뒤 다시 기본 웹페이지 화면을 보여줌

if __name__ == '__main__': # 현재 파일을 직접 실행했을 때만 아래 코드가 실행되도록 함
   app.run(host = '0.0.0.0', port = '80') # Flask 웹서버를 모든 IP에서 접속 가능하게 하고 80번 포트로 실행
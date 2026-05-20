import speech_recognition as sr  # 마이크에서 음성을 입력받아 텍스트로 변환하기 위한 speech_recognition 라이브러리 가져옴
import requests  # OpenWeatherMap API에 HTTP 요청을 보내기 위한 requests 라이브러리 가져옴
import os  # 운영체제 명령어(espeak)를 실행하기 위한 os 라이브러리 가져옴
import time  # 시간 지연 처리를 위한 time 라이브러리 가져옴

API_KEY = "Enter your API key here"  # OpenWeatherMap에서 발급받은 개인 API 키 입력 (각 실험 환경의 API 키로 변경 필요)
url = f"https://api.openweathermap.org/data/2.5/weather?q=Seoul&appid={API_KEY}&units=metric"  # 서울의 현재 날씨 정보를 섭씨 단위로 요청하는 OpenWeatherMap API URL 구성

def speak(option, msg):  # 입력받은 텍스트를 espeak TTS 엔진을 통해 음성으로 출력하는 함수 정의
    os.system("espeak {} '{}'".format(option, msg))  # espeak 명령어에 옵션과 메시지를 전달하여 한글 음성으로 출력

try:  # 키보드 인터럽트(Ctrl+C) 발생 시 프로그램이 정상 종료되도록 외부 try 블록으로 감쌈
    while True:  # True가 항상 참이므로 무한 반복하여 연속적인 음성 인식 수행
        r = sr.Recognizer()  # 음성 인식 처리를 담당하는 Recognizer 객체 생성
        
        with sr.Microphone() as source:  # 시스템 기본 마이크를 입력 소스로 설정 (with 구문으로 자동 자원 관리)
            print("Say something!")  # 사용자에게 음성 입력을 요청하는 안내 메시지 출력
            audio = r.listen(source)  # 마이크로부터 음성을 녹음하여 audio 변수에 오디오 데이터로 저장
            
        try:  # 음성 인식 과정에서 발생할 수 있는 예외를 처리하기 위한 내부 try 블록
            text = r.recognize_google(audio, language='ko-KR')  # 녹음된 오디오를 Google Web Speech API로 전송하여 한국어(ko-KR) 텍스트로 변환
            print("You said: " + text)  # 인식된 텍스트를 터미널에 출력
            if text in "날씨":  # 인식된 텍스트가 "날씨" 문자열에 포함되는지 확인 (키워드 매칭)
                print("날씨 음성을 인식하였습니다.")  # 키워드 매칭 성공 메시지를 터미널에 출력
                response = requests.get(url)  # OpenWeatherMap API에 GET 요청을 전송하여 응답 객체 수신
                data = response.json()  # 응답 객체의 본문을 JSON 형식으로 파싱하여 Python 딕셔너리로 변환
                temp = data["main"]["temp"]  # JSON 데이터에서 현재 기온(섭씨) 값 추출
                humi = data["main"]["humidity"]  # JSON 데이터에서 현재 습도(%) 값 추출
                
                msg = '    기온은 ' + str(int(temp)) + '도 습도는 ' + str(humi) + '퍼센트 입니다'  # 추출한 기온과 습도 값을 포함하는 한글 안내 문장 생성
                
                option = '-s 180 -p 50 -a 200 -v ko+f5'  # espeak 옵션 설정 (속도 180, 음높이 50, 음량 200, 한국어 여성 음성 ko+f5)
                speak(option, msg)  # speak 함수를 호출하여 안내 문장을 한글 음성으로 출력
            
        except sr.UnknownValueError:  # 음성은 감지되었으나 내용을 인식하지 못한 경우 발생하는 예외 처리
            print("Google Speech Recognition could not understand audio")  # 음성 인식 실패 메시지를 터미널에 출력
        except sr.RequestError as e:  # Google Speech API 서버 요청 자체가 실패한 경우 발생하는 예외 처리
            print("Could not request results from Google Speech Recognition service; {0}".format(e))  # API 요청 실패 메시지와 함께 오류 내용 출력

except KeyboardInterrupt:  # Ctrl+C 키 입력 시 발생하는 KeyboardInterrupt 예외 처리
    pass  # 아무 처리 없이 무한 루프를 탈출하여 프로그램 정상 종료
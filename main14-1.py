from gpiozero import MotionSensor # gpiozero 라이브러리에서 MotionSensor 클래스 가져옴
import time # time 라이브러리를 가져옴
from picamera2 import Picamera2 # picamera2 라이브러리에서 Picamera2 클래스 가져옴
import datetime # 날짜와 시간 정보를 다루기 위한 datetime 라이브러리 가져옴

pirPin = MotionSensor(16) # PIR 인체감지센서를 GPIO 16번 핀에 연결하여 객체 생성

picam2 = Picamera2() # Picamera2 객체 생성
camera_config = picam2.create_preview_configuration() # 카메라 미리보기 설정 생성
picam2.configure(camera_config) # 생성한 카메라 설정을 적용
picam2.start() # 카메라 작동 시작

try: # 오류가 날 수 있는 코드를 감싸는 역할
    while True: # True는 계속 반복하라는 뜻(무한루프)
        try: # 센서 감지 및 사진 촬영 중 오류가 날 수 있는 부분을 감쌈
            sensorValue = pirPin.value # PIR 센서의 현재 값을 읽어서 sensorValue 변수에 저장
            if sensorValue == 1: # 센서값이 1이면 움직임이 감지된 상태
                now = datetime.datetime.now() # 현재 날짜와 시간을 가져옴
                print(now) # 감지된 현재 시간을 터미널에 출력
                fileName = now.strftime('%Y-%m-%d %H:%M:%S') # 현재 시간을 파일 이름 형식의 문자열로 변환
                picam2.capture_file(fileName + '.jpg') # 파일 이름 뒤에 .jpg를 붙여 사진을 촬영하고 저장
                time.sleep(0.5) # 연속 촬영이 너무 많이 되지 않도록 0.5초 대기
        except: # 촬영 중 오류가 발생하더라도 프로그램이 멈추지 않게 함
            pass

except KeyboardInterrupt: # 사용자가 키보드로 강제종료시 오류없이 넘어감
    pass
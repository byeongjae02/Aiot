import paho.mqtt.client as mqtt  # MQTT 클라이언트 기능을 사용하기 위한 paho.mqtt.client 라이브러리 가져옴
import time  # 시간 지연 처리를 위한 time 라이브러리 가져옴
from gpiozero import LED  # 라즈베리파이 GPIO 핀을 제어하기 위한 gpiozero 라이브러리에서 LED 클래스 가져옴
import threading  # 메시지 발행과 구독을 동시에 처리하기 위한 threading 라이브러리 가져옴

greenLed = LED(16)  # GPIO 16번 핀에 연결된 초록 LED 객체 생성
blueLed = LED(20)  # GPIO 20번 핀에 연결된 파랑 LED 객체 생성
redLed = LED(21)  # GPIO 21번 핀에 연결된 빨강 LED 객체 생성

def on_message(client, userdata, msg):  # MQTT 브로커로부터 메시지를 수신했을 때 자동으로 호출되는 콜백 함수 정의
    print(msg.topic+" "+str(msg.payload))  # 터미널에 수신한 메시지의 토픽과 페이로드를 출력
    message = msg.payload.decode()  # 바이트 형태의 페이로드를 UTF-8 문자열로 디코딩
    print(message)  # 디코딩된 메시지 내용을 터미널에 출력
    if message == "green_on":  # 수신한 메시지가 "green_on"이면
        greenLed.on()  # GPIO 16번 핀을 HIGH 상태로 전환하여 초록 LED 켜기
    elif message == "green_off":  # 수신한 메시지가 "green_off"이면
        greenLed.off()  # GPIO 16번 핀을 LOW 상태로 전환하여 초록 LED 끄기
    elif message == "blue_on":  # 수신한 메시지가 "blue_on"이면
        blueLed.on()  # GPIO 20번 핀을 HIGH 상태로 전환하여 파랑 LED 켜기
    elif message == "blue_off":  # 수신한 메시지가 "blue_off"이면
        blueLed.off()  # GPIO 20번 핀을 LOW 상태로 전환하여 파랑 LED 끄기
    elif message == "red_on":  # 수신한 메시지가 "red_on"이면
        redLed.on()  # GPIO 21번 핀을 HIGH 상태로 전환하여 빨강 LED 켜기
    elif message == "red_off":  # 수신한 메시지가 "red_off"이면
        redLed.off()  # GPIO 21번 핀을 LOW 상태로 전환하여 빨강 LED 끄기

client = mqtt.Client()  # MQTT 클라이언트 객체 생성
client.on_message = on_message  # 메시지 수신 시 호출될 콜백 함수를 on_message 함수로 등록

broker_address="192.168.137.230"  # MQTT 브로커가 실행 중인 라즈베리파이의 IP 주소 입력 (각 실험 환경의 IP 주소로 변경 필요)
client.connect(broker_address)  # 지정한 브로커 IP 주소로 MQTT 브로커에 연결
client.subscribe("led",1)  # "led" 토픽을 QoS 1 수준으로 구독 (QoS 1은 최소 1회 이상 메시지 전달 보장)

count = 0  # PC로 전송할 카운트 값을 저장할 변수 초기화
def send_thread():  # 별도 스레드에서 주기적으로 메시지를 발행하는 함수 정의
    global count  # 함수 외부에 선언된 count 변수를 함수 내부에서 수정할 수 있도록 global 키워드 사용
    while 1:  # 1은 항상 참이므로 무한 반복
        count = count + 1  # 카운트 값을 1 증가
        client.publish("hello", str(count))  # "hello" 토픽으로 현재 카운트 값을 문자열로 변환하여 발행
        time.sleep(1.0)  # 1초 동안 대기한 뒤 다시 메시지 발행

task = threading.Thread(target = send_thread)  # send_thread 함수를 실행할 스레드 객체 생성
task.start()  # 생성한 스레드를 시작하여 send_thread 함수가 별도 스레드에서 실행되도록 함

client.loop_forever()  # 메시지 수신 대기 무한 루프 실행 (이 함수는 프로그램을 차단하지만 별도 스레드에서 메시지 발행이 계속됨)
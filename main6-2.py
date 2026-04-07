from gpiozero import Buzzer, DigitalInputDevice  # gpiozero 라이브러리에서 Buzzer와 DigitalInputDevice 클래스 가져옴
import time  # time 라이브러리 가져옴

bz = Buzzer(18)  # GPIO 18번 핀에 연결된 부저 객체 생성
gas = DigitalInputDevice(17)  # GPIO 17번 핀에 연결된 가스 센서 객체 생성

try:  # 오류가 날 수 있는 코드를 감싸는 역할
    while True:  # True는 항상 참이므로 무한 반복
        if gas.value == 0:  # gas.value가 0이면 가스가 감지된 상태(LOW 신호)
            print("가스 감지됨")  # 터미널에 가스 감지 메시지 출력
            bz.on()  # 부저 켜기
        else:  # gas.value가 1이면 정상 상태(HIGH 신호)
            print("정상")  # 터미널에 정상 메시지 출력
            bz.off()  # 부저 끄기

        time.sleep(0.2)  # 0.2초마다 센서 상태를 반복 확인

except KeyboardInterrupt:  # 사용자가 키보드로 강제종료 시 오류 없이 넘어감
    pass

bz.off()  # 프로그램 종료 시 부저 끄기
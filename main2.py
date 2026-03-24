from gpiozero import LED # gpiozero 라이브러리에서 LED클래스 가져옴
from time import sleep # Time 라이브러리에서 sleep함수 가져옴

# 차량 신호등 LED가 연결된 GPIO 핀 설정
carLedRed = LED(2)      # 차량용 빨간불
carLedBlue = LED(3)     # 차량용 파란불
carLedGreen = LED(4)    # 차량용 초록불

# 보행자 신호등 LED가 연결된 GPIO 핀 설정
humanLedRed = LED(20)   # 보행자용 빨간불
humanLedGreen = LED(21) # 보행자용 초록불

try: # 오류가 날 수 있는 코드를 감싸는 역할
    while 1: # 1은 True로 취급(무한루프)
        # 차량 - 초록불 / 보행자 - 빨간불
        carLedRed.value = 0
        carLedBlue.value = 0
        carLedGreen.value = 1
        humanLedRed.value = 1
        humanLedGreen.value = 0
        sleep(3.0) # 현재상태 3초 유지

        # 차량 - 파란불 / 보행자 - 빨간불
        carLedRed.value = 0
        carLedBlue.value = 1
        carLedGreen.value = 0
        humanLedRed.value = 1
        humanLedGreen.value = 0
        sleep(1.0) # 현재상태 1초 유지

        # 차량 - 빨간불 / 보행자 - 초록불
        carLedRed.value = 1
        carLedBlue.value = 0
        carLedGreen.value = 0
        humanLedRed.value = 0
        humanLedGreen.value = 1
        sleep(3.0) # 현재상태 3초 유지

except KeyboardInterrupt: # 사용자가 키보드로 강제종료시 오류없이 넘어감
    pass

# 프로그램 종료 시 모든 LED 끄기
carLedRed.value = 0
carLedBlue.value = 0
carLedGreen.value = 0
humanLedRed.value = 0
humanLedGreen.value = 0
import urllib.request  # URL을 통해 외부 API 서버에 요청을 보내기 위한 urllib.request 라이브러리 가져옴
import json  # JSON 형식의 데이터를 Python 딕셔너리 형태로 변환하기 위한 json 라이브러리 가져옴
import datetime  # 현재 날짜와 시간을 확인하기 위한 datetime 라이브러리 가져옴
import asyncio  # 비동기 처리를 하기 위한 asyncio 라이브러리 가져옴
from telegram import Bot  # telegram 라이브러리에서 Bot 클래스 가져옴

telegram_id = 'Enter your chat ID here'  # 텔레그램 메시지를 받을 채팅방의 chat_id 입력
my_token = 'Enter your bot token here'  # 텔레그램 봇을 제어하기 위한 bot token 입력
api_key = 'Enter your API key here'  # OpenWeatherMap API를 사용하기 위한 API key 입력 (각 api키,토큰,id는 개인정보임으로 깃허브에 업로드x)

bot = Bot(token=my_token)  # 입력한 bot token을 이용하여 텔레그램 봇 객체 생성

ALERT_HOURS = [7, 10, 13, 16, 19, 22]  # 7시, 10시, 13시, 16시, 19시, 22시에 알림을 보내기 위한 시간 목록
ALERT_TIMES = ["08:30", "15:20"]  # 사용자가 직접 지정한 시간에 알림을 보내기 위한 시간 목록

def getWeather():  # OpenWeatherMap API에서 날씨 정보를 가져오는 함수 정의
    url = f"https://api.openweathermap.org/data/2.5/forecast?q=Seoul&appid={api_key}&units=metric&lang=en&cnt=8"  # 서울의 3시간 간격 날씨 예보 데이터를 요청하는 URL 생성

    with urllib.request.urlopen(url) as r:  # 생성한 URL로 OpenWeatherMap 서버에 요청을 보내고 응답을 받아옴
        data = json.loads(r.read())  # 서버에서 받은 JSON 데이터를 Python에서 사용할 수 있는 딕셔너리 형태로 변환

    text = ""  # 텔레그램으로 전송할 날씨 메시지를 저장할 문자열 변수 생성

    for i in range(8):  # 3시간 간격으로 제공되는 날씨 예보 데이터 8개를 반복 처리
        item = data['list'][i]  # 전체 날씨 데이터 중 i번째 예보 데이터를 가져옴
        hour = str((int(item['dt_txt'][11:13]) + 9) % 24).zfill(2)  # UTC 기준 시간을 한국 시간으로 변환하고 두 자리 형식으로 맞춤
        temp = item['main']['temp']  # 해당 시간대의 기온 정보 가져옴
        humi = item['main']['humidity']  # 해당 시간대의 습도 정보 가져옴
        desc = item['weather'][0]['description']  # 해당 시간대의 날씨 설명 정보 가져옴
        text += f"({hour}h {temp}C {humi}% {desc})\n"  # 시간, 기온, 습도, 날씨 설명을 하나의 문자열로 추가

    return text  # 완성된 날씨 예보 문자열을 반환

async def main():  # 텔레그램 알림을 비동기 방식으로 실행하는 main 함수 정의
    try:  # 오류가 날 수 있는 코드를 감싸는 역할
        while True:  # True는 항상 참이므로 무한 반복
            now = datetime.datetime.now()  # 현재 날짜와 시간 정보를 가져옴
            hm = now.strftime('%H:%M')  # 현재 시간을 HH:MM 형식의 문자열로 변환

            is_alert_hour = now.hour in ALERT_HOURS and now.minute == 0 and now.second == 0  # 현재 시간이 정해진 정각 알림 시간인지 확인
            is_alert_time = hm in ALERT_TIMES and now.second == 0  # 현재 시간이 사용자가 직접 지정한 알림 시간인지 확인

            if is_alert_hour or is_alert_time:  # 정각 알림 시간이거나 사용자 지정 알림 시간이면 실행
                msg = getWeather()  # OpenWeatherMap API에서 날씨 정보를 가져와 메시지 문자열 생성
                print(msg)  # 터미널에 전송할 날씨 메시지 출력
                await bot.send_message(chat_id=telegram_id, text=msg)  # 텔레그램 봇을 통해 지정된 chat_id로 날씨 메시지 전송

            await asyncio.sleep(1)  # 1초 동안 대기한 뒤 다시 현재 시간을 확인

    except KeyboardInterrupt:  # 사용자가 키보드로 강제종료 시 오류 없이 넘어감
        pass  # 별도 동작 없이 프로그램 종료 처리

asyncio.run(main())  # main 함수를 비동기 방식으로 실행
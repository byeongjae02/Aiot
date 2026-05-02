import urllib.request, json, tkinter, tkinter.font # urllib.request, json, tkinter, tkinter.font 라이브러리 가져옴

API_KEY = "YOUR_OPENWEATHERMAP_API_KEY" # OpenWeatherMap에서 발급받은 API Key를 저장함 (개인 API는 깃허브등 공유폴더에는 입력 X)

def tick1Min(): # 온도와 습도 데이터를 가져와 GUI 화면에 표시하는 함수 정의
    url = f"https://api.openweathermap.org/data/2.5/weather?q=Seoul&appid={API_KEY}&units=metric" # 서울의 현재 날씨 데이터를 요청하기 위한 OpenWeatherMap API 주소 생성
    
    with urllib.request.urlopen(url) as r: # 생성한 URL로 OpenWeatherMap 서버에 요청을 보내고 응답 데이터를 받아옴
        data = json.loads(r.read()) # 서버에서 받은 JSON 형식의 데이터를 Python에서 사용할 수 있는 형태로 변환함
    
    temp = data["main"]["temp"] # JSON 데이터에서 현재 온도 값을 가져와 temp 변수에 저장함
    humi = data["main"]["humidity"] # JSON 데이터에서 현재 습도 값을 가져와 humi 변수에 저장함
    
    label.config(text=f"{temp:.1f}C   {humi}%") # 가져온 온도와 습도 값을 GUI 화면의 Label에 표시함
    window.after(60000, tick1Min) # 60000ms, 즉 60초 후에 tick1Min 함수를 다시 실행하여 값을 갱신함

window = tkinter.Tk() # tkinter를 이용하여 GUI 창 객체 생성
window.title("TEMP HUMI DISPLAY") # GUI 창의 제목을 TEMP HUMI DISPLAY로 설정
window.geometry("400x100") # GUI 창의 크기를 가로 400, 세로 100으로 설정
window.resizable(False, False) # GUI 창의 크기를 사용자가 변경하지 못하도록 설정

font = tkinter.font.Font(size=30) # GUI에 표시할 글자의 크기를 30으로 설정
label = tkinter.Label(window, text="", font=font) # 온도와 습도 값을 표시할 Label 위젯 생성
label.pack() # 생성한 Label 위젯을 GUI 창에 배치함

tick1Min() # 프로그램 실행 시 바로 온도와 습도 데이터를 가져와 화면에 표시함
window.mainloop() # GUI 창이 종료되지 않고 계속 실행되도록 이벤트 루프 시작
# server.py
# 무인 카페 좌석 효율 분석 대시보드 (웹서버 담당)
# - Flask 웹서버로 대시보드 화면을 제공함
# - 카메라는 사용하지 않고, analyze.py 가 저장한 data/stats.json 만 읽음
# 실행:  python server.py
# 접속:  같은 기기 http://localhost:5000 / 다른 기기 http://<라즈베리파이IP>:5000

import os  # 파일 경로 처리를 위한 os 라이브러리 가져옴
import json  # 통계 파일을 읽기 위한 json 라이브러리 가져옴
from flask import Flask, jsonify, render_template  # 웹서버 구성을 위한 Flask 관련 기능들 가져옴

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # 현재 코드 파일이 위치한 폴더 경로를 구함
DATA_FILE = os.path.join(BASE_DIR, "data", "stats.json")  # 통계가 저장된 stats.json 파일 경로 지정

app = Flask(__name__)  # Flask 웹 애플리케이션 객체 생성

@app.route("/")  # 기본 주소(/)로 접속하면 아래 함수가 실행되도록 경로 지정
def dashboard():  # 대시보드 화면을 보여주는 함수 정의
    return render_template("dashboard.html")  # templates 폴더의 dashboard.html을 렌더링하여 반환

@app.route("/api/stats")  # /api/stats 주소로 접속하면 아래 함수가 실행되도록 경로 지정
def api_stats():  # 통계 데이터를 JSON으로 전달하는 함수 정의
    try:  # 통계 파일 읽기를 시도
        with open(DATA_FILE, "r", encoding="utf-8") as f:  # 통계 파일을 읽기 모드로 열고
            return jsonify(json.load(f))  # 파일 내용을 JSON 형태로 변환하여 응답
    except Exception:  # 파일이 없거나 읽기에 실패하면 (분석 시작 전 등)
        return jsonify({  # 빈 통계 구조를 만들어 응답
            "updated": "데이터 수집 대기 중", "seats": 8, "total": 0,  # 갱신 안내·좌석 수·총 세션 0
            "type": {"work": 0, "drink": 0, "etc": 0},  # 이용 유형별 0
            "gender": {"male": 0, "female": 0, "unknown": 0},  # 성별별 0
            "dwell": {"work_sum": 0, "work_n": 0, "drink_sum": 0, "drink_n": 0},  # 체류시간 0
            "hourly": {f"{h:02d}": {"sessions": 0, "occ_sum": 0, "occ_n": 0, "occ_peak": 0}  # 시간대별
                       for h in range(24)},  # 0~23시 0으로 초기화
            "live": {"persons": 0, "type": "-", "occ_pct": 0},  # 실시간 상태 0
        })

if __name__ == "__main__":  # 이 파일이 직접 실행될 때만 아래 코드를 수행
    app.run(host="0.0.0.0", port=5000, debug=False)  # 5000 포트에서 외부 접속을 허용하여 웹서버 실행

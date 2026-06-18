# analyze.py
# 무인 카페/스터디카페 좌석 효율 분석기 (카메라 담당)
# - 물체검출(MobileNet-SSD)로 손님(person)과 물건을 인식함
#     작업형 단서: 노트북/책/키보드/마우스   |   음료형 단서: 컵/병
# - 손님이 머무는 한 번을 "세션"으로 보고, 작업형/음료형으로 분류해 통계 저장
# - 시간대별 좌석 점유율(동시 인원/좌석수)과 평균 체류시간을 기록
# - 검출 박스가 그려진 영상을 별도 포트(5001)로 실시간 송출(CCTV)
# - 성별은 보조 지표로, 세션 시작 시 1회만 추정 (모델 없으면 자동 생략)
# 실행:  python analyze.py
# 주의:  이 코드만 카메라를 사용함. server.py 는 통계 파일만 읽음.

import os  # 파일 경로 처리를 위한 os 라이브러리 가져옴
import cv2  # 영상 처리 및 객체 검출을 위한 OpenCV 라이브러리 가져옴
import json  # 통계 데이터를 파일로 저장·불러오기 위한 json 라이브러리 가져옴
import time  # 시간 측정 및 대기 처리를 위한 time 라이브러리 가져옴
import datetime  # 날짜·시간(시간대 집계)을 다루기 위한 datetime 라이브러리 가져옴
import threading  # 영상 스트림을 별도 스레드로 실행하기 위한 threading 라이브러리 가져옴
from flask import Flask, Response  # 실시간 검출 영상(CCTV)을 송출하기 위한 Flask, Response 가져옴

# ---------------------------------------------------------------------------
# 1) 매장/측정 설정  (← 본인 매장에 맞게 숫자만 바꾸면 됨)
# ---------------------------------------------------------------------------
SEATS = 8                 # 매장 총 좌석 수 (좌석 점유율 계산 기준) 지정
CONF_THRESHOLD = 0.45     # 객체 검출 신뢰도 기준값 지정 (이 값 미만 검출은 무시)
ABSENCE_DEBOUNCE = 3.0    # 손님이 이 시간(초) 이상 안 보이면 세션 종료로 판단하는 기준 지정
MIN_SESSION_SEC = 1.5     # 이보다 짧게 감지된 세션은 오작동으로 보고 무시하는 기준 지정
OCC_SAMPLE_EVERY = 5.0    # 좌석 점유 인원을 몇 초마다 표본 측정할지 주기 지정
LIVE_SAVE_EVERY = 2.0     # 대시보드 실시간 표시용 데이터를 몇 초마다 저장할지 주기 지정

WORK_ITEMS  = {"laptop", "book", "keyboard", "mouse"}  # 작업형으로 분류할 사물 목록 지정
DRINK_ITEMS = {"cup", "bottle"}  # 음료형으로 분류할 사물 목록 지정

# ---------------------------------------------------------------------------
# 2) 경로 및 모델 파일
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # 현재 코드 파일이 위치한 폴더 경로를 구함
DATA_FILE = os.path.join(BASE_DIR, "data", "stats.json")  # 통계를 저장할 stats.json 파일 경로 지정
MODELS_DIR = os.path.join(BASE_DIR, "models")  # 모델 파일들이 들어 있는 models 폴더 경로 지정

OD_WEIGHTS = os.path.join(MODELS_DIR, "frozen_inference_graph.pb")  # 객체 검출 모델의 가중치 파일 경로 지정
OD_CONFIG  = os.path.join(MODELS_DIR, "ssd_mobilenet_v2_coco_2018_03_29.pbtxt")  # 객체 검출 모델의 구조 파일 경로 지정

FACE_CASCADE = os.path.join(MODELS_DIR, "haarcascade_frontalface_alt.xml")  # (보조)성별 추정용 얼굴 검출 모델 경로 지정
GENDER_PROTO = os.path.join(MODELS_DIR, "deploy_gender.prototxt")  # (보조)성별 분류 모델의 구조 파일 경로 지정
GENDER_MODEL = os.path.join(MODELS_DIR, "gender_net.caffemodel")  # (보조)성별 분류 모델의 가중치 파일 경로 지정
MODEL_MEAN = (78.4263377603, 87.7689143744, 114.895847746)  # 성별 모델 전처리에 사용하는 평균값 지정
GENDER_LIST = ["male", "female"]  # 성별 모델이 출력하는 분류 라벨(남/여) 지정

# 검출 결과 번호(classId)를 사물 이름으로 바꾸기 위한 COCO 90개 클래스 이름 목록 지정
COCO = ["unlabeled","person","bicycle","car","motorcycle","airplane","bus","train",
"truck","boat","traffic light","fire hydrant","street sign","stop sign","parking meter",
"bench","bird","cat","dog","horse","sheep","cow","elephant","bear","zebra","giraffe","hat",
"backpack","umbrella","shoe","eye glasses","handbag","tie","suitcase","frisbee","skis",
"snowboard","sports ball","kite","baseball bat","baseball glove","skateboard","surfboard",
"tennis racket","bottle","plate","wine glass","cup","fork","knife","spoon","bowl","banana",
"apple","sandwich","orange","broccoli","carrot","hot dog","pizza","donut","cake","chair",
"couch","potted plant","bed","mirror","dining table","window","desk","toilet","door","tv",
"laptop","mouse","remote","keyboard","cell phone","microwave","oven","toaster","sink",
"refrigerator","blender","book","clock","vase","scissors","teddy bear","hair drier","toothbrush"]

# ---------------------------------------------------------------------------
# 3) 통계 초기화 / 저장
# ---------------------------------------------------------------------------
def empty_stats():  # 통계를 처음부터 새로 시작할 때 사용할 빈 통계 구조를 만드는 함수 정의
    return {  # 아래 항목들로 구성된 통계 딕셔너리를 반환
        "date": datetime.date.today().isoformat(),  # 오늘 날짜를 기록 (날짜가 바뀌면 통계 초기화 기준이 됨)
        "updated": "",  # 마지막으로 갱신된 시각 (저장 시 채워짐)
        "seats": SEATS,  # 좌석 수를 통계에 함께 저장
        "total": 0,  # 총 세션(방문) 수 0으로 초기화
        "type": {"work": 0, "drink": 0, "etc": 0},  # 이용 유형별(작업/음료/기타) 세션 수 0으로 초기화
        "gender": {"male": 0, "female": 0, "unknown": 0},  # (보조)성별별 세션 수 0으로 초기화
        "dwell": {"work_sum": 0.0, "work_n": 0,  # 작업형 체류시간 합계·건수(평균 계산용) 초기화
                  "drink_sum": 0.0, "drink_n": 0},  # 음료형 체류시간 합계·건수(평균 계산용) 초기화
        "hourly": {f"{h:02d}": {"sessions": 0, "occ_sum": 0, "occ_n": 0, "occ_peak": 0}  # 0~23시 시간대별
                   for h in range(24)},  # 세션수·점유인원합·표본수·최대인원을 0으로 초기화
        "live": {"persons": 0, "type": "-", "occ_pct": 0},  # 대시보드 실시간 표시용 현재 상태 초기화
    }

def load_stats():  # 기존 통계 파일을 불러오거나, 없으면 새 통계를 만드는 함수 정의
    today = datetime.date.today().isoformat()  # 오늘 날짜를 구함
    try:  # 파일 읽기를 시도
        with open(DATA_FILE, "r", encoding="utf-8") as f:  # 통계 파일을 읽기 모드로 열고
            data = json.load(f)  # 파일 내용을 딕셔너리로 불러옴
        if data.get("date") == today:  # 저장된 날짜가 오늘과 같으면 (같은 날의 통계이면)
            data["seats"] = SEATS  # 좌석 수 설정만 최신값으로 갱신하고
            return data  # 기존 통계를 그대로 이어서 사용하도록 반환
    except Exception:  # 파일이 없거나 읽기에 실패하면
        pass  # 무시하고 아래로 진행
    return empty_stats()  # 날짜가 다르거나 파일이 없으면 빈 통계를 새로 만들어 반환

def save_stats(stats):  # 통계를 파일에 안전하게 저장하는 함수 정의
    stats["updated"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # 현재 시각을 갱신 시각으로 기록
    tmp = DATA_FILE + ".tmp"  # 임시 파일 경로를 지정
    with open(tmp, "w", encoding="utf-8") as f:  # 먼저 임시 파일에 쓰기 모드로 열고
        json.dump(stats, f, ensure_ascii=False, indent=2)  # 통계를 JSON 형식으로 임시 파일에 저장
    os.replace(tmp, DATA_FILE)  # 임시 파일을 실제 파일로 교체 (읽는 도중 파일이 깨지는 것을 방지)

# ---------------------------------------------------------------------------
# 4) 모델 로딩
# ---------------------------------------------------------------------------
print("[모델] 물체검출 모델 로딩...")  # 모델 로딩 시작을 터미널에 출력
od_net = cv2.dnn.readNetFromTensorflow(OD_WEIGHTS, OD_CONFIG)  # 가중치(.pb)와 구조(.pbtxt)로 객체 검출 신경망 생성

USE_GENDER = all(os.path.exists(p) for p in (FACE_CASCADE, GENDER_PROTO, GENDER_MODEL))  # 성별 모델 3개 파일이 모두 있는지 확인
if USE_GENDER:  # 성별 모델 파일이 모두 존재하면
    face_cascade = cv2.CascadeClassifier(FACE_CASCADE)  # 얼굴 검출용 분류기 객체 생성
    gender_net = cv2.dnn.readNetFromCaffe(GENDER_PROTO, GENDER_MODEL)  # 성별 분류 신경망 생성
    print("[모델] 성별 추정 사용")  # 성별 추정을 사용한다고 출력
else:  # 성별 모델 파일이 없으면
    print("[모델] 성별 모델 없음 → 성별 추정 생략(나머지는 정상 동작)")  # 성별만 생략한다고 출력
print("[모델] 로딩 완료")  # 모델 로딩 완료를 출력

def detect_objects(frame):  # 한 프레임에서 사람·사물을 검출하는 함수 정의
    """프레임에서 person 수, 등장한 물건 이름 집합, 그리고 박스 목록을 반환"""  # 함수 설명
    h, w = frame.shape[:2]  # 프레임의 세로·가로 픽셀 크기를 구함
    blob = cv2.dnn.blobFromImage(frame, 1.0, (300, 300), (0, 0, 0),  # 영상을 300×300 크기의 신경망 입력(blob)으로 변환
                                 swapRB=True, crop=False)  # 채널 순서를 RGB로 교환하고, 자르기는 하지 않음
    od_net.setInput(blob)  # 변환한 blob을 신경망 입력으로 설정
    out = od_net.forward()  # 신경망을 순전파하여 검출 결과를 얻음
    persons, items, boxes = 0, set(), []  # 사람 수·사물 이름 집합·박스 목록을 초기화
    for i in range(out.shape[2]):  # 검출된 후보 객체들을 하나씩 순회
        score = float(out[0, 0, i, 2])  # 해당 객체의 신뢰도(confidence)를 가져옴
        if score < CONF_THRESHOLD:  # 신뢰도가 기준값보다 낮으면
            continue  # 무시하고 다음 객체로 넘어감
        cid = int(out[0, 0, i, 1])  # 객체의 분류 번호(classId)를 가져옴
        name = COCO[cid] if 0 <= cid < len(COCO) else ""  # 분류 번호를 사물 이름으로 변환
        is_person = (name == "person")  # 그 객체가 사람인지 판단
        is_item = (name in WORK_ITEMS or name in DRINK_ITEMS)  # 작업형·음료형 사물인지 판단
        if not (is_person or is_item):  # 사람도 관심 사물도 아니면
            continue  # 무시하고 다음 객체로 넘어감
        if is_person:  # 사람이면
            persons += 1  # 사람 수를 1 증가
        else:  # 관심 사물이면
            items.add(name)  # 사물 이름을 집합에 추가
        x1 = int(out[0, 0, i, 3] * w); y1 = int(out[0, 0, i, 4] * h)  # 정규화 좌표를 실제 픽셀 좌상단 좌표로 환산
        x2 = int(out[0, 0, i, 5] * w); y2 = int(out[0, 0, i, 6] * h)  # 정규화 좌표를 실제 픽셀 우하단 좌표로 환산
        boxes.append((name, score, x1, y1, x2, y2))  # 박스 정보(이름·신뢰도·좌표)를 목록에 추가
    return persons, items, boxes  # 사람 수, 사물 집합, 박스 목록을 반환

def box_color(name):  # 사물 종류에 따라 박스 색상(BGR)을 정하는 함수 정의
    if name == "person":      return (239, 141, 91)   # 사람이면 파란색 반환
    if name in WORK_ITEMS:    return (62, 178, 255)    # 작업형 사물이면 주황색 반환
    if name in DRINK_ITEMS:   return (197, 209, 79)    # 음료형 사물이면 청록색 반환
    return (200, 200, 200)  # 그 외에는 회색 반환

def draw_overlay(frame, boxes, persons, scene_type):  # 검출 박스와 상태바를 영상에 그리는 함수 정의
    """검출 박스와 상단 상태바를 프레임에 그림"""  # 함수 설명
    for name, score, x1, y1, x2, y2 in boxes:  # 박스 목록을 하나씩 순회
        c = box_color(name)  # 사물 종류에 맞는 색상을 가져옴
        cv2.rectangle(frame, (x1, y1), (x2, y2), c, 2)  # 검출 위치에 사각형을 그림
        label = f"{name} {int(score*100)}%"  # 사물 이름과 신뢰도(%)로 라벨 문자열을 만듦
        cv2.rectangle(frame, (x1, y1 - 18), (x1 + 9 * len(label), y1), c, -1)  # 라벨 배경 사각형을 채워 그림
        cv2.putText(frame, label, (x1 + 2, y1 - 5),  # 라벨 텍스트를 박스 위에 그림
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (20, 20, 20), 1)  # 글꼴·크기·색상 지정
    cv2.rectangle(frame, (0, 0), (frame.shape[1], 28), (40, 34, 22), -1)  # 화면 상단에 상태바 배경을 그림
    tlabel = {"work": "WORK", "drink": "DRINK"}.get(scene_type, "-")  # 현재 유형을 표시용 문자열로 변환
    cv2.putText(frame, f"SeatSense LIVE | persons: {persons} | type: {tlabel}",  # 현재 인원과 유형을 상태바에 출력
                (8, 19), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (62, 178, 255), 1)  # 글꼴·크기·색상 지정
    return frame  # 박스와 상태바가 그려진 프레임을 반환

def guess_gender(frame):  # (보조) 세션 시작 시 성별을 1회 추정하는 함수 정의
    """세션 시작 시 1회 호출 — 얼굴이 잡히면 성별 추정, 아니면 unknown"""  # 함수 설명
    if not USE_GENDER:  # 성별 모델을 사용하지 않으면
        return "unknown"  # 미상으로 반환
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)  # 얼굴 검출을 위해 흑백 영상으로 변환
    faces = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(60, 60))  # 영상에서 얼굴을 검출
    if len(faces) == 0:  # 얼굴이 검출되지 않으면
        return "unknown"  # 미상으로 반환
    x, y, w, h = faces[0]  # 첫 번째로 검출된 얼굴의 좌표를 가져옴
    face = frame[y:y + h, x:x + w]  # 얼굴 영역만 잘라냄
    blob = cv2.dnn.blobFromImage(face, 1.0, (227, 227), MODEL_MEAN, swapRB=False)  # 얼굴을 성별 모델 입력 형태로 변환
    gender_net.setInput(blob)  # 변환한 입력을 성별 신경망에 설정
    return GENDER_LIST[gender_net.forward()[0].argmax()]  # 성별을 추정하여 가장 높은 값의 라벨을 반환

# ---------------------------------------------------------------------------
# 5) 카메라 및 상태 변수 준비
# ---------------------------------------------------------------------------
camera = cv2.VideoCapture(0)  # 시스템에 연결된 USB 웹캠을 열어 카메라 객체 생성 (인식 안 되면 1 또는 -1)
camera.set(3, 640); camera.set(4, 480)  # 입력 영상의 가로 640·세로 480 해상도로 설정

stats = load_stats()  # 기존 통계를 불러오거나 새 통계를 생성
save_stats(stats)  # 시작 시점의 통계를 파일에 한 번 저장

session = None  # 현재 진행 중인 세션 정보를 담을 변수 초기화 (없음 상태)
last_person_time = 0  # 손님이 마지막으로 검출된 시각을 저장할 변수 초기화
last_occ_sample = 0  # 좌석 점유율을 마지막으로 표본 측정한 시각 초기화
last_live_save = 0  # 실시간 상태를 마지막으로 저장한 시각 초기화

# ---------------------------------------------------------------------------
# 6) 실시간 영상 스트림 (CCTV 화면) — 별도 포트 5001 에서 MJPEG 송출
#    대시보드(server.py, 5000)가 이 영상을 <img>로 가져가 보여줌
# ---------------------------------------------------------------------------
output_frame = None  # 검출 박스가 그려진 최신 프레임을 담을 변수 초기화 (스트림 송출용)
frame_lock = threading.Lock()  # 여러 스레드가 프레임을 안전하게 공유하도록 잠금 객체 생성
stream_app = Flask("stream")  # 실시간 영상 송출을 담당할 별도 Flask 앱 생성

def gen_frames():  # 최신 프레임을 MJPEG 형식으로 계속 내보내는 함수 정의
    while True:  # 무한 반복하며 프레임을 송출
        with frame_lock:  # 프레임을 안전하게 읽기 위해 잠금
            frame = None if output_frame is None else output_frame.copy()  # 최신 프레임을 복사해 가져옴
        if frame is None:  # 아직 프레임이 없으면
            time.sleep(0.05); continue  # 잠깐 대기 후 다음 반복
        ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70])  # 프레임을 JPEG로 인코딩
        if not ok:  # 인코딩 실패 시
            continue  # 건너뜀
        yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n"  # MJPEG 스트림 형식으로 프레임 한 장을 내보냄
               + buf.tobytes() + b"\r\n")  # 인코딩된 영상 데이터를 이어 붙여 전송
        time.sleep(0.05)  # 약 20fps로 제한하기 위해 잠깐 대기

@stream_app.route("/video")  # /video 주소로 접속하면 아래 함수가 실행되도록 경로 지정
def video():  # 실시간 영상을 응답하는 함수 정의
    return Response(gen_frames(),  # gen_frames가 만드는 영상 스트림을
                    mimetype="multipart/x-mixed-replace; boundary=frame")  # MJPEG 형식으로 응답

def start_stream():  # 영상 송출 서버를 실행하는 함수 정의
    stream_app.run(host="0.0.0.0", port=5001, threaded=True,  # 5001 포트에서 외부 접속 허용·다중 처리로 실행
                   debug=False, use_reloader=False)  # 백그라운드 스레드에서 안전하게 실행하도록 설정

threading.Thread(target=start_stream, daemon=True).start()  # 영상 송출 서버를 별도 스레드로 시작
print("[영상] 실시간 스트림 시작 → http://<라즈베리파이IP>:5001/video")  # 스트림 주소를 터미널에 출력

def finalize_session():  # 세션이 끝났을 때 통계에 반영하는 함수 정의
    """세션 종료 처리: 유형/시간대/성별/체류시간 통계에 반영"""  # 함수 설명
    global session  # 전역 session 변수를 수정하기 위해 선언
    if session is None:  # 진행 중인 세션이 없으면
        return  # 아무것도 하지 않고 종료
    dur = time.time() - session["start"]  # 세션 시작부터 현재까지의 체류시간(초)을 계산
    if dur < MIN_SESSION_SEC:  # 체류시간이 너무 짧으면 (오작동으로 보고)
        session = None  # 세션을 버리고
        return  # 종료
    t = session["type"] or "etc"  # 세션의 이용 유형을 가져옴 (없으면 기타)
    stats["total"] += 1  # 총 세션 수를 1 증가
    stats["type"][t] += 1  # 해당 이용 유형의 세션 수를 1 증가
    stats["hourly"][session["hh"]]["sessions"] += 1  # 세션이 시작된 시간대의 세션 수를 1 증가
    stats["gender"][session["gender"]] += 1  # (보조) 추정된 성별의 세션 수를 1 증가
    if t in ("work", "drink"):  # 작업형 또는 음료형이면
        stats["dwell"][t + "_sum"] += dur / 60.0  # 해당 유형의 체류시간 합계(분)에 더함
        stats["dwell"][t + "_n"] += 1  # 해당 유형의 체류 건수를 1 증가
    save_stats(stats)  # 갱신된 통계를 파일에 저장
    print(f"[세션 #{stats['total']}] {session['hh']}시 / {t} / "  # 종료된 세션 정보를 터미널에 출력
          f"{session['gender']} / {dur/60:.1f}분")  # 시간대·유형·성별·체류시간을 함께 출력
    session = None  # 세션을 비움 (다음 손님 대기)

# ---------------------------------------------------------------------------
# 7) 메인 루프
# ---------------------------------------------------------------------------
print(f"[시작] 좌석 {SEATS}석 기준 분석 시작 (종료: Ctrl+C)")  # 분석 시작을 터미널에 출력
try:  # 실행 중 Ctrl+C로 종료할 수 있도록 예외 처리 시작
    while True:  # 카메라가 동작하는 동안 매 프레임 반복 처리
        ok, frame = camera.read()  # 카메라에서 한 프레임을 읽어옴
        if not ok:  # 프레임을 제대로 읽지 못하면
            time.sleep(0.1); continue  # 잠깐 대기 후 다음 반복
        now = time.time()  # 현재 시각을 구함
        hh = datetime.datetime.now().strftime("%H")  # 현재 시(時)를 두 자리 문자열로 구함

        persons, items, boxes = detect_objects(frame)  # 현재 프레임에서 사람·사물·박스를 검출

        if items & WORK_ITEMS:  # 검출된 사물 중 작업형 사물이 있으면
            scene_type = "work"  # 현재 장면을 작업형으로 판정
        elif items & DRINK_ITEMS:  # 작업형은 없고 음료형 사물이 있으면
            scene_type = "drink"  # 현재 장면을 음료형으로 판정
        else:  # 관심 사물이 없으면
            scene_type = None  # 유형 없음으로 둠

        annotated = draw_overlay(frame.copy(), boxes, persons, scene_type)  # 검출 박스·상태바를 그린 영상을 만듦
        with frame_lock:  # 프레임을 안전하게 공유하기 위해 잠금
            output_frame = annotated  # 스트림 송출용 최신 프레임으로 저장

        if persons > 0:  # 화면에 사람이 있으면
            last_person_time = now  # 마지막으로 사람이 보인 시각을 갱신
            if session is None:  # 진행 중인 세션이 없으면 (새 손님 등장)
                session = {"start": now, "hh": hh, "type": scene_type,  # 새 세션을 시작 (시작시각·시간대·유형 기록)
                           "gender": guess_gender(frame)}  # 세션 시작 시 성별을 1회 추정해 기록
            else:  # 세션이 진행 중이면
                if scene_type == "work":  # 작업형 사물이 보이면
                    session["type"] = "work"  # 세션 유형을 작업형으로 확정(우선)
                elif scene_type == "drink" and session["type"] != "work":  # 음료형이 보이고 아직 작업형이 아니면
                    session["type"] = "drink"  # 세션 유형을 음료형으로 갱신
        else:  # 화면에 사람이 없으면
            if session is not None and (now - last_person_time) > ABSENCE_DEBOUNCE:  # 일정 시간 이상 사람이 안 보이면
                finalize_session()  # 세션을 종료 처리

        if now - last_occ_sample >= OCC_SAMPLE_EVERY:  # 점유율 표본 측정 주기가 되면
            cell = stats["hourly"][hh]  # 현재 시간대의 통계 칸을 가져옴
            cell["occ_sum"] += persons  # 현재 동시 인원을 합계에 더함
            cell["occ_n"] += 1  # 표본 수를 1 증가
            cell["occ_peak"] = max(cell["occ_peak"], persons)  # 최대 동시 인원을 갱신
            last_occ_sample = now  # 마지막 표본 측정 시각을 갱신

        if now - last_live_save >= LIVE_SAVE_EVERY:  # 실시간 상태 저장 주기가 되면
            stats["live"] = {  # 대시보드 표시용 현재 상태를 갱신
                "persons": persons,  # 현재 검출된 인원 수
                "type": {"work": "작업", "drink": "음료"}.get(scene_type, "-"),  # 현재 이용 유형(한글 표시)
                "occ_pct": round(min(persons, SEATS) / SEATS * 100) if SEATS else 0,  # 현재 좌석 점유율(%)
            }
            save_stats(stats)  # 현재 상태를 파일에 저장
            last_live_save = now  # 마지막 저장 시각을 갱신

        time.sleep(0.1)  # CPU 부담을 줄이기 위해 잠깐 대기
except KeyboardInterrupt:  # 사용자가 Ctrl+C를 누르면
    print("\n[종료] 분석 종료")  # 종료 메시지를 출력
finally:  # 종료 시 항상 실행
    finalize_session()  # 진행 중이던 세션이 있으면 마지막으로 저장
    camera.release()  # 카메라 자원을 해제

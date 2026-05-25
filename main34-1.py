import cv2  # 영상 처리 및 얼굴/눈 검출을 위한 OpenCV 라이브러리 가져옴
from gpiozero import Buzzer  # 라즈베리파이 GPIO 핀에 연결된 부저를 제어하기 위한 Buzzer 클래스 가져옴
import time  # 시간 관련 처리를 위한 time 라이브러리 가져옴

buzzerPin = Buzzer(16)  # GPIO 16번 핀에 연결된 능동부저를 제어하는 Buzzer 객체 생성

def main():  # 졸음방지 디바이스의 전체 동작을 수행하는 메인 함수 정의
    camera = cv2.VideoCapture(-1)  # 시스템에 연결된 웹캠을 자동으로 탐지하여 카메라 객체 생성
    camera.set(3,640)  # 입력 영상의 가로 해상도를 640픽셀로 설정 (속성 번호 3은 가로 크기)
    camera.set(4,480)  # 입력 영상의 세로 해상도를 480픽셀로 설정 (속성 번호 4는 세로 크기)
    
    face_xml = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'  # OpenCV 기본 제공 얼굴 검출용 Haar Cascade 모델 파일 경로 지정
    eye_xml = cv2.data.haarcascades + 'haarcascade_eye.xml'  # OpenCV 기본 제공 눈 검출용 Haar Cascade 모델 파일 경로 지정
    face_cascade = cv2.CascadeClassifier(face_xml)  # 얼굴 검출용 Haar Cascade 분류기 객체 생성
    eye_cascade = cv2.CascadeClassifier(eye_xml)  # 눈 검출용 Haar Cascade 분류기 객체 생성
    
    while( camera.isOpened() ):  # 카메라가 정상적으로 열려 있는 동안 매 프레임을 반복 처리
        _, image = camera.read()  # 카메라로부터 한 프레임을 읽어 image 변수에 컬러 영상으로 저장
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)  # 입력된 컬러(BGR) 영상을 검출 연산에 적합한 흑백 영상으로 변환

        faces = face_cascade.detectMultiScale(gray,scaleFactor=1.1,minNeighbors=5,minSize=(100,100),flags=cv2.CASCADE_SCALE_IMAGE)  # 흑백 영상에서 얼굴을 검출하여 좌표 목록 반환 (탐지 윈도우 10%씩 확대, 최소 5회 검출 시 확정, 최소 크기 100×100)
        print("faces detected Number: " + str(len(faces)))  # 현재 프레임에서 검출된 얼굴 개수를 터미널에 출력

        if len(faces):  # 검출된 얼굴이 1개 이상 존재하는 경우에만 이후 처리 수행
            for (x,y,w,h) in faces:  # 검출된 각 얼굴의 좌표(x, y)와 크기(w, h)를 순회
                cv2.rectangle(image,(x,y),(x+w,y+h),(255,0,0),2)  # 검출된 얼굴 위치에 파란색 사각형을 그려 화면에 표시
                
                face_gray = gray[y:y+h, x:x+w]  # 눈 검출을 위해 얼굴 영역(ROI)에 해당하는 흑백 영상만 잘라냄
                face_color = image[y:y+h, x:x+w]  # 눈에 사각형을 그리기 위해 얼굴 영역에 해당하는 컬러 영상만 잘라냄
                
                eyes = eye_cascade.detectMultiScale(face_gray,scaleFactor=1.1,minNeighbors=5)  # 잘라낸 얼굴 영역 내부에서만 눈을 검출하여 오검출을 줄임
                
                if len(eyes) <= 1:  # 검출된 눈이 1개 이하이면 눈을 감은 졸음 상태로 판단
                    buzzerPin.on()  # 부저를 작동시켜 경보음 출력
                else:  # 눈이 2개 이상 검출되면 깨어 있는 정상 상태로 판단
                    buzzerPin.off()  # 부저를 꺼서 경보음 중지
                
                for (ex,ey,ew,eh) in eyes:  # 검출된 각 눈의 좌표(ex, ey)와 크기(ew, eh)를 순회
                    cv2.rectangle(face_color, (ex, ey), (ex+ew, ey+eh), (0,255,0), 2)  # 검출된 눈 위치에 초록색 사각형을 그려 화면에 표시
        
        cv2.imshow('result', image)  # 검출 결과가 표시된 영상을 'result' 창에 실시간 출력
        
        if cv2.waitKey(1) == ord('q'):  # 키 입력을 1ms 대기하며 확인하여 'q' 키가 입력되면
            break  # 반복문을 종료하여 프로그램 정지
    
    cv2.destroyAllWindows()  # 프로그램 종료 시 열려 있는 모든 OpenCV 창을 닫음
    buzzerPin.off()  # 프로그램 종료 시 부저가 켜진 상태로 남지 않도록 강제로 끔

if __name__ == '__main__':  # 이 파일이 직접 실행될 때만 아래 코드를 수행 (모듈로 임포트될 경우 실행 안 함)
    main()  # main 함수를 호출하여 졸음방지 디바이스 프로그램 시작
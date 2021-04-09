import socket
import cv2
import numpy
import face_recognition
from datetime import datetime, timedelta
import numpy as np
import platform
import pickle
import sys
import struct
import base64
from PIL import Image
Image.LOAD_TRUNCATED_IMAGES = True
from io import BytesIO
from datetime import datetime
import time
import RPi.GPIO as GPIO
import os
import sys
from playsound import playsound


Image.LOAD_TRUNCATED_IMAGES = True
from io import BytesIO


# jetson-nano 카메라 캡쳐 함수
def get_jetson_gstreamer_source(capture_width=720, capture_height=480, display_width=720, display_height=480,
                                framerate=60, flip_method=0):
    return (
            f'nvarguscamerasrc ! video/x-raw(memory:NVMM), ' +
            f'width=(int){capture_width}, height=(int){capture_height}, ' +
            f'format=(string)NV12, framerate=(fraction){framerate}/1 ! ' +
            f'nvvidconv flip-method={flip_method} ! ' +
            f'video/x-raw, width=(int){display_width}, height=(int){display_height}, format=(string)BGRx ! ' +
            'videoconvert ! video/x-raw, format=(string)BGR ! appsink'
    )


def recvall(sock, count):
    buf = b''
    while count:
        newbuf = sock.recv(count)
        if not newbuf: return None
        buf += newbuf
        count -= len(newbuf)
    return buf

def restart():
    # 문이 열렸으므로 재시작
    executable = sys.executable
    args = sys.argv[:]
    args.insert(0, sys.executable)
    time.sleep(1)
    print('restart program')
    os.execvp(executable, args)


def run():
    # 연결할 서버(수신단)의 ip주소와 port번호
    TCP_IP = '164.125.234.91'
    TCP_PORT = 5010

    # 송신을 위한 socket 준비
    sock = socket.socket()
    sock.connect((TCP_IP, TCP_PORT))
    cam = cv2.VideoCapture(get_jetson_gstreamer_source(), cv2.CAP_GSTREAMER)
    start_time = time.time()

    ## 0~100에서 90의 이미지 품질로 설정 (default = 95)
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
    ret, frame = cam.read()
    while True:
        ret, frame = cam.read()
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = small_frame[:, :, ::-1]
        # cv2. imencode(ext, img [, params])
        # encode_param의 형식으로 frame을 jpg로 이미지를 인코딩한다.
        result, frame = cv2.imencode('.jpg', frame, encode_param)
        # frame을 String 형태로 변환
        data = numpy.array(frame)
        stringData = data.tostring()
        # 서버에 데이터 전송
        sock.sendall((str(len(stringData))).encode().ljust(16) + stringData)
        resp = sock.recv(1024)
        duration = time.time()-start_time
        if (resp.decode('utf-8') == 'I'):
            if duration >= 20:
                #print("20초 경과로 프로그램이 꺼집니다.")
                #cam.release()
                #cv2.destroyAllWindows()
                #restart()
                 continue
        elif(resp.decode('utf-8') == 'AA'):
            playsound("/home/iotlab/Desktop/unregistered.mp3")
            print('Intruder!')
            nowDate = datetime.now()
            length = recvall(sock, 16)
            stringdata = recvall(sock, int(length))
            img = base64.decodebytes(stringdata)
            im = Image.open(BytesIO(img))
            im.save(nowDate.strftime("/home/iotlab/dlib-19.17/recog/A.jpg"))
            showing = cv2.imread("/home/iotlab/dlib-19.17/recog/A.jpg", cv2.IMREAD_COLOR)
            show_img = cv2.resize(showing, dsize=(480, 400), interpolation=cv2.INTER_AREA)
            cv2.putText(show_img, "Not Registered Face", (5, 18), cv2.FONT_HERSHEY_DUPLEX, 0.8, (0, 0, 255), 1)
            cv2.imshow("Recog_Face", show_img)
            cv2.waitKey(3000)
            cv2.destroyAllWindows()
            continue
        elif(resp.decode('utf-8') == 'BB'):
            playsound("/home/iotlab/Desktop/registerd.mp3")
            print('****Welcome Home****')
            GPIO.setmode(GPIO.BOARD)

            # initialize EnA, In1 and In2
            GPIO.setup(ENA, GPIO.OUT, initial=GPIO.LOW)
            GPIO.setup(IN1, GPIO.OUT, initial=GPIO.LOW)
            GPIO.setup(IN2, GPIO.OUT, initial=GPIO.LOW)

            # Stop
            GPIO.output(ENA, GPIO.HIGH)
            GPIO.output(IN1, GPIO.LOW)
            GPIO.output(IN2, GPIO.LOW)
            time.sleep(0.2)

            # Backward
            GPIO.output(IN1, GPIO.LOW)
            GPIO.output(IN2, GPIO.HIGH)
            time.sleep(0.2)

            # Stop
            GPIO.output(ENA, GPIO.LOW)
            GPIO.output(IN1, GPIO.LOW)
            GPIO.output(IN2, GPIO.LOW)
            time.sleep(3)

            GPIO.cleanup()
            cam.release()
            cv2.destroyAllWindows()
            break
        elif cv2.waitKey(1) & 0xFF == ord('q'):
            cam.release()
            cv2.destroyAllWindows()
            break
        else:
            continue

    cam.release()


if __name__ == '__main__':
    GPIO.setmode(GPIO.BOARD)
    PIR_PIN = 26
    ENA = 33
    IN1 = 35
    IN2 = 37
    GPIO.setup(PIR_PIN, GPIO.IN)
    try:
        time.sleep(1)
        print('PIR Module Ready')

        while True:
            GPIO.setmode(GPIO.BOARD)
            GPIO.setup(PIR_PIN, GPIO.IN)
            PIR_PIN = 26
            if GPIO.input(PIR_PIN):
                t = time.localtime()
                print('% d: % d: % d Motion Detected!' % (t.tm_hour, t.tm_min, t.tm_sec))
                run()
                cv2.VideoCapture(get_jetson_gstreamer_source(), cv2.CAP_GSTREAMER).release()
                restart()
            else:
                continue
            time.sleep(1)

    except ConnectionRefusedError:
        cv2.VideoCapture(get_jetson_gstreamer_source(), cv2.CAP_GSTREAMER).release()
        cv2.destroyAllWindows()
        time.sleep(10)
        restart()
    except BrokenPipeError:
        cv2.VideoCapture(get_jetson_gstreamer_source(), cv2.CAP_GSTREAMER).release()
        cv2.destroyAllWindows()
        time.sleep(10)
        restart()
    except ConnectionResetError:
        cv2.VideoCapture(get_jetson_gstreamer_source(), cv2.CAP_GSTREAMER).release()
        cv2.destroyAllWindows()
        time.sleep(10)
        restart()


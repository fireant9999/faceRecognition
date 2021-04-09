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
import select
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
    print("문이 열림")
    # 문이 열렸으므로 재시작
    executable = sys.executable
    args = sys.argv[:]
    args.insert(0, sys.executable)
    time.sleep(1)
    print('restart program')
    os.execvp(executable, args)


def run():
    GPIO.setmode(GPIO.BOARD)
    PIR_PIN = 26
    ENA = 33
    IN1 = 35
    IN2 = 37
    GPIO.setup(PIR_PIN, GPIO.IN)
    # 연결할 서버(수신단)의 ip주소와 port번호
    TCP_IP = '164.125.234.91'
    TCP_PORT = 5004

    # 송신을 위한 socket 준비
    sock = socket.socket()
    sock.connect((TCP_IP, TCP_PORT))

    cam = cv2.VideoCapture(get_jetson_gstreamer_source(), cv2.CAP_GSTREAMER)

    ## 0~100에서 90의 이미지 품질로 설정 (default = 95)
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
    ret, frame = cam.read()
    while True:
        ret, frame = cam.read()
        cv2.putText(frame, "Registering for 20 seconds...", (18, 30), cv2.FONT_HERSHEY_DUPLEX, 0.8, (0, 0, 255), 1)
        cv2.imshow('frame', frame)
        cv2.waitKey(10)
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = small_frame[:, :, ::-1]
        # cv2. imencode(ext, img [, params])
        # encode_param의 형식으로 frame을 jpg로 이미지를 인코딩한다.
        result, frame = cv2.imencode('.jpg', frame, encode_param)
        # frame을 String 형태로 변환
        data = numpy.array(frame)
        stringData = data.tostring()
        # 서버에 데이터 전송
        # (str(len(stringData))).encode().ljust(16)
        # sock.send('Sending video')
        sock.sendall((str(len(stringData))).encode().ljust(16) + stringData)
        resp = sock.recv(1024)

        if (resp.decode('utf-8') == 'I'):
            continue
        elif (resp.decode('utf-8') == 'CC'):
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

            sock.close()
            GPIO.cleanup()
            cam.release()
            cv2.VideoCapture(get_jetson_gstreamer_source(), cv2.CAP_GSTREAMER).release()
            cv2.destroyAllWindows()
            restart()        
        elif cv2.waitKey(1) & 0xFF == ord('q'):
            cv2.destroyAllWindows()
            break
        else:
            continue

    cam.release()


if __name__ == '__main__':
    IP = '192.168.0.50'
    PORT = 5045
    ADDR = (IP, PORT)
    SIZE = 1024

    Server_socket1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    Server_socket1.bind(ADDR)
    Server_socket1.listen()

    read_socket_list = [Server_socket1]
    conn_read_socket_list, conn_write_socket_list, conn_except_socket_list =select.select(read_socket_list, [], [])
    print("waiting for Signal!")
    for conn_read_socket in conn_read_socket_list:
        if conn_read_socket == Server_socket1:
            client_socket, client_addr = Server_socket1.accept()
            msg = client_socket.recv(SIZE)
            if msg.decode('UTF-8') == 'A':
                try:
                        playsound("register_start.mp3")
                        run()
                        cv2.VideoCapture(get_jetson_gstreamer_source(), cv2.CAP_GSTREAMER).release()
                        cv2.destroyAllWindows()

                except ConnectionRefusedError:
                        print('conn err')
                        cv2.VideoCapture(get_jetson_gstreamer_source(), cv2.CAP_GSTREAMER).release()
                        cv2.destroyAllWindows()
                        GPIO.cleanup()
                        time.sleep(5)
                        restart()
                except BrokenPipeError:
                        print('Broken Pipe Error')
                        cv2.VideoCapture(get_jetson_gstreamer_source(), cv2.CAP_GSTREAMER).release()
                        cv2.destroyAllWindows()
                        time.sleep(5)
                        restart()

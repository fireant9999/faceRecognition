import cv2
import time
import threading
from flask import Response, Flask
import time
import os
import sys
import socket
import select

# Flask 객체로 Image frame 전달
global video_frame
video_frame = None

# 다양한 브라우저에서 프레임들의 thread-safe 출력을 잠근다.
global thread_lock
thread_lock = threading.Lock()

# Raspberry Camera에 접근하기 위한 GStreamer 파이프라인
GSTREAMER_PIPELINE = 'nvarguscamerasrc ! video/x-raw(memory:NVMM), width=1920, height=1080, format=(string)NV12, framerate=21/1 ! nvvidconv flip-method=0 ! video/x-raw, width=960, height=616, format=(string)BGRx ! videoconvert ! video/x-raw, format=(string)BGR ! appsink wait-on-eos=false max-buffers=1 drop=True'

# 어플리케이션을 위한 Flask 오브젝트 생성
app = Flask(__name__)

def restart():
    print("프로그램 재시작")
    executable = sys.executable
    args = sys.argv[:]
    args.insert(0, sys.executable)
    time.sleep(1)
    os.execvp(executable, args)

def captureFrames():
    global video_frame, thread_lock
    start_time = time.time()
    # OpenCV로부터 비디오 캡처
    video_capture = cv2.VideoCapture(GSTREAMER_PIPELINE, cv2.CAP_GSTREAMER)

    while True and video_capture.isOpened():
        return_key, frame = video_capture.read()
        duration = time.time() - start_time
        if not return_key:
            break

        # 프레임의 복사본을 생성하고 video_frame 변수에 저장
        with thread_lock:
            video_frame = frame.copy()

        key = cv2.waitKey(30) & 0xff
        if key == 27:
            break
        if duration >= 30:
            print("20초 경과")
            video_capture.release()
            restart()
            break
    video_capture.release()


def encodeFrame():
    global thread_lock
    while True:
        # video_frame 변수에 접근하기 위한 thread_lock 습득
        with thread_lock:
            global video_frame
            if video_frame is None:
                continue
            return_key, encoded_image = cv2.imencode(".jpg", video_frame)
            if not return_key:
                continue

        # 바이트 배열로 결과 이미지
        yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' +
               bytearray(encoded_image) + b'\r\n')


@app.route("/")
def streamFrames():
    return Response(encodeFrame(), mimetype="multipart/x-mixed-replace; boundary=frame")


if __name__ == '__main__':
    IP = '192.168.0.50'
    PORT = 5040
    ADDR = (IP, PORT)
    SIZE = 1024

    Server_socket1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    Server_socket1.bind(ADDR)
    Server_socket1.listen()

    read_socket_list = [Server_socket1]
    conn_read_socket_list, conn_write_socket_list, conn_except_socket_list =select.select(read_socket_list, [], [])

    for conn_read_socket in conn_read_socket_list:
        if conn_read_socket == Server_socket1:
            client_socket, client_addr = Server_socket1.accept()
            msg = client_socket.recv(SIZE)
            if msg.decode('UTF-8') == 'A':
                print("실행합니다.")
                # thread를 생성하고 이미지 프레임을 캡처하는 메소드를 첨가
                process_thread = threading.Thread(target=captureFrames)
                process_thread.daemon = True
                # Start the thread
                process_thread.start()

                # start the Flask Web Application
                # While it can be run on any feasible IP, IP = 192.168.0.50 renders the web app on
                # the host machine's localhost and is discoverable by other machines on the same network
                app.run("192.168.0.50", port="8000")

import socket
import time
import RPi.GPIO as GPIO
import os
import sys

def restart():
    print("문이 열림")
    # 문이 열렸으므로 재시작
    executable = sys.executable
    args = sys.argv[:]
    args.insert(0, sys.executable)
    time.sleep(1)
    print('restart program')
    os.execvp(executable, args)

def motor_act():
    HOST = '192.168.0.50'
    PORT = 5030

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    GPIO.setmode(GPIO.BOARD)
    PIR_PIN = 26
    ENA = 33
    IN1 = 35
    IN2 = 37
    GPIO.setup(PIR_PIN, GPIO.IN)

    server_socket.bind((HOST, PORT))
    server_socket.listen()
    client_socket, addr = server_socket.accept()
    print('Connected by', addr)

    while True:
        data = client_socket.recv(1024)
        if (data.decode('utf-8') == 'D'):
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

            break

        #print('Received from', addr, data.decode())
        #client_socket.sendall(data)

    client_socket.close()
    server_socket.close()

if __name__ == '__main__':
    motor_act()
    restart()

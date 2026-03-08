import cv2
import time
import sys

def test():
    cv2.namedWindow('Test window')

def listen():
    while True:
        if cv2.waitKey(25) & 0xFF == ord('q'):
            break

        time.sleep(0.01)

        key = cv2.waitKey()
        if key != -1:
            print(chr(key), end=' ')
            sys.stdout.flush()


            if(chr(key) == 'q'):
                break



if __name__ == "__main__":
    test()
    listen()

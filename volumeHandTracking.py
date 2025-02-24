import cv2
import mediapipe as mp
import time
import math
import numpy as np
import handTrackingModule as htm
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume


wCam, hCam = 1280, 720


cap = cv2.VideoCapture(0)
cap.set(3, wCam)
cap.set(4, hCam)

detector = htm.HandDetector(detectionCon=0.7)

devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(
    IAudioEndpointVolume._iid_, CLSCTX_ALL, None
)
volume = cast(interface, POINTER(IAudioEndpointVolume))

volRange = volume.GetVolumeRange()
minVol = volRange[0]
maxVol = volRange[1]

alpha = 0.2  # Smoothing factor (adjust between 0.1 - 0.3 for best results)
smoothed_vol = None
volume_locked = False

def is_lock_gesture(lmList):
    """Detects if the hand is making a fist (lock gesture)."""
    return (
        lmList[8][2] > lmList[6][2] and  # Index finger bent
        lmList[12][2] > lmList[10][2] and  # Middle finger bent
        lmList[16][2] > lmList[14][2] and  # Ring finger bent
        lmList[20][2] > lmList[18][2]  # Pinky bent
    )

pTime = 0
cTime = 0
while True:
    success, img = cap.read()
    img = detector.findHands(img)
    lmList = detector.findPosition(img, draw=False)
    if len(lmList) != 0:
        if is_lock_gesture(lmList):  # If fist is detected, lock volume
            volume_locked = True
        else:
            volume_locked = False  # Unlock when hand is open

        if not volume_locked:

            x1, y1 = lmList[4][1], lmList[4][2]
            x2, y2 = lmList[8][1], lmList[8][2]
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

            cv2.circle(img, (x1, y1), 15, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (x2, y2), 15, (255, 0, 255), cv2.FILLED)
            cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), 3)
            cv2.circle(img, (cx, cy), 15, (255, 0, 255), cv2.FILLED)

            length = math.hypot(x2 - x1, y2 - y1)
            print(length)

            # new_vol = np.interp(length, [35, 200], [minVol, maxVol])
            normalized_length = (length - 35) / (300 - 40)
            normalized_length = max(0, min(normalized_length, 1))
            scaled_length = 1 / (1 + np.exp(-6 * (normalized_length - 0.4))) 
            new_vol = minVol + (maxVol - minVol) * scaled_length
            if smoothed_vol is None:
                smoothed_vol = new_vol  # Initialize on first frame
            else:
                smoothed_vol = alpha * new_vol + (1 - alpha) * smoothed_vol
            
            # Ensure smoothed_vol remains a float
            smoothed_vol = float(max(minVol, min(smoothed_vol.real, maxVol)))

            volume.SetMasterVolumeLevel(smoothed_vol, None)

            # vol = np.interp(length, [35,200], [minVol, maxVol])
            # volume.SetMasterVolumeLevel(vol, None)
            

            if length<25:
                cv2.circle(img, (cx, cy), 15, (0, 255, 0), cv2.FILLED)




    cTime = time.time()
    fps = 1/(cTime-pTime)
    pTime = cTime

    cv2.putText(img, str(int(fps)), (10,70), cv2.FONT_HERSHEY_PLAIN, 3,
                (255,0,255),3)

    # cv2.imshow("Image", img)
    cv2.waitKey(1)
import cv2
import numpy as np


def load_tools():
    tools = []
    return tools


def track_movement(video, tools) -> int:
    cur = []
    append = True
    bool_0, bool_1,bool_2,bool_3,bool_4 = [False] * 5
    array = np.zeros((5,5), dtype=int)


    while True:  
            
        status, frame = video.read()  
        if not status:  
            break
        
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        h = hsv[:,:,0]
        
        # cv2.rectangle(frame,(330,30),(540,170),(255,0,255),2) #0
        # cv2.rectangle(frame,(15,320),(165,525),(255,0,255),2)#1
        # cv2.rectangle(frame,(330,320),(550,520),(255,0,255),2)#2
        # cv2.rectangle(frame,(710,320),(860,525),(255,0,255),2)#3
        # cv2.rectangle(frame,(340,670),(550,810),(255,0,255),2)#4


        point_0 = np.sum(h[30:170, 330:540])
        bool_0 = True if point_0 > 33612 else False
            
        point_1 = np.sum(h[320:525, 15:165])
        bool_1 = True if point_1 > 55838 else False 
             
        point_2 = np.sum(h[320:520, 330:550])
        bool_2 = True if point_2 > 26531 else False


        point_3 = np.sum(h[320:525, 710:860])
        bool_3 = True if point_3 > 54255 else False
        

        point_4 = np.sum(h[670:810, 340:550])
        bool_4 = True if point_4 > 30139 else False
             
        
        if not(bool_0) and not(bool_1) and not(bool_2) and not(bool_3) and not(bool_4):
            append = True


        if bool_0 and append:   
            cur.append(0)
            append = False

        elif bool_1 and append: 
            cur.append(1)
            append = False

        elif bool_2 and append: 
            cur.append(2)
            append = False

        elif bool_3 and append:
            cur.append(3)
            append = False

        elif bool_4 and append: 
            cur.append(4)
            append = False

        
        # cv2.imshow("frame", frame)
        # k = cv2.waitKey(10)
        # if k == ord("q"):
        #     break

    print(cur)
    for i in range(len(cur)-1):
        start = cur[i]
        end = cur[i+1]
        array[start][end] +=1

    
    return array
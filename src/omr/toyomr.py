import cv2
from pyzbar.pyzbar import decode, ZBarSymbol
import math
import numpy as np

def norm_squared(a,b):
    """
    returns the square of norm of vectors a, b.
    """
    return sum( (ai-bi)*(ai-bi) for (ai,bi) in zip(a,b))

def get_th_by_2mean(data):
    """
    returns therethold which divides data to two clusters. 
    """
    x1=max(data)
    x0=min(data)
    for i in range(1000):
       th = (x1+x0)/2
       d1 = [ di for di in data if di > th ]
       if len(d1) > 0:
           x1 = sum(d1)/len(d1)
       else:
           x1 = max(data)
       d0 = [ di for di in data if di <= th ]
       if len(d0) > 0:
           x0 = sum(d0)/len(d0)
       else:
           x0 = min(data)
       if th == (x1+x0) /2:
           return th
    return th

def detect_marked_marker_box(frame, targetbox):
    """
    returns the list of keys of marked boxes 
    INPUT:
    frame - gray scale image
    targetbox - dictionary of cordinates  ((x1,y1),(x2,y2)) of boxes with northwest point (x1,y1) and southeast point (x2,y2).
    """
    frame = cv2.GaussianBlur(frame,(5,5),0)
    if len(targetbox) == 0:
        return []
    data = []

    #for k in targetbox.keys():
    #    ((x1,y1),(x2,y2)) =targetbox[k]
    #    data.extend(np.ravel(frame[y1:y2,x1:x2]))
    #th =get_th_by_2mean(data)
    #(res,frame) = cv2.threshold(frame,th,255, cv2.THRESH_BINARY)
    frame = 255 - frame

    score={}
    for k in targetbox.keys():
        ((x1,y1),(x2,y2)) =targetbox[k]
        score[k]=np.sum(frame[y1:y2,x1:x2])/((x2-x1)*(y2-y1))
        print((x2-x1)*(y2-y1))
    th=get_th_by_2mean(score.values())
    ans = [k for k in score.keys() if score[k] > th]
    return ans

def detect_marker_box(frame,targetkeys=None):
    """
    return the coodinates of boxes containing marker.
    INPUT:
    frame - image
    targetkeys -  list of pairs of keys of virtical barcode (for x-coordinate) and horizontal barcode (for y-coodinate).
    """
    value = decode(frame, symbols=[ZBarSymbol.CODE39])
    data={}
    if value:
        for barcode in value:
            key = barcode.data.decode('utf-8')
            data[key]=barcode.rect
    
    if targetkeys == None:
        vmarker=[]
        hmarker=[]
        for k in data.keys():
            (x, y, w, h) = data[k]
            if w < h:
                if w > 0:
                    vmarker.append(k)
            else:
                if h > 0:
                    hmarker.append(k)
        targetkeys = [ (k1,k2) for k1 in vmarker for k2 in hmarker ]
    else:
        targetkeys = [ (k1,k2) for (k1,k2) in targetkeys if k1 in data and k2 in data] 
    ans = {}
    for (k1,k2) in targetkeys:
        ans[(k1,k2)] = ((data[k1][0],data[k2][1]),(data[k1][0]+data[k1][2],data[k2][1]+data[k2][3]))  
    return ans

def detect_position_marker(frame):
    """
    returns degrees of angle of image if position marker is detected; otherwise None.
    INPUT:
    frame - image
    """
    value = decode(frame, symbols=[ZBarSymbol.QRCODE])
    if value:
        data={}
        keys = []
        ids = []
        for qrcode in value:
            key = qrcode.data.decode('utf-8')
            if key.startswith("marker:"):
                x_av=0
                y_av=0
                for (x,y) in qrcode.polygon:
                    x_av=x_av+x
                    y_av=y_av+y
                x_av = x_av / len(qrcode.polygon)
                y_av = y_av / len(qrcode.polygon)
                #x, y, w, h = qrcode.rect
                data[key]=((x_av,y_av),qrcode.polygon)
                keys.append(key)
                post=key[9:]
                if post not in ids:
                    ids.append(post)
        if keys == []:
            return None
        vlinekeys=[]
        hlinekeys=[]
        for post in ids:
            if "marker:SE"+post in keys:
                if "marker:SW"+post in keys:
                    hlinekeys.append(("marker:SW"+post,"marker:SE"+post))
                if "marker:NE"+post in keys:
                    vlinekeys.append(("marker:NE"+post,"marker:SE"+post))
            if "marker:NW"+post in keys:
                if "marker:SW"+post in keys:
                    vlinekeys.append(("marker:NW"+post,"marker:SW"+post))
                if "marker:NE"+post in keys:
                    hlinekeys.append(("marker:NW"+post,"marker:NE"+post))
        lines=[(norm(data[k1][0],data[k2][0]),data[k1][0],data[k2][0],"h") for (k1,k2) in hlinekeys] + [(norm(data[k1][0],data[k2][0]),data[k1][0],data[k2][0],"v") for (k1,k2) in vlinekeys]
        if lines != []:
            lines.sort()
            c=lines[-1]
            ans= math.degrees(math.atan2(c[2][1]-c[1][1],c[2][0]-c[1][0]))
        
            if c[-1]=="v":
                ans = ans-90

            return ans
    else:
        return None






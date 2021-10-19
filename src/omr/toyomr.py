import sys
import cv2
from pyzbar.pyzbar import decode, ZBarSymbol
import math
import numpy as np

class OMRbase:
    def norm_squared(self,a,b):
        """
        returns the square of norm of vectors a, b.
        """
        return sum( (ai-bi)*(ai-bi) for (ai,bi) in zip(a,b))

    def get_th_by_2mean(self,data):
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

    def detect_postion_markers(self,frame):
        """
        returns pair of dict D and list L, D[k1][k2] is rect of qrcode for problem k1 at k2, L is list of strings for all qrcodes. 
        """
        value = decode(frame, symbols=[ZBarSymbol.QRCODE])
        all_strings = []
        position_markers = {}
        if value:
            for qrcode in value:
                key = qrcode.data.decode('utf-8')
                all_strings.append(key)
                if key.startswith("marker:"):
                    k=key[10:]
                    k2=key[7:9]
                    if k not in position_markers:
                        position_markers[k]={}
                    position_markers[k][k2]=qrcode.rect
        all_strings.sort()
        return (position_markers,all_strings)

    def detect_angle(self,frame):
        """
        returns degrees of angle of image if position marker is detected; otherwise None.  the range of degree is depend on the range of output of math.atan2.
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
            lines=[(self.norm_squared(data[k1][0],data[k2][0]),data[k1][0],data[k2][0],"h") for (k1,k2) in hlinekeys] + [(self.norm_squared(data[k1][0],data[k2][0]),data[k1][0],data[k2][0],"v") for (k1,k2) in vlinekeys]
            if lines != []:
                lines.sort()
                c=lines[-1]
                ans= math.degrees(math.atan2(c[2][1]-c[1][1],c[2][0]-c[1][0]))

                if c[-1]=="v":
                    ans = ans-90

                return ans
        else:
            return None


    def get_hmarker_area(self,position_markers):
        ans =[]
        keys = [ k for k in position_markers.keys() if "E" in k ]
        if keys != []:
            e = min(position_markers[k].left for k in keys )
            ans.append(((e,-1),(0,-1)))
        keys = [ k for k in position_markers.keys() if "W" in k ]
        if keys != []:
            w = max( position_markers[k].left+position_markers[k].width for k in keys)
            ans.append(((0,w+1),(0,-1)))
        return ans

    def get_vmarker_area(self,position_markers):
        ans =[]
        keys = [ k for k in position_markers.keys() if "S" in k ]
        if keys != []:
            s = min(position_markers[k].top for k in keys )
            ans.append(((0,-1),(s,-1)))
        keys = [ k for k in position_markers.keys() if "N" in k ]
        if keys != []:
            n = max( position_markers[k].top+position_markers[k].height for k in keys)
            ans.append(((0,-1),(0,n)))
        return ans


    def detect_hmarker_position(self,frame,marker_areas):
        """
        returns dict of list of (x, y1, y2)
        """
        ans = {}
        for ((x1,x2),(y1,y2)) in marker_areas:
            area = frame[y1:y2,x1:x2]
            value = decode(area, symbols=[ZBarSymbol.CODE39])
            if value:
                for barcode in value:
                    key = barcode.data.decode('utf-8')
                    if barcode.rect.height == 0:
                        continue
                    if key not in ans:
                        ans[key]=[]
                    ans[key].append((barcode.rect.left+x1,barcode.rect.top+y1,barcode.rect.top+y1+barcode.rect.height))
        return ans

    def detect_vmarker_position(self,frame,marker_areas):
        """
        returns dict of list of (y, x1, x2)
        """
        ans = {}
        for ((x1,x2),(y1,y2)) in marker_areas:
            area = frame[y1:y2,x1:x2]
            value = decode(area, symbols=[ZBarSymbol.CODE39])
            if value:
                for barcode in value:
                    key = barcode.data.decode('utf-8')
                    if barcode.rect.width == 0:
                        continue
                    if key not in ans:
                        ans[key]=[]
                    ans[key].append((barcode.rect.top+y1,barcode.rect.left+x1,barcode.rect.left+x1+barcode.rect.width))
        return ans



    def detect_hmarker_and_vmarker_position_globally(self,frame):
        """
        returns pair of dicts, for fallback.
        """
        value = decode(frame, symbols=[ZBarSymbol.CODE39])
        hmarkers={}
        vmarkers={}
        if value:
            for barcode in value:
                key = barcode.data.decode('utf-8')
                if barcode.rect.height != 0:
                    if key not in hmarkers:
                        hmarkers[key]=[]
                    hmarkers[key].append((barcode.rect.left,barcode.rect.top,barcode.rect.top+barcode.rect.height))
                if barcode.rect.width != 0:
                    if key not in vmarkers:
                        vmarkers[key]=[]
                    vmarkers[key].append((barcode.rect.top,barcode.rect.left,barcode.rect.left+barcode.rect.width))
        return (hmarkers,vmarkers)


    def get_marking_boxes(self,vmarkers,hmarkers,vmarkers_fallback,hmarkers_fallback,target_keys=None):
        if target_keys == None:
            target_keys = [(k1,k2) for k1 in vmarkers.keys() for k2 in hmarkers.keys()]

        ans = {}
        ignored_keys = []
        for (k1,k2) in target_keys:
            if k1 in vmarkers:
                x1 = min(a for (d,a,b) in vmarkers[k1])
                x2 = max(b for (d,a,b) in vmarkers[k1])
            elif k1 in vmarkers_fallback:
                x1 = min(a for (d,a,b) in vmarkers_fallback[k1])
                x2 = max(b for (d,a,b) in vmarkers_fallback[k1])
            else:
                ignored_keys.append((k1,k2))
                continue
            if k2 in hmarkers:
                y1 = min(a for (d,a,b) in hmarkers[k2])
                y2 = max(b for (d,a,b) in hmarkers[k2])
            elif k2 in hmarkers_fallback:
                y1 = min(a for (d,a,b) in hmarkers_fallback[k2])
                y2 = max(b for (d,a,b) in hmarkers_fallback[k2])
            else:
                ignored_keys.append((k1,k2))
                continue
            ans[(k1,k2)]=(x1,x2,y1,y2)
        return (ans,ignored_keys)

    def detect_marked_keys(self,frame,targetboxes):
        """
        returns the list of keys of marked boxes 
        INPUT:
        frame - gray scale image
        targetboxes - dictionary of cordinates (x1,x2,y1,y2) of boxes with northwest point (x1,y1) and southeast point (x2,y2).
        """
        frame = cv2.GaussianBlur(frame,(5,5),0)
        if len(targetboxes) == 0:
            return []
        data = []

        #for k in targetboxes.keys():
        #    (x1,x2,y1,y2) =targetboxes[k]
        #    data.extend(np.ravel(frame[y1:y2,x1:x2]))
        #th = self.get_th_by_2mean(data)
        #(res,frame) = cv2.threshold(frame,th,255, cv2.THRESH_BINARY)

        frame = 255 - frame

        score={}
        for k in targetboxes.keys():
            (x1,x2,y1,y2) =targetboxes[k]
            score[k]=np.sum(frame[y1:y2,x1:x2])/((x2-x1)*(y2-y1))
        th=self.get_th_by_2mean(score.values())
        ans = [k for k in score.keys() if score[k] > th]
        return ans

class OMR4Camera(OMRbase):
    def __init__(self,cap,questions):
        self.cap=cap
        self.questions = questions

    def get_detected_answers_for_questions_as_csv_lines(self):
        ans = []
        (answers,strings) = self.get_detected_answers_for_questions()
        s=",".join([si for si in strings if not si.startswith("marker:")])
        for questionid in answers.keys():
            m=",".join(["&".join(qi) for qi in answers[questionid]])
            d=questionid+','+m+','+s
            ans.append(d)
        return ans
    def get_detected_answers_for_questions(self):
        strings = self.detected_strings[:]
        strings.sort()
        ans = {}
        for questionid in self.questions.keys():
            if questionid not in self.detected_data:
                continue
            marked_keys=self.detected_data[questionid]
            ans[questionid]=[[a for (k,a) in qi if k in marked_keys] for qi in self.questions[questionid]]
        return(ans,strings)
        
    def modify_angle(self,frame,default_rotation_mat,default_rotaion_90):
        img_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        degrees=self.detect_angle(img_gray)
        if degrees != None:
            if (45 < degrees % 180 and degrees % 180  < 135) :
                needs_rotate_90=True
                degrees=degrees+90
                (w,h)=img_gray.shape
            else:
                needs_rotate_90=False
                (h,w)=img_gray.shape
            rotation_mat = cv2.getRotationMatrix2D((w/2,h/2), degrees, 1)
        else:
            rotation_mat = default_rotation_mat
            needs_rotate_90 = default_rotaion_90
        if needs_rotate_90:                
            frame=cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
        (h,w,c)=frame.shape
        return (cv2.warpAffine(frame,rotation_mat,(w,h)),rotation_mat,needs_rotate_90)

    def try_to_detect(self,img_gray,position_markers_for_question):
        harea=self.get_hmarker_area(position_markers_for_question)
        varea=self.get_vmarker_area(position_markers_for_question)
        hmarkers=self.detect_hmarker_position(img_gray,harea)
        vmarkers=self.detect_vmarker_position(img_gray,varea)
        (hmarkers_fallback,vmarkers_fallback)=self.detect_hmarker_and_vmarker_position_globally(img_gray)
        (marking_boxes,ignored_keys)=self.get_marking_boxes(vmarkers,hmarkers,vmarkers_fallback,hmarkers_fallback,target_keys=None)
        marked_keys=self.detect_marked_keys(img_gray, marking_boxes)
        return (marked_keys,marking_boxes,ignored_keys,(hmarkers,vmarkers))

    def get_key_of_marking_box_at(self,x,y):
        for questionid in self.marking_boxes.keys():
            for k in self.marking_boxes.keys[questionid]():
                (x1,x2,y1,y2)=self.marking_boxes[questionid][k]
                if  x1<x and x<x2 and y1<y and  y < y2:
                    return (questionid,k)
        return None
    
    def toggle_data(self,questionid,key):
        (questionid,k)=key
        if questionid not in self.fixed_keys:
            self.fixed_keys[questionid] = []
        if k in self.fixed_keys[questionid]:
            self.fixed_keys[questionid].append(k)
        if k in self.detected_data[questionid]:
            self.detected_data[questionid]= [x for x in self.detected_data[questionid] if k != x]
        else:
            self.detected_data[questionid].append(k)
            
    def mous_event_call_back(self,event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            key=self.get_key_of_marking_box_at(x,y)
            if key != None:
                self.toggle_data(key)

    def update_marking_boxes(self,questionid,marking_boxes):
        if questionid not in self.marking_boxes:
            self.marking_boxes[questionid]={}
        for k in marking_boxes.keys():
            self.marking_boxes[questionid][k]=marking_boxes[k]

    def update_detected_strings(self,strings):
        for k in strings:
            if k not in self.detected_strings:
                self.detected_strings.append(k)
                self.detected_strings.sort()

    def update_detected_data(self,questionid,marked_keys):
        if questionid not in self.detected_data:
            self.detected_data[questionid]=[]
        if questionid not in self.fixed_keys:
            self.fixed_keys[questionid]=[]
        for k in marked_keys:
            if k in self.fixed_keys[questionid]:
                continue
            if k in self.detected_data[questionid]:
                continue
            self.detected_data[questionid].append(k)

    def reset_detected_data(self):
        self.detected_strings = []
        self.fixed_keys = {}
        self.detected_data = {}
        self.marking_boxes = {}

    def draw_detected_data(self,frame):
        font = cv2.FONT_HERSHEY_SIMPLEX
        for questionid in self.marking_boxes.keys():
            for k in self.marking_boxes[questionid].keys():
                (x1,x2,y1,y2)=self.marking_boxes[questionid][k]
                if k in self.fixed_keys[questionid]:
                    frame=cv2.line(frame,(x1,y1),(x2,y2),(256,128,128),2)
                if k in self.detected_data[questionid]:
                    frame=cv2.rectangle(frame,(x1,y1),(x2,y2),(255,255,0),2)
                    frame=cv2.putText(frame,"{:s}-{:s}".format(k[0],k[1]),(x1,y1-6),font,.3,(255,0,255),1,cv2.LINE_AA)
                else:
                    frame=cv2.rectangle(frame,(x1,y1),(x2,y2),(255,255,255),1)
        s="/".join([ k for k in self.detected_strings if not k.startswith("marker:")])
        frame=cv2.putText(frame,s,(0,30),font,1.0,(255,255,255),4,cv2.LINE_AA)
        frame=cv2.putText(frame,s,(0,30),font,1.0,(64,64,128),2,cv2.LINE_AA)
        return frame

    def draw_markers(self,frame,position_markers,hmarkers,vmarkers):
        font = cv2.FONT_HERSHEY_SIMPLEX
        for k in position_markers.keys():
            (x,y,w,h) = position_markers[k]
            frame=cv2.rectangle(frame,(x,y),(x+w,y+h),(0,255,0),1)
            frame=cv2.putText(frame,k,(x,y-6),font,.3,(255,0,0),1,cv2.LINE_AA)
        for k in hmarkers.keys():
            for (d,a,b) in hmarkers[k]:
                frame=cv2.line(frame,(d,a),(d,b),(128,128,0),4)
                frame=cv2.putText(frame,k,(d+10,a+6),font,.3,(255,0,255),1,cv2.LINE_AA)
        for k in vmarkers.keys():
            for (d,a,b) in vmarkers[k]:
                frame=cv2.line(frame,(a,d),(b,d),(128,128,0),4)
                frame=cv2.putText(frame,k,(a,d-6),font,.3,(255,0,255),1,cv2.LINE_AA)
        return frame

    def detect_with_gui(self):
        font = cv2.FONT_HERSHEY_SIMPLEX
        rotation_mat = cv2.getRotationMatrix2D((0,0),0, 1)
        needs_rotate_90 = False
        self.reset_detected_data()
        while self.cap.isOpened():
            (ret, frame) = self.cap.read()
            if ret:
                (frame,rotation_mat,needs_rotate_90)=self.modify_angle(frame,rotation_mat,needs_rotate_90)
                img_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                (position_markers,strings)=self.detect_postion_markers(img_gray)
                self.update_detected_strings(strings)
                for key in position_markers.keys():                    
                    (marked_keys,marking_boxes,ignored_keys,(hmarkers,vmarkers))=self.try_to_detect(img_gray,position_markers[key])
                    self.update_detected_data(key,marked_keys)
                    self.update_marking_boxes(key,marking_boxes)

                    frame = self.draw_markers(frame,position_markers[key],hmarkers,vmarkers)

                frame=self.draw_detected_data(frame)
                cv2.imshow('toyomr scan image', frame)
                cv2.setMouseCallback('toyomr scan image',self.mous_event_call_back)
                # quit
                keyinput=cv2.waitKey(1)
                if keyinput & 0xFF == ord('q'):
                    break
                elif keyinput & 0xFF == ord('a'):
                    break
                elif keyinput & 0xFF == ord(' '):
                    self.reset_detected_data()
                elif keyinput & 0xFF == 27:
                    #ESC
                    break
                elif keyinput & 0xFF == 13:
                    #enter
                    #self.detected_data.sort()
                    #self.detected_strings.sort()

                    print(self.get_detected_answers_for_questions_as_csv_lines())








    
def main():
    if len(sys.argv) < 2:
        usage="{:s} devicenum".format(sys.argv[0])
        print(usage)
        return
    videodevicenum = int(sys.argv[1])
    question = [ [(chr(ord("A")+i),"{:d}{:d}".format(j,k))  for k in range(1,5)] for j in range(1,6) for i in range(10)]
    question_a = [[ (qij,"{:d}".format(j+1)) for (j,qij) in enumerate(qi) ] for qi in question]
    a=[["0","1","2","3","4","5","6"],["7","8","9","A"],["B","C","D"],["E","F"]]
    b=[["G","H","I"],["J","K","L","M"],["N","O"],["P","Q","R"]]
    question =[[("Y",aij) for aij in ai] for ai in a]+[ [("Z",bij) for bij in bi]for bi in b]
    question_b = [[ (qij,"{:d}".format(j+1)) for (j,qij) in enumerate(qi) ] for qi in question]
    questions = {"B":question_a,"A":question_b}
    cap = cv2.VideoCapture(videodevicenum)
    omr = OMR4Camera(cap,questions)
    omr.detect_with_gui()
    cap.release()


if __name__ == "__main__":
    main()

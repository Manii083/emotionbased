from django.shortcuts import render
from django.template import RequestContext
from django.contrib import messages
from django.http import HttpResponse
from django.conf import settings
from django.core.files.storage import FileSystemStorage
import cv2
from keras.models import load_model
from keras.preprocessing.image import img_to_array
import numpy as np
import os
from playsound import playsound
import base64
from django.core.files.base import ContentFile
import multiprocessing
from keras.models import model_from_json


value = []
global label, p
detection_model_path = 'models/haarcascade_frontalface_default.xml'
emotion_model_path = 'models/_mini_XCEPTION.106-0.65.hdf5'
face_detection = cv2.CascadeClassifier(detection_model_path)
EMOTIONS = ['angry','disgust','scared','happy','neutral','sad','surprise']

# Create your views here.
def index(request):
    if request.method == 'GET':
       return render(request, 'index.html', {})

def basic(request):
    if request.method == 'GET':
       return render(request, 'basic.html', {})

def DetectEmotion(request):
    if request.method == 'POST':
        name = request.POST.get('t1', False)
        output = checkEmotion()
        context= {'data':output}
        return render(request, 'PlaySong.html', context)
    
def WebCam(request):
    if request.method == 'GET':
        data = str(request)
        formats, imgstr = data.split(';base64,')
        imgstr = imgstr[0:(len(imgstr)-2)]
        data = base64.b64decode(imgstr)
        if os.path.exists('EmotionApp/static/photo/test.png'):
            os.remove('EmotionApp/static/photo/test.png')
        with open('EmotionApp/static/photo/test.png', 'wb') as f:
            f.write(data)
        f.close()
        context= {'data':"done"}
        return HttpResponse("Image saved")
        

def Upload(request):
    if request.method == 'GET':
       return render(request, 'Upload.html', {})

def StopSound(request):
    if request.method == 'GET':
        global p
        p.terminate()
        output = "Audio Stopped Successfully"
        context= {'data':output}
        return render(request, 'index.html', context)

# def SongPlay(request):
#     if request.method == 'POST':
#       global label, p 
#       name = request.POST.get('t1', False)
#       p = multiprocessing.Process(target=playsound, args=('songs/'+label+"/"+name,))
#       p.start()
#       output = '<center><font size=\"3\" color=\"black\">Your Mood Detected as : '+label+'<br/>Below are some selected songs based on your mood</font><br/></center><table align=\"right\">'
#       output+='<tr><td><font size=\"3\" color=\"black\">Choose&nbsp;Song</td><td><select name=\"t1\">'
#       for i in range(len(value)):
#           output+='<option value='+value[i]+'>'+value[i]+'</option>'
#       output+='</select></td></tr><tr><td></td><td><input type=\"submit\" value=\"Play\"></td></td></tr>'
#       output += '<td><a href=\'StopSound?data='+name+'\'><font size=3 color=black>Click Here to Stop</font></a></td></tr>'
#       output += '</table></body></html>'
#       context= {'data':output}
#       return render(request, 'PlaySong.html', context)  
# def SongPlay(request):
#     if request.method == 'POST':
#         global label, p 
#         name = request.POST.get('t1', False)
#         song_path = 'songs/' + label + '/' + name

#         # Check if the file exists
#         if not os.path.exists(song_path):
#             output = f'<center><font size="3" color="red">Error: File not found! Please check the song selection.</font></center>'
#             context = {'data': output}
#             return render(request, 'PlaySong.html', context)

#         # If the file exists, play it
#         p = multiprocessing.Process(target=playsound, args=(song_path,))
#         p.start()
#         output = (
#             f'<center><font size="3" color="black">Your Mood Detected as: {label}<br>'
#             f'Below are some selected songs based on your mood</font><br></center>'
#             f'<table align="right">'
#             f'<tr><td><font size="3" color="black">Choose&nbsp;Song</td>'
#             f'<td><select name="t1">'
#         )
#         for i in range(len(value)):
#             output += f'<option value={value[i]}>{value[i]}</option>'
#         output += '</select></td></tr><tr><td></td><td><input type="submit" value="Play"></td></tr>'
#         output += f'<td><a href="StopSound?data={name}"><font size="3" color="black">Click Here to Stop</font></a></td></tr>'
#         output += '</table></body></html>'
#         context = {'data': output}
        
#         return render(request, 'PlaySong.html', context)
def SongPlay(request):
    

    if request.method == 'POST':
        global label, p 
        name = request.POST.get('t1', False)
        song_path = os.path.abspath(os.path.join('songs', label, name))

        # Debugging: Print path details
        print("Label:", label)
        print("Name:", name)
        print("Attempting to access:", song_path)

        # Check if the file exists
        if not os.path.exists(song_path):
            print("File not found at:", song_path)  # Debugging
            output = f'<center><font size="3" color="red">Error: File not found! Please check the song selection.</font></center>'
            context = {'data': output}
            return render(request, 'PlaySong.html', context)

        # If the file exists, play it
        p = multiprocessing.Process(target=playsound, args=(song_path,))
        p.start()
        output = (
            f'<center><font size="3" color="black">Your Mood Detected as: {label}<br>'
            f'Below are some selected songs based on your mood</font><br></center>'
            f'<table align="right">'
            f'<tr><td><font size="3" color="black">Choose&nbsp;Song</td>'
            f'<td><select name="t1">'
        )
        for i in range(len(value)):
            output += f'<option value={value[i]}>{value[i]}</option>'
        output += '</select></td></tr><tr><td></td><td><input type="submit" value="Play"></td></tr>'
        output += f'<td><a href="StopSound?data={name}"><font size="3" color="black">Click Here to Stop</font></a></td></tr>'
        output += '</table></body></html>'
        context = {'data': output}
        return render(request, 'PlaySong.html', context)


def checkEmotion():
    global label
    # Load the model
    with open('models/cnnmodel.json', "r") as json_file:
        loaded_model_json = json_file.read()
        emotion_classifier = model_from_json(loaded_model_json)
    json_file.close()
    emotion_classifier.load_weights("models/cnnmodel_weights.h5")
    emotion_classifier._make_predict_function()

    # Load and preprocess the image
    orig_frame = cv2.imread('EmotionApp/static/photo/test.png')
    frame = cv2.imread('EmotionApp/static/photo/test.png', 0)
    faces = face_detection.detectMultiScale(
        frame, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30), flags=cv2.CASCADE_SCALE_IMAGE
    )
    print("===================" + str(len(faces)))

    if len(faces) > 0:
        faces = sorted(faces, reverse=True, key=lambda x: (x[2] - x[0]) * (x[3] - x[1]))[0]
        (fX, fY, fW, fH) = faces
        roi = orig_frame[fY:fY + fH, fX:fX + fW]
        roi = cv2.resize(roi, (32, 32))
        roi = roi.reshape(1, 32, 32, 3)
        roi = roi.astype('float32')
        img = roi / 255

        # Predict emotion
        preds = emotion_classifier.predict(img)
        predict = np.argmax(preds)
        label = EMOTIONS[predict]
        print(str(predict) + "====" + str(label))

        # Populate song list
        path = 'songs/' + label
        value.clear()
        for r, d, f in os.walk(path):
            for file in f:
                value.append(file)  # Full filename with extension
        print("Songs found:", value)

        # Generate HTML output
        output = f'<center><font size="3" color="black">Your Mood Detected as: {label}<br/>Below are some selected songs based on your mood</font><br/></center>'
        output += '<table align="right">'
        output += '<tr><td><font size="3" color="black">Choose&nbsp;Song</td><td><select name="t1">'
        for song in value:
            output += f'<option value="{song}">{song}</option>'
        output += '</select></td></tr><tr><td></td><td><input type="submit" value="Play"></td></td></tr></table></body></html>'
    else:
        output = '<font size="3" color="black">Unable to predict emotion from image</font>'
    return output

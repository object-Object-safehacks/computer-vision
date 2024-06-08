from flask import Flask, request, jsonify, render_template, send_from_directory, redirect, url_for
import torch
from PIL import Image
import io
from ultralytics import YOLO
import os
import cv2
import numpy as np


app = Flask(__name__)
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
#app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024

model_path = "content/datasets/runs/obb/train2/weights/best.pt"
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = YOLO(model_path)
model.to(device)

def readIndex():
    try:
        f = open("filesIndex.txt", "r")
        return(f.read())
    except: 
        f = open("filesIndex.txt", "x")
        f = open("filesIndex.txt", "r")
        return(f.read())  

def writeIndex(text):
    f = open("filesIndex.txt", "a")
    f.write(text)
    f.close()

#def saveToDevice(path, image):


def process_video(filepath):
    cap = cv2.VideoCapture(filepath)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Choose the codec suitable for your needs
    output_filepath = os.path.splitext(filepath)[0] + '_processed.mp4'
    out = cv2.VideoWriter(output_filepath, fourcc, 20.0, (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))))
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        results = model(frame, stream=True)
        framenum = 0 
        for result in results:
            boxes = result.boxes  # Boxes object for bounding box outputs
            masks = result.masks  # Masks object for segmentation masks outputs
            keypoints = result.keypoints  # Keypoints object for pose outputs
            probs = result.probs  # Probs object for classification outputs
            obb = result.obb  # Oriented boxes object for OBB outputs
#                result.show()  # display to screen        
            result.save(filename="concatonate.png")
            writeOutFrame = cv2.imread("concatonate.png") # cv2 doesn't work direct importing yolov8, need convert first
            out.write(writeOutFrame) 
            framenum += 1
            print(framenum)
            break # no need to continue after first frame because no more

    
    cap.release()
    out.release()
    return send_from_directory(app.config['UPLOAD_FOLDER'], os.path.basename(output_filepath), as_attachment=True)


    

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file1' not in request.files:
            return 'There is no file1 in the form!'
        file1 = request.files['file1']
        filename = file1.filename
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file1.save(filepath)
        filename, fileExtension = os.path.splitext(filepath)
            #results = model([filepath])  # return a list of Results objects, image only
        imageExtensions = set(['.png', '.jpg', '.jpeg'])
        
        if fileExtension in imageExtensions: 
            results = model(filepath, stream=False, conf=0.8) 
        # Process results list
            for result in results:
                boxes = result.boxes  # Boxes object for bounding box outputs
                masks = result.masks  # Masks object for segmentation masks outputs
                keypoints = result.keypoints  # Keypoints object for pose outputs
                probs = result.probs  # Probs object for classification outputs
                obb = result.obb  # Oriented boxes object for OBB outputs
#                result.show()  # display to screen
                result.save(filename=filepath)  # save to disk
                file_name = os.path.basename(filepath)
                return send_from_directory(app.config['UPLOAD_FOLDER'], file_name)
        
        else:
            #return(process_video(filepath))
            cap = cv2.VideoCapture(filepath)
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Choose the codec suitable for your needs
            output_filepath = os.path.splitext(filepath)[0] + '_processed.mp4'
            out = cv2.VideoWriter(output_filepath, fourcc, 20.0, (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))))
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                results = model(frame, stream=False, conf=0.8)
                framenum = 0 
                for result in results:
                    boxes = result.boxes  # Boxes object for bounding box outputs
                    masks = result.masks  # Masks object for segmentation masks outputs
                    keypoints = result.keypoints  # Keypoints object for pose outputs
                    probs = result.probs  # Probs object for classification outputs
                    obb = result.obb  # Oriented boxes object for OBB outputs
        #                result.show()  # display to screen        
                    result.save(filename="concatonate.png")
                    writeOutFrame = cv2.imread("concatonate.png") # cv2 doesn't work direct importing yolov8, need convert first
                    out.write(writeOutFrame) 
                    framenum += 1
                    print(framenum)
                    break # no need to continue after first frame because no more

    
        cap.release()
        out.release()
        return send_from_directory(app.config['UPLOAD_FOLDER'], os.path.basename(output_filepath), as_attachment=False)
        

    elif request.method == 'GET':
        return render_template('index.html')

def deployProduction():
    return Flask(__name__)

if __name__ == '__main__':
#    app.run(debug=True, port=2222)
    from waitress import serve # production
    serve(app, host="0.0.0.0", port=8082)

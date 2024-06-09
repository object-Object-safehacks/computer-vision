from flask import Flask, request, jsonify, render_template, send_from_directory, redirect, url_for
import torch
from PIL import Image
import io
from ultralytics import YOLO
import os
import cv2
import numpy as np
import requests
import mimetypes
import json
import time

domainUrl = "https://bananacv.pablonara.com"
app = Flask(__name__)
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
#app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024

model_path = "content1/datasets/runs/obb/train4/weights/best.pt"
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = YOLO(model_path)
model.to(device)

#def awaitVTresponse(sleepTime):
#    try: 
#        responseData = response.json()
#        idValue = responseData['data']['attributes']['stats']['malicious']
#        if idValue > 0:
#            print("detect!")
#            trueOrFalse.append(True)
#            guiUrlBase = "https://www.virustotal.com/gui/file-analysis/"
#            md5sum = responseData['data']['meta']['file_info']['md5']
#            urlsToReturn.append(guiUrlBase + md5)
#        else:
#            guiUrlBase = "https://www.virustotal.com/gui/file-analysis/"
#            md5sum = responseData['data']['meta']['file_info']['md5']
#            trueOrFalse.append(False)
#            urlsToReturn.append()
#    except Exception as e:
#        print("processing")
#        time.sleep(sleepTime)
        


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
            #obb = result.obb  # Oriented boxes object for OBB outputs
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
        fileExtension = set(['.png', '.jpg', '.jpeg'])
        
        if fileExtension in imageExtensions: 
            results = model(filepath, stream=False, conf=0.5) 
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
                results = model(frame, stream=False, conf=0.5)
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

# API
@app.route('/process_urls', methods=['POST'])
def process_urls():
    # Extract the JSON data from the request
    data = request.get_json()
    print(data)

 

# Extract the list of links from the dictionary
    links_list = data['files']

# Iterate over each link and print them
    trueOrFalse = []
    urlsToReturn = []
    extension = ''
    for link in links_list:
        headerType=''
        if link.startswith(('http://', 'https://')):
            # Handle URL
            response = requests.get(link)
            
            # Get the original filename from the URL
            filename = link.split('/')[-1].split('?')[0]  # Remove query parameters
            
            # Get the content type from the response headers
            content_type = response.headers.get('Content-Type')
            print(extension)
            # Map content type to file extension
            extension = mimetypes.guess_extension(content_type)
            #print('mimetypes: ' + extension)
                        
            if not filename.lower().endswith(extension):
                filename += extension
                print(extension)

            #    print(extension)
            if extension == None:
                trueOrFalse.append(None)
                urlsToReturn.append(link)
                continue


            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            
            print(filepath)

            with open(filepath, 'wb') as f:
                f.write(response.content)

            if extension == '.zip': # VT proof of concept check
                print(link)
                
                
                url = "https://www.virustotal.com/api/v3/files"
                files = { "file": ("payload.zip", open("./"+filepath, "rb"), "application/zip") }
                payload = { "password": "123" }
                headers = {
                    "accept": "application/json",
                    #"content-type": "multipart/form-data",
                    "x-apikey": "YOUR_API_KEY"
                }
                response = requests.post(url, data=payload, files=files, headers=headers)
                print (response.text)
                print (response.text)
                data = response.json()
                #data_dict = json.loads(data)
                
                # Access the 'id' value
                urlGet = "https://www.virustotal.com/api/v3/urls/"
                id_value = data['data']['links']['self']
                print(id_value)
                headers = {
                    "accept": "application/json",
                    "x-apikey": "YOUR_API_KEY"
                }
                print(id_value)
                response = requests.get(id_value, headers=headers)
                print(response.text)
                try:
                    responseData = response.json()
                    idValue = responseData['data']['attributes']['stats']['malicious']
                    if idValue > 0:
                        print("detect!")
                        trueOrFalse.append(True)
                        guiUrlBase = "https://www.virustotal.com/gui/file-analysis/"
                        md5sum = responseData['meta']['file_info']['md5']
                        urlsToReturn.append(guiUrlBase + md5sum)
                        print("test")
                    else:
                        guiUrlBase = "https://www.virustotal.com/gui/file-analysis/"
                        md5sum = responseData['meta']['file_info']['md5']
                        trueOrFalse.append(False)
                        urlsToReturn.append(guiUrlBase + md5sum)
                    print('reached here.')
                except Exception as e:
                    print(e)
                    print("processing")
                    time.sleep(25)
                    try:
                        responseData = response.json()
                        idValue = responseData['data']['attributes']['stats']['malicious']
                        if idValue > 0:
                            print("detect!")
                            trueOrFalse.append(True)
                            guiUrlBase = "https://www.virustotal.com/gui/file-analysis/"
                            md5sum = responseData['meta']['file_info']['md5']
                            urlsToReturn.append(guiUrlBase + md5sum)
                        else:
                            guiUrlBase = "https://www.virustotal.com/gui/file-analysis/"
                            md5sum = responseData['meta']['file_info']['md5']
                            trueOrFalse.append(False)
                            urlsToReturn.append(guiUrlBase + md5sum)
                    except Exception as e:
                        print("processing")
                        time.sleep(25)
                        try:
                            responseData = response.json()
                            idValue = responseData['data']['attributes']['stats']['malicious']
                            if idValue > 0:
                                print("detect!")
                                trueOrFalse.append(True)
                                guiUrlBase = "https://www.virustotal.com/gui/file-analysis/"
                                md5sum = responseData['meta']['file_info']['md5']
                                urlsToReturn.append(guiUrlBase + md5sum)
                                
                            else:
                                guiUrlBase = "https://www.virustotal.com/gui/file-analysis/"
                                md5sum = responseData['meta']['file_info']['md5']
                                trueOrFalse.append(False)
                                urlsToReturn.append(guiUrlBase + md5sum)
                                
                        except Exception as e:
                            print("VirusTotal timed out, assuming false")
                            trueOrFalse.append(False)
                            urlsToReturn.append(guiUrlBase + md5sum)
                            print(e)
                    

            # If there's no extension in the filename, append the correct one
            #if not filename.lower().endswith(extension):
                #filename += extension
            #print(extension)
            # Save the file with the correct extension
            #filepath = os.path.join(UPLOAD_FOLDER, filename)
            
            #with open(filepath, 'wb') as f:
                #f.write(response.content)
           
           
        else:
            file1 = request.files.get(link)
            #file1 = request.files[link]
            filename = file1.filename
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file1.save(filepath)
        filename, fileExtension = os.path.splitext(filepath)
            #results = model([filepath])  # return a list of Results objects, image only
        imageExtensions = set(['.png', '.jpg', '.jpeg', 'image/png', 'image/jpg', 'image/jpeg', 'image/webp'])
        

        if extension  in imageExtensions: 
            results = model(filepath, stream=False, conf=0.5, save_txt=True) 
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
                print(result.obb)
                count = len(results[0].obb)
                print("count", count)
                #print(boxes.conf)
                #classes: Dict[int, str] = results.names
                #resultsWithProbs: List[Tuple[Results, str]] = [(result, classes[result.boxes.cls.numpy()[0]]) for result in results]
                try:
                    if count == 0:
                        trueOrFalse.append(False)
                        print("false")
                    else:
                        trueOrFalse.append(True)
                        print("true")
                except Exception as e:
                    trueOrFalse.append(False)
                    print("Frue")
                    print(e)
                
                urlsToReturn.append(domainUrl + url_for('static', filename="uploads/"+file_name))
        
        else:
            #return(process_video(filepath))
            cap = cv2.VideoCapture(filepath)
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Choose the codec suitable for your needs
            output_filepath = os.path.splitext(filepath)[0] + '_processed.mp4'
            out = cv2.VideoWriter(output_filepath, fourcc, 20.0, (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))))
            framenum = 0 

            while True:
                detected = False
                ret, frame = cap.read()
                if not ret:
                    break
                results = model(frame, stream=True, conf=0.5)
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
                    count = len(results[0].obb)
                    #count = len(results[0].obb)
                    if count == 0:
                        trueOrFalse.append(False)
                    else:
                        trueOrFalse.append(True)

                    break # no need to continue after first frame because no more

    
            cap.release()
            out.release()
            #count = len(results[0].obb)
            #if boxes.conf == 'None':
                #trueOrFalse.append(False)
            #else:
                #trueOrFalse.append(True)
                    
            urlsToReturn.append(domainUrl + url_for('static', filename='uploads/'+output_filepath))

    data = {
    'results': trueOrFalse,
    'urls': urlsToReturn
    }

                

    return jsonify(data)

if __name__ == '__main__':
    #app.run(debug=True, port=8082)
    from waitress import serve # production
    serve(app, host="0.0.0.0", port=8082, threads=4)

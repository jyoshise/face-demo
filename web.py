import os
import simplejson
import requests
import argparse
import base64
import httplib2

from flask import Flask, render_template, redirect, url_for, request, make_response
from flask import send_from_directory
from werkzeug import secure_filename
from PIL import Image
from PIL import ImageDraw, ImageFont
# from googleapiclient import discovery
# from oauth2client.client import GoogleCredentials
from havenondemand.hodindex import HODClient

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = '/home/stackato/app/static'
app.debug = True

ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

"""
API call for Google Cloud Vision API
credentials must be specified as environment variable GOOGLE_APPLICATION_CREDENTIALS.
"""
# DISCOVERY_URL='https://{api}.googleapis.com/$discovery/rest?version={apiVersion}'
# def get_vision_service():
#    credentials = GoogleCredentials.get_application_default()
#    return discovery.build('vision', 'v1', credentials=credentials,
#                           discoveryServiceUrl=DISCOVERY_URL)

"""
API call for HPE Heaven OnDemand
API key for HOD must be specified as environment variable HAVEN_API_KEY.
"""
hodclient = HODClient(apikey=os.environ['HAVEN_API_KEY'], apiversiondefault=1)
hodurl="http://api.havenondemand.com/1/api/sync/{}/v1"
def hodpostrequests(function,data={},files={}):
               data["apikey"]=os.environ['HAVEN_API_KEY']
               callurl=hodurl.format(function)
               r=requests.post(callurl,data=data,files=files)
               return r.json()

@app.route("/")
def index():
    return render_template('layout.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        max_results = request.form['faces']
        if file and allowed_file(file.filename):
            infile = secure_filename(file.filename)
#            g_outfile = "g_out_" + secure_filename(file.filename)
            h_outfile = "h_out_" + secure_filename(file.filename)
            input_filename = app.config['UPLOAD_FOLDER'] + "/" + infile
#            g_output_filename = app.config['UPLOAD_FOLDER'] + "/" + g_outfile
            h_output_filename = app.config['UPLOAD_FOLDER'] + "/" + h_outfile
            file.save(input_filename)

    with open(input_filename, 'rb') as image:
#        g_faces = detect_face(image, max_results)
#        image.seek(0)
        h_faces = hodpostrequests('detectfaces', files={'file': image}, data={'additional': True})
        image.seek(0)
#        g_highlight_faces(image, g_faces, g_output_filename)
#        image.seek(0)
        h_highlight_faces(image, h_faces, h_output_filename)

#    return render_template('show_result.html', input_filename=infile, g_output_filename=g_outfile, h_output_filename=h_outfile, g_count=len(g_faces), h_count=len(h_faces['face']), g_faces=g_faces, h_faces=h_faces)
    return render_template('show_result.html', input_filename=infile, h_output_filename=h_outfile, h_count=len(h_faces['face']), h_faces=h_faces)

"""
# [START detect_face]
def detect_face(face_file, max_results=4):
    image_content = face_file.read()
    batch_request = [{
        'image': {
            'content': base64.b64encode(image_content).decode('UTF-8')
            },
        'features': [{
            'type': 'FACE_DETECTION',
            'maxResults': max_results,
            }]
        }]

    service = get_vision_service()
    request = service.images().annotate(body={
        'requests': batch_request,
        })
    response = request.execute()

    return response['responses'][0]['faceAnnotations']
# [END detect_face]
"""

"""
# [START highlight_faces]
def g_highlight_faces(image, faces, output_filename):
    im = Image.open(image)
    draw = ImageDraw.Draw(im)

    for face in faces:
        box = [(v.get('x', 0.0), v.get('y', 0.0)) for v in face['fdBoundingPoly']['vertices']]
        draw.line(box + [box[0]], width=5, fill='#ff8800')
    del draw
    return im.save(output_filename)
# [END highlight_faces]
"""

# [START highlight_faces]
def h_highlight_faces(image, faces, output_filename):
    im = Image.open(image)
    draw = ImageDraw.Draw(im)
    fnt = ImageFont.truetype('/home/stackato/app/static/Ubuntu-R.ttf', 30)
    for face in faces['face']:
        left = face.get('left')
        top = face.get('top')
        width = face.get('width')
        height = face.get('height')
        addinfo = face.get('additional_information')
        if addinfo == None:
            age = 'unknown'
        else:
            age = addinfo.get('age')
        draw.line(((left,top),(left+width,top),(left+width,top+height),(left,top+height),(left,top)), width=5, fill='#01a982')
        draw.text((left,top+height), age, font=fnt, fill='#01a982')
    del draw
    return im.save(output_filename)
# [END highlight_faces]


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

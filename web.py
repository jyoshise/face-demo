import os
import simplejson
import requests
from flask import Flask, render_template, redirect, url_for, request, make_response
from flask import send_from_directory
from werkzeug import secure_filename

import argparse
import base64

from PIL import Image
from PIL import ImageDraw

from googleapiclient import discovery
import httplib2
from oauth2client.client import GoogleCredentials

from havenondemand.hodindex import HODClient
hodclient = HODClient(apikey=os.environ['HAVEN_API_KEY'], apiversiondefault=1)
hodurl="http://api.havenondemand.com/1/api/sync/{}/v1"

ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = '/home/stackato/app/static'
app.debug = True

# [START get_vision_service]
DISCOVERY_URL='https://{api}.googleapis.com/$discovery/rest?version={apiVersion}'


def get_vision_service():
    credentials = GoogleCredentials.get_application_default()
    return discovery.build('vision', 'v1', credentials=credentials,
                           discoveryServiceUrl=DISCOVERY_URL)
# [END get_vision_service]

def hodpostrequests(function,data={},files={}):
               data["apikey"]=os.environ['HAVEN_API_KEY']
               callurl=hodurl.format(function)
               r=requests.post(callurl,data=data,files=files)
               return r.json()

@app.route("/")
def index():
    return render_template('layout.html')

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        max_results = request.form['faces']
#        max_results = 10
        if file and allowed_file(file.filename):
            infile = secure_filename(file.filename)
            g_outfile = "g_out_" + secure_filename(file.filename)
            h_outfile = "h_out_" + secure_filename(file.filename)
            input_filename = app.config['UPLOAD_FOLDER'] + "/" + infile
            g_output_filename = app.config['UPLOAD_FOLDER'] + "/" + g_outfile
            h_output_filename = app.config['UPLOAD_FOLDER'] + "/" + h_outfile
            file.save(input_filename)
# [START main]
    with open(input_filename, 'rb') as image:
# google vision API
        g_faces = detect_face(image, max_results)
# Haven API
        image.seek(0)
        h_faces = hodpostrequests('detectfaces', files={'file': image})

        # Reset the file pointer, so we can read the file again
        image.seek(0)
        g_highlight_faces(image, g_faces, g_output_filename)
        image.seek(0)
        h_highlight_faces(image, h_faces, h_output_filename)

    return render_template('show_result.html', input_filename=infile, g_output_filename=g_outfile, h_output_filename=h_outfile, g_count=len(g_faces), h_count=len(h_faces['face']), g_faces=g_faces, h_faces=h_faces)

# [END main]


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


# [START highlight_faces]
def g_highlight_faces(image, faces, output_filename):
    im = Image.open(image)
    draw = ImageDraw.Draw(im)

    for face in faces:
        box = [(v.get('x', 0.0), v.get('y', 0.0)) for v in face['fdBoundingPoly']['vertices']]
        draw.line(box + [box[0]], width=5, fill='#00ff00')
    del draw
    return im.save(output_filename)
# [END highlight_faces]

# [START highlight_faces]
def h_highlight_faces(image, faces, output_filename):
    im = Image.open(image)
    draw = ImageDraw.Draw(im)

    for face in faces['face']:
        left = face.get('left')
        top = face.get('top')
        width = face.get('width')
        height = face.get('height')
        draw.line(((left,top),(left+width,top),(left+width,top+height),(left,top+height),(left,top)), width=5, fill='#0000FF')
    del draw
    return im.save(output_filename)
# [END highlight_faces]


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

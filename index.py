import time
import os
import simplejson
import requests
import argparse
import base64

from flask import Flask, render_template, redirect, url_for, request, make_response
from flask import send_from_directory
from werkzeug import secure_filename
from PIL import Image
from PIL import ImageDraw, ImageFont

# Variables
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = '/home/stackato/app/static'
app.debug = True

ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

_url = 'https://api.projectoxford.ai/face/v1.0/detect'
_key = os.environ['AZURE_API_KEY']
_maxNumRetries = 10

def processRequest( json, data, headers, params = None ):

    """
    Helper function to process the request to Project Oxford

    Parameters:
    json: Used when processing images from its URL. See API Documentation
    data: Used when processing image read from disk. See API Documentation
    headers: Used to pass the key information and the data type request
    """

    retries = 0
    result = None

    while True:

        response = requests.request( 'post', _url, json = json, data = data, headers = headers, params = params )

        if response.status_code == 429:

            print "Message: %s" % ( response.json()['error']['message'] )

            if retries <= _maxNumRetries:
                time.sleep(1)
                retries += 1
                continue
            else:
                print 'Error: failed after retrying!'
                break

        elif response.status_code == 200 or response.status_code == 201:
#
            if 'content-length' in response.headers and int(response.headers['content-length']) == 0:
                result = None
            elif 'content-type' in response.headers and isinstance(response.headers['content-type'], str):
                if 'application/json' in response.headers['content-type'].lower():
                    result = response.json() if response.content else None
                elif 'image' in response.headers['content-type'].lower():
                    result = response.content
        else:
            print "Error code: %d" % ( response.status_code )
            print "Message: %s" % ( response.json()['error']['message'] )

        break

    return result
#
# [START highlight_faces]
def h_highlight_faces(image, result, output_filename):
    im = Image.open(image)
    draw = ImageDraw.Draw(im)
    fnt = ImageFont.truetype('/home/stackato/app/static/Ubuntu-R.ttf', 40)
    for currFace in result:
        faceRectangle = currFace['faceRectangle']
        faceAttributes = currFace['faceAttributes']
        left = faceRectangle['left']
        top = faceRectangle['top']
        width = faceRectangle['width']
        height = faceRectangle['height']
        age = faceAttributes['age']
#        if faceAttributes['gender']=='female':
#            age = age-5
#
        textToWrite = "%c (%d)" % ( 'M' if faceAttributes['gender']=='male' else 'F', age )
        fillcolor = '#55ff00' if faceAttributes['gender']=="male" else '#ff4400'

# Draw outline
        draw.line(((left,top),(left+width,top),(left+width,top+height),(left,top+height),(left,top)), width=2, fill=fillcolor)

# Draw landmarks
        faceLandmarks = currFace['faceLandmarks']
        for _, currLandmark in faceLandmarks.iteritems():
            draw.ellipse(((int(currLandmark['x']-1),int(currLandmark['y']-1)),(int(currLandmark['x']+1),int(currLandmark['y']+1))), fill=fillcolor)

# Draw text label
        draw.rectangle(((left,top+height),(left+width,top+height+50)), fill=fillcolor)
        draw.text((left,top+height), textToWrite, font=fnt, fill='#ffffff')

    del draw
    return im.save(output_filename)
# [END highlight_faces]



@app.route("/")
def index():
    return render_template('layout.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    params = { 'returnFaceAttributes': 'age,gender',
            'returnFaceLandmarks': 'true'}
    headers = dict()
    headers['Ocp-Apim-Subscription-Key'] = _key
    headers['Content-Type'] = 'application/octet-stream'

    json = None

    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            infile = secure_filename(file.filename)
            h_outfile = "h_out_" + secure_filename(file.filename)
            input_filename = app.config['UPLOAD_FOLDER'] + "/" + infile
            h_output_filename = app.config['UPLOAD_FOLDER'] + "/" + h_outfile
            file.save(input_filename)

#
    with open(input_filename, 'rb') as image:
        data = image.read()
        result = processRequest( json, data, headers, params )
        image.seek(0)
        h_highlight_faces(image, result, h_output_filename)

    return render_template('show_result.html', input_filename=infile, h_output_filename=h_outfile, h_faces=result)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

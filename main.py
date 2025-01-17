import os
from flask import Flask, render_template, request, g, flash, redirect, url_for, session
from couchdb.design import ViewDefinition
from flaskext.couchdb import CouchDBManager
from flask_bootstrap import Bootstrap
from form import ContactForm
from dataform import *
from userInfo import Login, Register
from imgSearch import imgSearch
from dbDoucment import *
import json
import uuid

#import paramiko

import tempfile
import subprocess
import time
from subprocess import call
##########################################################
import cv2
import numpy as np
import urllib
from flask import jsonify, make_response

from io import StringIO
import sys
#print ("===========================PRINTING SYSTEM PATH=================================")
#print (sys.path)
sys.path.append('/usr/local/lib/python3.5/dist-packages')

#import StringIO
import contextlib

#########################################################



###NEW UPDATE

#import paramiko

# subprocess.Popen(["pip", "install", "xmltodict"]).communicate()
# subprocess.Popen(["pip3", "install", "xmltodict"]).communicate()
#


# subprocess.Popen(["/usr/bin/git", "clone", "https://github.com/cameronbwhite/Flask-CAS.git"]).communicate()
# # subprocess.Popen(["cd", "Flask-CAS"]).communicate()
# subprocess.Popen(["python", "Flask-CAS/setup.py", "install"]).communicate()



#Include the webapps Blueprints
from app_txl_cloud import app_txl_cloud

from bioinformatics import bioinformatics

from app_collaborative_sci_workflow import app_collaborative_sci_workflow

from app_code_clone import app_code_clone

app = Flask(__name__)
#register the blueprints...










bootstrap = Bootstrap(app)
app.secret_key = 'development key'

app.config['UPLOAD_FOLDER'] = 'static/uploads/'
app.config['ALLOWED_EXTENSIONS'] = set(['jpg', 'png', 'tiff', 'jpeg', 'JPG', 'JPEG', 'PNG', 'TIFF'])
app.config.update(
    COUCHDB_SERVER='http://localhost:5984',
    COUCHDB_DATABASE='plantphenotype'
)

# import subprocess
# subprocess.Popen(["pip", "install", "xmltodict"]).communicate()

from FlaskCAS.flask_cas import CAS
from FlaskCAS.flask_cas import login_required
# from xmltodict import parse
cas = CAS(app, '/cas')

app.config['CAS_SERVER'] = 'https://cas.usask.ca'
app.config['CAS_AFTER_LOGIN'] = 'index' #// this is a method name see belowlo
app.config['CAS_AFTER_LOGOUT'] = 'sign_out'


views_by_source = ViewDefinition('source', 'findid', '''
    function (doc) {
        if (doc.source && doc.annotation && doc.imglink) {
            emit (doc.source, doc)
        };
    }
    ''')
views_by_user = ViewDefinition('login', 'findPassword', '''
    function (doc) {
        if (doc.username && doc.password) {
            emit(doc.username, doc.password)
        };
    }
    ''')
views_by_Lsysmodel = ViewDefinition('Lsysmodel', 'findUserModel', '''
    function (doc) {
        if (doc.user && doc.src) {
            emit(doc.user, doc)
        };
    }
    ''')

views_by_non_validated_clones = ViewDefinition('hello', 'my_non_validated_clones', '''
    function (doc) {
         if (doc.is_clone_doc == 'yes' && doc.is_validated_by_any_user == 'no') {
            emit(doc._id, doc)
        };   
    }
    ''')

views_by_validated_clones = ViewDefinition('hello', 'my_validated_clones', '''
    function (doc) {
         if (doc.is_clone_doc == 'yes') {
            emit(doc._id, doc)
        };   
    }
    ''')


# userInfo & uplaod imgs database
manager = CouchDBManager()
manager.setup(app)
manager.add_viewdef([views_by_source, views_by_user, views_by_Lsysmodel, views_by_non_validated_clones, views_by_validated_clones])
manager.sync(app)

app.register_blueprint(app_txl_cloud)

app.register_blueprint(bioinformatics)

app.register_blueprint(app_collaborative_sci_workflow)

app.register_blueprint(app_code_clone)

# imgs search database
search_obj = imgSearch()

imgId = []
idseq = 0


def image_source(selectedSource):
    sources = []
    for row in views_by_source(g.couch):
        sources.append(row.key)
    sources = list(set(sources))
    sources.sort()
    if selectedSource in sources:
        # move selectedSource to header of list
        sources.remove(selectedSource)
        sources.insert(0, selectedSource)
    return sources


def image_source2():
    sources = ['none']
    for row in views_by_source(g.couch):
        sources.append(row.key)
    sources = list(set(sources))
    return sources


def image_source3(directory):
    global imgId
    for row in views_by_source(g.couch):
        if row.key == directory:
            imgId.append(row.id)


def image_source4(src):
    for row in views_by_source(g.couch):
        if row.value['imglink'] == src:
            return row.id
        else:
            return None


def lsysmodel_user(name):
    for row in views_by_Lsysmodel(g.couch):
        if row.key == name:
            return row.id
    return None


def allowed_files(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']


@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    l_login = Login()
    l_register = Register()
    return render_template("index.html", login=l_login, register=l_register)


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    form2 = Dataform()
    sources2 = image_source2()
    form2.Sel_Dir.choices = {(x, x) for x in sources2}
    if request.method == 'GET':
        return render_template("upload.html", form=form2)
    elif request.method == 'POST':
        uploaded_files = request.files.getlist("file[]")
        for file in uploaded_files:
            if file and allowed_files(file.filename):
                filename = file.filename
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                try:
                    if form2.Sel_Dir.data == 'none':
                        entry = PlantPhenotype(source=form2.dir_name.data, imglink=filepath,
                                               annotation=form2.Annotation.data)
                        entry.store()
                    else:
                        entry = PlantPhenotype(source=form2.Sel_Dir.data, imglink=filepath,
                                               annotation=form2.Annotation.data)
                        entry.store()
                except Exception as e:
                    flash("Databased error. Failed to Uploaded")
                    return render_template("upload.html", form=form2)
            else:
                flash("File has error. Failed to upload")
                return render_template("upload.html", form=form2)
        flash("Successfully Uploaded")
        return redirect(url_for('dataInsert'))


@app.route('/dataInsertSec', methods=['GET', 'POST'])
def dataInsert():
    global idseq, imgId
    form = ContactForm()
    sources = image_source(form.source.data)
    form.source.choices = [(x, x) for x in sources]
    if request.method == 'POST':
        if request.form['submit'] == 'Simulation':
            entry = PlantPhenotype.load(imgId[idseq])
            matchResult = search_obj.search(entry.imglink)
            print(json.dumps(matchResult, indent=4))
            return render_template("searchResult.html", imgPaths=json.dumps(matchResult))
        if request.form['submit'] == 'Next Picture':
            print("next picture")
            print(len(imgId))
            idseq += 1
            print(idseq)
            if idseq >= len(imgId):
                idseq = len(imgId) - 1
            entry = PlantPhenotype.load(imgId[idseq])
            form.textArea.data = entry.annotation
            return render_template("dataInsertSec.html", name=session.get('name'), form=form,
                                   source=json.dumps(entry.imglink))
        elif request.form['submit'] == 'Prev. Picture':
            print("prev picture")
            idseq -= 1
            if idseq < 0:
                idseq = 0
            entry = PlantPhenotype.load(imgId[idseq])
            form.textArea.data = entry.annotation
            return render_template("dataInsertSec.html", name=session.get('name'), form=form,
                                   source=json.dumps(entry.imglink))
        elif request.form['submit'] == 'Update Source':
            print("update source")
            print(form.source.data)
            imgId = []
            image_source3(form.source.data)
            idseq = 0
            entry = PlantPhenotype.load(imgId[idseq])
            form.textArea.data = entry.annotation
            return render_template("dataInsertSec.html", name=session.get('name'), form=form,
                                   source=json.dumps(entry.imglink))
        elif request.form['submit'] == 'Update Annotation':
            print("update annotation")
            entry = PlantPhenotype.load(imgId[idseq])
            entry.annotation = form.textArea.data
            try:
                entry.store()
                entry = PlantPhenotype.load(imgId[idseq])
                form.textArea.data = entry.annotation
                return render_template("dataInsertSec.html", name=session.get('name'), form=form,
                                       source=json.dumps(entry.imglink))
            except Exception as e:
                flash("Entry error %s", e)
                entry = PlantPhenotype.load(imgId[idseq])
                form.textArea.data = entry.annotation
                return render_template("dataInsertSec.html", name=session.get('name'), form=form,
                                       source=json.dumps(entry.imglink))
    else:
        if sources == []:
            form.textArea.data = ""
            return render_template("dataInsertSec.html", name=session.get('name'), form=form)
        else:
            image_source3(sources[0])
            entry = PlantPhenotype.load(imgId[idseq])
            form.textArea.data = entry.annotation
            return render_template("dataInsertSec.html", name=session.get('name'), form=form,
                                   source=json.dumps(entry.imglink))


@app.route('/updateAnotation', methods=['POST'])
def updateAnotation():
    if request.form is not None:
        print(request.form)
        try:
            plantPhenotype = PlantPhenotype.load(image_source4(request.form['src']))
            plantPhenotype.annotation = request.form['textArea']
            plantPhenotype.height = request.form['height']
            plantPhenotype.width = request.form['width']
            plantPhenotype.area = request.form['area']
            plantPhenotype.size = request.form['size']
            plantPhenotype.weather = request.form['weatherCondition']
            plantPhenotype.soilCondition = request.form['soilCondition']
            plantPhenotype.location = request.form['location']
            plantPhenotype.localSat = request.form['localSat']
            plantPhenotype.store()
            return "Succeed!"
        except Exception as e:
            return "Server Error!"
    else:
        return "Failed!"


@app.route('/login', methods=['POST'])
def login():
    l_form = Login(request.form)
    name = l_form.login_user.data
    password = l_form.login_pass.data
    row = (views_by_user(g.couch))[name]

    # verify username and password
    if l_form.validate():
        try:
            if not row or password != list(row)[0].value:
                flash("Username or password incorrect")
                raise ValueError("Username or password incorrect")
        except Exception as e:
            return redirect(url_for('index'))
    else:
        print("Welcome to the user: ")
        return redirect(url_for('index'))

    # store user name
    session['name'] = l_form.login_user.data
    return redirect(url_for('dataInsert'))


@app.route('/register', methods=['POST'])
def register():
    l_form = Register(request.form)
    if l_form.validate():
        users = Users()
        users.username = l_form.username.data
        users.password = l_form.password.data
        users.email = l_form.email.data
        users.store()
        flash("Congratulation! Register Completed!")
        session['name'] = l_form.username.data
        return redirect(url_for('dataInsert'))
    else:
        flash("Register Error!")
        return redirect(url_for('index'))


@app.route('/LSystem', methods=['POST', 'GET'])
def lsystemModel():
    lsystemform = LSystemform()
    id_model = lsysmodel_user(session.get('name'))

    if id_model is not None:
        entry = LSystemModel.load(id_model)
        lsystemform.speed.data = entry.speed
        lsystemform.scale.data = entry.scale
        lsystemform.depth.data = entry.depth
        lsystemform.maxAngle.data = entry.maxAngle
        lsystemform.minAngle.data = entry.minAngle
        lsystemform.rotation.data = entry.rotation
        lsystemform.velocity.data = entry.velocity
        lsystemform.segment.data = entry.segments
        lsystemform.ruleA.data = entry.rules['ruleA']
        lsystemform.ruleB.data = entry.rules['ruleB']
        lsystemform.ruleC.data = entry.rules['ruleC']
        lsystemform.ruleD.data = entry.rules['ruleD']
        lsystemform.ruleE.data = entry.rules['ruleE']

        lsystemform.imgobj = entry.src #Image.open(BytesIO(base64.b64decode(entry.src)))
        #response = send_file(tempFileObj, as_attachment=True, attachment_filename='myfile.jpg')
        #print(lsystemform.data)
    else:
        lsystemform.speed.data = 1.0
        lsystemform.scale.data = 0.45
        lsystemform.depth.data = 6
        lsystemform.maxAngle.data = 0.60
        lsystemform.minAngle.data = 0.55
        lsystemform.rotation.data = 0.05
        lsystemform.velocity.data = 0.1
        lsystemform.segment.data = 2000
        lsystemform.ruleA.data = "ASLss*[+AL][-AL]///>"
        lsystemform.ruleB.data = ""
        lsystemform.ruleC.data = ""
        lsystemform.ruleD.data = ""
        lsystemform.ruleE.data = ""
        lsystemform.imgobj = "Plant Image"
    return render_template("LSystem.html", name=session.get('name'), image = lsystemform.imgobj, form=lsystemform)


#     imgData = base64.b64decode(imgSrc[22:])
#     leniimg = open('E://img.png', 'wb')
#     leniimg.write(imgData)
#     leniimg.close()

@app.route('/saveModel', methods=['POST'])
def saveModel():
    print(request.form)
    if request.form is not None:
        lSystemModel = LSystemModel()
        lSystemModel.depth = float(request.form['depth'])
        lSystemModel.maxAngle = float(request.form['maxAngle'])
        lSystemModel.minAngle = float(request.form['minAngle'])
        lSystemModel.rotation = float(request.form['rotation'])
        lSystemModel.scale = float(request.form['scale'])
        lSystemModel.segments = float(request.form['segments'])
        lSystemModel.velocity = float(request.form['velocity'])
        lSystemModel.speed = float(request.form['speed'])
        lSystemModel.src = request.form['src'][22:]  # because of the format of base64 image
        lSystemModel.rules = dict(ruleA=request.form['ruleA'], ruleB=request.form['ruleB'],
                                  ruleC=request.form['ruleC'], ruleD=request.form['ruleD'],
                                  ruleE=request.form['ruleE'])
        lSystemModel.user = session.get('name')
        lSystemModel.store()
        return "Succeed!"
    else:
        return "Failed!"








##############################################################################################
############################ P2IRC API CODES STARTS HERE #####################################


#p2irc apis homepage
@app.route('/p2irc_apis')
def p2irc_apis_homepage():
    return render_template('cloud_vision.html')

#p2irc apis homepage
@app.route('/cloud_vision_pipeline_save')
def cloud_vision_pipeline_save():
    return render_template('cloud_vision_pipeline_save.html')

@app.route('/p2irc_cloud_codes')
def p2irc_cloud_codes_homepage():
    return render_template('p2irc_cloud_codes.html')



tasks = [
    {
        'id': 1,
        'title': u'Buy groceries',
        'description': u'Milk, Cheese, Pizza, Fruit, Tylenol', 
        'done': False
    },
    {
        'id': 2,
        'title': u'Learn Python',
        'description': u'Need to find a good Python tutorial on the web', 
        'done': False
    }
]

@app.route('/get_image/rgblink/<path:url>',  methods=['GET'])
def get_image8(url):
	
	
	
    img = cv2.imread('static/img/1.jpg')
	
    img = cv2.cvtColor( img, cv2.COLOR_RGB2GRAY )
    cv2.imwrite( "static/img/gray.png", img )
    
    return jsonify({'allTasks': tasks})





@app.route('/get_image/rgb2gray/',  methods=['GET'])
def rgb2gray():
	image_location = request.args.get('img_loc')

	img = cv2.imread(image_location)
	img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
	cv2.imwrite('static/img/gray.png', img)

	return jsonify({'allTasks':tasks})





@app.route('/get_image/noise_removal/',  methods=['GET'])
def noise_removal():
	image_location = request.args.get('img_loc')

	img = cv2.imread(image_location)
	img = cv2.fastNlMeansDenoisingColored(img,None,10,10,7,21)
	cv2.imwrite('static/img/gray.png', img)

	return jsonify({'allTasks':tasks})



@app.route('/pythoncom',  methods=['POST'])
def Python_com():

	program = request.form['textarea_source_code']
	#program = 'for i in range(3):\n    print("Python is cool")'

	
	old_stdout = sys.stdout
	redirected_output = sys.stdout = StringIO()
	res = exec(program)
	sys.stdout = old_stdout

	return redirected_output.getvalue()
	#return jsonify(res)
	#return jsonify({'allTasks':tasks})





#######################################IMAGE TOOLS NEW STARTS #################################
@app.route('/img_tools/img_tools_noiseRemoval_process/',  methods=['POST'])
def img_tools_noiseRemoval_process():
	image_location = request.form['image_location']
	filter_strength = float(request.form['filter_strength'])
	window_size = int(request.form['window_size'])
	weight_window_size = int(request.form['weight_window_size'])
	img_output_location = request.form['img_output_location']

	img = cv2.imread(image_location)
	img = cv2.fastNlMeansDenoisingColored(img,None,filter_strength,10,window_size,weight_window_size)
	cv2.imwrite(img_output_location, img)

	return jsonify({'allTasks':tasks})



@app.route('/img_tools/img_tools_rgb2gray_process/',  methods=['POST'])
def img_tools_rgb2gray_process():
	image_location = request.form['image_location']
	img_output_location = request.form['img_output_location']

	img = cv2.imread(image_location)
	img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
	cv2.imwrite(img_output_location, img)

	return jsonify({'allTasks':tasks})


@app.route('/img_tools/img_tools_binThreshold_process/',  methods=['POST'])
def img_tools_binThreshold_process():
	image_location = request.form['image_location']
	threshold_value = int(request.form['threshold_value'])
	img_output_location = request.form['img_output_location']


	img = cv2.imread(image_location)
	ret,img = cv2.threshold(img,threshold_value,255,cv2.THRESH_BINARY)
	cv2.imwrite(img_output_location, img)

	return jsonify({'allTasks':tasks})



@app.route('/img_tools/img_tools_rgb2hsv_process/',  methods=['POST'])
def img_tools_rgb2hsv_process():
	image_location = request.form['image_location']
	hsv_channel = request.form['hsv_channel']
	img_output_location = request.form['img_output_location']


	img = cv2.imread(image_location)
	hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
	h, s, v = cv2.split(hsv)

	if hsv_channel == 'h':
		cv2.imwrite(img_output_location, h)
	elif hsv_channel == 's':
		cv2.imwrite(img_output_location, s)
	elif hsv_channel == 'v':
		cv2.imwrite(img_output_location, v)

	return jsonify({'allTasks':tasks})



@app.route('/img_tools/img_tools_medianBlur_process/',  methods=['POST'])
def img_tools_medianBlur_process():
	image_location = request.form['image_location']
	kernel_size = int(request.form['kernel_size'])
	img_output_location = request.form['img_output_location']


	img = cv2.imread(image_location)
	img = cv2.medianBlur(img,kernel_size)
	cv2.imwrite(img_output_location, img)

	return jsonify({'allTasks':tasks})



@app.route('/img_tools/img_tools_rgb2lab_process/',  methods=['POST'])
def img_tools_rgb2lab_process():
	image_location = request.form['image_location']
	lab_channel = request.form['lab_channel']
	img_output_location = request.form['img_output_location']


	img = cv2.imread(image_location)
	lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
	l, a, b = cv2.split(lab)

	if lab_channel == 'l':
		cv2.imwrite(img_output_location, l)
	elif lab_channel == 'a':
		cv2.imwrite(img_output_location, a)
	elif lab_channel == 'b':
		cv2.imwrite(img_output_location, b)

	return jsonify({'allTasks':tasks})



@app.route('/img_tools/img_tools_bitwiseOr_process/',  methods=['POST'])
def img_tools_bitwiseOr_process():
	image_location = request.form['image_location']
	second_img = request.form['second_img']
	img_output_location = request.form['img_output_location']


	img1 = cv2.imread(image_location)
	img2 = cv2.imread(second_img)
	img = cv2.bitwise_or(img1,img2)
	cv2.imwrite(img_output_location, img)

	return jsonify({'allTasks':tasks})


@app.route('/img_tools/img_tools_imgMasking_process/',  methods=['POST'])
def img_tools_imgMasking_process():
	image_location = request.form['image_location']
	mask_img = request.form['mask_img']
	mask_color = request.form['mask_color']
	img_output_location = request.form['img_output_location']

	if mask_color == 'white':
		img = cv2.imread(image_location)
		mask2 = cv2.imread(mask_img)

		masked_img = cv2.bitwise_and(img, mask2) ##good

		mask_inv = cv2.bitwise_not(mask2)
		white_mask = cv2.bitwise_or(masked_img, mask_inv)
		#white_masked = cv2.add(masked_img, white_mask)

		cv2.imwrite(img_output_location, white_mask)
	elif mask_color == 'black':
		img = cv2.imread(image_location)
		mask2 = cv2.imread(mask_img)

		masked_img = cv2.bitwise_and(img, mask2) ##good
		cv2.imwrite(img_output_location, masked_img)

	return jsonify({'allTasks':tasks})



@app.route('/img_tools/img_tools_analyzeObject_process/',  methods=['POST'])
def img_tools_analyzeObject_process():
	image_location = request.form['image_location']
	img_output_location = request.form['img_output_location']


	img = cv2.imread(image_location)
	img_gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
	ret, thresh = cv2.threshold(img_gray, 85, 255,0)
	
	
	
		
	return jsonify({'allTasks':tasks})
#######################################IMAGE TOOLS NEW ENDS #################################




############################ P2IRC API CODES ENDS HERE #######################################
##############################################################################################











##################################################################
#############################REGISTRATION STARTS #################



import string
#import webbrowser
import skimage.io as io
import numpy as np
from scipy.misc import imsave
from io import BytesIO
import cv2
import numpy as np
from skimage import *
import math
import errno
import os



def warp_image(I, H):
    return cv2.warpPerspective(I, H, (I.shape[1], I.shape[0]))

def transform_channels(C, H):
    return [warp_image(C[i], H[i]) for i in range(len(C))]



def match_key_points(right_key_points, left_key_points,
                     right_features, left_features, ratio, reproj_thresh):
    
    matcher = cv2.DescriptorMatcher_create("BruteForce")
    
    raw_matches = matcher.knnMatch(right_features, left_features, 2)

    
    matches = [(m[0].trainIdx, m[0].queryIdx)
               for m in raw_matches
               if len(m) == 2 and m[0].distance < m[1].distance * ratio]

   
    if len(matches) > 4:
        # Split right and left into numphy arrays
        src_pts = np.float32([right_key_points[i] for (_, i) in matches])
        dst_pts = np.float32([left_key_points[i] for (i, _) in matches])

        # Use the cv2 to actually connect the dots between the two pictures
        (H, status) = cv2.findHomography(src_pts,
                                         dst_pts,
                                         cv2.RANSAC,
                                         reproj_thresh)
        src_t = np.transpose(src_pts)
        dst_t = np.transpose(dst_pts)
        back_proj_error = 0
        inlier_count = 0
        # X coords are [0] and y are [1]
        for i in range(0, src_t.shape[1]):
            x_i = src_t[0][i]
            y_i = src_t[1][i]
            x_p = dst_t[0][i]
            y_p = dst_t[1][i]
            num1 = (H[0][0] * x_i + H[0][1] * y_i + H[0][2])
            num2 = (H[1][0] * x_i + H[1][1] * y_i + H[1][2])
            dnm = (H[2][0] * x_i + H[2][1] * y_i + H[2][2])

#            print((x_p-num1/dnm)**2)
            tmp = (x_p - (num1 / dnm))**2 + (y_p - (num2 / dnm))**2
            if status[i] == 1:
                back_proj_error += tmp
                inlier_count += 1

        return (matches, H, status, back_proj_error, inlier_count)
    else:
        return None




def find_keypoints_and_features(image):
    
    
    descriptor = cv2.xfeatures2d.SIFT_create(nfeatures=10)

    (key_points, features) = descriptor.detectAndCompute(image, None)

    key_points = np.float32([key_point.pt for key_point in key_points])
    return (key_points, features)







def register_channels(C, idx=0, ratio=.75, reproj_thresh=4):
    
    

    # Compute SIFT features for each channel.
    # Channel images are converted to unsigned byte.  All proper scaling
    # is done by image_as_ubyte regardless of dtype of the input images.
    keypoints_and_features = [
        find_keypoints_and_features(
            img_as_ubyte(chan)) for chan in C]

    #print(keypoints_and_features)
    # Generate list of indices excluding the target channel index.

    channels_to_register = list(range(len(C)))
    #print(channels_to_register)
    del channels_to_register[idx]

    # Generate keypoint matches between each channel to be registered
    # and the target image.
    matched_key_points = [match_key_points(keypoints_and_features[i][0],
                                           keypoints_and_features[idx][0],
                                           keypoints_and_features[i][1],
                                           keypoints_and_features[idx][1],
                                           ratio=ratio,
                                           reproj_thresh=reproj_thresh)
                          for i in channels_to_register]

    # extract the homography matrices from 'matched_key_points'.
    H = [x[1] for x in matched_key_points]
    BPError = [x[3] for x in matched_key_points]
    Inliers = [x[4] for x in matched_key_points]
    # Add the identity matrix for the target channel.
    H.insert(idx, np.identity(3))
    return H, BPError, Inliers


def decompose_homography(H):
    a = H[0, 0]
    b = H[0, 1]
    c = H[0, 2]
    d = H[1, 0]
    e = H[1, 1]
    f = H[1, 2]

    p = math.sqrt(a * a + b * b)
    r = (a * e - b * d) / (p)
    q = (a * d + b * e) / (a * e - b * d)

    translation = (c, f)
    scale = (p, r)
    shear = q
    theta = math.atan2(b, a)

    return (translation, theta, scale, shear)

import glob
@app.route('/img_reg',  methods=['POST'])
def img_reg():
	image_location = request.form['image_location']
	img_output_location = request.form['img_output_location']

	img_files = [0,1,2]
	c = 0
	for file in glob.glob(image_location + "*.png"):
		img_files[c] = file.replace("\\", "/")
		c = c+1

	img_names = ['static/reg/IMG_0000_1.tif', 'static/reg/IMG_0000_2.tif','static/reg/IMG_0000_2.tif' ]
	#img_names = [img_files[0], img_files[1], img_files[2]]
	#img_names = ['static/reg/input/1.png', 'static/reg/input/2.png','static/reg/input/3.png' ]

	#,'static/reg/IMG_0000_3.tif','static/reg/IMG_0000_4.tif','static/reg/IMG_0000_5.tif'

	C = [np.array(io.imread((name),as_grey=True)) for name in img_names]



	#for c in C:
		#print(find_keypoints_and_features(img_as_ubyte(c)))

	H, BPError, Inliers = register_channels(C)
	#BPError.insert(0, 0)
	T = transform_channels(C, H)
	# Decompose the homogrpahy and calculate the bounding box of the
			# good data, where all 5 channels are present
	
	max_x = []
	max_y = []
	max_theta = []
	for j in H:
		max_x.append(abs(decompose_homography(j)[0][0]))
		max_y.append(abs(decompose_homography(j)[0][1]))
		max_theta.append(abs(decompose_homography(j)[1]))
	
	rot = math.ceil(math.sin(max(max_theta)) * C[0].shape[1])
	crop_x = math.ceil(max(max_x))
	crop_y = math.ceil(max(max_y))

	border_x = (crop_x + rot, C[0].shape[1] - crop_x - rot)
	border_y = (crop_y + rot, C[0].shape[0] - crop_y - rot)

	bounding_box = ((border_x[0], border_x[1]), (border_y[0], border_y[1]))
	
	for j in range(len(T)):
		#io.imsave("static/reg/output/" +  str(j + 1) +".png", T[j])
		io.imsave(img_output_location +  str(j + 1) +".png", T[j])


	return jsonify({'allTasks':tasks})
	







#############################REGISTRATION ENDS####################
##################################################################







##################################################################
##################SEGMENTATION STARTS ############################
import numpy as np
import cv2
from itertools import tee
import math



def normalize_gaps(gaps, num_items):
	gaps = list(gaps)

	gaps_arr = np.array(gaps, dtype=np.float64)
	if gaps_arr.shape == (1,):
		gap_size = gaps_arr[0]
		gaps_arr = np.empty(num_items - 1)
		gaps_arr.fill(gap_size)
	elif gaps_arr.shape != (num_items - 1,):
		raise ValueError('gaps should have shape {}, but has shape {}.'
		.format((num_items - 1,), gaps_arr.shape))
	return gaps_arr


def get_repeated_seqs_2d_array(buffer_size, item_size, gaps, num_repeats_of_seq):
	start = buffer_size
	steps = gaps + item_size
	items = np.insert(np.cumsum(steps), 0, np.array(0)) + start
	return np.tile(items, (num_repeats_of_seq, 1))





def set_plot_layout_relative_meters(buffer_blocwise_m, plot_width_m,gaps_blocs_m,num_plots_per_bloc, buffer_plotwise_m, plot_height_m, gaps_plots_m,num_blocs):
	# this one already has the correct grid shape.
	plot_top_left_corners_x = get_repeated_seqs_2d_array(buffer_blocwise_m, plot_width_m,
	gaps_blocs_m,
	num_plots_per_bloc)
	# this one needs to be transposed to assume the correct grid shape.
	plot_top_left_corners_y = get_repeated_seqs_2d_array(buffer_plotwise_m, plot_height_m,
	gaps_plots_m,
	num_blocs).T
	num_plots = num_blocs * num_plots_per_bloc
	num_plots = num_blocs * num_plots_per_bloc
	plot_top_left_corners = np.stack((plot_top_left_corners_x, plot_top_left_corners_y)).T.reshape((num_plots, 2))

	plot_height_m_buffered = plot_height_m - 2 * buffer_plotwise_m
	plot_width_m_buffered = plot_width_m - 2 * buffer_blocwise_m

	plot_top_right_corners = np.copy(plot_top_left_corners)

	plot_top_right_corners[:, 0] = plot_top_right_corners[:, 0] + plot_width_m_buffered

	plot_bottom_left_corners = np.copy(plot_top_left_corners)
	plot_bottom_left_corners[:, 1] = plot_bottom_left_corners[:, 1] + plot_height_m_buffered

	plot_bottom_right_corners = np.copy(plot_top_left_corners)

	plot_bottom_right_corners[:, 0] = plot_bottom_right_corners[:, 0] + plot_width_m_buffered

	plot_bottom_right_corners[:, 1] = plot_bottom_right_corners[:, 1] + plot_height_m_buffered



	plots_all_box_coords = np.concatenate((plot_top_left_corners, plot_top_right_corners,
	plot_bottom_right_corners, plot_bottom_left_corners), axis=1)

	plots_corners_relative_m = plots_all_box_coords
	return plots_corners_relative_m



def plot_segmentation(num_blocs,num_plots_per_bloc,plot_width,plot_height):
	#num_blocs = 5
	#num_plots_per_bloc = 17
	gaps_blocs = np.array([50])
	gaps_plots = np.array([5])
	buffer_blocwise = 1
	buffer_plotwise = 1
	#plot_width = 95
	#plot_height = 30


	num_blocs = int(num_blocs)
	num_plots_per_bloc = int(num_plots_per_bloc)
	buffer_blocwise_m = float(buffer_blocwise)
	buffer_plotwise_m = float(buffer_plotwise)
	plot_width_m = float(plot_width)
	plot_height_m = float(plot_height)

	if not all((num_blocs >= 1,
	num_plots_per_bloc >= 1,
	buffer_blocwise_m >= 0,
	buffer_plotwise_m >= 0,
	plot_width_m >= 0,
	plot_height_m >= 0)):
		raise ValueError("invalid field layout parameters.")


	gaps_blocs_m = normalize_gaps(gaps_blocs, num_blocs)
	gaps_plots_m = normalize_gaps(gaps_plots, num_plots_per_bloc)
	plots_corners_relative_m = None


	return set_plot_layout_relative_meters(buffer_blocwise_m, plot_width_m,gaps_blocs_m,num_plots_per_bloc, buffer_plotwise_m, plot_height_m, gaps_plots_m,num_blocs)
 



@app.route('/img_seg',  methods=['POST'])
def img_seg():
	image_location = request.form['image_location']
	img_output_location = request.form['img_output_location']

	xOffset = int( request.form['xOffset'])
	yOffset = int(request.form['yOffset'])
	blocks = int(request.form['blocks'])
	plots = int(request.form['plots'])
	p_width = int( request.form['p_width'])
	p_height = int(request.form['p_height'])



	coord = plot_segmentation(blocks, plots, p_width, p_height)

	
	#img = cv2.imread('static/reg/IMG_0000_1.tif')
	img = cv2.imread(image_location)

	#cv2.line(img,(10,400),(400,400),(255,255,255),2)

	xOffset = xOffset #20
	yOffset = yOffset #400




	for i in range(coord.shape[0]):
		cv2.line(img, (int(coord[i,0]+xOffset), int(coord[i,1] + yOffset)), ( int(coord[i,2]+xOffset), int(coord[i,3] + yOffset)), (255,255,255),2)
		cv2.line(img, (int(coord[i,2]+xOffset), int(coord[i,3] + yOffset)), ( int(coord[i,4]+xOffset), int(coord[i,5] + yOffset)), (255,255,255),2)
		cv2.line(img, (int(coord[i,4]+xOffset), int(coord[i,5] + yOffset)), ( int(coord[i,6]+xOffset), int(coord[i,7] + yOffset)), (255,255,255),2)
		cv2.line(img, (int(coord[i,6]+xOffset), int(coord[i,7] + yOffset)), ( int(coord[i,0]+xOffset), int(coord[i,1] + yOffset)), (255,255,255),2)
		#print 'hello'


	#cv2.imwrite('static/reg/cloud_plot_seg.png',img)
	cv2.imwrite(img_output_location,img)
	


	return jsonify({'allTasks':tasks})


#############################SEGMENTATION ENDS####################
##################################################################





















######################################################################
#############################FASTQC STARTS############################
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
@app.route("/fastqc")
def fastqc_index():
    return render_template("fastqc_upload.html")

@app.route("/fastqc_upload", methods=['POST'])
def fastqc_upload():
	target = os.path.join(APP_ROOT, 'static/fastqc_output')
	# print(target)

	if not os.path.isdir(target):
		os.mkdir(target)

	fileList = []
	nameList = []
	for file in request.files.getlist("file"):
		#print(file)
		filename = file.filename
		if filename == '' or filename == None:
			return render_template("upload.html")
		else:
			if filename.endswith('.fastq'):
				newName = filename.replace('.fastq','')
				nameList.append(str(newName))
			else:
				nameList.append(str(filename))
			#nameList.append(str(filename))
			destination = "/".join([target, filename])
			# print(destination)
			file.save(destination)
			absDest = os.path.abspath(destination)
			# subprocess.call(['python', '/home/bbs048/Documents/Bishal/PyCharm/WebInterface/myWrapper.py', '-i', str(absDest)])
			subprocess.Popen(["/usr/bin/perl", "/home/ubuntu/Webpage/fastqc_wrapper/FastQC/fastqc", "-i", str(absDest)]).communicate()
			fileList.append(str(absDest))

	return render_template("fastqc_complete.html", fileName=nameList, fileLoc=fileList)


import os, subprocess, glob, ntpath, zipfile, gzip, tarfile
from flask import Flask, render_template, request, redirect, jsonify
from werkzeug.datastructures import FileStorage
from subprocess import call
import urllib

def path_leaf(path):
    head, tail = ntpath.split(path)
    return tail or ntpath.basename(head)


@app.route("/fastqc_new/", methods=['POST'])
def fastqc_upload_new():

    userDir = request.form['textDir']
    userRegex = request.form['textRegex']

    target = os.path.join(APP_ROOT, 'static/fastqc_output/')
    if not os.path.isdir(target):
        os.mkdir(target)

    userPath = os.path.join(userDir, userRegex)
    absPath = os.path.abspath(userPath)
    fileList = glob.glob('/home/gom766/Downloads/*.GZIP')

    return jsonify({ 'userRegex': str(fileList), 'userDir': userPath})

'''
    for file in fileList:
        filename = path_leaf(file)

        if filename.endswith('.tar.gz') or filename.endswith('.gz') or filename.endswith('.tar') or filename.endswith('.zip'):
            newLoc = 'decomp_' + str(filename) + '/'
            newTarget = os.path.join(target, newLoc)

            if os.path.isdir(newTarget):
                currentNum = 2
                currentTarget = newTarget
                while os.path.isdir(currentTarget):
                    currentLoc = 'decomp_' + str(filename) + '_' + str(currentNum) + '/'
                    currentTarget = os.path.join(target, currentLoc)
                    currentNum += 1
                newTarget = currentTarget
                os.mkdir(newTarget)
            elif not os.path.isdir(newTarget):
                os.mkdir(newTarget)

            if filename.endswith('.tar.gz') or filename.endswith('.gz') or filename.endswith('.tar'):
                tar = tarfile.open(file)
                tar.extractall(newTarget)
                tar.close()

            elif filename.endswith('.zip'):
                zip_ref = zipfile.ZipFile(file, 'r')
                zip_ref.extractall(newTarget)
                zip_ref.close()

            decompFolder = os.listdir(newTarget)
            for name in decompFolder:
                folderName = name
            decompFolderLoc = os.path.join(newTarget, folderName)
            decompFileList = os.listdir(decompFolderLoc)
            newFileList = []
            for decompFile in decompFileList:
                decompFilePath = os.path.join(decompFolderLoc, decompFile)
                newFileList.append(decompFilePath)

            for newFile in newFileList:
                newFileName = path_leaf(newFile)

                if newFileName.endswith('.fastq'):
                    newName = newFileName.replace('.fastq', '')
                    # nameList.append(str(newLoc) + str(folderName) + '/' + str(newName))
                    nameList.append(str(newLoc) + str(folderName) + '/' + str(newFileName))
                    fastqcList.append(str(newLoc) + str(folderName) + '/' + str(newName))
                else:
                    nameList.append(str(newLoc) + str(folderName) + '/' + str(newFileName))
                    fastqcList.append(str(newLoc) + str(folderName) + '/' + str(newFileName))

                nameList.append(str(newLoc) + str(folderName) + '/' + str(newFileName))

                absDest = os.path.abspath(newFile)
                subprocess.Popen(["/usr/bin/perl", "/home/ubuntu/Webpage/fastqc_wrapper/FastQC/fastqc", "-i",
                                  str(absDest)]).communicate()
                locList.append(str(absDest))

            #return jsonify({'allTasks': 'FastQC Failed...'})

        else:
            if filename.endswith('.fastq'):
                newName = filename.replace('.fastq', '')
                nameList.append(str(filename))
                fastqcList.append(str(newName))
            else:
                nameList.append(str(filename))
                fastqcList.append(str(filename))

            destination = "/".join([target, filename])

            with open(str(file), 'rb') as fp:
                file = FileStorage(fp)
                file.save(destination)

            absDest = os.path.abspath(destination)
            #subprocess.Popen(["perl", "../fastqc", "-i", str(absDest)])
            subprocess.Popen(["/usr/bin/perl", "/home/ubuntu/Webpage/fastqc_wrapper/FastQC/fastqc", "-i",
                              str(absDest)]).communicate()

            #return render_template("upload.html", fileName=nameList, fileLoc=locList, fastqcName=fastqcList)

'''

    #return jsonify({'allTasks': str(fastqcList), 'userRegex': fileList,'userDir': userPath})

#############################FASTQC ENDS##############################
######################################################################














######################################################################
#############################PEARS STARTS#############################







#############################PEARS ENDS###############################
######################################################################



























##################################################################
##################P2IRC FEATURE FINDER STARTS ####################
import numpy as np
import skimage.io as io
import skimage.draw as draw
import skimage.color as color
#import matplotlib.pyplot as plt
import cv2
from PIL import Image as im
from shapely.geometry import Polygon
from skimage.feature import blob_log
from math import sqrt

def feature_finder(roi, image_set, feature, thresh=0.0):

    # Do some type checking on the arguments
    if type(roi) is not Polygon:
        raise TypeError("region_of_interest is not of type Polygon")
    if type(image_set) is not list:
        raise TypeError("image_set is not of type list")
    if type(feature) is not list:
        raise TypeError("feature is not of type list")
    if roi is None:
        raise TypeError("Invalid region_of_interest given in feature_finder.py")
    if image_set is None:
        raise TypeError("Invalid image given in feature_finder.py")
    if thresh > 1 or thresh < 0:
        raise TypeError("Invalid range given, must between 0 and 1")
    if not feature:
        raise TypeError("Features list is empty is Empty")
    if not image_set:
        raise TypeError("image_set is empty is Empty")

    # Create lists for the x and y points for easy calculation of min and max
    # and the masks/masked images
    # The results are stored in a keyed dictionary with the keys being the
    # respective features that were calculated.
    x_points, y_points = roi.exterior.coords.xy
    masks = []
    masked_images = []
    result = {}

    # Create a white polygon and make everything else black, creating a mask of
    # the region of interest
    for i in range(len(image_set)):
        # Create the masks
        masks.append(np.array(image_set[i]))

        # Create a polygon from the list of points given
        rr, cc = draw.polygon(y_points, x_points)

        # Take the created polygon and make a mask out of it
        masks[i][rr, cc] = 1
        masks[i][masks[i] != 1] = 0

        # Apply the mask to the original image
        masked_images.append(image_set[i] * masks[i])
        masked_images[i] = masked_images[i][np.min(y_points):np.max(y_points),
                                            np.min(x_points):np.max(x_points)]

    # Flower Counter. Uses blob detection
    if "canola_flower_finder" in feature:
        # Calculate the Yellow-ness of the image
        # Yellow = R+G-B and clip all values so they are between 0 and 1
        yellow = np.clip((masked_images[2] + masked_images[1] - masked_images[0]), thresh, 1)

        # Use a blob detector to find the yellow flowers
        blobs_log = blob_log(yellow, max_sigma=10, num_sigma=1,
                             threshold=0.1, overlap=1)
        # Compute radii in the 3rd column. which is sigma*sqrt(2)
        blobs_log[:, 2] = blobs_log[:, 2] * sqrt(2)

        # convert the grayscale image to RGB to highlight in color
        highlight = color.gray2rgb(yellow)

        # for each blob draw a circle around it
        for blob in blobs_log:
            y, x, r = blob
            rr, cc, val = draw.circle_perimeter_aa(int(y), int(x), int(r)*3)

            # clip values of the circle that are outside of the region of interest
            rr = np.clip(rr, 0, yellow.shape[0] - 1)
            cc = np.clip(cc, 0, yellow.shape[1] - 1)

            # Draw Circles
            highlight[rr, cc] = [1,0,0]

        # save the image with highlights and the total number of flowers found
        result["canola_flower_finder"] = highlight
        result["canola_flower_count"] = blobs_log.shape[0]

    # NDVI feature calculation
    if "NDVI" or "NDVI_hist" in feature:
        num = np.subtract(masked_images[3], masked_images[2])
        dnm = np.add(masked_images[3], masked_images[2])

        NDVI = np.divide(num, dnm)
        NDVI[NDVI < thresh] = 0

        if "NDVI" in feature:
            result["NDVI"] = NDVI
        if "NDVI_hist" in feature:
            tmp, _ = np.histogram(NDVI)
            result["NDVI_hist"] = tmp


    # Calculate the greeness, which is on a scale of 0 to 1
    if "greeness" or "greeness_hist" in feature:
        grn = masked_images[1]/(masked_images[0] + masked_images[1] + masked_images[2])
        grn[grn < thresh] = 0
        if "greeness" in feature:
            result["greeness"] = grn
        if "greeness_hist" in feature:
            result["greeness_hist"] = np.histogram(grn)

    # Blue Channel
    if ("blue" or "blue_hist") in feature:
        if "blue" in feature:
            result["blue"] = masked_images[0]
        if "blue_hist" in feature:
            tmp, _ = np.histogram(masked_images[0])
            result["blue_hist"] = tmp

    # Green Channel
    if ("green" or "green_hist") in feature:
        if "green" in feature:
            result["green"] = masked_images[1]
        if "green_hist" in feature:
            tmp, _ = np.histogram(masked_images[1])
            result["green_hist"] = tmp

    # Red Channel
    if ("red" or "red_hist") in feature:
        if "red" in feature:
            result["red"] = masked_images[2]
        if "red_hist" in feature:
            tmp, _ = np.histogram(masked_images[2])
            result["red_hist"] = tmp

    # Near Infa-Red Channel
    if ("nir" or "nir_hist") in feature:
        if "nir" in feature:
            result["nir"] = masked_images[3]
        if "nir_hist" in feature:
            tmp, _ = np.histogram(masked_images[3])
            result["nir_hist"] = tmp

    # Red-edge Channel
    if ("red_edge" or "red_edge_hist") in feature:
        if "red_edge" in feature:
            result["red_edge"] = masked_images[4]
        if "red_edge_hist" in feature:
            tmp, _ = np.histogram(masked_images[4])
            result["red_edge_hist"] = tmp

    # Create an RGB image
    if ("rgb" or "RGB") in feature:
        rgb = np.dstack((masked_images[2],
                         masked_images[1],
                         masked_images[0]))
        result["rgb"] = rgb

    return result


@app.route('/test_feature_finder')
def test_feature_finder():
	roi = Polygon([(100,100), (100,800), (400,800), (400, 100)])
	b = io.imread("static/img/1.jpg")
	image_set = [b]
	feat = ["greeness"]
	#features = feature_finder(roi, image_set, feature=feat, thresh=0.0)

	return render_template('p2irc_apis.html')

##################P2IRC FEATURE FINDER ENDS ######################
##################################################################


























#################################################################################
#################################################################################
#################################################################################
#################################################################################
###################CODE CLONE VALIDATION STARTS##################################
#################################################################################
#################################################################################
#################################################################################
#################################################################################
from flaskext.couchdb import Document, TextField, FloatField, DictField, Mapping,ListField


class CodeClones(Document):
	clone_id = TextField()
	tool = DictField(Mapping.build(id=TextField(),name=TextField()))
	system = DictField(Mapping.build(
		id=TextField(),
		name=TextField()
	))
	fragment_1 = DictField(Mapping.build(
		path=TextField(),
		start_line=TextField(),
		end_line=TextField()
	))
	fragment_2 = DictField(Mapping.build(
		path=TextField(),
		start_line=TextField(),
		end_line=TextField()
	))
	auto_validation_result = ListField(DictField(Mapping.build(
		algorithm = TextField(),
		result = TextField()
	)))
	is_validated_by_any_user = TextField(default='no')
	is_clone_doc = TextField(default='yes')
	user_validation_result = ListField(DictField(Mapping.build(
		user = TextField(),
		result = TextField()
	)))


import pandas as pd
def load_dataSet(fileName, data_columns):
	data = pd.read_csv(fileName, sep=',', header=None)
	data.columns = data_columns
	return data


import itertools

def getCodeFragment(path, start_line, end_line):
	codeFragment = ''
	with open(str(path).strip('"'), "r") as text_file:
		for line in itertools.islice(text_file, int(start_line), int(end_line)):
			codeFragment = codeFragment + line

	return codeFragment





@app.route('/init_clone_srv', methods=['GET'])
def init_clone_srv():
	allRows = []
	for row in views_by_validated_clones(g.couch):
		tmp = CodeClones.load(row.key)
		allRows.append(row)
		tmp.is_validated_by_any_user='no'
		tmp.store()
	return jsonify({'res': allRows})



@app.route('/ccv_old')
def ccv_old():
	#c =  CodeClones()
	#c.username = "A new User"
	#c.password = "A new Password"
	#c.store()

	#entry = CodeClones.load('d7dd92d4391d6ddbec202f75a60089f9')
	#entry.password = 'yay... password edited....'
	#entry.store()

	#sources = []
	#for row in views_by_user(g.couch):
	#	sources.append(row.value)
	#sources = list(sources)

    #document = views_by_user(g.couch)
 #   with open("code.java", "r") as f:
#	     content = f.read()
	#views_by_non_validated_clones

	sources = []
	for row in views_by_non_validated_clones(g.couch):
		sources.append(row.key)
	sources = list(sources)



	doc_length = len(sources)#checking if there is any further clone available or not to validate

	#No un-validated clone docs available
	if(doc_length == 0):
		#set some value representing end of clone validation docs.
		doc_id = 'NA'
		neural_net_response = 'NA'
		svm_response = 'NA'

		codeFragment_1 = 'No more clones available for validation.'
		codeFragment_2 = 'No more clones available for validation.'

	else:
		#p = str(CodeClones.load(sources[0]).fragment_2.path).strip('"')
		clone_doc = CodeClones.load(sources[0])
		doc_id = clone_doc.id

		"""
		fragment_1_code = ''
		with open(str(CodeClones.load(sources[0]).fragment_1.path).strip('"'), "r") as text_file:
			for line in itertools.islice(text_file, int(clone_doc.fragment_1.start_line), int(clone_doc.fragment_1.end_line)):
				#lines.append(line)
				fragment_1_code = fragment_1_code + line


		fragment_2_code = ''
		with open(p, "r") as text_file:
			for line in itertools.islice(text_file, int(clone_doc.fragment_2.start_line), int(clone_doc.fragment_2.end_line)):
				#lines.append(line)
				fragment_2_code = fragment_2_code + line
		""" 
		codeFragment_1 = getCodeFragment('clones/'+clone_doc.fragment_1.path, clone_doc.fragment_1.start_line, clone_doc.fragment_1.end_line)
		codeFragment_2 = getCodeFragment('clones/'+clone_doc.fragment_2.path, clone_doc.fragment_2.start_line, clone_doc.fragment_2.end_line)
	
		neural_net_response = ''
		svm_response = ''
		for response in clone_doc.auto_validation_result:
			if response['algorithm'] == 'Neural Network':
				neural_net_response = response['result'];
			if response['algorithm'] == 'SVM':
				svm_response = response['result'];


	return render_template('codeclone_validation.html', 
	codeFragment_1=codeFragment_1, 
	codeFragment_2=codeFragment_2,
	neural_net_response = neural_net_response,
	svm_response = svm_response,
	doc_id=doc_id)




@app.route('/get_next_code_fragments_for_validation',  methods=['POST'])
def get_next_code_fragments_for_validation():
	prev_doc_id = request.form['doc_id']
	user_response = request.form['user_response']

	clone_doc = CodeClones.load(prev_doc_id)
	clone_doc.is_validated_by_any_user = "yes"
	clone_doc.user_validation_result.append(user='golammostaeen', result=user_response)
	clone_doc.store()




	#cd = CodeClones.load('bf54d49f8654f0653c85a9cd2f011ab0')

	sources = []
	for row in views_by_non_validated_clones(g.couch):
		sources.append(row.key)
	sources = list(sources)

	doc_length = len(sources)#checking if there is any further clone available or not to validate

	#No un-validated clone docs available
	if(doc_length == 0):
		#set some value representing end of clone validation docs.
		doc_id = 'NA'
		neural_net_response = 'NA'
		svm_response = 'NA'

		codeFragment_1 = 'No more clones available for validation.'
		codeFragment_2 = 'No more clones available for validation.'
	
	else:
		cd = CodeClones.load(sources[0])


		doc_id = cd.id
		codeFragment_1 = getCodeFragment('clones/'+cd.fragment_1.path, cd.fragment_1.start_line,cd.fragment_1.end_line)
		codeFragment_2 = getCodeFragment('clones/'+cd.fragment_2.path, cd.fragment_2.start_line,cd.fragment_2.end_line)

		neural_net_response = ''
		svm_response = ''
		for response in clone_doc.auto_validation_result:
			if response['algorithm'] == 'Neural Network':
				neural_net_response = response['result'];
			if response['algorithm'] == 'SVM':
				svm_response = response['result'];
	

	



	return jsonify({ 'doc_id':doc_id,
	'codeFragment_1': codeFragment_1, 
	'codeFragment_2': codeFragment_2,
	'neural_net_response':neural_net_response,
	'svm_response': svm_response })







@app.route('/codeclone_stats')
def codeclone_stats():
    #return 'hello'
    return render_template('codeclone_stats.html')


@app.route('/online_txl')
def online_txl():
    return render_template('codeclone_online_txl.html')


import subprocess

@app.route('/txl',  methods=['POST'])
def txl():

	#getting the txl and the input file to parse
	txl_source = request.form['txl_source']
	input_to_parse = request.form['input_to_parse']

	

	#generate a unique random file name for preventing conflicts
	fileName = str(uuid.uuid4())
	txl_source_file = '/home/ubuntu/Webpage/txl_tmp_file_dir/'+fileName+'.txl'

	fileName2 = str(uuid.uuid4())
	input_to_parse_file = '/home/ubuntu/Webpage/txl_tmp_file_dir/'+fileName2+'.txt'



	#write submitted txl and input to corresponding files
	with open(txl_source_file,"w") as fo:
		fo.write(txl_source)

	with open(input_to_parse_file,"w") as fo2:
		fo2.write(input_to_parse)




		
	#parsing
	#proc = subprocess.Popen('ls')
	p = subprocess.Popen(['/usr/local/bin/txl', '-Dapply', txl_source_file, input_to_parse_file],  stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	#p = subprocess.Popen(['txl', '-Dapply' , 'txl_tmp_file_dir/80a90237-f5af-4c16-aa4a-5bfae9d5698e.txl' , 'txl_tmp_file_dir/input_txl.txt'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	#p.wait()
	out, err = p.communicate()
	#p = subprocess.call(['ls', '-l'])
	#out, err = p.communicate()
	#output = subprocess.call(['ls', '-l'], shell=True)
	


	#once done remove the file
	os.remove(txl_source_file)
	os.remove(input_to_parse_file)

	#preparing the log file for better readabilty...
	err = str(err,'utf-8').replace('\n','<br>') #add new line for html
	out = str(out,'utf-8').replace('\n','<br>') #add new line for html
	err = err.replace(txl_source_file,'YOUR_TXL_FILE')
	err = err.replace(input_to_parse_file,'YOUR_INPUT_FILE') 

	return jsonify({'txl_log': str(err), 'txl_output': str(out)})



def execTxl(txlFilePath, sourceCode, lang, saveOutputFile=False):
	#get an unique file name for storing the code temporarily
	fileName = str(uuid.uuid4())
	sourceFile = '/home/ubuntu/Webpage/txl_tmp_file_dir/'+fileName+'.txt'

	
	#write submitted source code to corresponding files
	with open(sourceFile,"w") as fo:
		fo.write(sourceCode)

	#get the required txl file for feature extraction
	#txlPath = '/home/ubuntu/Webpage/txl_features/txl_features/java/PrettyPrint.txl'

	#do the feature extraction by txl
	p = subprocess.Popen(['/usr/local/bin/txl', '-Dapply', txlFilePath, sourceFile],  stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	out, err = p.communicate()


	#convert to utf-8 format for easier readibility
	out = str(out,'utf-8')
	err = str(err,'utf-8')

	err = err.replace(sourceFile, 'YOUR_SOURCE_FILE')
	err = err.replace(txlFilePath, 'REQUIRED_TXL_FILE')

	#once done remove the temp file
	os.remove(sourceFile)


	if saveOutputFile==False:
		return out, err
	else:
		outputFileLocation = str(uuid.uuid4())
		outputFileLocation = '/home/ubuntu/Webpage/txl_tmp_file_dir/'+outputFileLocation+'.txt'
		with open(outputFileLocation,"w") as fo:
			fo.write(out)

		return outputFileLocation, out, err
	



#sourceCodeFeatures ---->> prettyPrint
@app.route('/sourceCodeFeatures/prettyPrint',  methods=['POST'])
def prettyPrint():
	#getting the txl and the input file to parse
	sourceCode = request.form['sourceCode']
	lang = request.form['lang']

	txlFilePath = '/home/ubuntu/Webpage/txl_features/txl_features/java/PrettyPrint.txl'

	out, err = execTxl(txlFilePath, sourceCode, lang)

	return jsonify({'error_msg': 'None', 'log_msg': err,'output': out})


#sourceCodeFeatures ---->> tokenize
@app.route('/sourceCodeFeatures/tokenize',  methods=['POST'])
def tokenize():
	#getting the txl and the input file to parse
	sourceCode = request.form['sourceCode']
	lang = request.form['lang']

	txlFilePath = '/home/ubuntu/Webpage/txl_features/txl_features/java/tokenize.txl'

	out, err = execTxl(txlFilePath, sourceCode, lang)

	return jsonify({'error_msg': 'None', 'log_msg': err,'output': out})

#sourceCodeFeatures ---->> blindNormalizeLiterals
@app.route('/sourceCodeFeatures/blindNormalizeLiterals',  methods=['POST'])
def blindNormalizeLiterals():
	#getting the txl and the input file to parse
	sourceCode = request.form['sourceCode']
	lang = request.form['lang']

	txlFilePath = '/home/ubuntu/Webpage/txl_features/txl_features/java/blindNormalizeLiterals.txl'

	out, err = execTxl(txlFilePath, sourceCode, lang)

	return jsonify({'error_msg': 'None', 'log_msg': err,'output': out})

#sourceCodeFeatures ---->> blindRenameIdentifiersAndPrimitives
@app.route('/sourceCodeFeatures/blindRenameIdentifiersAndPrimitives',  methods=['POST'])
def blindRenameIdentifiersAndPrimitives():
	#getting the txl and the input file to parse
	sourceCode = request.form['sourceCode']
	lang = request.form['lang']

	txlFilePath = '/home/ubuntu/Webpage/txl_features/txl_features/java/blindRenameIdentifiersAndPrimitives.txl'

	out, err = execTxl(txlFilePath, sourceCode, lang)

	return jsonify({'error_msg': 'None', 'log_msg': err,'output': out})


#sourceCodeFeatures ---->> all
@app.route('/sourceCodeFeatures/all',  methods=['POST'])
def sourceCodeFeatures_all():
	#getting the txl and the input file to parse
	sourceCode = request.form['sourceCode']
	lang = request.form['lang']
	
	resp = []

	txlFilePath = '/home/ubuntu/Webpage/txl_features/txl_features/java/blindRenameIdentifiersAndPrimitives.txl'
	out, err = execTxl(txlFilePath, sourceCode, lang)
	resp.append({'feature':'blindRenameIdentifiersAndPrimitives','error_msg': 'None', 'log_msg': err,'output': out})

	txlFilePath = '/home/ubuntu/Webpage/txl_features/txl_features/java/tokenize.txl'
	out, err = execTxl(txlFilePath, sourceCode, lang)
	resp.append({'feature':'tokenize','error_msg': 'None', 'log_msg': err,'output': out})

	txlFilePath = '/home/ubuntu/Webpage/txl_features/txl_features/java/blindNormalizeLiterals.txl'
	out, err = execTxl(txlFilePath, sourceCode, lang)
	resp.append({'feature':'blindNormalizeLiterals','error_msg': 'None', 'log_msg': err,'output': out})

	txlFilePath = '/home/ubuntu/Webpage/txl_features/txl_features/java/PrettyPrint.txl'
	out, err = execTxl(txlFilePath, sourceCode, lang)
	resp.append({'feature':'prettyPrint','error_msg': 'None', 'log_msg': err,'output': out})

	return jsonify(resp)



def getCodeCloneSimilarity(sourceCode1, sourceCode2, lang, txlFilePath):
	saveOutputFile=True
	outputFileLocation1, out1, err1 = execTxl(txlFilePath, sourceCode1, lang, saveOutputFile)
	outputFileLocation2, out2, err2 = execTxl(txlFilePath, sourceCode2, lang, saveOutputFile)

	p = subprocess.Popen(['/usr/bin/java', '-jar', '/home/ubuntu/Webpage/txl_tmp_file_dir/calculateCloneSimilarity.jar',outputFileLocation1, outputFileLocation2],  stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	similarityValue, err = p.communicate()

	
	similarityValue = str(similarityValue,'utf-8')
	similarityValue = similarityValue.replace('\n', '')
	err = str(err,'utf-8')

	#once done remove the temp files
	os.remove(outputFileLocation1)
	os.remove(outputFileLocation2)

	return similarityValue




#sourceCodeFeatures ---->> similaritiesNormalizedByLine
@app.route('/codeCloneFeatures/similaritiesNormalizedByLine',  methods=['POST'])
def similaritiesNormalizedByLine():
	#getting the txl and the input file to parse
	sourceCode1 = request.form['sourceCode_1']
	sourceCode2 = request.form['sourceCode_2']
	lang = request.form['lang']


	txlFilePath = '/home/ubuntu/Webpage/txl_features/txl_features/java/PrettyPrint.txl'
	type1sim_by_line = getCodeCloneSimilarity(sourceCode1, sourceCode2, lang, txlFilePath)

	txlFilePath = '/home/ubuntu/Webpage/txl_features/txl_features/java/normalizeLiteralsToDefault.txl'
	type2sim_by_line = getCodeCloneSimilarity(sourceCode1, sourceCode2, lang, txlFilePath)

	txlFilePath = '/home/ubuntu/Webpage/txl_features/txl_features/java/normalizeLiteralsToZero.txl'
	type3sim_by_line = getCodeCloneSimilarity(sourceCode1, sourceCode2, lang, txlFilePath)

	out = {'type_1_similarity_by_line':type1sim_by_line, 'type_2_similarity_by_line':type2sim_by_line,'type_3_similarity_by_line':type3sim_by_line}


	return jsonify({'error_msg': 'None', 'log_msg': 'Preprocessing Source Codes...\nNormalizing Source Codes...\nCalculating Similarities...\nDone.','output': out})


#sourceCodeFeatures ---->> similaritiesNormalizedByToken
@app.route('/codeCloneFeatures/similaritiesNormalizedByToken',  methods=['POST'])
def similaritiesNormalizedByToken():
	#getting the txl and the input file to parse
	sourceCode1 = request.form['sourceCode_1']
	sourceCode2 = request.form['sourceCode_2']
	lang = request.form['lang']


	txlFilePath = '/home/ubuntu/Webpage/txl_features/txl_features/java/consistentRenameIdentifiers.txl'
	type1sim_by_token = getCodeCloneSimilarity(sourceCode1, sourceCode2, lang, txlFilePath)

	txlFilePath = '/home/ubuntu/Webpage/txl_features/txl_features/java/normalizeLiteralsToZero.txl'
	type2sim_by_token = getCodeCloneSimilarity(sourceCode1, sourceCode2, lang, txlFilePath)

	txlFilePath = '/home/ubuntu/Webpage/txl_features/txl_features/java/normalizeLiteralsToZero.txl'
	type3sim_by_token = getCodeCloneSimilarity(sourceCode1, sourceCode2, lang, txlFilePath)

	out = {'type_1_similarity_by_token':type1sim_by_token, 'type_2_similarity_by_token':type2sim_by_token,'type_3_similarity_by_token':type3sim_by_token}


	return jsonify({'error_msg': 'None', 'log_msg': 'Preprocessing Source Codes...\nNormalizing Source Codes...\nCalculating Similarities...\nDone.','output': out})



import pickle
import pybrain

#codeCloneFeatures ---->> getValidationScore
@app.route('/codeCloneFeatures/getValidationScore',  methods=['POST'])
def getValidationScore():
	#getting the txl and the input file to parse
	sourceCode1 = request.form['sourceCode_1']
	sourceCode2 = request.form['sourceCode_2']
	lang = request.form['lang']

	#load the trained Neural Net
	fileObject = open('/home/ubuntu/Webpage/pybrain/trainedNetwork', 'rb')
	loaded_fnn = pickle.load(fileObject, encoding='latin1')
	network_prediction = loaded_fnn.activate([0.2,0.5,0.6,0.1,0.3,0.7])

	out = {'false_clone_probability_score':network_prediction[0], 'true_clone_probability_score':network_prediction[1]}


	return jsonify({'error_msg': 'None', 'log_msg': 'Preprocessing Source Codes...\nNormalizing Source Codes...\nCalculating Similarities...\nDone.','output': out})


#################################################################################
#################################################################################
#################################################################################
#################################################################################
####################CODE CLONE VALIDATION ENDS###################################
#################################################################################
#################################################################################
#################################################################################
#################################################################################












if __name__ == "__main__":
	#socketio.run(app)
    app.debug = True
    app.run("0.0.0.0")

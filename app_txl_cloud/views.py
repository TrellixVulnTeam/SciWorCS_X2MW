from app_txl_cloud import app_txl_cloud
from flask import render_template



from flask import Flask,render_template,jsonify, g, redirect, url_for, session
from io import StringIO
import sys
import subprocess
import tempfile
from flask import request
import os
import uuid


#for couch db...
from couchdb.design import ViewDefinition
from flaskext.couchdb import CouchDBManager




views_by_txl_user = ViewDefinition('hello', 'findEmailAndDocID', '''
	function (doc) {
		if (doc.the_doc_type == 'txl_user') {
			emit(doc.user_email, doc._id)
		};
	}
	''')




views_by_txl_project_authors = ViewDefinition('hello', 'findTXLProjectAuthors', '''
	function (doc) {
		if (doc.the_doc_type == 'txl_project') {
			emit(doc.author, doc._id)
		};
	}
	''')


views_by_txl_project_shared_members = ViewDefinition('hello', 'findTXLProjectSharedMembers', '''
	function (doc) {
		if (doc.the_doc_type == 'txl_project') {
			emit(doc.shared_with, doc._id)
		};
	}
	''')





from flask import current_app as app


app = Flask(__name__)
app.config.update(
    COUCHDB_SERVER='http://localhost:5984',
    COUCHDB_DATABASE='plantphenotype'
)

manager = CouchDBManager()
with app.app_context():
	manager.setup(app)
	manager.add_viewdef([views_by_txl_user, views_by_txl_project_authors, views_by_txl_project_shared_members])
	manager.sync(app)
















@app_txl_cloud.route('/editor')
def txl_index():
	return render_template('quick_txl.html')







@app_txl_cloud.route('/txl', methods=['POST'])
def txl():
	# getting the txl and the input file to parse
	txl_source = request.form['txl_source']
	input_to_parse = request.form['input_to_parse']

	# generate a unique random file name for preventing conflicts
	fileName = str(uuid.uuid4())
	txl_source_file = 'app_txl_cloud/txl_tmp_file_dir/' + fileName + '.txl'

	fileName = str(uuid.uuid4())
	input_to_parse_file = 'app_txl_cloud/txl_tmp_file_dir/' + fileName + '.txt'

	# write submitted txl and input to corresponding files
	with open(txl_source_file, "w") as fo:
		fo.write(txl_source)

	with open(input_to_parse_file, "w") as fo:
		fo.write(input_to_parse)

	# parsing
	p = subprocess.Popen(['/usr/local/bin/txl', '-Dapply', txl_source_file, input_to_parse_file], stdout=subprocess.PIPE,
						 stderr=subprocess.PIPE)
	# p = subprocess.Popen(['ls'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	out, err = p.communicate()

	# once done remove the file
	#os.remove(txl_source_file)
	#os.remove(input_to_parse_file)

	# preparing the log file for better readabilty...
	# err = err.replace('\n','<br>') #add new line for html
	err = str(err,'utf-8')
	out = str(out,'utf-8')
	err = err.replace(txl_source_file, 'YOUR_TXL_FILE')
	err = err.replace(input_to_parse_file, 'YOUR_INPUT_FILE')

	return jsonify({'txl_log': err, 'txl_output': out})










@app_txl_cloud.route('/load_example_txl_program', methods=['POST'])
def load_example_txl_program():
	# getting the example program name
	example_name = request.form['txl_example_program_name']

	txl_example_program_dir = 'app_txl_cloud/txl_sources/examples/'

	file_location = txl_example_program_dir + example_name + '/' + example_name

	txl_source = ''
	with open(file_location + '.txl', 'r') as f:
		for line in f:
			txl_source = txl_source + line

	input_to_parse = ''
	with open(file_location + '.txt', 'r') as f:
		for line in f:
			input_to_parse = input_to_parse + line

	# txl_source = str(txl_source, 'utf-8')
	return jsonify({'example_txl_source': txl_source, 'input_to_parse': input_to_parse})



















#################################################################################
################# Project Related Codes #########################################
#################################################################################

from flaskext.couchdb import Document, TextField, FloatField, DictField, Mapping, ListField
from datetime import datetime




@app_txl_cloud.route('/txl-cloud')
def txl_cloud():
	return render_template('txl_cloud_welcome.html')








@app_txl_cloud.route('/txl_login')
def txl_login():
	return render_template('txl_login.html')


@app_txl_cloud.route('/txl_create_ac', methods=['POST'])
def txl_create_ac():
	user_email = request.form['txl_reg_email']
	user_name = request.form['txl_reg_name']
	user_password = request.form['txl_reg_password']

	new_txl_user = TXL_User()
	new_txl_user.user_email = user_email
	new_txl_user.user_password = user_password
	new_txl_user.user_full_name = user_name
	new_txl_user.store()

	return jsonify({'response_code': 'OK'})


@app_txl_cloud.route('/txl_varify_user', methods=['POST'])
def txl_varify_user():
	# get user credentials
	txl_login_email = request.form['txl_login_email']
	txl_login_password = request.form['txl_login_password']
	# return redirect(url_for('myProjects'))

	row = (views_by_txl_user(g.couch))[txl_login_email]

	this_txl_user = ''
	if not row:
		return redirect(url_for('app_txl_cloud.txl_login'))
	else:
		this_txl_user = TXL_User.load(list(row)[0].value)

	if this_txl_user.user_email != txl_login_email or this_txl_user.user_password != txl_login_password:
		return redirect(url_for('app_txl_cloud.txl_login'))
	else:
		# first_name = p2irc_user.first_name
		# last_name = p2irc_user.last_name
		# email = p2irc_user.email
		session['txl_user_email'] = this_txl_user.user_email
		return redirect(url_for('app_txl_cloud.myProjects'))

	return render_template('txl_login.html')








@app_txl_cloud.route('/myProjects')
def myProjects():
	user_email = session.get('txl_user_email')  # 'golammostaeen@gmail.com' # obtained from the session

	# get my authoring project list
	my_authored_projects = []
	for row in (views_by_txl_project_authors(g.couch)):
		if row.key == user_email:
			project_doc_id = row.value
			this_project = TXL_Project.load(project_doc_id)
			this_project_name = this_project.project_name
			this_project_description = this_project.project_description
			my_authored_projects.append({'project_doc_id': project_doc_id, 'project_name': this_project_name,
										 'project_description': this_project_description})

	# get the list of projects shared with me...
	projects_shared_with_me = []
	for row in (views_by_txl_project_shared_members(g.couch)):
		if str(user_email) in list(row.key):
			project_doc_id = row.value
			this_project = TXL_Project.load(project_doc_id)
			this_project_name = this_project.project_name
			this_project_description = this_project.project_description
			projects_shared_with_me.append({'project_doc_id': project_doc_id, 'project_name': this_project_name,
											'project_description': this_project_description})

	return render_template('my_projects.html', my_authored_projects=my_authored_projects,
						   projects_shared_with_me=projects_shared_with_me)


class TXL_Project(Document):
	project_name = TextField()
	project_description = TextField()
	project_location = TextField()
	project_creation_date = TextField()
	author = TextField()
	the_doc_type = TextField(default='txl_project')
	shared_with = ListField(TextField())


class TXL_User(Document):
	user_email = TextField()
	user_password = TextField()
	user_full_name = TextField()
	the_doc_type = TextField(default='txl_user')


@app_txl_cloud.route('/txl_create_new_project', methods=['POST'])
def txl_create_new_project():
	# get the new project name and description
	new_project_name = request.form['new_project_name']
	new_project_description = request.form['new_project_description']

	# create the corresponding project location
	user_email = session.get('txl_user_email')  # 'golammostaeen@gmail.com' # obtained from the session
	new_project_location = 'app_txl_cloud/txl_sources/user_projects/' + user_email + '/' + new_project_name

	# create the project
	msg = ''
	response_code = 'OK'
	if not os.path.exists(new_project_location):
		os.makedirs(new_project_location)
		os.makedirs(new_project_location + "/txl_files")  # for storing all txl files
		os.makedirs(new_project_location + "/input_files")  # for storing all input files
		msg = 'Project Created Successfully!'
	else:
		msg = 'Project Creation Failed!!!\nProject Already Exists. Please Try With A Different Name...'
		response_code = 'NOT_OK'

	# store the information to the database if everything is OK
	new_doc_id = 'None'  # default value
	if response_code == 'OK':
		new_doc_id = uuid.uuid4().hex
		new_txl_project = TXL_Project()
		new_txl_project.project_location = new_project_location
		new_txl_project.project_name = new_project_name
		new_txl_project.author = user_email  # from session
		new_txl_project.project_creation_date = str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
		new_txl_project.project_description = new_project_description
		new_txl_project.id = new_doc_id

		new_txl_project.store()

	return jsonify({'msg': msg, 'response_code': response_code, 'doc_id': new_doc_id})


# txl project main page...
@app_txl_cloud.route('/txl/project/', methods=['GET'])
def txl_project():
	# get the project id
	project_id = request.args.get('pid')
	this_project = TXL_Project.load(project_id)

	txl_contents = os.listdir(this_project.project_location + "/txl_files/")  # list of all txl files
	input_files = os.listdir(this_project.project_location + "/input_files/")  # list of all input files

	return render_template('txl_project.html', project_id=project_id, txl_contents=txl_contents,
						   input_files=input_files)


@app_txl_cloud.route('/read_txl_project_files', methods=['POST'])
def read_txl_project_files():
	# getting the file details for the project
	project_doc_id = request.form['project_doc_id']
	file_type = request.form['file_type']
	file_name = request.form['file_name']

	# get the project location from the corresponding doc
	project_location = TXL_Project.load(project_doc_id).project_location

	# get the file exact file location based on its type (i.e. txl_files or input_files?)
	file_location = ''
	if file_type == 'txl':
		file_location = project_location + '/txl_files/' + file_name
	else:
		file_location = project_location + '/input_files/' + file_name

	# finally read the file...
	file_content = ''
	with open(file_location, 'r') as f:
		for line in f:
			file_content = file_content + line

	return jsonify({'file_content': file_content})


@app_txl_cloud.route('/add_new_file_txl_project', methods=['POST'])
def add_new_file_txl_project():
	# getting the file details for the project
	project_doc_id = request.form['project_doc_id']
	file_type = request.form['file_type']
	file_name = request.form['file_name']

	# get the project location from the corresponding doc
	project_location = TXL_Project.load(project_doc_id).project_location

	# get the file exact file location based on its type (i.e. txl_files or input_files?)
	file_location = ''
	if file_type == 'txl':
		file_location = project_location + '/txl_files/' + file_name
	else:
		file_location = project_location + '/input_files/' + file_name

	response_code = 'OK'
	if os.path.exists(file_location) == True:
		response_code = 'FILE_ALREADY_EXIST'
	else:
		new_file = open(file_location, "w")
		new_file.close()

	return jsonify({'response_code': response_code})


@app_txl_cloud.route('/save_document', methods=['POST'])
def save_document():
	# getting the file details for the project
	project_doc_id = request.form['project_doc_id']
	file_type = request.form['file_type']
	file_name = request.form['file_name']
	file_content = request.form['file_content']

	# get the project location from the corresponding doc
	project_location = TXL_Project.load(project_doc_id).project_location

	# get the file exact file location based on its type (i.e. txl_files or input_files?)
	file_location = ''
	if file_type == 'txl':
		file_location = project_location + '/txl_files/' + file_name
	else:
		file_location = project_location + '/input_files/' + file_name

	# write submitted file contents to the corresponding files
	with open(file_location, "w") as fo:
		fo.write(file_content)

	return jsonify({'msg': 'Last Autosaved Your Project At ==> ' + str(datetime.now().strftime('%H:%M:%S'))})


#################################################################
######### Member Related Codes ##################################
#################################################################
@app_txl_cloud.route('/add_new_member_to_project', methods=['POST'])
def add_new_member_to_project():
	# getting the project detail
	project_doc_id = request.form['project_doc_id']
	# which user to add
	user_to_add = request.form['user_to_add']

	# this project
	this_project = TXL_Project.load(project_doc_id)

	# get the list of members with whom project shared already
	list_shared_with = this_project.shared_with

	# check if the user exists or not
	user_count = 0
	user_doc_id = 'None'
	for row in (views_by_txl_user(g.couch)):
		if row.key == user_to_add:
			user_count = user_count + 1
			user_doc_id = row.value
			break

	msg = ''
	response_code = 'ERR'
	user_full_name = ''

	if user_count == 0:
		msg = 'User Does Not Exist!!!\nPlease Check and Try Again...'
		response_code = 'ERR_NOT_FOUND'
	else:
		# check if the user is already a member to this project
		if user_to_add in list_shared_with:
			msg = 'User Already a Member to This Project...!'
			response_code = 'ERR_ALREADY_MEMBER'
		elif user_to_add == this_project.author:
			msg = 'Failed To Add!!!\nA Project Author is Already a Member to the Project...'
			response_code = 'ERR_AUTHOR'
		else:
			# finally add this user in the shared list...
			list_shared_with.append(user_to_add)
			this_project.store()
			user_full_name = TXL_User.load(user_doc_id).user_full_name
			response_code = 'OK'
			msg = 'Member Added Successfully...'

	return jsonify({'response_code': response_code, 'msg': msg, 'user_full_name': user_full_name})












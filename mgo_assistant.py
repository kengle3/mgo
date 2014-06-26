import argparse
import os
import shutil
import sys
import subprocess
import logging
import shlex
import datetime


# Takes in a command and a log. The log is a string representing the area calling the command.
#
# An example of these would be 'install', 'serve', and 'uninstall'
#
# By default this function uses the location of the helper install script.
def run_command(command, log=None, cwd=None):
	if cwd == None:
		cwd = os.path.dirname(os.path.realpath(__file__))
	
	if log is not None:
		logger = logging.getLogger(log)
		log_file_location = os.path.join(current_directory, 'logs', log+'.log')
		log_file_handler = logging.FileHandler(log_file_location)
		logger.addHandler(log_file_handler)
		logger.setLevel(logging.INFO)
		log = logger.handlers[0].stream
		time_stamp = datetime.datetime.now()
		logger.info('')
		logger.info('@@@@@@@@@@@@@@@@ Start '+ str(time_stamp) +' @@@@@@@@@@@@@@@@')
		logger.info('')

	process = subprocess.Popen(shlex.split(command), stderr=subprocess.STDOUT, stdout=log, cwd=cwd)

	# Wait to ensure chronological order
	response = process.wait()

	if response == 1 :
		print
		print '--------------------------------------------------------------------------------'
		print
		print command + ' command failed! See the log file at: '+ log_file_location
		print
		print '--------------------------------------------------------------------------------'
		print


# Checks to see if pip is currently installed. If it is not installed, then it will attempt to install it
def check_pip():
	log_name = 'pip_install'
	try:
		import pip
	except ImportError:
		print
		print 'Pip is not installed.'
		print 
		print 'May I install pip?'
		check = query_yes_no()
		print
		if check:
			print
			command = 'python get-pip.py'
			run_command(command, log_name)
		else:
			exit()
		try:
			import pip
			command = 'touch .pip'
			run_command(command)
			print 'Pip installed'
			print 
		except ImportError:
				print 'Pip install failed. Refer to log at ' + os.path.join(current_directory, 'logs', log_name+'.log.')
				exit()

# Checks to see if virtualenv is currently installed. If it is not installed, then it will attempt to install it
def check_virtualenv():
	log_name = 'virtualenv_install'
	try:
		import virtualenv
	except ImportError:
		print 'Virtualenv is not installed.'
		print 
		print 'May I install virtualenv?'
		check = query_yes_no()
		print
		if check:
			print
			command = 'pip install virtualenv'
			run_command(command, log_name)
		try:
			import virtualenv
			command = 'touch .virtualenv'
			run_command(command)
			print 'Virtualenv installed.'
		except ImportError:
			print 'Virtualenv install failed. Refer to log at ' + os.path.join(current_directory, 'logs', log_name+'.log.')
			exit()

def query_yes_no():
	yes = set(['yes','y', 'ye'])
	no = set(['no','n', ''])

	print 'y/N?'

	choice = raw_input().lower()
	if choice in yes:
	   return True
	elif choice in no:
	   return False
	else:
		query_yes_no()

parser = argparse.ArgumentParser(description='This is a helper script for my coding exercise. This file must be run as root because it will attempt to download and install requirements. Requires Python 2.7+')
parser.add_argument('-i', '--install',  
	choices=['production', 'development'],
	help="Installs the Coding Exercise. Either the production or development version can be installed. Both can be installed at the same time, but only one can be running at a time.",
	)
parser.add_argument('-u', '--uninstall',  
	choices=['production', 'development'],
	help="Uninstalls the Coding Exercise in the same directory as the helper script. Either the production or development version can be uninstalled. If the environment selected does not exist, then the script will exit. Only one environment can be served at a time.",
	)
parser.add_argument('-s', '--serve',  
	choices=['production', 'development'],
	help="Serves the Coding Exercise over localhost. Either the production or development version can be served. If the environment selected does not exist, then the script will exit.",
	)
args = parser.parse_args()

if os.getuid() != 0:
	print "This script must be run as root. Please refer to the help (-h) for more information."
	exit()

current_directory = os.path.dirname(os.path.realpath(__file__))
code_directory = os.path.join(current_directory, 'code')

if args.install != None:
	check_pip()
	check_virtualenv()

	path_to_install = os.path.join(current_directory, args.install)
	directory_check = os.path.isdir(path_to_install)
	
	# Check for previous install

	if not directory_check:
		os.makedirs(path_to_install)
	else:
		print 'Please uninstall '+args.install+' before reinstalling.'
		exit()

	# set up virtual environment

	command = 'virtualenv ' + path_to_install

	run_command(command, 'virtualenv')

	bin_directory = os.path.join(path_to_install, 'bin')

	if args.install == 'development':
		# Setup pyramid
		
		print
		print 'Setting up Pyramid. This may take a few minutes.'
		print 'Downloading and installing its dependencies into a virtual environment.'
		print
		
		command = os.path.join(bin_directory, 'easy_install') + ' pyramid'
		run_command(command, 'pyramid_install_development', cwd = path_to_install)

		# Create Project

		print
		print 'Creating the project.'
		print

		command = os.path.join('bin', 'pcreate -s alchemy mgo')

		run_command(command, 'pyramid_project_creation', cwd = path_to_install)

		print
		print 'Moving development code to the project.'
		print

		mgo_code_directory = os.path.join(code_directory, 'mgo')
		mgo_development_directory = os.path.join(path_to_install, 'mgo')

		# Replace default project files with our own application

		shutil.rmtree(mgo_development_directory)
		shutil.copytree(mgo_code_directory, mgo_development_directory)

		# Run project setup script now that our project code is in place.

		os.chdir(mgo_development_directory)

		print
		print 'Running the project setup.'
		print

		command = os.path.join(bin_directory, 'python') + ' setup.py develop'
		run_command(command, log='setup_project', cwd=mgo_development_directory)

		#######################
		# Initialize DB
		#######################

		print
		print 'Initializing the Database.'
		print

		path_to_install = os.path.join(current_directory, args.install)

		path_to_install = os.path.join(path_to_install, 'mgo')

		command = os.path.join(bin_directory, 'alembic') + ' init alembic'

		run_command(command, log = 'alembic_init', cwd=mgo_development_directory)

		command = os.path.join(bin_directory, 'alembic') + ' upgrade head'

		run_command(command, log = 'alembic_init', cwd=mgo_development_directory)

		print
		print 'Install Complete!'
		print

		exit()

	else:

		print 'Not yet implemented.'
		print
		print 'This command will install a production version of the application'

		# print
		# print 'Setting up production. This may take a few minutes.'
		# print 'Downloading and installing its dependencies into a virtual environment.'
		# print

		# command = os.path.join(path_to_install, 'bin', 'easy_install') + ' ' + os.path.join(code_directory, 'mgo-1.0.tar.gz')
		# run_command(command, 'production', cwd=path_to_install)

		# #######################
		# # Initialize DB
		# #######################

		# # ToDo

		# print 
		# print 'Install Complete!'
		# print

		exit()

if args.serve != None:
	path_to_install = os.path.join(current_directory, args.serve)
	directory_check = os.path.isdir(path_to_install)
	if not directory_check:
		print 'You must install before you can serve the application.'
		exit()
	else:
		bin_directory = os.path.join(path_to_install, 'bin')
		command = os.path.join(bin_directory, 'pserve')+' '+os.path.join(current_directory, args.serve+'.ini')
		print 'Serving '+args.serve+' on localhost:6543.'
		run_command(command, log='serving_'+args.serve)
		exit()

if args.uninstall != None:
	path_to_install = os.path.join(current_directory, args.uninstall)
	directory_check = os.path.exists(path_to_install)
	if directory_check:
		print 'Are you sure you want to uninstall '+args.uninstall+'?'
		check = query_yes_no()
		if check:
			run_command('rm -r '+ path_to_install)
			print 'Uninstall complete.'

			dot_file_path =	os.path.dirname(os.path.realpath(__file__))

			if os.path.exists(os.path.join(dot_file_path, '.virtualenv')):
				print 'Virtualenv was installed by this helper script. Would you like to uninstall it?'
				response = query_yes_no()
				if response:
					command = 'pip uninstall virtualenv'
					run_command(command)
					run_command('rm .virtualenv')
					print 'Uninstalled virtualenv.'
				else:
					print 'Virutalenv not uninstalled.'

			if os.path.exists(os.path.join(dot_file_path, '.pip')):
				print 'Pip was installed by this helper script. Would you like to uninstall it?'
				response = query_yes_no()
				if response:
					command = 'pip uninstall pip'
					run_command(command)
					run_command('rm .pip')
					print 'Uninstalled pip.'
				else:
					print 'Pip not uninstalled.'
			
			exit()
		
		else:
			print 'Uninstall aborted.'
			exit()
	else:
		print args.uninstall + ' not installed.'
		exit()

parser.print_help()

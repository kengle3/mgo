Coding Exercise
===
Python 2.7 is required to run

Go to the directory you prefer to install the code at in terminal.

Pulling from GitHub:

Travel to the directory you wish to install the application in Terminal

Type:
git pull https://github.com/kengle3/mgo.git

This will pull the code from GitHub. Once it finishes downloading, you will be ready to install to application


Installation:

Type:

sudo python mgo_assistant.py -i development

sudo is required because this file will download and install project dependencies

You will be asked to install pip and virtualenv. They are required packages for the project and the installer. mgo_assistant.py will also assist in uninstalling them.


Serving:
After the application has installed, type:

sudo python mgo_assistant.py -s development

This will serve the application on localhost:6543. This means you can go to a browser and type the url localhost:6543 to reach the application.

The application will continue to run in the terminal until the user presses control-c to stop it


Uninstall:
To uninstall the application, type:

sudo python mgo_assistant.py -u development

If the installer needed to install pip and virtualenv, it will prompt you if you'd like to uninstall those as well. 

For further help with mgo_assistant, try the command sudo python mgo_assistant.py. This will display help for the assistant.


Creating an account:

An account must first be created to enter the application. This can be done by hitting 'Create Account' in the menu.


People:

The application has a few different options for displaying people on the website.

View all People - Displays all people currently in the database

People Filters - Allows a filtered search of people currently in the database

Add Person - Adds an individual to the database

Add Test People - Adds test users to the database

Delete all People - Deletes all people from the database


Files:

Files is a file browser that displays assets stored within the files folder in the application. Initially it will prompt for a directory path. Hitting the ‘Go' button will display all the files in root folder. From here you can view individual files or delve further into directories. If there is a valid parent directory, then the user is presented with the option to go up a level to the parent directory.  The current path is displayed in the directory path text box. 


Status:

The status directory checks the required and installed packages on the system. It also checks to ensure that the database schema is the expected version. If the application finds a discrepancy in the packages installed, then a highlight is displayed to the user. If the database schema is not the expected version, then a message is provided letting the user know.
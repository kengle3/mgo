import cgi
import re
import os
from docutils.core import publish_parts
from pyramid.static import static_view
import urllib2
import json
import pip
from sqlalchemy import select

from sqlalchemy import func

from pyramid.httpexceptions import (
    HTTPFound,
    HTTPNotFound,
    )

from pyramid.response import Response
from pyramid.view import (view_config, forbidden_view_config,)

from pyramid.security import (
    remember,
    forget,
    )

from .security import USERS

from sqlalchemy.exc import DBAPIError

from .models import (
    DBSession,
    Person,
    Account,
    )

#########################################################################################################
#
# Homepage
#
#########################################################################################################

@view_config(route_name='view_home', renderer='templates/site.jinja2')
def view_home(request):
    return dict(
        message = 'Welcome to the Site!',
        logged_in = request.authenticated_userid,
        )

#########################################################################################################
#
# Account Functions
#
#########################################################################################################

def check_if_account_exists(username):
    user = DBSession.query(Account).filter(Account.username==username).first()
    if user is None:
        return False
    return True

@view_config(route_name='create_account', renderer='templates/create_account.jinja2', permission='view')
def create_account(request):
    message = ''
    if 'form.submitted' in request.params:
        username = request.params['username']
        password = request.params['password']
        password_confirm = request.params['password_confirm']
        if password != '' and username != '':
            if not check_if_account_exists(username):
                if password == password_confirm:
                    account = Account(username = username, password = password)
                    DBSession.add(account)
                    return HTTPFound(
                        location = request.route_url('view_home'),
                        )
                else:
                    message = 'Passwords do not match'
            else:
                message = 'Account already in use'
        else:
            message = 'Please enter a username and password'
    
    save_url = request.route_url('create_account')
    
    return dict(
        save_url = save_url, 
        logged_in = request.authenticated_userid,
        message = message,
        )

@view_config(route_name='login', renderer='templates/login.jinja2')
@forbidden_view_config(renderer='templates/login.jinja2')
def login(request):
    login_url = request.route_url('login')
    referrer = request.url
    
    if referrer == login_url:
        referrer = '/' # never use the login form itself as came_from
    
    came_from = request.params.get('came_from', referrer)
    message = ''
    login = ''
    password = ''
    
    if 'form.submitted' in request.params:
        
        json_payload = json.dumps(
            {
                'login':request.params['login'],
                'password':request.params['password'],
            }
        )
        
        headers = {'Content-Type':'application/json; charset=utf-8'}
        req = urllib2.Request(request.route_url('verify'), json_payload, headers)
        resp = urllib2.urlopen(req)
        data = resp.read()
        data = json.loads(data)
        if data['answer'] == 'OK':
            
            headers = remember(request, 'editor')
            return HTTPFound(
                location = came_from,
                 headers = headers,
                 )           
        
        message = 'Incorrect Login'

    return dict(
        message = message,
        url = request.route_url('login'),
        came_from = came_from,
        login = login,
        password = password,
        )

# Accepts a username and password from JSON and returns if the login is valid
# This is to show that permissions work, and not a demonstration of a secure application
@view_config(route_name='verify', renderer='json')
def verify(request):
    values = request.json_body
    login = values['login']
    password = values['password']

    user = DBSession.query(Account).filter(Account.username==login).first()
    
    reject = dict(
        answer='NO',
        )

    accept = dict(
        answer='OK',
        )

    if user is None:
        return reject

    if user.password == password:
        return accept

    return reject

@view_config(route_name='logout')
def logout(request):
    headers = forget(request)
    return HTTPFound(
        location = request.route_url('view_home'),
         headers = headers,
         )

#########################################################################################################
#
# People Functions
#
#########################################################################################################

people_api_version = '1.0'

# displays a list of actions we can perform regarding people
@view_config(route_name='people_actions', renderer='templates/people_actions.jinja2', permission='edit')
def people_actions(request):
    return dict(
        logged_in = request.authenticated_userid,
        )

# add a person to the database
@view_config(route_name='add_person', renderer='templates/add_person.jinja2', permission='edit')
def add_person(request):
    if 'form.submitted' in request.params:
        first = request.params['first_name']
        last = request.params['last_name']
        age = request.params['age']
        department = request.params['department']
        college = request.params['college']
        person = Person(first_name=first, last_name=last, age=age, department=department, college=college)
        DBSession.add(person)
        return HTTPFound(location = request.route_url('people_actions'))
    return dict(
        save_url = request.route_url('add_person'), 
        logged_in = request.authenticated_userid,
        )

#Adds Test People from a .csv file named testUsers located in test_files
@view_config(route_name='add_test_people', permission='edit')
def add_test_people(request):
    import csv
    
    path = os.path.dirname(__file__) + '/test_files/test_users.csv'
    cr = csv.reader(open(path,"rb"))
    
    for row in cr:    
        first = row[0]
        last = row[1]
        age = row[2]
        department = row[3]
        college = row[4]
        person = Person(first_name=first, last_name=last, age=age, department=department, college=college)
        DBSession.add(person)
    
    return HTTPFound(
        location = request.route_url('people_actions'),
        )

# deletes a person from the database
@view_config(route_name='delete_person', permission='edit')
def delete_person(request):
    user_id = int(request.matchdict['user_id'])
    DBSession.query(Person).filter(Person.id==user_id).delete()
    
    return HTTPFound(
        location = request.route_url('people_actions'),
        )

# deletes all people from the database
@view_config(route_name='delete_all_people', permission='edit')
def delete_all_people(request):
    DBSession.query(Person).delete()
    
    return HTTPFound(
        location = request.route_url('people_actions'),
        )

# Calculates pagination information and normalizes it so our results
# Stay within their proper bounds
#
# It also attempts to perform error correction
# (Someone manually enters variables into the url)
#
# Given: The unsanitized offset and resultsPerPage
# Returns: (page_number, total_pages, offset)
def generate_table_info(query, offset, results_per_page):
    count = query.count()

    if count == 0:
        return (1, 1, 0)
    if results_per_page <= 0:
        results_per_page = 10
    if offset < 0 or offset >= count:
        offset = 0

    # Check that we are at the beginning of a page. If not, backtrack to the start fo the page
    backtrack = offset % results_per_page
    if backtrack != 0:
        offset = offset - backtrack

    page_number = offset / results_per_page + 1

    total_pages = count / results_per_page
    remainder = count % results_per_page
    if remainder != 0:
        total_pages = total_pages + 1

    return (page_number, total_pages, offset)

#Generates the list of people when the Department filter is not applied
@view_config(route_name='get_page_of_people', renderer='templates/view_people.jinja2', permission='edit')
def get_page_of_people(request):
    offset = int(request.matchdict['offset'])
    results_per_page = int(request.matchdict['results_per_page'])
    order_by = request.matchdict['order_by']

    json_payload = json.dumps({ 'offset':offset, 'results_per_page':results_per_page, 'first_name':'', 'last_name':'', 'age':'', 'department':'', 'college':'', 'order_by':order_by })
    headers = {'Content-Type':'application/json; charset=utf-8'}
    path = request.route_url('get_page')
    req = urllib2.Request(path, json_payload, headers)
    resp = urllib2.urlopen(req)
    data = resp.read()
    data = json.loads(data)

    version_number = data['version']
    if version_number == '1.0':
        people = data['people']
        page_number = data['page_number']
        total_pages = data['total_pages']
        offset = data['offset']
        results_per_page = data['results_per_page']

        previous_page_url = request.route_url('get_page_of_people', offset=offset-results_per_page, results_per_page=results_per_page, order_by=order_by)
        next_page_url = request.route_url('get_page_of_people', offset=offset+results_per_page, results_per_page=results_per_page, order_by=order_by)

        if offset <= 0:
            previous_page_url = ''

        if total_pages <= page_number or offset > total_pages * results_per_page:
            next_page_url = ''

        message = ''
        if people == []:
            message = 'There are no people in the database'
    else:
        message = 'Server is incorrect version. Please update.'

    return dict(
        people = people,
        logged_in = request.authenticated_userid,
        message = message,
        next_page_url = next_page_url,
        previous_page_url = previous_page_url,
        page_number = page_number,
        total_pages = total_pages,
        referrer = request.referrer,
        )

@view_config(route_name='get_page', renderer='json') 
def get_page(request):
    values = request.json_body

    first_name = values['first_name']
    last_name = values['last_name']
    age = values['age']
    department = values['department']
    college = values['college']
    order_by = values['order_by']
    offset = int(values['offset'])
    results_per_page = int(values['results_per_page'])

    # It is my understanding sqlAlchemy sanitizes my inputs

    query = DBSession.query(Person)

    if first_name != '':
        query = query.filter(func.lower(Person.first_name) == func.lower(first_name))
    if last_name != '':
        query = query.filter(func.lower(Person.last_name) == func.lower(last_name))
    if age != '':
        query = query.filter(Person.age == age)
    if department != '':
        query = query.filter(func.lower(Person.department) == func.lower(department))
    if college != '':
        query = query.filter(func.lower(Person.college) == func.lower(college))

    if order_by == 'first_name':
        query = query.order_by(Person.first_name)
    elif order_by == 'age':
        query = query.order_by(Person.age)
    elif order_by == 'department':
        query = query.order_by(Person.department)
    elif order_by == 'college':
        query = query.order_by(Person.college)
    else:
        query = query.order_by(Person.last_name)

    if results_per_page <= 0:
        results_per_page = 10

    (page_number, total_pages, offset) = generate_table_info(query, offset, results_per_page)

    people = query.slice(offset, offset+results_per_page).all()


    return dict(
        people = people,
        offset = offset,
        page_number = page_number,
        total_pages = total_pages,
        results_per_page = results_per_page,
        version = people_api_version,
        )

@view_config(route_name='get_page_of_people_by_first_name', renderer='templates/view_people.jinja2', permission='edit')
def get_page_of_people_by_first_name(request):
    offset = int(request.matchdict['offset'])
    results_per_page = int(request.matchdict['results_per_page'])
    first_name = request.matchdict['first_name']

    order_by = request.matchdict['order_by']

    json_payload = json.dumps({ 'offset':offset, 'results_per_page':results_per_page, 'first_name':first_name, 'last_name':'', 'age':'', 'department':'', 'college':'', 'order_by': order_by })
    headers = {'Content-Type':'application/json; charset=utf-8'}
    req = urllib2.Request(request.route_url('get_page'), json_payload, headers)
    resp = urllib2.urlopen(req)
    data = resp.read()
    data = json.loads(data)

    version_number = data['version']
    if version_number == '1.0':
        people = data['people']
        page_number = data['page_number']
        total_pages = data['total_pages']
        offset = data['offset']
        results_per_page = data['results_per_page']

        previous_page_url = request.route_url('get_page_of_people_by_first_name', offset=offset-results_per_page, results_per_page=results_per_page, first_name=first_name, order_by=order_by)
        next_page_url = request.route_url('get_page_of_people_by_first_name', offset=offset+results_per_page, results_per_page=results_per_page, first_name=first_name, order_by=order_by)

        if offset <= 0:
            previous_page_url = ''

        if total_pages <= page_number or offset > total_pages * results_per_page:
            next_page_url = ''

        message = ''
        if people == []:
            message = 'There are no people in the database'
    else:
        message = 'Server is incorrect version. Please update.'

    return dict(
        people = people,
        logged_in = request.authenticated_userid,
        message = message,
        next_page_url = next_page_url,
        previous_page_url = previous_page_url,
        page_number = page_number,
        total_pages = total_pages,
        referrer = request.referrer,

        )

@view_config(route_name='get_page_of_people_by_last_name', renderer='templates/view_people.jinja2', permission='edit')
def get_page_of_people_by_last_name(request):
    offset = int(request.matchdict['offset'])
    results_per_page = int(request.matchdict['results_per_page'])
    last_name = request.matchdict['last_name']

    order_by = request.matchdict['order_by']

    json_payload = json.dumps({ 'offset':offset, 'results_per_page':results_per_page, 'first_name':'', 'last_name':last_name, 'age':'', 'department':'', 'college':'', 'order_by': order_by })
    headers = {'Content-Type':'application/json; charset=utf-8'}
    req = urllib2.Request(request.route_url('get_page'), json_payload, headers)
    resp = urllib2.urlopen(req)
    data = resp.read()
    data = json.loads(data)

    version_number = data['version']
    if version_number == '1.0':
        people = data['people']
        page_number = data['page_number']
        total_pages = data['total_pages']
        offset = data['offset']
        results_per_page = data['results_per_page']

        previous_page_url = request.route_url('get_page_of_people_by_last_name', offset=offset-results_per_page, results_per_page=results_per_page, last_name=last_name, order_by=order_by)
        next_page_url = request.route_url('get_page_of_people_by_last_name', offset=offset+results_per_page, results_per_page=results_per_page, last_name=last_name, order_by=order_by)

        if offset <= 0:
            previous_page_url = ''

        if total_pages <= page_number or offset > total_pages * results_per_page:
            next_page_url = ''

        message = ''
        if people == []:
            message = 'There are no people in the database'
    else:
        message = 'Server is incorrect version. Please update.'

    return dict(
        people = people,
        logged_in = request.authenticated_userid,
        message = message,
        next_page_url = next_page_url,
        previous_page_url = previous_page_url,
        page_number = page_number,
        total_pages = total_pages,
        referrer = request.referrer,
        )

# returns a listing of people who are of a particular age from the database
@view_config(route_name='get_page_of_people_by_age', renderer='templates/view_people.jinja2', permission='edit')
def get_page_of_people_by_age(request):
    offset = int(request.matchdict['offset'])
    results_per_page = int(request.matchdict['results_per_page'])
    age = request.matchdict['age']
    order_by = request.matchdict['order_by']

    json_payload = json.dumps({ 'offset':offset, 'results_per_page':results_per_page, 'first_name':'', 'last_name':'', 'age':age, 'department':'', 'college':'', 'order_by': order_by })
    headers = {'Content-Type':'application/json; charset=utf-8'}
    req = urllib2.Request(request.route_url('get_page'), json_payload, headers)
    resp = urllib2.urlopen(req)
    data = resp.read()
    data = json.loads(data)

    version_number = data['version']
    if version_number == '1.0':
        people = data['people']
        page_number = data['page_number']
        total_pages = data['total_pages']
        offset = data['offset']
        results_per_page = data['results_per_page']

        previous_page_url = request.route_url('get_page_of_people_by_age', offset=offset-results_per_page, results_per_page=results_per_page, age=age, order_by=order_by)
        next_page_url = request.route_url('get_page_of_people_by_age', offset=offset+results_per_page, results_per_page=results_per_page, age=age, order_by=order_by)

        if offset <= 0:
            previous_page_url = ''

        if total_pages <= page_number or offset > total_pages * results_per_page:
            next_page_url = ''

        message = ''
        if people == []:
            message = 'There are no people in the database'
    else:
        message = 'Server is incorrect version. Please update.'

    return dict(
        people = people,
        logged_in = request.authenticated_userid,
        message = message,
        next_page_url = next_page_url,
        previous_page_url = previous_page_url,
        page_number = page_number,
        total_pages = total_pages,
        referrer = request.referrer,
        )

@view_config(route_name='get_page_of_people_by_department', renderer='templates/view_people.jinja2', permission='edit')
def get_page_of_people_by_department(request):
    offset = int(request.matchdict['offset'])
    results_per_page = int(request.matchdict['results_per_page'])
    department = request.matchdict['department']

    order_by = request.matchdict['order_by']

    json_payload = json.dumps({ 'offset':offset, 'results_per_page':results_per_page, 'first_name':'', 'last_name':'', 'age':'', 'department':department, 'college':'', 'order_by': order_by })
    headers = {'Content-Type':'application/json; charset=utf-8'}
    req = urllib2.Request(request.route_url('get_page'), json_payload, headers)
    resp = urllib2.urlopen(req)
    data = resp.read()
    data = json.loads(data)

    version_number = data['version']
    if version_number == '1.0':
        people = data['people']
        page_number = data['page_number']
        total_pages = data['total_pages']
        offset = data['offset']
        results_per_page = data['results_per_page']

        previous_page_url = request.route_url('get_page_of_people_by_department', offset=offset-results_per_page, results_per_page=results_per_page, department=department, order_by=order_by)
        next_page_url = request.route_url('get_page_of_people_by_department', offset=offset+results_per_page, results_per_page=results_per_page, department=department, order_by=order_by)

        if offset <= 0:
            previous_page_url = ''

        if total_pages <= page_number or offset > total_pages * results_per_page:
            next_page_url = ''

        message = ''
        if people == []:
            message = 'There are no people in the database'
    else:
        message = 'Server is incorrect version. Please update.'

    return dict(
        people = people,
        logged_in = request.authenticated_userid,
        message = message,
        next_page_url = next_page_url,
        previous_page_url = previous_page_url,
        page_number = page_number,
        total_pages = total_pages,
        referrer = request.referrer,
        )

@view_config(route_name='get_page_of_people_by_college', renderer='templates/view_people.jinja2', permission='edit')
def get_page_of_people_by_college(request):
    offset = int(request.matchdict['offset'])
    results_per_page = int(request.matchdict['results_per_page'])
    college = request.matchdict['college']

    order_by = request.matchdict['order_by']

    json_payload = json.dumps({ 'offset':offset, 'results_per_page':results_per_page, 'first_name':'', 'last_name':'', 'age':'', 'department':'', 'college':college, 'order_by': order_by })
    headers = {'Content-Type':'application/json; charset=utf-8'}
    req = urllib2.Request(request.route_url('get_page'), json_payload, headers)
    resp = urllib2.urlopen(req)
    data = resp.read()
    data = json.loads(data)

    version_number = data['version']
    if version_number == '1.0':
        people = data['people']
        page_number = data['page_number']
        total_pages = data['total_pages']
        offset = data['offset']
        results_per_page = data['results_per_page']

        previous_page_url = request.route_url('get_page_of_people_by_college', offset=offset-results_per_page, results_per_page=results_per_page, college=college, order_by=order_by)
        next_page_url = request.route_url('get_page_of_people_by_college', offset=offset+results_per_page, results_per_page=results_per_page, college=college, order_by=order_by)

        if offset <= 0:
            previous_page_url = ''

        if total_pages <= page_number or offset > total_pages * results_per_page:
            next_page_url = ''

        message = ''
        if people == []:
            message = 'There are no people in the database'
    else:
        message = 'Server is incorrect version. Please update.'

    return dict(
        people = people,
        logged_in = request.authenticated_userid,
        message = message,
        next_page_url = next_page_url,
        previous_page_url = previous_page_url,
        page_number = page_number,
        total_pages = total_pages,
        referrer = request.referrer,
        )

@view_config(route_name='people_filters', renderer='templates/people_filters.jinja2', permission='edit')
def people_filters(request):
    if 'first_name_form.submitted' in request.params:
        if request.params['first_name'] != '':
            return HTTPFound(
                location = request.route_url('get_page_of_people_by_first_name', first_name=request.params['first_name'], offset=0, results_per_page=10, order_by='department'),
            )
        else:
            return HTTPFound(
                location = request.route_url('get_page_of_people', offset=0, results_per_page=10, order_by='last_name'),
            )
    if 'last_name_form.submitted' in request.params:
        if request.params['last_name'] != '':
            return HTTPFound(
                location = request.route_url('get_page_of_people_by_last_name', last_name=request.params['last_name'], offset=0, results_per_page=10, order_by='department'),
            )
        else:
            return HTTPFound(
                location = request.route_url('get_page_of_people', offset=0, results_per_page=10, order_by='last_name'),
            )
    if 'age_form.submitted' in request.params:
        if request.params['age'] != '':
            return HTTPFound(
                location = request.route_url('get_page_of_people_by_age', age=request.params['age'], offset=0, results_per_page=10, order_by='department'),
            )
        else:
            return HTTPFound(
                location = request.route_url('get_page_of_people', offset=0, results_per_page=10, order_by='last_name'),
            )
    if 'department_form.submitted' in request.params:
        if request.params['department'] != '':
            return HTTPFound(
                location = request.route_url('get_page_of_people_by_department', department=request.params['department'], offset=0, results_per_page=10, order_by='last_name'),
            )
        else:
            return HTTPFound(
                location = request.route_url('get_page_of_people', offset=0, results_per_page=10, order_by='last_name'),
            )
    if 'college_form.submitted' in request.params:
        if request.params['college'] != '':
            return HTTPFound(
                location = request.route_url('get_page_of_people_by_college', college=request.params['college'], offset=0, results_per_page=10, order_by='department'),
            )
        else:
            return HTTPFound(
                location = request.route_url('get_page_of_people', offset=0, results_per_page=10, order_by='last_name'),
            )
    return dict(save_url = request.route_url('people_filters'),
        logged_in = request.authenticated_userid,
        )

#########################################################################################################
#
# File Functions
#
#########################################################################################################

file_api_version = 1.0

# Combines the path_split and format_path helper functions since they compliment each other
# Sanitizes a string to ensure a consistent string path is output
def sanitize_file_path(s):
    return format_path(path_split(s))

# This helper function splits a file path into a list.
# Using the Python split method leaves empty strings since it is intended to compliment .join()
# A split and join would give the original string

# This function removes the slashes and sets each text portion of the file path as an elements of the list.

# Examples:

# '/Dogs' would become ['Dogs']
# '/Dogs/' would become ['Dogs']
# '/Dogs/Cats' would become ['Dogs', 'Cats']
# 'Dogs/Cats/' would become ['Dogs', 'Cats']
def path_split(s):
    return [ x for x in s.split('/') if x ]

# Takes a list and constructs a relative path with it
def format_path(list):
    path=''
    
    for element in list:
        # Don't allow going to upper level directories. If they try to direct them to the root of files
        if element == '..':
            return ''
        path = path + element + '/'
    
    # Remove the extra slash placed on the end
    path = path[:-1]
    return path

# Takes in a JSON encoded file path and returns a listing of files and directories
# contained within that path
#
# The root directory is files (mgo/mgo/files)
@view_config(route_name='file_request', renderer='json')
def file_request(request):
    path = request.json_body['path']
    sanitized_path = sanitize_file_path(path)
    full_path = os.path.dirname(__file__) + '/files/' + sanitized_path
    
    if os.path.isdir(full_path):
        files = [ f for f in os.listdir(full_path) if os.path.isfile(os.path.join(full_path,f)) ]
        directories = [ f for f in os.listdir(full_path) if os.path.isdir(os.path.join(full_path,f)) ]
        message = ''

    else:
        files = []
        directories = []
        message = 'Invalid File Path'

    sanitized_path_array = path_split(path)

    sanitized_path_array = sanitized_path_array[:-1]
    parent_directory_path = format_path(sanitized_path_array)

    # if len(sanitized_path_array) != 0:
    #     parent_directory_list = sanitized_path_array.pop(-1)
    # else:
    #     parent_directory_list = ''
    # parent_directory_path = format_path(parent_directory_list)
    
    return dict(
        directories = directories, 
        files = files,
        version = file_api_version,
        parent_directory_path = parent_directory_path,
        message = message,
        )


# This is the form that generates the list of files and directories in a given Directory
# The root directory is the /files directory
@view_config(route_name='file', renderer='templates/file.jinja2', permission='edit')
def file(request):
    if 'path' in request.params:
        json_payload = json.dumps({'path':request.params['path']})
        headers = {'Content-Type':'application/json; charset=utf-8'}
        req = urllib2.Request(request.route_url('file_request'), json_payload, headers)
        resp = urllib2.urlopen(req)
        data = resp.read()
        data = json.loads(data)

        return dict(
            directories = data['directories'], 
            files = data['files'], 
            view_url = request.static_url('mgo:files/'), 
            save_url = request.route_url('file'), 
            path = sanitize_file_path(request.params['path']),
            logged_in = request.authenticated_userid,
            parent_directory_path = data['parent_directory_path'],
            message = data['message']
            )

    return dict(
        directories = [], 
        files = [], 
        save_url = request.route_url('file'), 
        path = '', 
        logged_in = request.authenticated_userid,
        parent_directory_path = '',
        message = ''
        )

#########################################################################################################
#
# Status Functions
#
#########################################################################################################

# Helper function for status. It converts the output of a pip freeze to a dictionary.
# key: package
# value: version number
def freeze_to_dictionary(filePath):
    freeze = dict()
    file = open(filePath,"r")
    
    for line in file:
        split = line.partition("==")

        # Remove possible string terminators
        package = split[0].rstrip("\r\n")
        version = str(split[2]).rstrip("\r\n")
        freeze[package] = version
    
    file.close()
    return freeze

# Allows the user to see an example of the highlighting feature.
# This points to a different txt in the same format as requirements.txt
#
# It also demonstrates that if a package is missing, then it shows Not Installed.
@view_config(route_name='status_highlight', renderer='templates/status.jinja2')
def status_highlight(request):
    # This path is used to point to the demonstration requirements.txt
    path = os.path.dirname(__file__)

    # I think there is probably a more elegant way of doing this, but I'm not familiar enough with pip as a library
    #
    # Would do further research into pip's API to see if its possible to check installed distributions against a requirements.txt file directly in pip.
    # Was having trouble finding much programming documentation regarding pip's API

    installed = dict()
    for dist in pip.get_installed_distributions(local_only=True):
        inst = str(dist.as_requirement())
        splitString = inst.partition('==')

        # Remove possible string terminators
        package = splitString[0].rstrip("\r\n")
        version = splitString[2].rstrip("\r\n")
        installed[package] = version

    required = freeze_to_dictionary(path+'/requirements.txt')

    packages = []
    for key in sorted(required, key=str.lower):
        try:
            element = (key, installed[key], required[key])
            packages.append(element)
        except:
            element = (key, 'Not Installed', required[key])
            packages.append(element)

    return dict(
        packages = packages, 
        logged_in = request.authenticated_userid,
        example_url = '',
        database_version = 'demo',
        expected_database_version = '3a2964d51f2',
        )    

def get_database_revision():
    s = select(['version_num'],from_obj='alembic_version')
    result = DBSession.execute(s).fetchone()
    return result['version_num']


# Allows the user to check the status of the application directly on the website
# Reports the version of packages
@view_config(route_name='status', renderer='templates/status.jinja2', permission='edit')
def status(request):
    # These three lines traverse up the file path to the location requirements.txt is generated by pserve
    parent_directory = os.path.join(os.path.dirname(__file__), os.path.pardir)
    parent_directory = os.path.join(parent_directory, os.path.pardir)
    path = os.path.abspath(os.path.join(parent_directory, os.path.pardir))

    # I think there is probably a more elegant way of doing this, but I'm not familiar enough with pip as a library
    #
    # Would do further research into pip's API to see if its possible to check installed distributions against a requirements.txt file directly in pip.
    # Was having trouble finding much programming documentation regarding pip's API

    installed = dict()
    for dist in pip.get_installed_distributions(local_only=True):
        inst = str(dist.as_requirement())
        splitString = inst.partition('==')

        # Remove possible string terminators
        package = splitString[0].rstrip("\r\n")
        version = splitString[2].rstrip("\r\n")
        installed[package] = version
        
    required = freeze_to_dictionary(path+'/requirements.txt')

    packages = []
    for key in sorted(required, key=str.lower):
        try:
            element = (key, installed[key], required[key])
            packages.append(element)
        except:
            element = (key, 'Not Installed', required[key])
            packages.append(element)

    return dict(
        packages = packages, 
        logged_in = request.authenticated_userid,
        example_url = request.route_url('status_highlight'),
        database_version = get_database_revision(),
        expected_database_version = '3a2964d51f2',
        )
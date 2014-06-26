import unittest
import transaction
import os
import json

from pyramid import testing

def _initTestingDB():
	from sqlalchemy import create_engine
	from mgo.models import (
		DBSession,
		Person,
		Account,
		Base,
	)
	engine = create_engine('sqlite://')
	Base.metadata.create_all(engine)
	DBSession.configure(bind=engine)
	return DBSession

def _registerRoutes(config):
	config.add_route('view_home', '/')

	# File Routes

	config.add_static_view('static', 'static', cache_max_age=3600)
	config.add_static_view('files', 'files', cache_max_age=3600)
	config.add_route('file_request','/file_request')
	config.add_route('file','/file')

	# Status Routes

	config.add_route('status','/status')

	# Account Routes

	config.add_route('login', '/login')
	config.add_route('logout', '/logout')
	config.add_route('verify', '/verify')
	config.add_route('create_account', '/signup')


	# Routes relating to People section

	config.add_route('people_actions', '/people')
	config.add_route('add_person','/people/add')
	config.add_route('add_test_people','/add_test_people')
	config.add_route('delete_all_people','/delete/all')
	config.add_route('delete_person','/delete/{user_id}')
	config.add_route('get_page','/get_page')
	config.add_route('people_filters','/people_filters')
	config.add_route('get_page_of_people','/people/{offset}/{results_per_page}/{order_by}')
	config.add_route('get_page_of_people_by_last_name', '/people/last_name/{last_name}/{offset}/{results_per_page}/{order_by}')
	config.add_route('get_page_of_people_by_age','/people/age/{age}/{offset}/{results_per_page}/{order_by}')
	config.add_route('get_page_of_people_by_first_name', '/people/first_name/{first_name}/{offset}/{results_per_page}/{order_by}')
	config.add_route('get_page_of_people_by_department', '/people/department/{department}/{offset}/{results_per_page}/{order_by}')
	config.add_route('get_page_of_people_by_college', '/people/college/{college}/{offset}/{results_per_page}/{order_by}')

#########################################################################################################
#
# Homepage Tests
#
#########################################################################################################


class view_home_tests(unittest.TestCase):
	def setUp(self):
		self.config = testing.setUp()

	def tearDown(self):
		testing.tearDown()

	def _callFUT(self, request):
		from mgo.views import view_home
		return view_home(request)

	def test_it(self):
		_registerRoutes(self.config)
		request = testing.DummyRequest()
		response = self._callFUT(request)
		self.assertEqual(response['message'], 'Welcome to the Site!')

#########################################################################################################
#
# Account Tests
#
#########################################################################################################

class check_if_account_exists_tests(unittest.TestCase):
	def setUp(self):
		self.session = _initTestingDB()
		self.config = testing.setUp()

	def tearDown(self):
		self.session.remove()
		testing.tearDown()

	def _callFUT(self, request):
		from mgo.views import check_if_account_exists
		return check_if_account_exists(request)

	def test_account_exists(self):
		from mgo.models import Account
		_registerRoutes(self.config)
		request = testing.DummyRequest()
		acc = Account(username='login', password='password')
		self.session.add(acc)
		request.matchdict = {'username':'login', 'password':'password'}
		info = self._callFUT('login')
		self.assertEqual(info, True)

	def test_account_doesnt_exist(self):
		from mgo.models import Account
		_registerRoutes(self.config)
		request = testing.DummyRequest()
		request.matchdict = {'username':'login', 'password':'password'}
		info = self._callFUT('login')
		self.assertEqual(info, False)


class create_account_tests(unittest.TestCase):
	def setUp(self):
		self.session = _initTestingDB()
		self.config = testing.setUp()

	def tearDown(self):
		self.session.remove()
		testing.tearDown()

	def _callFUT(self, request):
		from mgo.views import create_account
		return create_account(request)

	def test_it_notsubmitted(self):
		_registerRoutes(self.config)
		request = testing.DummyRequest()
		info = self._callFUT(request)
		self.assertEqual(info['save_url'], 'http://example.com/signup')

	def test_it_submitted(self):
		from mgo.models import Account
		_registerRoutes(self.config)
		request = testing.DummyRequest({'form.submitted':True,
										'username':'Test',
										'password':'Tester',
										'password_confirm':'Tester'})
		self._callFUT(request)
		person = self.session.query(Account).one()
		self.assertEqual(person.username, 'Test')
		self.assertEqual(person.password, 'Tester')

	def test_empty_input(self):
		from mgo.models import Account
		_registerRoutes(self.config)
		request = testing.DummyRequest({'form.submitted':True,
										'username':'',
										'password':'',
										'password_confirm':''})
		self._callFUT(request)
		person = self.session.query(Account).count()
		self.assertEqual(person, 0)

	def test_confirmation(self):
		from mgo.models import Account
		_registerRoutes(self.config)
		request = testing.DummyRequest({'form.submitted':True,
										'username':'test',
										'password':'test',
										'password_confirm':'incorrect'})
		self._callFUT(request)
		person = self.session.query(Account).count()
		self.assertEqual(person, 0)


class create_login_tests(unittest.TestCase):
	def setUp(self):
		self.session = _initTestingDB()
		self.config = testing.setUp()

	def tearDown(self):
		self.session.remove()
		testing.tearDown()

	def _callFUT(self, request):
		from mgo.views import login
		return login(request)

	def test_it_notsubmitted(self):
		_registerRoutes(self.config)
		request = testing.DummyRequest()
		request.url='http://example.com/login'
		info = self._callFUT(request)
		self.assertEqual(info['message'], '')

class verify_tests(unittest.TestCase):
	def setUp(self):
		self.session = _initTestingDB()
		self.config = testing.setUp()

	def tearDown(self):
		self.session.remove()
		testing.tearDown()

	def _callFUT(self, request):
		from mgo.views import verify
		return verify(request)

	def test_it_okay(self):
		from mgo.models import Account
		_registerRoutes(self.config)
		request = testing.DummyRequest()
		acc = Account(username='login', password='password')
		self.session.add(acc)
		request.json_body={'login':'login', 'password':'password'}
		request.header={'Content-Type':'application/json; charset=utf-8'}
		info = self._callFUT(request)
		self.assertEqual(info, {'answer': 'OK'})

	def test_not_okay(self):
		from mgo.models import Account
		_registerRoutes(self.config)
		request = testing.DummyRequest()
		acc = Account(username='login', password='no')
		self.session.add(acc)
		request.json_body={'login':'login', 'password':'password'}
		request.header={'Content-Type':'application/json; charset=utf-8'}
		info = self._callFUT(request)
		self.assertEqual(info, {'answer': 'NO'})

#########################################################################################################
#
# People Tests
#
# Note: urllib2 does not play nice with DummyRequest. When DummyRequest is sent to a function using
#		urllib2 it attempts to open http://example.com/<your page> literally instead of hypothetically.
#
#		Due to this get_page is tested extensively
#
#########################################################################################################

class get_page(unittest.TestCase):
	def setUp(self):
		self.session = _initTestingDB()
		self.config = testing.setUp()

	def tearDown(self):
		self.session.remove()
		testing.tearDown()

	def _callFUT(self, request):
		from mgo.views import get_page
		return get_page(request)

	def test_get_page_empty_json(self):
		offset = '0'
		results_per_page = '10'
		first_name = ''
		last_name = ''
		age = ''
		department = ''
		college = ''
		order_by = 'first_name'
		json_payload = { 'offset':offset, 'results_per_page':results_per_page, 'first_name':first_name, 'last_name':last_name, 'age':age, 'department':department, 'college':college, 'order_by': order_by }
		request = testing.DummyRequest(json_body=json_payload)
		response = self._callFUT(request)
		self.assertEqual(response['page_number'], 1)
		self.assertEqual(response['people'], [])
		self.assertEqual(response['results_per_page'], 10)
		self.assertEqual(response['offset'], 0)
		self.assertEqual(response['total_pages'], 1)

	def test_get_page_one_person_json(self):
		from mgo.models import Person
		person = Person(first_name='Test', last_name='Tester', age=21, department='Computer Science', college='Engineering',)
		self.session.add(person)

		offset = '0'
		results_per_page = '10'
		first_name = ''
		last_name = ''
		age = ''
		department = ''
		college = ''
		order_by = 'first_name'
		json_payload = { 'offset':offset, 'results_per_page':results_per_page, 'first_name':first_name, 'last_name':last_name, 'age':age, 'department':department, 'college':college, 'order_by': order_by }
		request = testing.DummyRequest(json_body=json_payload)
		response = self._callFUT(request)
		self.assertEqual(response['page_number'], 1)
		self.assertEqual(response['people'], [person])
		self.assertEqual(response['results_per_page'], 10)
		self.assertEqual(response['offset'], 0)
		self.assertEqual(response['total_pages'], 1)

	def test_get_page_pagination_one_json(self):
		from mgo.models import Person
		person_one = Person(first_name='Test', last_name='Tester', age=21, department='Computer Science', college='Engineering',)
		self.session.add(person_one)

		person_two = Person(first_name='Tester', last_name='Tester', age=21, department='Computer Science', college='Engineering',)
		self.session.add(person_two)

		offset = '0'
		results_per_page = '1'
		first_name = ''
		last_name = ''
		age = ''
		department = ''
		college = ''
		order_by = 'first_name'
		json_payload = { 'offset':offset, 'results_per_page':results_per_page, 'first_name':first_name, 'last_name':last_name, 'age':age, 'department':department, 'college':college, 'order_by': order_by }
		request = testing.DummyRequest(json_body=json_payload)
		response = self._callFUT(request)
		self.assertEqual(response['page_number'], 1)
		self.assertEqual(response['people'], [person_one])
		self.assertEqual(response['results_per_page'], 1)
		self.assertEqual(response['offset'], 0)
		self.assertEqual(response['total_pages'], 2)

	def test_get_page_pagination_two_json(self):
		from mgo.models import Person
		person_one = Person(first_name='Test', last_name='Tester', age=21, department='Computer Science', college='Engineering',)
		self.session.add(person_one)

		person_two = Person(first_name='Tester', last_name='Test', age=21, department='Computer Science', college='Engineering',)
		self.session.add(person_two)

		offset = '1'
		results_per_page = '1'
		first_name = ''
		last_name = ''
		age = ''
		department = ''
		college = ''
		order_by = 'first_name'
		json_payload = { 'offset':offset, 'results_per_page':results_per_page, 'first_name':first_name, 'last_name':last_name, 'age':age, 'department':department, 'college':college, 'order_by': order_by }
		request = testing.DummyRequest(json_body=json_payload)
		response = self._callFUT(request)
		self.assertEqual(response['page_number'], 2)
		self.assertEqual(response['people'], [person_two])
		self.assertEqual(response['results_per_page'], 1)
		self.assertEqual(response['offset'], 1)
		self.assertEqual(response['total_pages'], 2)

	def test_get_page_pagination_invalid_negative_offset_json(self):
		from mgo.models import Person
		person_one = Person(first_name='Test', last_name='Tester', age=21, department='Computer Science', college='Engineering',)
		self.session.add(person_one)

		person_two = Person(first_name='Tester', last_name='Test', age=21, department='Computer Science', college='Engineering',)
		self.session.add(person_two)

		offset = '-1'
		results_per_page = '1'
		first_name = ''
		last_name = ''
		age = ''
		department = ''
		college = ''
		order_by = 'first_name'
		json_payload = { 'offset':offset, 'results_per_page':results_per_page, 'first_name':first_name, 'last_name':last_name, 'age':age, 'department':department, 'college':college, 'order_by': order_by }
		request = testing.DummyRequest(json_body=json_payload)
		response = self._callFUT(request)
		self.assertEqual(response['page_number'], 1)
		self.assertEqual(response['people'], [person_one])
		self.assertEqual(response['results_per_page'], 1)
		self.assertEqual(response['offset'], 0)
		self.assertEqual(response['total_pages'], 2)

	def test_get_page_pagination_invalid_large_offset_json(self):
		from mgo.models import Person
		person_one = Person(first_name='Test', last_name='Tester', age=21, department='Computer Science', college='Engineering',)
		self.session.add(person_one)

		person_two = Person(first_name='Tester', last_name='Test', age=21, department='Computer Science', college='Engineering',)
		self.session.add(person_two)

		offset = '99'
		results_per_page = '1'
		first_name = ''
		last_name = ''
		age = ''
		department = ''
		college = ''
		order_by = 'first_name'
		json_payload = { 'offset':offset, 'results_per_page':results_per_page, 'first_name':first_name, 'last_name':last_name, 'age':age, 'department':department, 'college':college, 'order_by': order_by }
		request = testing.DummyRequest(json_body=json_payload)
		response = self._callFUT(request)
		self.assertEqual(response['page_number'], 1)
		self.assertEqual(response['people'], [person_one])
		self.assertEqual(response['results_per_page'], 1)
		self.assertEqual(response['offset'], 0)
		self.assertEqual(response['total_pages'], 2)

	def test_get_page_pagination_zero_results_json(self):
		from mgo.models import Person
		person_one = Person(first_name='Test', last_name='Tester', age=21, department='Computer Science', college='Engineering',)
		self.session.add(person_one)

		person_two = Person(first_name='Tester', last_name='Test', age=21, department='Computer Science', college='Engineering',)
		self.session.add(person_two)

		offset = '0'
		results_per_page = '0'
		first_name = ''
		last_name = ''
		age = ''
		department = ''
		college = ''
		order_by = 'first_name'
		json_payload = { 'offset':offset, 'results_per_page':results_per_page, 'first_name':first_name, 'last_name':last_name, 'age':age, 'department':department, 'college':college, 'order_by': order_by }
		request = testing.DummyRequest(json_body=json_payload)
		response = self._callFUT(request)
		self.assertEqual(response['page_number'], 1)
		self.assertEqual(response['people'], [person_one, person_two])
		self.assertEqual(response['results_per_page'], 10)
		self.assertEqual(response['offset'], 0)
		self.assertEqual(response['total_pages'], 1)

	def test_get_page_pagination_negative_results_json(self):
		from mgo.models import Person
		person_one = Person(first_name='Test', last_name='Tester', age=21, department='Computer Science', college='Engineering',)
		self.session.add(person_one)

		person_two = Person(first_name='Tester', last_name='Test', age=21, department='Computer Science', college='Engineering',)
		self.session.add(person_two)

		offset = '0'
		results_per_page = '-1'
		first_name = ''
		last_name = ''
		age = ''
		department = ''
		college = ''
		order_by = 'first_name'
		json_payload = { 'offset':offset, 'results_per_page':results_per_page, 'first_name':first_name, 'last_name':last_name, 'age':age, 'department':department, 'college':college, 'order_by': order_by }
		request = testing.DummyRequest(json_body=json_payload)
		response = self._callFUT(request)
		self.assertEqual(response['page_number'], 1)
		self.assertEqual(response['people'], [person_one, person_two])
		self.assertEqual(response['results_per_page'], 10)
		self.assertEqual(response['offset'], 0)
		self.assertEqual(response['total_pages'], 1)

	def test_get_page_pagination_negative_results_and_offset_json(self):
		from mgo.models import Person
		person_one = Person(first_name='Test', last_name='Tester', age=21, department='Computer Science', college='Engineering',)
		self.session.add(person_one)

		person_two = Person(first_name='Tester', last_name='Test', age=21, department='Computer Science', college='Engineering',)
		self.session.add(person_two)

		offset = '-1'
		results_per_page = '-1'
		first_name = ''
		last_name = ''
		age = ''
		department = ''
		college = ''
		order_by = 'first_name'
		json_payload = { 'offset':offset, 'results_per_page':results_per_page, 'first_name':first_name, 'last_name':last_name, 'age':age, 'department':department, 'college':college, 'order_by': order_by }
		request = testing.DummyRequest(json_body=json_payload)
		response = self._callFUT(request)
		self.assertEqual(response['page_number'], 1)
		self.assertEqual(response['people'], [person_one, person_two])
		self.assertEqual(response['results_per_page'], 10)
		self.assertEqual(response['offset'], 0)
		self.assertEqual(response['total_pages'], 1)

	def test_get_page_pagination_error_checking(self):
		from mgo.models import Person

		# Set up test data

		chris = Person(first_name='Chris', last_name='Zoolander', age=2, department='Computer Science', college='Test',)
		self.session.add(chris)
		amy = Person(first_name='Amy', last_name='Wong', age=4, department='Science', college='Zoo',)
		self.session.add(amy)
		brian = Person(first_name='Brian', last_name='Xavier', age=3, department='Math', college='Green',)
		self.session.add(brian)
		zach = Person(first_name='Zach', last_name='Alexander', age=5, department='Computer Science', college='Red',)
		self.session.add(zach)
		gary = Person(first_name='Gary', last_name='Haas', age=1, department='Science', college='Blue',)
		self.session.add(gary)
		alan = Person(first_name='Alan', last_name='Turing', age=6, department='Math', college='White',)
		self.session.add(alan)

		# Set up query data

		offset = '1'
		results_per_page = '6'
		first_name = ''
		last_name = ''
		age = ''
		department = ''
		college = ''
		order_by = 'first_name'
		json_payload = { 'offset':offset, 'results_per_page':results_per_page, 'first_name':first_name, 'last_name':last_name, 'age':age, 'department':department, 'college':college, 'order_by': order_by }
		request = testing.DummyRequest(json_body=json_payload)
		response = self._callFUT(request)
		
		# Check results

		self.assertEqual(response['page_number'], 1)
		self.assertEqual(response['people'], [alan, amy, brian, chris, gary, zach])
		self.assertEqual(response['results_per_page'], 6)
		self.assertEqual(response['offset'], 0)
		self.assertEqual(response['total_pages'], 1)

	def test_get_page_pagination_error_checking_two(self):
		from mgo.models import Person

		# Set up test data

		chris = Person(first_name='Chris', last_name='Zoolander', age=2, department='Computer Science', college='Test',)
		self.session.add(chris)
		amy = Person(first_name='Amy', last_name='Wong', age=4, department='Science', college='Zoo',)
		self.session.add(amy)
		brian = Person(first_name='Brian', last_name='Xavier', age=3, department='Math', college='Green',)
		self.session.add(brian)
		zach = Person(first_name='Zach', last_name='Alexander', age=5, department='Computer Science', college='Red',)
		self.session.add(zach)
		gary = Person(first_name='Gary', last_name='Haas', age=1, department='Science', college='Blue',)
		self.session.add(gary)
		alan = Person(first_name='Alan', last_name='Turing', age=6, department='Math', college='White',)
		self.session.add(alan)

		# Set up query data

		offset = '5'
		results_per_page = '6'
		first_name = ''
		last_name = ''
		age = ''
		department = ''
		college = ''
		order_by = 'first_name'
		json_payload = { 'offset':offset, 'results_per_page':results_per_page, 'first_name':first_name, 'last_name':last_name, 'age':age, 'department':department, 'college':college, 'order_by': order_by }
		request = testing.DummyRequest(json_body=json_payload)
		response = self._callFUT(request)
		
		# Check results

		self.assertEqual(response['page_number'], 1)
		self.assertEqual(response['people'], [alan, amy, brian, chris, gary, zach])
		self.assertEqual(response['results_per_page'], 6)
		self.assertEqual(response['offset'], 0)
		self.assertEqual(response['total_pages'], 1)

	def test_get_page_grouping_last_name(self):
		from mgo.models import Person

		# Set up test data

		chris = Person(first_name='Chris', last_name='Zoolander', age=2, department='Computer Science', college='Test',)
		self.session.add(chris)
		amy = Person(first_name='Amy', last_name='Wong', age=4, department='Science', college='Zoo',)
		self.session.add(amy)
		brian = Person(first_name='Brian', last_name='Xavier', age=3, department='Math', college='Green',)
		self.session.add(brian)
		zach = Person(first_name='Zach', last_name='Alexander', age=5, department='Computer Science', college='Red',)
		self.session.add(zach)
		gary = Person(first_name='Gary', last_name='Haas', age=1, department='Science', college='Blue',)
		self.session.add(gary)
		alan = Person(first_name='Alan', last_name='Turing', age=6, department='Math', college='White',)
		self.session.add(alan)

		# Set up query data

		offset = '0'
		results_per_page = '6'
		first_name = ''
		last_name = ''
		age = ''
		department = ''
		college = ''
		order_by = 'last_name'
		json_payload = { 'offset':offset, 'results_per_page':results_per_page, 'first_name':first_name, 'last_name':last_name, 'age':age, 'department':department, 'college':college, 'order_by': order_by }
		request = testing.DummyRequest(json_body=json_payload)
		response = self._callFUT(request)
		
		# Check results

		self.assertEqual(response['page_number'], 1)
		self.assertEqual(response['people'], [zach, gary, alan, amy, brian, chris])
		self.assertEqual(response['results_per_page'], 6)
		self.assertEqual(response['offset'], 0)
		self.assertEqual(response['total_pages'], 1)

	def test_get_page_grouping_age(self):
		from mgo.models import Person

		# Set up test data

		chris = Person(first_name='Chris', last_name='Zoolander', age=2, department='Computer Science', college='Test',)
		self.session.add(chris)
		amy = Person(first_name='Amy', last_name='Wong', age=4, department='Science', college='Zoo',)
		self.session.add(amy)
		brian = Person(first_name='Brian', last_name='Xavier', age=3, department='Math', college='Green',)
		self.session.add(brian)
		zach = Person(first_name='Zach', last_name='Alexander', age=5, department='Computer Science', college='Red',)
		self.session.add(zach)
		gary = Person(first_name='Gary', last_name='Haas', age=1, department='Science', college='Blue',)
		self.session.add(gary)
		alan = Person(first_name='Alan', last_name='Turing', age=6, department='Math', college='White',)
		self.session.add(alan)

		# Set up query data

		offset = '0'
		results_per_page = '6'
		first_name = ''
		last_name = ''
		age = ''
		department = ''
		college = ''
		order_by = 'age'
		json_payload = { 'offset':offset, 'results_per_page':results_per_page, 'first_name':first_name, 'last_name':last_name, 'age':age, 'department':department, 'college':college, 'order_by': order_by }
		request = testing.DummyRequest(json_body=json_payload)
		response = self._callFUT(request)
		
		# Check results

		self.assertEqual(response['page_number'], 1)
		self.assertEqual(response['people'], [gary, chris, brian, amy, zach, alan])
		self.assertEqual(response['results_per_page'], 6)
		self.assertEqual(response['offset'], 0)
		self.assertEqual(response['total_pages'], 1)

	def test_get_page_grouping_department(self):
		from mgo.models import Person

		# Set up test data

		chris = Person(first_name='Chris', last_name='Zoolander', age=2, department='Computer Science', college='Test',)
		self.session.add(chris)
		amy = Person(first_name='Amy', last_name='Wong', age=4, department='Science', college='Zoo',)
		self.session.add(amy)
		brian = Person(first_name='Brian', last_name='Xavier', age=3, department='Math', college='Green',)
		self.session.add(brian)
		zach = Person(first_name='Zach', last_name='Alexander', age=5, department='Computer Science', college='Red',)
		self.session.add(zach)
		gary = Person(first_name='Gary', last_name='Haas', age=1, department='Science', college='Blue',)
		self.session.add(gary)
		alan = Person(first_name='Alan', last_name='Turing', age=6, department='Math', college='White',)
		self.session.add(alan)

		# Set up query data

		offset = '0'
		results_per_page = '6'
		first_name = ''
		last_name = ''
		age = ''
		department = ''
		college = ''
		order_by = 'department'
		json_payload = { 'offset':offset, 'results_per_page':results_per_page, 'first_name':first_name, 'last_name':last_name, 'age':age, 'department':department, 'college':college, 'order_by': order_by }
		request = testing.DummyRequest(json_body=json_payload)
		response = self._callFUT(request)
		
		# Check results

		self.assertEqual(response['page_number'], 1)
		self.assertEqual(response['people'], [chris, zach, brian, alan, amy, gary])
		self.assertEqual(response['results_per_page'], 6)
		self.assertEqual(response['offset'], 0)
		self.assertEqual(response['total_pages'], 1)

	def test_get_page_grouping_college(self):
		from mgo.models import Person

		# Set up test data

		chris = Person(first_name='Chris', last_name='Zoolander', age=2, department='Computer Science', college='Test',)
		self.session.add(chris)
		amy = Person(first_name='Amy', last_name='Wong', age=4, department='Science', college='Zoo',)
		self.session.add(amy)
		brian = Person(first_name='Brian', last_name='Xavier', age=3, department='Math', college='Green',)
		self.session.add(brian)
		zach = Person(first_name='Zach', last_name='Alexander', age=5, department='Computer Science', college='Red',)
		self.session.add(zach)
		gary = Person(first_name='Gary', last_name='Haas', age=1, department='Science', college='Blue',)
		self.session.add(gary)
		alan = Person(first_name='Alan', last_name='Turing', age=6, department='Math', college='White',)
		self.session.add(alan)

		# Set up query data

		offset = '0'
		results_per_page = '6'
		first_name = ''
		last_name = ''
		age = ''
		department = ''
		college = ''
		order_by = 'college'
		json_payload = { 'offset':offset, 'results_per_page':results_per_page, 'first_name':first_name, 'last_name':last_name, 'age':age, 'department':department, 'college':college, 'order_by': order_by }
		request = testing.DummyRequest(json_body=json_payload)
		response = self._callFUT(request)
		
		# Check results

		self.assertEqual(response['page_number'], 1)
		self.assertEqual(response['people'], [gary, brian, zach, chris, alan, amy])
		self.assertEqual(response['results_per_page'], 6)
		self.assertEqual(response['offset'], 0)
		self.assertEqual(response['total_pages'], 1)

	def test_get_page_filter_first_name(self):
		from mgo.models import Person

		# Set up test data

		chris = Person(first_name='Chris', last_name='Zoolander', age=2, department='Computer Science', college='Test',)
		self.session.add(chris)
		amy = Person(first_name='Amy', last_name='Wong', age=4, department='Science', college='Zoo',)
		self.session.add(amy)
		brian = Person(first_name='Brian', last_name='Xavier', age=3, department='Math', college='Green',)
		self.session.add(brian)
		zach = Person(first_name='Zach', last_name='Alexander', age=5, department='Computer Science', college='Red',)
		self.session.add(zach)
		gary = Person(first_name='Gary', last_name='Haas', age=1, department='Science', college='Blue',)
		self.session.add(gary)
		alan = Person(first_name='Alan', last_name='Turing', age=6, department='Math', college='White',)
		self.session.add(alan)

		# Set up query data

		offset = '0'
		results_per_page = '6'
		first_name = 'chris'
		last_name = ''
		age = ''
		department = ''
		college = ''
		order_by = ''
		json_payload = { 'offset':offset, 'results_per_page':results_per_page, 'first_name':first_name, 'last_name':last_name, 'age':age, 'department':department, 'college':college, 'order_by': order_by }
		request = testing.DummyRequest(json_body=json_payload)
		response = self._callFUT(request)
		
		# Check results

		self.assertEqual(response['page_number'], 1)
		self.assertEqual(response['people'], [chris])
		self.assertEqual(response['results_per_page'], 6)
		self.assertEqual(response['offset'], 0)
		self.assertEqual(response['total_pages'], 1)

	def test_get_page_filter_last_name(self):
		from mgo.models import Person

		# Set up test data

		chris = Person(first_name='Chris', last_name='Zoolander', age=2, department='Computer Science', college='Test',)
		self.session.add(chris)
		amy = Person(first_name='Amy', last_name='Wong', age=4, department='Science', college='Zoo',)
		self.session.add(amy)
		brian = Person(first_name='Brian', last_name='Xavier', age=3, department='Math', college='Green',)
		self.session.add(brian)
		zach = Person(first_name='Zach', last_name='Alexander', age=5, department='Computer Science', college='Red',)
		self.session.add(zach)
		gary = Person(first_name='Gary', last_name='Haas', age=1, department='Science', college='Blue',)
		self.session.add(gary)
		alan = Person(first_name='Alan', last_name='Turing', age=6, department='Math', college='White',)
		self.session.add(alan)

		# Set up query data

		offset = '0'
		results_per_page = '6'
		first_name = ''
		last_name = 'Alexander'
		age = ''
		department = ''
		college = ''
		order_by = ''
		json_payload = { 'offset':offset, 'results_per_page':results_per_page, 'first_name':first_name, 'last_name':last_name, 'age':age, 'department':department, 'college':college, 'order_by': order_by }
		request = testing.DummyRequest(json_body=json_payload)
		response = self._callFUT(request)
		
		# Check results

		self.assertEqual(response['page_number'], 1)
		self.assertEqual(response['people'], [zach])
		self.assertEqual(response['results_per_page'], 6)
		self.assertEqual(response['offset'], 0)
		self.assertEqual(response['total_pages'], 1)

	def test_get_page_filter_age(self):
		from mgo.models import Person

		# Set up test data

		chris = Person(first_name='Chris', last_name='Zoolander', age=2, department='Computer Science', college='Test',)
		self.session.add(chris)
		amy = Person(first_name='Amy', last_name='Wong', age=4, department='Science', college='Zoo',)
		self.session.add(amy)
		brian = Person(first_name='Brian', last_name='Xavier', age=3, department='Math', college='Green',)
		self.session.add(brian)
		zach = Person(first_name='Zach', last_name='Alexander', age=5, department='Computer Science', college='Red',)
		self.session.add(zach)
		gary = Person(first_name='Gary', last_name='Haas', age=1, department='Science', college='Blue',)
		self.session.add(gary)
		alan = Person(first_name='Alan', last_name='Turing', age=6, department='Math', college='White',)
		self.session.add(alan)

		# Set up query data

		offset = '0'
		results_per_page = '6'
		first_name = ''
		last_name = ''
		age = '3'
		department = ''
		college = ''
		order_by = ''
		json_payload = { 'offset':offset, 'results_per_page':results_per_page, 'first_name':first_name, 'last_name':last_name, 'age':age, 'department':department, 'college':college, 'order_by': order_by }
		request = testing.DummyRequest(json_body=json_payload)
		response = self._callFUT(request)
		
		# Check results

		self.assertEqual(response['page_number'], 1)
		self.assertEqual(response['people'], [brian])
		self.assertEqual(response['results_per_page'], 6)
		self.assertEqual(response['offset'], 0)
		self.assertEqual(response['total_pages'], 1)

	def test_get_page_filter_department(self):
		from mgo.models import Person

		# Set up test data

		chris = Person(first_name='Chris', last_name='Zoolander', age=2, department='Computer Science', college='Test',)
		self.session.add(chris)
		amy = Person(first_name='Amy', last_name='Wong', age=4, department='Science', college='Zoo',)
		self.session.add(amy)
		brian = Person(first_name='Brian', last_name='Xavier', age=3, department='Math', college='Green',)
		self.session.add(brian)
		zach = Person(first_name='Zach', last_name='Alexander', age=5, department='Computer Science', college='Red',)
		self.session.add(zach)
		gary = Person(first_name='Gary', last_name='Haas', age=1, department='Science', college='Blue',)
		self.session.add(gary)
		alan = Person(first_name='Alan', last_name='Turing', age=6, department='Math', college='White',)
		self.session.add(alan)

		# Set up query data

		offset = '0'
		results_per_page = '6'
		first_name = ''
		last_name = ''
		age = ''
		department = 'Math'
		college = ''
		order_by = ''
		json_payload = { 'offset':offset, 'results_per_page':results_per_page, 'first_name':first_name, 'last_name':last_name, 'age':age, 'department':department, 'college':college, 'order_by': order_by }
		request = testing.DummyRequest(json_body=json_payload)
		response = self._callFUT(request)
		
		# Check results

		self.assertEqual(response['page_number'], 1)
		self.assertEqual(response['people'], [alan, brian])
		self.assertEqual(response['results_per_page'], 6)
		self.assertEqual(response['offset'], 0)
		self.assertEqual(response['total_pages'], 1)

	def test_get_page_filter_college(self):
		from mgo.models import Person

		# Set up test data

		chris = Person(first_name='Chris', last_name='Zoolander', age=2, department='Computer Science', college='Test',)
		self.session.add(chris)
		amy = Person(first_name='Amy', last_name='Wong', age=4, department='Science', college='Zoo',)
		self.session.add(amy)
		brian = Person(first_name='Brian', last_name='Xavier', age=3, department='Math', college='Green',)
		self.session.add(brian)
		zach = Person(first_name='Zach', last_name='Alexander', age=5, department='Computer Science', college='Red',)
		self.session.add(zach)
		gary = Person(first_name='Gary', last_name='Haas', age=1, department='Science', college='Blue',)
		self.session.add(gary)
		alan = Person(first_name='Alan', last_name='Turing', age=6, department='Math', college='White',)
		self.session.add(alan)

		# Set up query data

		offset = '0'
		results_per_page = '6'
		first_name = ''
		last_name = ''
		age = ''
		department = ''
		college = 'zoo'
		order_by = ''
		json_payload = { 'offset':offset, 'results_per_page':results_per_page, 'first_name':first_name, 'last_name':last_name, 'age':age, 'department':department, 'college':college, 'order_by': order_by }
		request = testing.DummyRequest(json_body=json_payload)
		response = self._callFUT(request)
		
		# Check results

		self.assertEqual(response['page_number'], 1)
		self.assertEqual(response['people'], [amy])
		self.assertEqual(response['results_per_page'], 6)
		self.assertEqual(response['offset'], 0)
		self.assertEqual(response['total_pages'], 1)

	def test_get_page_invalid_filter_college(self):
		from mgo.models import Person

		# Set up test data

		chris = Person(first_name='Chris', last_name='Zoolander', age=2, department='Computer Science', college='Test',)
		self.session.add(chris)
		amy = Person(first_name='Amy', last_name='Wong', age=4, department='Science', college='Zoo',)
		self.session.add(amy)
		brian = Person(first_name='Brian', last_name='Xavier', age=3, department='Math', college='Green',)
		self.session.add(brian)
		zach = Person(first_name='Zach', last_name='Alexander', age=5, department='Computer Science', college='Red',)
		self.session.add(zach)
		gary = Person(first_name='Gary', last_name='Haas', age=1, department='Science', college='Blue',)
		self.session.add(gary)
		alan = Person(first_name='Alan', last_name='Turing', age=6, department='Math', college='White',)
		self.session.add(alan)

		# Set up query data

		offset = '0'
		results_per_page = '6'
		first_name = 'brian'
		last_name = ''
		age = ''
		department = ''
		college = 'zoo'
		order_by = ''
		json_payload = { 'offset':offset, 'results_per_page':results_per_page, 'first_name':first_name, 'last_name':last_name, 'age':age, 'department':department, 'college':college, 'order_by': order_by }
		request = testing.DummyRequest(json_body=json_payload)
		response = self._callFUT(request)
		
		# Check results

		self.assertEqual(response['page_number'], 1)
		self.assertEqual(response['people'], [])
		self.assertEqual(response['results_per_page'], 6)
		self.assertEqual(response['offset'], 0)
		self.assertEqual(response['total_pages'], 1)

class add_people_tests(unittest.TestCase):
	def setUp(self):
		self.session = _initTestingDB()
		self.config = testing.setUp()

	def tearDown(self):
		self.session.remove()
		testing.tearDown()

	def _callFUT(self, request):
		from mgo.views import add_person
		return add_person(request)

	def test_it_notsubmitted(self):
		_registerRoutes(self.config)
		request = testing.DummyRequest()
		info = self._callFUT(request)
		self.assertEqual(info['save_url'], 'http://example.com/people/add')

	def test_it_submitted(self):
		from mgo.models import Person
		_registerRoutes(self.config)
		request = testing.DummyRequest({'form.submitted':True,
										'first_name':'Test',
										'last_name':'Tester',
										'age':21,
										'department':'Computer Science',
										'college':'Engineering',
										})
		self._callFUT(request)
		person = self.session.query(Person).filter_by(first_name='Test').one()
		self.assertEqual(person.first_name, 'Test')
		self.assertEqual(person.last_name, 'Tester')
		self.assertEqual(person.age, 21)
		self.assertEqual(person.department, 'Computer Science')
		self.assertEqual(person.college, 'Engineering')

class generate_table_info_tests(unittest.TestCase):
	def setUp(self):
		self.session = _initTestingDB()
		self.config = testing.setUp()

	def tearDown(self):
		self.session.remove()
		testing.tearDown()

	def _callFUT(self, query, offset, results_per_page):
		from mgo.views import generate_table_info
		return generate_table_info(query, offset, results_per_page)

	def test_generate_table_info_empty_query(self):
		from mgo.models import Person
		query = self.session.query(Person)
		(page_number, total_pages, offset) = self._callFUT(query, 0, 1)
		self.assertEqual(1, page_number)
		self.assertEqual(1, total_pages)
		self.assertEqual(0, offset)

	def test_generate_table_info_one_query(self):
		from mgo.models import Person
		person = Person(first_name='Test', last_name='Tester', age=21, department='Computer Science', college='Engineering',)
		self.session.add(person)
		query = self.session.query(Person)
		(page_number, total_pages, offset) = self._callFUT(query, 0, 1)
		self.assertEqual(1, page_number)
		self.assertEqual(1, total_pages)
		self.assertEqual(0, offset)

	def test_generate_table_info_negative_offset(self):
		from mgo.models import Person
		person = Person(first_name='Test', last_name='Tester', age=21, department='Computer Science', college='Engineering',)
		self.session.add(person)
		query = self.session.query(Person)
		(page_number, total_pages, offset) = self._callFUT(query, -1, 1)
		self.assertEqual(1, page_number)
		self.assertEqual(1, total_pages)
		self.assertEqual(0, offset)

	def test_generate_table_info_negative_results_per_page(self):
		from mgo.models import Person
		person = Person(first_name='Test', last_name='Tester', age=21, department='Computer Science', college='Engineering',)
		self.session.add(person)
		query = self.session.query(Person)
		(page_number, total_pages, offset) = self._callFUT(query, 1, -1)
		self.assertEqual(1, page_number)
		self.assertEqual(1, total_pages)
		self.assertEqual(0, offset)

	def test_generate_table_info_negative_results_per_page_and_negative_offset(self):
		from mgo.models import Person
		person = Person(first_name='Test', last_name='Tester', age=21, department='Computer Science', college='Engineering',)
		self.session.add(person)
		query = self.session.query(Person)
		(page_number, total_pages, offset) = self._callFUT(query, -1, -1)
		self.assertEqual(1, page_number)
		self.assertEqual(1, total_pages)
		self.assertEqual(0, offset)

	def test_generate_table_info_multiple_pages(self):
		from mgo.models import Person
		person = Person(first_name='Test', last_name='Tester', age=21, department='Computer Science', college='Engineering',)
		self.session.add(person)
		person = Person(first_name='Test', last_name='Tester', age=21, department='Computer Science', college='Engineering',)
		self.session.add(person)
		query = self.session.query(Person)
		(page_number, total_pages, offset) = self._callFUT(query, 0, 1)
		self.assertEqual(1, page_number)
		self.assertEqual(2, total_pages)
		self.assertEqual(0, offset)

	def test_generate_table_info_multiple_pages_remainder(self):
		from mgo.models import Person
		person = Person(first_name='Test', last_name='Tester', age=21, department='Computer Science', college='Engineering',)
		self.session.add(person)
		person = Person(first_name='Test', last_name='Tester', age=21, department='Computer Science', college='Engineering',)
		self.session.add(person)
		person = Person(first_name='Test', last_name='Tester', age=21, department='Computer Science', college='Engineering',)
		self.session.add(person)
		query = self.session.query(Person)
		(page_number, total_pages, offset) = self._callFUT(query, 0, 2)
		self.assertEqual(1, page_number)
		self.assertEqual(2, total_pages)
		self.assertEqual(0, offset)

	def test_generate_table_info_multiple_pages_final_page(self):
		from mgo.models import Person
		person = Person(first_name='Test', last_name='Tester', age=21, department='Computer Science', college='Engineering',)
		self.session.add(person)
		person = Person(first_name='Test', last_name='Tester', age=21, department='Computer Science', college='Engineering',)
		self.session.add(person)
		person = Person(first_name='Test', last_name='Tester', age=21, department='Computer Science', college='Engineering',)
		self.session.add(person)
		person = Person(first_name='Test', last_name='Tester', age=21, department='Computer Science', college='Engineering',)
		self.session.add(person)
		query = self.session.query(Person)
		(page_number, total_pages, offset) = self._callFUT(query, 2, 2)
		self.assertEqual(2, page_number)
		self.assertEqual(2, total_pages)
		self.assertEqual(2, offset)

	def test_generate_table_info_offset_overflow(self):
		from mgo.models import Person
		person = Person(first_name='Test', last_name='Tester', age=21, department='Computer Science', college='Engineering',)
		self.session.add(person)
		person = Person(first_name='Test', last_name='Tester', age=21, department='Computer Science', college='Engineering',)
		self.session.add(person)
		person = Person(first_name='Test', last_name='Tester', age=21, department='Computer Science', college='Engineering',)
		self.session.add(person)
		person = Person(first_name='Test', last_name='Tester', age=21, department='Computer Science', college='Engineering',)
		self.session.add(person)
		query = self.session.query(Person)
		(page_number, total_pages, offset) = self._callFUT(query, 5, 2)
		self.assertEqual(1, page_number)
		self.assertEqual(2, total_pages)
		self.assertEqual(0, offset)

	def test_generate_table_info_backtrack(self):
		from mgo.models import Person
		person = Person(first_name='Test', last_name='Tester', age=21, department='Computer Science', college='Engineering',)
		self.session.add(person)
		person = Person(first_name='Test', last_name='Tester', age=21, department='Computer Science', college='Engineering',)
		self.session.add(person)
		person = Person(first_name='Test', last_name='Tester', age=21, department='Computer Science', college='Engineering',)
		self.session.add(person)
		person = Person(first_name='Test', last_name='Tester', age=21, department='Computer Science', college='Engineering',)
		self.session.add(person)
		query = self.session.query(Person)
		(page_number, total_pages, offset) = self._callFUT(query, 1, 2)
		self.assertEqual(1, page_number)
		self.assertEqual(2, total_pages)
		self.assertEqual(0, offset)

class delete_person_tests(unittest.TestCase):
	def setUp(self):
		self.session = _initTestingDB()
		self.config = testing.setUp()

	def tearDown(self):
		self.session.remove()
		testing.tearDown()

	def _callFUT(self, request):
		from mgo.views import delete_person
		return delete_person(request)

	def test_delete_person(self):
		from mgo.models import Person
		_registerRoutes(self.config)
		person = Person(first_name='Test', last_name='Tester', age=21, department='Computer Science', college='Engineering',)
		person2 = Person(first_name='Test2', last_name='Tester2', age=21, department='Computer Science', college='Engineering',)
		request = testing.DummyRequest()
		request.matchdict = {'user_id':1}
		self.session.add(person)
		self.session.add(person2)
		info = self._callFUT(request)
		personResult = self.session.query(Person).one()
		self.assertEqual(personResult, person2)

	def test_delete_person2(self):
		from mgo.models import Person
		_registerRoutes(self.config)
		person = Person(first_name='Test', last_name='Tester', age=21, department='Computer Science', college='Engineering',)
		request = testing.DummyRequest()
		request.matchdict = {'user_id':1}
		self.session.add(person)
		info = self._callFUT(request)
		personResult = self.session.query(Person)
		self.assertEqual(personResult.count(), 0)

class delete_people_tests(unittest.TestCase):
	def setUp(self):
		self.session = _initTestingDB()
		self.config = testing.setUp()

	def tearDown(self):
		self.session.remove()
		testing.tearDown()

	def _callFUT(self, request):
		from mgo.views import delete_all_people
		return delete_all_people(request)

	def test_delete_people(self):
		from mgo.models import Person
		_registerRoutes(self.config)
		person = Person(first_name='Test', last_name='Tester', age=21, department='Computer Science', college='Engineering',)
		person2 = Person(first_name='Test2', last_name='Tester2', age=21, department='Computer Science', college='Engineering',)
		request = testing.DummyRequest()
		self.session.add(person)
		self.session.add(person2)
		info = self._callFUT(request)
		personResult = self.session.query(Person)
		self.assertEqual(personResult.count(), 0)

#########################################################################################################
#
# File Tests
#
#########################################################################################################

class file_tests(unittest.TestCase):
	def setUp(self):
		self.session = _initTestingDB()
		self.config = testing.setUp()

	def tearDown(self):
		self.session.remove()
		testing.tearDown()

	def _callFUT(self, request):
		from mgo.views import file
		return file(request)

	def test_it_notsubmitted(self):
		_registerRoutes(self.config)
		request = testing.DummyRequest()
		info = self._callFUT(request)
		self.assertEqual(info['save_url'], 'http://example.com/file')


class sanitize_file_path_tests(unittest.TestCase):
	def setUp(self):
		self.session = _initTestingDB()
		self.config = testing.setUp()

	def tearDown(self):
		self.session.remove()
		testing.tearDown()

	def _callFUT(self, s):
		from mgo.views import sanitize_file_path
		return sanitize_file_path(s)

	def test_no_slash(self):
		string = 'Dogs'
		result = self._callFUT(string)
		self.assertEqual(result, 'Dogs')

	def test_left_slash(self):
		string = '/Dogs'
		result = self._callFUT(string)
		self.assertEqual(result, 'Dogs')

	def test_right_slash(self):
		string = 'Dogs/'
		result = self._callFUT(string)
		self.assertEqual(result, 'Dogs')

	def test_surrounded_slash(self):
		string = '/Dogs/'
		result = self._callFUT(string)
		self.assertEqual(result, 'Dogs')

	def test_left_middle_slash(self):
		string = '/Dogs/Cats'
		result = self._callFUT(string)
		self.assertEqual(result, 'Dogs/Cats')

	def test_right_middle_slash(self):
		string = 'Dogs/Cats/'
		result = self._callFUT(string)
		self.assertEqual(result, 'Dogs/Cats')

	def test_multiple_surrounded_slash(self):
		string = '/Dogs/Cats/'
		result = self._callFUT(string)
		self.assertEqual(result, 'Dogs/Cats')

class path_split_tests(unittest.TestCase):
	def setUp(self):
		self.session = _initTestingDB()
		self.config = testing.setUp()

	def tearDown(self):
		self.session.remove()
		testing.tearDown()

	def _callFUT(self, s):
		from mgo.views import path_split
		return path_split(s)

	def test_no_slash(self):
		string = 'Dogs'
		result = self._callFUT(string)
		self.assertEqual(result, ['Dogs'])

	def test_left_slash(self):
		string = '/Dogs'
		result = self._callFUT(string)
		self.assertEqual(result, ['Dogs'])

	def test_right_slash(self):
		string = 'Dogs/'
		result = self._callFUT(string)
		self.assertEqual(result, ['Dogs'])

	def test_surrounded_slash(self):
		string = '/Dogs/'
		result = self._callFUT(string)
		self.assertEqual(result, ['Dogs'])

	def test_left_middle_slash(self):
		string = '/Dogs/Cats'
		result = self._callFUT(string)
		self.assertEqual(result, ['Dogs','Cats'])

	def test_right_middle_slash(self):
		string = 'Dogs/Cats/'
		result = self._callFUT(string)
		self.assertEqual(result, ['Dogs','Cats'])

	def test_multiple_surrounded_slash(self):
		string = '/Dogs/Cats/'
		result = self._callFUT(string)
		self.assertEqual(result, ['Dogs','Cats'])

class format_path_tests(unittest.TestCase):
	def setUp(self):
		self.session = _initTestingDB()
		self.config = testing.setUp()

	def tearDown(self):
		self.session.remove()
		testing.tearDown()

	def _callFUT(self, s):
		from mgo.views import format_path
		return format_path(s)

	def test_no_element(self):
		list = []
		result = self._callFUT(list)
		self.assertEqual(result, '')

	def test_one_element(self):
		list = ['Dogs']
		result = self._callFUT(list)
		self.assertEqual(result, 'Dogs')

	def test_two_elements(self):
		list = ['Dogs', 'Cats']
		result = self._callFUT(list)
		self.assertEqual(result, 'Dogs/Cats')

	def test_three_elements(self):
		list = ['Dogs', 'Cats', 'Ferrets']
		result = self._callFUT(list)
		self.assertEqual(result, 'Dogs/Cats/Ferrets')

	def test_exception_leftmost(self):
		list = ['..', 'Dogs', 'Cats', 'Ferrets']
		result = self._callFUT(list)
		self.assertEqual(result, '')

	def test_exception_inner(self):
		list = ['Dogs', '..', 'Cats', 'Ferrets']
		result = self._callFUT(list)
		self.assertEqual(result, '')

	def test_exception_rightmost(self):
		list = ['Dogs', 'Cats', 'Ferrets', '..']
		result = self._callFUT(list)
		self.assertEqual(result, '')

#########################################################################################################
#
# Status Tests
#
#########################################################################################################

class freeze_to_dictionary_tests(unittest.TestCase):
	def setUp(self):
		self.config = testing.setUp()

	def tearDown(self):
		testing.tearDown()

	def _callFUT(self, path):
		from mgo.views import freeze_to_dictionary
		return freeze_to_dictionary(path)

	def test_freeze_to_dictionary_one_requirement(self):
		_registerRoutes(self.config)
		request = testing.DummyRequest()
		response = self._callFUT(os.path.dirname(__file__)+'/test_files/requirements1.txt')
		#We never logged in
		self.assertEqual(response, {'pyramid':'1.5.1'})

	def test_freeze_to_dictionary_multiple_requirements(self):
		_registerRoutes(self.config)
		request = testing.DummyRequest()
		response = self._callFUT(os.path.dirname(__file__)+'/test_files/requirements.txt')
		#We never logged in
		self.assertEqual(response, {'pyramid':'1.5.1', 'PasteDeploy':'1.5.2', 'translationstring':'1.1'})

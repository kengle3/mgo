from pyramid.config import Configurator
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy

from sqlalchemy import engine_from_config

from mgo.security import groupfinder

from .models import (
    DBSession,
    Base,
    )


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine

    authn_policy = AuthTktAuthenticationPolicy(
        'sosecret', callback=groupfinder, hashalg='sha512')
    authz_policy = ACLAuthorizationPolicy()
    
    config = Configurator(settings=settings,
                        root_factory='mgo.models.RootFactory')
    
    config.set_authentication_policy(authn_policy)
    config.set_authorization_policy(authz_policy)
    
    config.include('pyramid_jinja2')
    
    config.add_route('view_home', '/')

    # File Routes

    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_static_view('files', 'files', cache_max_age=3600)
    config.add_route('file_request','/file_request')
    config.add_route('file','/file')

    # Status Routes

    config.add_route('status','/status')
    config.add_route('status_highlight','/status_highlight')

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

    config.scan()
    
    return config.make_wsgi_app()

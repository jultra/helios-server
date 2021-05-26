"""
Utilities for all views

Ben Adida (12-30-2008)
"""

from django.template import Context, Template, loader, RequestContext
from django.http import HttpResponse, Http404
from django.shortcuts import render_to_response, render
from django.contrib.messages import get_messages

from helios_auth.security import get_user

import helios_auth

from django.conf import settings

##
## BASICS
##

SUCCESS = HttpResponse("SUCCESS")

##
## template abstraction
##

def prepare_vars(request, vars):
  vars_with_user = vars.copy()
  
  if request:
    vars_with_user['user'] = get_user(request)
    vars_with_user['csrf_token'] = request.session['csrf_token']
    vars_with_user['SECURE_URL_HOST'] = settings.SECURE_URL_HOST
    
  vars_with_user['STATIC'] = '/static/auth'
  vars_with_user['MEDIA_URL'] = '/static/auth/'
  vars_with_user['TEMPLATE_BASE'] = helios_auth.TEMPLATE_BASE
  
  vars_with_user['settings'] = settings
  
  return vars_with_user
  
def render_template(request, template_name, values = None):
 # t = loader.get_template(template_name + '.html')

  #messages = get_messages(request)
  
  vars_with_user = prepare_vars(request, values or {})
  
  return render(request, 'helios_auth/templates/%s.html' % template_name, context=vars_with_user)
  

def render_template_raw(request, template_name, values=None):
  t = loader.get_template(template_name + '.html')
  values = values or {}
  vars_with_user = prepare_vars(request, values)
  return t.render(context=vars_with_user, request=request)

def render_json(json_txt):
  return HttpResponse(json_txt)

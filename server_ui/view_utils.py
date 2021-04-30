"""
Utilities for single election views

Ben Adida (2009-07-18)
"""

from django.conf import settings
from django.shortcuts import render_to_response

from helios_auth.security import get_user


from helios.models import ElectionOfficer
##
## template abstraction
##
def render_template(request, template_name, values = None):
  vars_with_user = values.copy() if values is not None else {}
  vars_with_user['user'] = get_user(request)
  vars_with_user['settings'] = settings
  vars_with_user['CURRENT_URL'] = request.path
  
  if 'election' in values and get_user(request):
      try:
          vars_with_user['officer'] = ElectionOfficer.get_by_election_and_user(election=values['election'], user=get_user(request))
      except:
          pass
  
  # csrf protection
  if 'csrf_token' in request.session:
    vars_with_user['csrf_token'] = request.session['csrf_token']
  
  return render_to_response('server_ui/templates/%s.html' % template_name, vars_with_user)
  

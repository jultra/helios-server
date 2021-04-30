"""
Some basic utils 
(previously were in helios module, but making things less interdependent

2010-08-17
"""

#from django.utils import simplejson
import json

## JSON
def to_json(d):
  return json.dumps(d, sort_keys=True)
  
def from_json(value):
  if value == "" or value is None: 
    return None
  if isinstance(value, str):
    try:
      return json.loads(value)
    except Exception as e:
      raise Exception("value is not JSON parseable, that's bad news") from e
  return value
  
def JSONtoDict(json):
  x=from_json(json)
  return x
    
def JSONFiletoDict(filename):
  with open(filename, 'r') as f:
    content = f.read()
  return from_json(content)
    



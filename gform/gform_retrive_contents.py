from __future__ import print_function

from apiclient import discovery
from httplib2 import Http
from oauth2client import client, file, tools

SCOPES = "https://www.googleapis.com/auth/forms.body.readonly"
DISCOVERY_DOC = "https://forms.googleapis.com/$discovery/rest?version=v1"

store = file.Storage('google-api/token.json')
creds = None
if not creds or creds.invalid:
    flow = client.flow_from_clientsecrets('client_secrets.json', SCOPES)
    creds = tools.run_flow(flow, store)
service = discovery.build('forms', 'v1', http=creds.authorize(
    Http()), discoveryServiceUrl=DISCOVERY_DOC, static_discovery=False)

# Prints the title of the sample form:
form_id = '1gVzloVmNaciaH_GD3hxdoF-8lbkhditM5I3Rn4q1_Jg'
result = service.forms().get(formId=form_id).execute()
print(result)
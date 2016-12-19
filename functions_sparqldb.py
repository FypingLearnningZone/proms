import settings
import requests
import json


def query(sparql_query, format_mimetype='application/sparql-results+json'):
    """ Make a secure SPARQL query
    """
    auth = (settings.SPARQL_AUTH_USR, settings.SPARQL_AUTH_PWD)
    data = {'query': sparql_query}
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': format_mimetype
    }
    r = requests.post(settings.SPARQL_QUERY_URI, auth=auth, data=data, headers=headers)
    try:
        return json.loads(r.text)
    except Exception as e:
        raise


def query_turtle(sparql_query):
    """ Make a secure query in TURTLE format
    """
    data = {'query': sparql_query, 'format': 'text/turtle'}
    auth = (settings.SPARQL_AUTH_USR, settings.SPARQL_AUTH_PWD)
    headers = {'Accept': 'text/turtle'}
    r = requests.post(settings.SPARQL_QUERY_URI, data=data, auth=auth, headers=headers)
    try:
        return r.text
    except Exception as e:
        raise


def insert(g, named_graph_uri=None):
    """ Securely insert a named graph into the DB
    """
    if named_graph_uri:
        data = {'update': 'INSERT DATA { GRAPH <' + named_graph_uri + '> { ' + g.serialize(format='nt') + ' } }'}
    else:  # insert into default graph
        data = {'update': 'INSERT DATA { ' + g.serialize(format='nt') + ' }'}
    auth = (settings.SPARQL_AUTH_USR, settings.SPARQL_AUTH_PWD)
    headers = {'Accept': 'text/turtle'}
    try:
        r = requests.post(settings.SPARQL_UPDATE_URI, headers=headers, data=data, auth=auth)
        if r.status_code != 200 and r.status_code != 201:
            raise Exception('The INSERT was not successful. The SPARQL database\' error message is: ' + r.content)
        return True
    except Exception as e:
        raise

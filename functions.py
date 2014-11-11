import settings
import re
import json
import pyproms
import cStringIO
from rdflib import Graph
import requests
from rulesets import proms


def get_proms_html_header():
    html = requests.get('http://scikey.org/theme/template-header.inc').text

    nav = open(settings.HOME_DIR + settings.STATIC_DIR + 'nav.html', 'r').read()
    html = html.replace('<?php include $nav ?>', nav)
    html = re.sub(r'<title>(.*)</title>', '<title>PROMS: Provenance Management System</title>', html)
    style = '''
        <style>
            .lined {
                border: solid 2px black;
                border-collapse: collapse;

                font-family: Verdana;
                font-size: 12px;
            }
            .lined th,
            .lined td {
                border: solid 1px black;
                padding: 3px;
            }
        </style>
    </head>
    '''
    html = re.sub('</head>', style, html)

    return html


def get_proms_html_footer():
    html = requests.get('http://scikey.org/theme/template-footer.inc').text
    html = html.replace('This web page is maintained', 'This system\'s web page is maintained')

    return html


def submit_stardog_query(query):
    url = settings.PROMS_DB_URI
    qsa = {'query': query}
    h = {'accept': 'application/sparql-results+json'}
    r = requests.get(url, params=qsa, headers=h, auth=('proms', 'proms'))

    if r.status_code == 200:
        return [True, r.text]
    else:
        return [False, 'ERROR: ' + r.text]


def get_reports():
    query = '''
                PREFIX dc: <http://purl.org/dc/elements/1.1/>
                SELECT DISTINCT ?s ?t
                WHERE {
                  ?s a proms:Report .
                  ?s dc:title ?t .
                }
                ORDER BY ?s
            '''
    return submit_stardog_query(query)


def get_reports_html(sparql_query_results_json):
    reports = json.loads(sparql_query_results_json)
    l = '<ul>'
    for report in reports['results']['bindings']:
        l += '<li><a href="' + str(report['s']['value']) + '">' + str(report['t']['value']) + '</a> (' + str(report['s']['value']) + ')</li>'
    l += '</ul>'

    return l


def put_report(report_in_turtle):
    #try to make a graph of the input text
    g = Graph()
    try:
        g.parse(cStringIO.StringIO(report_in_turtle), format="n3")
    except Exception as e:
        return [False, ['Could not parse input: ' + str(e)]]

    #conformance
    conf_results = proms.Proms(g).get_result()
    if conf_results['rule_results'][0]['passed']:
        #passed conformance so sent to DB
        #put data into a SPARQL 1.1 INSERT DATA query
        insert_query = 'INSERT DATA {' + g.serialize(format='n3') + '}'

        #insert into Stardog using the HTTP API
        url = 'http://localhost:5820/proms/update'
        h = {'content-type': 'application/sparql-update'}
        r = requests.post(url, data=insert_query, headers=h, auth=('proms', 'proms'))

        if r.status_code == 200:
            return [True]
        else:
            return [False, r.text]
    else:
        return [False, conf_results['rule_results'][0]['fail_reasons']]


def get_report(report_uri):
    #get the report metadata from DB
    query = '''
        SELECT DISTINCT ?s ?t ?sat ?eat ?job ?u
        WHERE {
          ?s a proms:Report .
          ?s dc:title ?t .
          ?s prov:startedAtTime ?sat .
          ?s prov:endedAtTime ?eat .
          ?s proms:jobId ?job .
        }
        ORDER BY ?s
    '''
    results = submit_stardog_query(query)

    return results['t']


def get_entities():
    query = '''
                PREFIX dc: <http://purl.org/dc/elements/1.1/>
                SELECT DISTINCT ?s ?t
                WHERE {
                  ?s a prov:Activity .
                  ?s dc:title ?t .
                }
                ORDER BY ?s
            '''
    return submit_stardog_query(query)


def get_entities_html(sparql_query_results_json):
    reports = json.loads(sparql_query_results_json)
    l = '<ul>'
    for report in reports['results']['bindings']:
        l += '<li><a href="' + str(report['s']['value']) + '">' + str(report['t']['value']) + '</a> (' + str(report['s']['value']) + ')</li>'
    l += '</ul>'

    return l


def get_activities():
    query = '''
                PREFIX dc: <http://purl.org/dc/elements/1.1/>
                SELECT DISTINCT ?s ?t
                WHERE {
                  ?s a prov:Activity .
                  ?s dc:title ?t .
                }
                ORDER BY ?s
            '''
    return submit_stardog_query(query)


def get_activities_html(sparql_query_results_json):
    reports = json.loads(sparql_query_results_json)
    l = '<ul>'
    for report in reports['results']['bindings']:
        l += '<li><a href="' + str(report['s']['value']) + '">' + str(report['t']['value']) + '</a> (' + str(report['s']['value']) + ')</li>'
    l += '</ul>'

    return l
import os
import requests
import settings
import database  # must have PROMS Server & DB running


def purge_db():
    u = 'DELETE WHERE {GRAPH ?g { ?s ?p ?o }}'
    database.update(u)


def load_rs():
    # load the example ReportingSystem, System 01
    r = requests.post(
        settings.BASE_URI + '/function/lodge-reportingsystem',
        data=open(os.path.join(settings.HOME_DIR, 'tests', 'example_data_rs_01.ttl')).read(),
        headers={'Content-Type': 'text/turtle'}
    )
    assert r.status_code == 201


def load_reports():
    # load 4 Reports for System 01
    r = requests.post(
        settings.BASE_URI + '/function/lodge-report',
        data=open(os.path.join(settings.HOME_DIR, 'tests', 'example_data_rs_01_report_01.ttl')).read(),
        headers={'Content-Type': 'text/turtle'}
    )
    assert r.status_code == 201

    r = requests.post(
        settings.BASE_URI + '/function/lodge-report',
        data=open(os.path.join(settings.HOME_DIR, 'tests', 'example_data_rs_01_report_02.ttl')).read(),
        headers={'Content-Type': 'text/turtle'}
    )
    assert r.status_code == 201

    r = requests.post(
        settings.BASE_URI + '/function/lodge-report',
        data=open(os.path.join(settings.HOME_DIR, 'tests', 'example_data_rs_01_report_03.ttl')).read(),
        headers={'Content-Type': 'text/turtle'}
    )
    assert r.status_code == 201

    r = requests.post(
        settings.BASE_URI + '/function/lodge-report',
        data=open(os.path.join(settings.HOME_DIR, 'tests', 'example_data_rs_01_report_04.ttl')).read(),
        headers={'Content-Type': 'text/turtle'}
    )
    assert r.status_code == 201


def test_example_data_rs_html():
    # get the HTML
    r = requests.get(
        '%(BASE_URI)s/register?_uri=%(quoted_uri)s'
        % {'BASE_URI': settings.BASE_URI, 'quoted_uri': 'http%3A%2F%2Fpromsns.org%2Fdef%2Fproms%23ReportingSystem'})
    html = r.content
    assert '<li><a href="/instance?_uri=http://pid.geoscience.gov.au/system/system-01">System 01</a></li>' in html


def test_example_data_rs_rdf():
    # get the RDFin turtle
    r = requests.get(
        '%(BASE_URI)s/register?_uri=%(quoted_uri)s&_format=text/turtle'
        % {'BASE_URI': settings.BASE_URI, 'quoted_uri': 'http%3A%2F%2Fpromsns.org%2Fdef%2Fproms%23ReportingSystem'})
    html = r.content
    # fragile test as using formatted RDF, not logical RDF
    assert '<http://pid.geoscience.gov.au/system/system-01> a <http://promsns.org/def/proms#ReportingSystem> ;' in html


if __name__ == '__main__':
    # start afresh
    purge_db()

    # load the example data (which are a type of test of course!)
    load_rs()
    load_reports()

    # run tests
    test_example_data_rs_html()
    test_example_data_rs_rdf()

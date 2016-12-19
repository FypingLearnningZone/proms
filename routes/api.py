from requests.exceptions import ConnectionError
import json
from flask import Blueprint, Response, request, render_template
import functions_reports
import functions_reportingsystems
import functions_pingbacks
import functions_agents
import functions_entities
import functions_sparqldb
import api_functions
import settings
from ldapi import LDAPI
api = Blueprint('api', __name__)


# TODO: this is a stub
@api.route('/function/lodge-reportingsystem', methods=['POST'])
def lodge_reportingsystem():
    # only accept RDF documents
    acceptable_mimes = [x[0] for x in LDAPI.MIMETYPES_PARSERS]
    ct = request.content_type
    if ct not in acceptable_mimes:
        return 'The ReportingSystem posted is not encoded with a valid RDF Content-Type. Must be one of: ' + \
               ', '.join(acceptable_mimes) + '.', 400

    # validate ReportingSystem
    sr = functions_reportingsystems.ReportingSystemsFunctions(request.data, request.content_type)
    if not sr.valid():
        return 'The ReportingSystem posted is not valid for the following reasons: ' + \
               ', '.join(sr.error_messages) + '.', 400

    # get the ReportingSystem's URI
    sr.determine_reportingsystem_uri()

    # store the ReportingSystem
    if not sr.stored():
        return 'ReportingSystem posted is valid but cannot be stored for the following reasons: ' + \
               ', '.join(sr.error_messages) + '.', 500

    # reply to sender
    return sr.reportingsystem_uri, 201


@api.route('/function/create-reportingsystem')
def create_reportingsystem():
    try:
        agents = functions_agents.get_agents_dict()
    except ConnectionError:
        return render_template('error_db_connection.html'), 500
    return render_template(
        'function_create_reportingsystem.html',
        agents=agents,
        web_subfolder=settings.WEB_SUBFOLDER
    )


@api.route('/function/lodge-report', methods=['POST'])
def lodge_report():
    # only accept RDF documents
    acceptable_mimes = [x[0] for x in LDAPI.MIMETYPES_PARSERS]
    ct = request.content_type
    if ct not in acceptable_mimes:
        return 'The Report posted is not encoded with a valid RDF Content-Type. Must be one of: ' + \
               ', '.join(acceptable_mimes) + '.', 400

    # validate Report
    sr = functions_reports.ReportsFunctions(request.data, request.content_type)
    if not sr.valid():
        return 'The Report posted is not valid for the following reasons: ' + ', '.join(sr.error_messages) + '.', 400

    # get the Report's URI
    sr.determine_report_uri()

    # store the Report
    if not sr.stored():
        return 'Report posted is valid but cannot be stored for the following reasons: ' + \
               ', '.join(sr.error_messages) + '.', 500

    # reply to sender
    return sr.report_uri, 201


@api.route('/function/create-report')
def create_report():
    try:
        reportingsystems = functions_reportingsystems.get_reportingsystems_dict()
        agents = functions_agents.get_agents_dict()
        entities = functions_entities.get_entities_dict()
    except ConnectionError:
        return render_template('error_db_connection.html'), 500

    return render_template(
        'function_create_report.html',
        agents=agents,
        entities=entities,
        reportingsystems=reportingsystems,
        web_subfolder=settings.WEB_SUBFOLDER
    )


@api.route('/function/lodge_pingback', methods=['POST'])
def lodge_pingback():
    # only valid Pingback Cotent-Types
    acceptable_mimes = [x[0] for x in LDAPI.MIMETYPES_PARSERS]  # TODO: change
    ct = request.content_type
    if ct not in acceptable_mimes:
        return 'The Pingback posted is not encoded with a valid Content-Type. Must be one of: ' + \
               ', '.join(acceptable_mimes) + '.', 400

    # validate Pingback
    p = functions_pingbacks.PingbacksFunctions(request.data, request.headers)
    if not p.valid():
        return \
            'The Pingback posted is not valid for the following reasons: ' + ', '\
            .join(p.error_messages) + '.', 400

    # store the Pingback
    if not p.stored():
        return \
            'Report posted is valid but cannot be stored for the following reasons: , '\
            .join(p.error_messages) + '.', 500

    # reply to sender
    return 204


# @api.route('/function/pingback', methods=['POST'])
# def pingback():
#     """
#     React to incoming pingback messages
#
#     :return: 204 if PROV-AQ successful, 201 if PROMS successfull, else 400 or 500 + msg
#     """
#     import pingbacks.handle_incoming.hi_functions as hi
#
#     # work out if it's a PROV-AQ message or a PROMS message
#     if hi.is_provaq_msg(request):
#         insert = hi.register_provaq_pingback(request)
#         if insert[0]:
#             return Response('', status=204)
#         else:
#             return Response('PROV-AQ pingback message not handled. ' + insert[1],
#                             status=400,
#                             mimetype='text/plain')
#     elif hi.is_proms_msg(hi.register_provaq_pingback(request)):
#         insert = hi.register_proms_pingback(request)
#         if insert[0]:
#             return Response('Created ' + insert[1] + ' triples.', status=201)
#         else:
#             return Response('PROMS pingback message not handled. ' + insert[1],
#                             status=400,
#                             mimetype='text/plain')
#     else:
#         # message not understood
#         return 'Pingback message not understood. Not recognised as PROV-AQ or PROMS msg.', 400
#
#     pingback_result = functions.register_pingback(request.data)
#     if pingback_result[0]:
#         return Response('OK', status=200)
#     else:
#         return pingback_result[1], 400


# TODO: tidy up with templates, inc. error_db_connection
@api.route('/function/sparql', methods=['GET', 'POST'])
def sparql():
    # Query submitted
    if request.method == 'POST':
        '''
        Pass on the SPARQL query to the underlying system PROMS is using (Fuseki etc.)
        '''
        if request.content_type == 'application/x-www-form-urlencoded':
            '''
            https://www.w3.org/TR/2013/REC-sparql11-protocol-20130321/#query-via-post-urlencoded

            2.1.2 query via POST with URL-encoded parameters

            Protocol clients may send protocol requests via the HTTP POST method by URL encoding the parameters. When
            using this method, clients must URL percent encode all parameters and include them as parameters within the
            request body via the application/x-www-form-urlencoded media type with the name given above. Parameters must
            be separated with the ampersand (&) character. Clients may include the parameters in any order. The content
            type header of the HTTP request must be set to application/x-www-form-urlencoded.
            '''
            if request.form.get('query') is None:
                return 'Your POST request to PROMS\' SPARQL endpoint must contain a \'query\' parameter if form ' \
                       'posting is used.', 400
            else:
                query = request.form.get('query')
        elif request.content_type == 'application/sparql-query':
            '''
            https://www.w3.org/TR/2013/REC-sparql11-protocol-20130321/#query-via-post-direct

            2.1.3 query via POST directly

            Protocol clients may send protocol requests via the HTTP POST method by including the query directly and
            unencoded as the HTTP request message body. When using this approach, clients must include the SPARQL query
            string, unencoded, and nothing else as the message body of the request. Clients must set the content type
            header of the HTTP request to application/sparql-query. Clients may include the optional default-graph-uri
            and named-graph-uri parameters as HTTP query string parameters in the request URI. Note that UTF-8 is the
            only valid charset here.
            '''
            query = request.data  # get the raw request
            if query is None:
                return 'Your POST request to PROMS\' SPARQL endpoint must contain the query in plain text in the ' \
                       'POST body if the Content-Type \'application/sparql-query\' is used.', 400

        # sorry, we only return JSON results. See the service description!
        query_result = functions_sparqldb.query(query)

        if query_result and 'results' in query_result:
            query_result = json.dumps(query_result['results']['bindings'])
        else:
            query_result = json.dumps(query_result)

        # resond to a form or with a raw result
        if 'form' in request.values and request.values['form'].lower() == 'true':
            return render_template(
                'function_sparql.html',
                query=query,
                query_result=query_result,
                web_subfolder=settings.WEB_SUBFOLDER)
        else:
            return Response(json.dumps(query_result), status=200, mimetype="application/sparql-results+json")
    # No query, display form
    else:  # GET
        if request.args.get('query') is not None:
            # SPARQL GET request
            '''
            https://www.w3.org/TR/2013/REC-sparql11-protocol-20130321/#query-via-get

            2.1.1 query via GET

            Protocol clients may send protocol requests via the HTTP GET method. When using the GET method, clients must
            URL percent encode all parameters and include them as query parameter strings with the names given above.

            HTTP query string parameters must be separated with the ampersand (&) character. Clients may include the
            query string parameters in any order.

            The HTTP request MUST NOT include a message body.
            '''
            # following check invalid due to higher order if/else
            # if request.args.get('query') is None:
            #     return Response(
            #         'Your GET request to PROMS\' SPARQL endpoint must contain a \'query\' query string argument.',
            #         status=400,
            #         mimetype="text/plain")
            query = request.args.get('query')
            query_result = functions_sparqldb.query(query)
            return Response(json.dumps(query_result), status=200, mimetype="application/sparql-results+json")
        else:
            # SPARQL Service Description
            '''
            https://www.w3.org/TR/sparql11-service-description/#accessing

            SPARQL services made available via the SPARQL Protocol should return a service description document at the
            service endpoint when dereferenced using the HTTP GET operation without any query parameter strings
            provided. This service description must be made available in an RDF serialization, may be embedded in
            (X)HTML by way of RDFa, and should use content negotiation if available in other RDF representations.
            '''

            acceptable_mimes = [x[0] for x in LDAPI.MIMETYPES_PARSERS] + ['text/html']
            best = request.accept_mimetypes.best_match(acceptable_mimes)
            if best == 'text/html':
                # show the SPARQL query form
                query = request.args.get('query')
                return render_template(
                    'function_sparql.html',
                    query=query,
                    web_subfolder=settings.WEB_SUBFOLDER)
            elif best is not None:
                return Response(
                    api_functions.get_sparql_service_description(
                        [item for item in LDAPI.MIMETYPES_PARSERS if item[0] == best]
                    ),
                    status=200,
                    mimetype=best)
            else:
                return 'Accept header must be one of ' + ', '.join(acceptable_mimes) + '.', 400


# @api.route('/function/create-report-formparts', methods=['POST'])
# def create_report_formparts(form_parts):
#     return Response(functions_reports.create_report_formparts(form_parts), status=200, mimetype='text/plain')



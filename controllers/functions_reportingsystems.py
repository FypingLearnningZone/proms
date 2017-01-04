import cStringIO
import uuid
from rdflib import Graph
import api_functions
import settings
from database import sparqlqueries
from modules import rulesets as reportingsystem_ruleset
from modules.ldapi import LDAPI


class IncomingReportingSystem:
    def __init__(self, reportingsystem_data, reportingsystem_mimetype):
        self.reportingsystem_data = reportingsystem_data
        self.reportingsystem_mimetype = reportingsystem_mimetype
        self.reportingsystem_graph = None
        self.error_messages = None
        self.reportingsystem_uri = None

    def valid(self):
        """Validates an incoming ReportingSystem using direct tests (can it be parsed?) and appropriate RuleSets"""
        # try to parse the Reportingsystem data
        try:
            self.reportingsystem_graph = Graph().parse(
                cStringIO.StringIO(self.reportingsystem_data),
                format=[item[1] for item in LDAPI.MIMETYPES_PARSERS if item[0] == self.reportingsystem_mimetype][0]
            )
        except Exception, e:
            self.error_messages = ['The serialised data cannot be parsed. Is it valid RDF?',
                                   'Parser says: ' + e.message]
            return False

        # RuleSet
        conformant_report = reportingsystem_ruleset.ReportingSytems(self.reportingsystem_graph)

        if not conformant_report.passed:
            self.error_messages = conformant_report.fail_reasons
            return False

        # if the Report has been parsed, we have found the Report type and it's passed it's relevant RuleSet, it's valid
        return True

    def determine_reportingsystem_uri(self):
        """Determines the URI for this ReportingSystem"""
        # if this ReportingSystem has a placeholder URI, find it and replace it with one generated by PROMS Server
        q = '''
            SELECT ?uri
            WHERE {
                ?uri a <http://promsns.org/def/proms#ReportingSystem> .
                FILTER regex(str(?uri), "placeholder")
            }
        '''
        uri = None
        for r in self.reportingsystem_graph.query(q):
            uri = r['uri']

        if uri is not None:
            self._generate_new_uri(uri)
        else:
            # since it has an existing URI, not a placeholder one, use the existing one
            q = '''
                SELECT ?uri
                WHERE {
                    ?uri a <http://promsns.org/def/proms#ReportingSystem> .
                }
            '''
            for r in self.reportingsystem_graph.query(q):
                self.reportingsystem_uri = r['uri']

        return True

    def _generate_new_uri(self, old_uri):
        # ask PROMS Server for a new RS URI
        new_uri = settings.REPORTINGSYSTEM_BASE_URI + str(uuid.uuid4())
        self.reportingsystem_uri = new_uri
        # add that new URI to the in-memory graph
        api_functions.replace_uri(self.reportingsystem_graph, old_uri, new_uri)

    def stored(self):
        """ Add a ReportingSystem to PROMS"""
        try:
            sparqlqueries.insert(self.reportingsystem_graph, self.reportingsystem_uri)
            return True
        except Exception as e:
            self.error_messages = ['Could not connect to the provenance database']
            return False

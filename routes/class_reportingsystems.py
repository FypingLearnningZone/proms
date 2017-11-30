from .class_incoming import IncomingClass
import io
import uuid
from rdflib import Graph, Namespace, URIRef, Literal, RDF, XSD
import settings
from modules import rulesets as reportingsystem_ruleset
from modules.ldapi import LDAPI
from datetime import datetime


class IncomingReportingSystem(IncomingClass):
    def __init__(self, request):
        IncomingClass.__init__(self, request)

        self._generate_named_graph_uri()

    def valid(self):
        """Validates an incoming ReportingSystem using direct tests (can it be parsed?) and appropriate RuleSets"""
        # try to parse the Reportingsystem data
        try:
            self.graph = Graph().parse(
                io.StringIO(self.request.data),
                format=[item[1] for item in LDAPI.MIMETYPES_PARSERS if item[0] == self.request.mimetype][0]
            )
        except Exception as e:
            self.error_messages = ['The serialised data cannot be parsed. Is it valid RDF?',
                                   'Parser says: ' + e.message]
            return False

        # RuleSet
        conformant_report = reportingsystem_ruleset.ReportingSytems(self.graph)

        if not conformant_report.passed:
            self.error_messages = conformant_report.fail_reasons
            return False

        # if the Report has been parsed, we have found the Report type and it's passed it's relevant RuleSet, it's valid
        return True

    def determine_uri(self):
        """Determines the URI for this ReportingSystem"""
        # TODO: replace these two SPARQL queries with one, use the inverse of the "placeholder" find
        # if this ReportingSystem has a placeholder URI, find it and replace it with one generated by PROMS Server
        q = '''
            SELECT ?uri
            WHERE {
                ?uri a <http://promsns.org/def/proms#ReportingSystem> .
                FILTER regex(str(?uri), "placeholder")
            }
        '''
        uri = None
        for r in self.graph.query(q):
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
            for r in self.graph.query(q):
                self.uri = r['uri']

        return True

    def _generate_new_uri(self, old_uri):
        # ask PROMS Server for a new RS URI
        new_uri = settings.REPORTINGSYSTEM_BASE_URI + str(uuid.uuid4())
        self.uri = new_uri
        # add that new URI to the in-memory graph
        api_functions.replace_uri(self.graph, old_uri, new_uri)

    def _generate_named_graph_uri(self):
        self.named_graph_uri = settings.REPORTINGSYSTEM_NAMED_GRAPH_BASE_URI + str(uuid.uuid4())

    def generate_named_graph_metadata(self):
        PROV = Namespace('http://www.w3.org/ns/prov#')
        self.graph.bind('prov', PROV)

        PROMS = Namespace('http://promsns.org/def/proms#')
        self.graph.bind('proms', PROMS)

        DCT = Namespace('http://purl.org/dc/terms/')
        self.graph.bind('dct', DCT)

        # what the type of thing this Named Graph is
        self.graph.add((
            URIRef(self.named_graph_uri),
            RDF.type,
            PROMS.ReportingSystemNamedGraph
        ))

        # ... the date this ReportingSystem was sent to this PROMS Server
        self.graph.add((
            URIRef(self.named_graph_uri),
            DCT.dateSubmitted,
            Literal(datetime.now().isoformat(), datatype=XSD.dateTime)
        ))

        # ... who contributed this ReportingSystem
        self.graph.add((
            URIRef(self.named_graph_uri),
            DCT.contributor,
            URIRef(self.request.remote_addr)
        ))

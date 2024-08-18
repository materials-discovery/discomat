import copy
import uuid, datetime
from collections import defaultdict
from urllib.parse import urlparse, urldefrag, urlsplit
from rdflib import Dataset, Graph, URIRef, Literal, RDF, RDFS
from rdflib.namespace import DC, DCTERMS, PROV, XSD
from rdflib import Namespace
from discomat.cuds.utils import mnemonic_label
from discomat.ontology.namespaces import CUDS, MIO
from discomat.cuds.cuds import Cuds
# from discomat.cuds.session_manager import SessionManager
from discomat.cuds.engine import Engine, rdflib_engine
from pyvis.network import Network
from IPython.display import display, HTML

from abc import ABC, abstractmethod

import os, sys, warnings, pickle

from types import MappingProxyType
from typing import Union


class Session(Cuds):
    """
    Open a session, which by default uses the default local engine (its just easier way for us to handle the
    dataset of rdflib essentially).
    """
    def __init__(self,
                 iri: Union[str, URIRef] = None,
                 pid: Union[str, URIRef] = None,
                 description: str = None,
                 label: str = None,
                 engine: 'Engine' = None
                 ):
        ontology_type = CUDS.Session
        description = description or f"Session: No Description provided, dont be lazy.."
        super().__init__(iri, pid, ontology_type, description, label)

        self.engine = engine or rdflib_engine() # fixme
        self.add(CUDS.engine, self.engine)

        # new relationship, should be added and tracked. fixme: use the __set and __get attr methods to automanage.
        self.session_id = self.uuid
        self.add(CUDS.sessionId, self.session_id)

        self.is_open = False
        self.add(CUDS.sessionStatus, self.is_open)


        # self.session_manager = SessionManager()  # fixme: move the definition of SessionManager before Session.
        # self.session_manager.register(self)  # pass self to session manager

        # we need to define the graphs managed by the session, these are managed by the engire.
        # dict of all graphs.
        self._session_graphs = {}
        # Note: for q in d.quads((None, None, None, URIRef('urn:x-rdflib:default'))):
        #     print(q)

    def create_graph(self, graph_id):
        """
            Note: Session Graphs are not to be confused with teh _graph of a CUDS object,
            session graphs are entire knowledge graphs and not those that have only direct relations
            with one main root subject. Cuds objects (and triplets) live in these Graphs.
        """
        return self.engine.create_graph(graph_id)

    def graph(self, graph_id):
        return self.create_graph(graph_id)

    def remove_graph(self, graph_id):
        return self.engine.remove_graph(graph_id)

    def __iter__(self):
        return iter(self.engine)

    def quads(self, s=None, p=None, o=None, g=None):
        return self.engine.quads(s,p,o,g)

    def triples(self, s=None, p=None, o=None, g=None):
        return self.engine.quads(s,p,o,g)

    def list_graphs(self):
        # return a list of all graphs (graph_id's)
        for g in self.engine.graphs:
            print(g)

    def graphs(self):
        return self.engine.graphs

    def query(self, query=None):
        """
        sparql query
        ecample:


        query = \"""
            SELECT ?s ?p ?o
        WHERE {
        GRAPH <http://example.org/graph1> {
         ?s ?p ?o .
              }
            }
            \"""


        """
        if query is None:
            query = """
                    SELECT ?s ?p ?o
                    WHERE {
                    ?s ?p ?o .
                    }
                    """
        # by default, all the graphs are queried (Conjuctive) unless a graph is specified.
        return self.engine.query(query)

    def add_triple (self, s=None, p=None, o=None):
        # added None as python does not allow no default following default
        # if not any([s, p, o]):  # or use all() for all not None, not sure...
        #     raise ValueError("s, p, and o are all None, at least one should be not None")
        # print(f"need to check provenance...")
        self.engine.add_triple(s, p, o)

    def add_quad (self, s=None, p=None, o=None, g_id=None):
        # added None as python does not allow no default following default
        # if not any([s, p, o]):  # or use all() for all not None, not sure...
        #     raise ValueError("s, p, and o are all None, at least one should be not None")
        # print(f"need to check provenance...")
        self.engine.add_quad(s, p, o, gid)
    def remove_triple (self, s=None, p=None, o=None ):
        if not any([s, p, o]):  # or use all() for all not None, not sure...
            raise ValueError("s, p, and o are all None, at least one should be not None")
        self.engine.remove_triple(s, p, o)  # need to add provenance...

    def remove_quad (self, s=None, p=None, o=None, g_id=None ):
        if not any([s, p, o]):  # or use all() for all not None, not sure...
            raise ValueError("s, p, and o are all None, at least one should be not None")
        self.engine.remove_quad(s, p, o, g_id)  # need to add provenance...

    def get_cuds(self, iri):
        """
        given an iri or the Cuds, search the session, i.e., all graphs for the
        properties needed for this Cuds.
        A Cuds is an iri with all direct relations including the basic ones (uuid, pid, etc).
        if A cuds cannot be built, create one using any partial information available
        """
        return NotImplemented

    def add_cuds(self, cuds):
        """add the cuds to the session, optionally specifying the graph.  """
        return NotImplemented

    def search_cuds(self, cuds):
        """ search for the CUDS, find if it is in the system using the iri of the CUDS
        could be replaced by smart __contains__ method, that based on the type of element queried, activates various
        methods. could be as simple as calling the engine with cuds iri on all graphs. """

        return NotImplemented

    def get_cuds_region(self, cuds, radiud):
        """        get the cuds up to a specific radius
        could be same as get_cuds but with optional radius, see ontology manager etc for implementations.

        """

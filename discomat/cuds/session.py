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
#from discomat.cuds.session_manager import SessionManager

from pyvis.network import Network
from IPython.display import display, HTML

from abc import ABC, abstractmethod

import os, sys, warnings, pickle

from types import MappingProxyType
from typing import Union


class Session(Cuds):
    """

    Open a session, which by default uses the default local engine.

    """

    def __init__(self,
                 iri: Union[str, URIRef] = None,
                 pid: Union[str, URIRef] = None,
                 description: str = None,
                 label: str = None,
                 engine: 'Engine' = None
                 ):
        ontology_type = CUDS.Session
        self.engine =  engine or None  #  this is always a local engine.
        self.description = description or f"Session: No Description provided, dont be lazy.."
        self.label = label or mnemonic_label(2)
        super().__init__(iri, pid, ontology_type, self.description, self.label)
        self.session_id = self.uuid
        self.engine = 'No Engine Implemented Yet'
        # self.engine = engine or LocalEngine(
        #         description=f"local engine defined as default for session {self.session_id}",
        #         label = f"LocalEngine")
        self.is_open = False

        # self.session_manager = SessionManager()  # fixme: move the definition of SessionManager before Session.
        # self.session_manager.register(self)  # pass self to session manager

    def create_graph(self, graph_id):
        # here by default, graph_id is required.
        print(f"should register the graph in the session manager and add it to provenance? or at least mark provenance")
        return self.engine.create_graph(graph_id)

    def delete_graph(self, graph_id):
        print(f"should de-register the graph in the session manager and add it to provenance")
        return self.engine.delete_graph(graph_id)

    def list_graphs(self):
        # return a list of all graphs (graph_id's)
        return self.engine.list_graphs()

    def query_graph(self, graph_id=None, query=None):
        if query is None:
            raise ValueError("query must not be None")
        # by default, the default graph is queried
        return self.engine.query_graph(graph_id, query)

    def add_triple(self, graph_id=None, s=None, p=None, o=None):
        # added None as python does not allow no default following default
        if not any([s, p, o]):  # or use all() for all not None, not sure...
            raise ValueError("s, p, and o are all None, at least one should be not None")
        print(f"need to check provenance...")
        self.engine.add_triple(graph_id, s, p, o)

    def remove_triple(self, graph_id=None, s=None, p=None, o=None):
        if not any([s, p, o]):  # or use all() for all not None, not sure...
            raise ValueError("s, p, and o are all None, at least one should be not None")
        self.engine.remove_triple(graph_id, s, p, o)  # need to add provenance...

    def get_cuds(self, iri):
        """
        given an iri or the Cuds, search the session, i.e., all graphs for the
        properties needed for this Cuds.

        A Cuds is an iri with all direct relations including the basic ones (uuid, pid, etc).

        if A cuds cannot be built, create one using any partial information available.


        """
        return NotImplemented

    def add_cuds(self, cuds):
        """add the cuds to the session, optionally specifying the graph.  """

        return NotImplemented

    def search_cuds(self, cuds):
        """ search for the CUDS, find if it is in the system using the iri of the CUDS
        could be feplaced by smart __contains__ method, that based on the type of element queried, activates various
        methods. could be as simple as calling the negine with ehcuds iri on all graphs. """

        return NotImplemented

    def get_cuds_region(self, cuds, radiud):
        """        get teh cuds up to a specific radius
        could be same as get_cuds but with optional radius, see ontology manager etc for implementations.

        """


import copy
import uuid, datetime
from collections import defaultdict
from urllib.parse import urlparse, urldefrag, urlsplit
from rdflib import Dataset, Graph, URIRef, Literal, RDF, RDFS
from rdflib.namespace import DC, DCTERMS, PROV, XSD
from rdflib import Namespace

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
                 engine: 'Engine' = None,
                 ):
        ontology_type = CUDS.Session,

        super().__init__(iri, pid, ontology_type, description, label)
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
        return self.engine.create_graph(graph_id)

    def delete_graph(self, graph_id):
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
        # added None as python does not allow non
        # default following default
        if not any([s, p, o]):  # or use all() for all not None, not sure...
            raise ValueError("s, p, and o are all None, at least one should be not None")
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

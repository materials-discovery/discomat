import uuid, datetime
from collections import defaultdict
from urllib.parse import urlparse, urldefrag, urlsplit

from rdflib import Dataset, Graph, URIRef, Literal, RDF, RDFS
from rdflib.namespace import DC, DCTERMS, PROV, XSD
from rdflib import Namespace

from discomat.ontology.namespaces import CUDS, MIO
from discomat.cuds.cuds import Cuds
from discomat.cuds.session import Session

from pyvis.network import Network
from IPython.display import display, HTML

from abc import ABC, abstractmethod

import os, sys, warnings, pickle

from types import MappingProxyType
from typing import Union

class Engine(Cuds):
    """
    each session has an engine which takes care of the actual low level data
    management and storage.

    should create graph, etc be methods of th session, which will call the engine?
    """

    def __init__(self,
                 iri: Union[str, URIRef] = None,
                 pid: Union[str, URIRef] = None,
                 ontology_type=None,
                 description=None,
                 label=None):

        ontology_type = URIRef("http://www.ddmd.io/mio#Engine")
        super().__init__(iri, pid, ontology_type, description, label)
        self._graphs = {}
    def create_graph(self, graph_id):
        """
        Create a graph within the Engine and assign it with graph_id.
        graph_id is coming from the session? not good I think.

        This, of course, assuming the engine
        supports graphs. which may or may not be the case,
        if the engine does not support it natively, we support it?!
        """
        g = Graph()
        """
        although the Engine is supposed to be very general, we alreay limit to rdflib. 
        what if it is a lammps graph? perhaps it is easier to manage all data using rdflib, but 
        some engines may have their own, non rdflib graph! """
        self._graphs[graph_id] = g
        return g

    def remove_graph(self, graph_id):
        try:
            g = self._graphs[graph_id]
        except KeyError:
            raise ValueError(f"Graph '{graph_id}' does not exist in this engine.")
        g = self._graphs[graph_id]
        g.clear()
        del self._graphs[graph_id]
        del (g)  # fixme: is there a safer way to do this? must be!

        # todo:add log and provenance

    @property
    def graphs(self):
        """
        use https://docs.python.org/3/library/types.html#types.MappingProxyType
        give back a read only proxy of the dict, so the user cannot change the graphs directly,
        only the engine can manage its own graphs.
        """
        return MappingProxyType(self._graphs)  # Return a read-only proxy to the dictionary


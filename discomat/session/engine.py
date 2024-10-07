import uuid, datetime
from collections import defaultdict
from urllib.parse import urlparse, urldefrag, urlsplit
from omikb.omikb import kb_toolbox

from rdflib import Dataset, Graph, URIRef, Literal, RDF, RDFS
from rdflib.namespace import DC, DCTERMS, PROV, XSD
from rdflib import Namespace
from rdflib.graph import DATASET_DEFAULT_GRAPH_ID

from discomat.ontology.namespaces import CUDS, MIO
from discomat.cuds.cuds import Cuds, add_to_root, ProxyCuds
from discomat.cuds.utils import to_iri
from enum import Enum

from pyvis.network import Network
from IPython.display import display, HTML

from abc import ABC, abstractmethod

import os, sys, warnings, pickle

from types import MappingProxyType
from typing import Union


rdf_default_graphs = {
    "FUSEKI_UNION_GRAPH": URIRef("urn:x-arq:UnionGraph"),
    "FUSEKI_DEFAULT_GRAPH": URIRef("urn:x-arq:defaultGraph"),
    "RDFLIB_DEFAULT_GRAPH": URIRef("urn:x-rdflib:default")
}

class Engine(Cuds):
    """
    each session has an engine instance, which takes care of the actual
     low-level data management and storage.
    """

    def __init__(self,
                 iri: Union[str, URIRef] = None,
                 pid: Union[str, URIRef] = None,
                 description=None,
                 label=None):

        ontology_type = CUDS.Engine
        description = description or f"Engine: No Description provided, dont be lazy.."

        super().__init__(iri=iri, pid=pid, ontology_type=ontology_type, description=description, label=label)
        self._graphs = {}
        self.default_graph_id = to_iri(CUDS.defaultGraph)  # URIRef("urn:x-rdflib:default") fixme: different name for fuseki. this should be the default graph of discomat.

    # def __contains__(self, triple):
    #     s, p, o = triple
    #     # Delegate
    #     s = to_iri(s)
    #     p = to_iri(p)
    #     o = to_iri(o)
    #     # print("hihi", s, p, o)
    #     # return (s, p, o) in self._dataset  # this should be overriden for each engine.
    #
    #     for g in self._dataset.contexts():
    #         if (s, p, o) in graph:
    #             return True
    #     return False
    def create_graph(self, graph_id):
        """
        Create a graph within the Engine and assign it with graph_id.
        graph_id is coming from the session? not good I think.

        This, of course, assuming the engine
        supports graphs. which may or may not be the case,
        if the engine does not support it natively, we support it?!
        """
        g = Graph()
        graph_id = to_iri(graph_id)
        # Add the basic root to the graph
        g.add((graph_id, RDF.type, CUDS.GraphId))
        g.add((graph_id, RDF.type, CUDS.RootNode))

        """
        although the Engine is supposed to be very general, we alreay limit to rdflib. 
        what if it is a lammps graph? perhaps it is easier to manage all data using rdflib, but 
        some engines may have their own, non rdflib graph! """
        self._graphs[graph_id] = g
        return g

    def remove_graph(self, graph_id):
        graph_id = to_iri(graph_id)
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

    def __iter__(self):
        return iter(self._graphs.values())

    def quads(self, s=None, p=None, o=None, g=None):
        return NotImplemented

    def triples(self, s=None, p=None, o=None, g=None):
        return NotImplemented

    def query(self, query):
        pass

    def add_triple(self, s=None, p=None, o=None):
        pass

    def add_quad(self, s=None, p=None, o=None, g_id=None):
        pass

    def remove_triple(self, s=None, p=None, o=None):
        pass

    def remove_quad(self, s=None, p=None, o=None, g_id=None):
        pass

    def get_cuds(self, iri):
        pass

    def add_cuds(self, cuds):
        pass

    def search_cuds(self, cuds):
        pass

    def get_cuds_region(self, cuds, radiud):
        pass


class RdflibEngine(Engine):
    """
    essentially uses an rdflib Dataset which is a modified conjuctive graph.
    """

    def __init__(self,
                 iri: Union[str, URIRef] = None,
                 pid: Union[str, URIRef] = None,
                 description=None,
                 label=None):

        ontology_type = CUDS.RdfLibEngine
        description = description or f"Engine: No Description provided, dont be lazy.."

        super().__init__(iri, pid, description, label)
        self._dataset = Dataset()
        self.default_graph_id = rdf_default_graphs["RDFLIB_DEFAULT_GRAPH"] #DATASET_DEFAULT_GRAPH_ID  # URIRef("urn:x-rdflib:default")

        g = self._dataset.graph(self.default_graph_id)
        graph_id = to_iri(self.default_graph_id)

        self._graphs = {graph_id: g}
        g.add((graph_id, RDF.type, CUDS.GraphId))
        g.add((graph_id, RDF.type, CUDS.RootNode))

    def create_graph(self, graph_id):
        """
        Parameters
        ----------
        graph_id

        """
        if graph_id is None:
            raise ValueError("We do not accept None as a name for named graph!")
        graph_id = to_iri(graph_id)
        g = self._dataset.graph(graph_id)
        # Add the basic root to the graph
        g.add((graph_id, RDF.type, CUDS.GraphId))
        g.add((graph_id, RDF.type, CUDS.RootNode))
        self.add(CUDS.hasGraphId, graph_id)
        self._graphs[graph_id] = g
        return graph_id

    def remove_graph(self, graph_id):  # fixme, we need a type for graph_id and then do Union[g_id or Graph]
        try:
            graph_id = to_iri(graph_id)
            g = self._graphs[graph_id]
            from discomat.cuds.utils import prd
            prd(f"in remove graph deep inside the engine: {g}, {graph_id}")
            self._dataset.remove_graph(g)
            del self._graphs[graph_id]
            self.remove(CUDS.hasGraphId, graph_id)
        except KeyError:
            raise ValueError(f"Graph '{graph_id}' does not exist in this engine.")

        # todo:add log and provenance

    @property
    def graphs(self):
        """
        use https://docs.python.org/3/library/types.html#types.MappingProxyType
        give back a read only proxy of the dict, so the user cannot change the graphs directly,
        only the engine can manage its own graphs.
        """
        return MappingProxyType(self._graphs)  # Return a read-only proxy to the dictionary

    def __iter__(self):
        """
        iter over the graphs in a session?
        Returns
        -------

        """
        return iter(self._graphs.values())

    def quads(self, s=None, p=None, o=None, g=None,/):
        return self._dataset.quads((s, p, o, g))

    def triples(self, s=None, p=None, o=None,/):
        return self._dataset.triples((s, p, o))

    def query(self, query):
        return self._dataset.query(query)

    # @add_to_root
    def add_triple(self, s=None, p=None, o=None):
        self._dataset.add((s, p, o))
        # for i, j, k in self._dataset.triples((None, None, None)):
        #     print(i, j, k)

    # @add_to_root
    def add_quad(self, s=None, p=None, o=None, g_id=None):
        return self._dataset.add((s, p, o, g_id))

    def remove_triple(self, s=None, p=None, o=None):
        return self._dataset.remove((s, p, o))

    def remove_quad(self, s=None, p=None, o=None, g_id=None):
        return self._dataset.remove((s, p, o, g_id))

    def get_cuds(self, iri):
        pass

    def add_cuds(self, cuds, g_id):
        g_id = to_iri(g_id) if g_id else self.default_graph_id
        the_graph = self._dataset.graph(g_id)
        for t in cuds:
            the_graph.add(t)

    def search_cuds(self, cuds):
        pass

    def get_cuds_region(self, cuds, radiud):
        pass


class FusekiEngine(Engine):
    """
    This is Fuseki session engine.
    this means, we are not managing an entire fuseki service, but rather
    simply interacting with a CUDS iri stored in this graph.
    only the direct CUDS relations are guaranteed to be in same graph as the iri.


    Uses some aspects of OMI ToolBox.
    While in rdflib the engine talked to a _dataset, here we need to talk to
    a sparql endpoint, and need something to keep track of it.
    This is done by loading a specific configuration from omikb using omikb.yml

    1. get in init also the name of the configuration,
    2. initialise connection and set it up with omikn, rgistering the relevant additional
    metadata to the _graph, which is the directly incured relations on the iri we define teh cuds for.
    """

    def __init__(self,
                 iri: Union[str, URIRef] = None,
                 pid: Union[str, URIRef] = None,
                 description=None,
                 label=None):

        kb = kb_toolbox() # we use omikb v 1.0, which needs update to use multiple profiles.
        #fixme update omikb to accept a service name, so support for both omi and dome is available
        # this will be omikb versin 1.01, if no name is provided, it uses the default one, so no change is needed there.

        ontology_type = CUDS.FusekiEngine
        description = description or f"Feski discomat Engine using OmiKB v1.01"

        super().__init__(iri, pid, description, label)

        #self._dataset = # need to read it from omikb.yml

        self.default_graph_id = rdf_default_graphs["FUSEKI_DEFAULT_GRAPH"] #DATASET_DEFAULT_GRAPH_ID  # URIRef("f")
        # for fuseki we have urn:x-arq:DefaultGraph and urn:x-arq:UnionGraph as union!
        # modify in the future to support arbitrary def graph from omikb.yml
        # g = self._dataset.graph(self.default_graph_id)
        graph_id = to_iri(self.default_graph_id)

        self._graphs = {graph_id: graph_id} # we do not use an instance of g as for rdflib engine, but rather the name of the graph only
        # g.add((graph_id, RDF.type, CUDS.GraphId))
        # g.add((graph_id, RDF.type, CUDS.RootNode))
        # use query to add relations.

    def create_graph(self, graph_id):
        """
        Parameters
        ----------
        graph_id

        """
        if graph_id is None:
            raise ValueError("We do not accept None as a name for named graph!")
        graph_id = to_iri(graph_id)
        g = self._dataset.graph(graph_id)
        # Add the basic root to the graph
        g.add((graph_id, RDF.type, CUDS.GraphId))
        g.add((graph_id, RDF.type, CUDS.RootNode))
        self.add(CUDS.hasGraphId, graph_id)
        self._graphs[graph_id] = g
        return graph_id

    def remove_graph(self, graph_id):  # fixme, we need a type for graph_id and then do Union[g_id or Graph]
        try:
            graph_id = to_iri(graph_id)
            g = self._graphs[graph_id]
            from discomat.cuds.utils import prd
            prd(f"in remove graph deep inside the engine: {g}, {graph_id}")
            self._dataset.remove_graph(g)
            del self._graphs[graph_id]
            self.remove(CUDS.hasGraphId, graph_id)
        except KeyError:
            raise ValueError(f"Graph '{graph_id}' does not exist in this engine.")

        # todo:add log and provenance

    @property
    def graphs(self):
        """
        use https://docs.python.org/3/library/types.html#types.MappingProxyType
        give back a read only proxy of the dict, so the user cannot change the graphs directly,
        only the engine can manage its own graphs.
        """
        return MappingProxyType(self._graphs)  # Return a read-only proxy to the dictionary

    def __iter__(self):
        return iter(self._graphs.values())

    def quads(self, s=None, p=None, o=None, g=None,/):
        return self._dataset.quads((s, p, o, g))

    def triples(self, s=None, p=None, o=None,/):
        return self._dataset.triples((s, p, o))

    def query(self, query):
        return self._dataset.query(query)

    # @add_to_root
    def add_triple(self, s=None, p=None, o=None):
        self._dataset.add((s, p, o))
        # for i, j, k in self._dataset.triples((None, None, None)):
        #     print(i, j, k)

    # @add_to_root
    def add_quad(self, s=None, p=None, o=None, g_id=None):
        return self._dataset.add((s, p, o, g_id))

    def remove_triple(self, s=None, p=None, o=None):
        return self._dataset.remove((s, p, o))

    def remove_quad(self, s=None, p=None, o=None, g_id=None):
        return self._dataset.remove((s, p, o, g_id))

    def get_cuds(self, iri):
        pass

    def add_cuds(self, cuds):
        pass

    def search_cuds(self, cuds):
        pass

    def get_cuds_region(self, cuds, radiud):
        pass


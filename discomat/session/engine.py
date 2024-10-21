import uuid, datetime
from collections import defaultdict
from urllib.parse import urlparse, urldefrag, urlsplit
from omikb.domekb import KbToolBox
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
    This is discomt Fuseki session engine. It supports all actions needed on anu CUDS a session.
    this means, we are not managing an entire fuseki service, but rather
    simply interacting with a CUDS iri stored in this graph.
    only the direct CUDS relations are guaranteed to be in same graph as the iri.


    Uses some aspects of OMI ToolBox.
    While in rdflib the engine talked to a _dataset, here we need to talk to
    a sparql endpoint, and need something to keep track of it.
    This is done by loading a specific configuration from omikb using omikb.yml

    1. get in init also the name of the configuration,
    2. initialise connection and set it up with omikn, rgistering the relevant additional
    metadata to the _graph, which is the directly incurred relations on the iri we define teh cuds for.


     service: the service name as in omikb.yml, of none, then use the default one (usually kb needed for oopenmode,
     hence it is better to define one).

     Note that it can be that the user session is using a remote session which in turn uses a remote engine, hence anotehr reason for teh proxy handler implementation with strings.


    """

    def __init__(self,
                 iri: Union[str, URIRef] = None,
                 pid: Union[str, URIRef] = None,
                 description=None,
                 label=None,
                 service=None):

        #  fixme update omikb to accept a service name, so support for both omi and
        #  dome is available
        #  this will be omikb versin 1.01, if no name is provided, it uses the default one,
        #  so no change is needed there.

        ontology_type = CUDS.FusekiEngine
        description = description or f"Fuseki DiscoMat Engine using OmiKB v1.01"

        super().__init__(iri, pid, description, label) # this creates the _graph of the engine.

        self._kb = KbToolBox(service)   # this has a different function depending in the engine
        # this is a structure that has: update_iri, query_iri, etc...

        # testing
        print("kb.ping", self._kb.ping())

        print(self._kb.is_online)

        print(self._kb.stats())

        self.default_graph_id = rdf_default_graphs["FUSEKI_DEFAULT_GRAPH"] #DATASET_DEFAULT_GRAPH_ID  # URIRef("f")
        # for fuseki we have urn:x-arq:DefaultGraph and urn:x-arq:UnionGraph as union!
        # modify in the future to support arbitrary def graph from omikb.yml
        # g = self._dataset.graph(self.default_graph_id)
        graph_id = to_iri(self.default_graph_id)

        self._graphs = {graph_id: graph_id} # we do not use an instance of g as for rdflib engine, but rather the name of the graph only
        # use query to add relations.

        # g.add((graph_id, RDF.type, CUDS.GraphId))
        # g.add((graph_id, RDF.type, CUDS.RootNode))
        g = graph_id
        # We should not do anything but open the connection and test with KBtoolBox.
        # update_query = f"""
        # PREFIX RDF: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        # PREFIX MISO: <https://materials-discovery.org/miso#>
        # PREFIX MIO: <https://materials-discovery.org/mio#>
        # PREFIX CUDS: <https://materials-discovery.org/cuds#>
        # PREFIX RDFS: <http://www.w3.org/2000/01/rdf-schema#>
        #
        # INSERT DATA {{
        #     GRAPH {g} {{
        #         {graph_id} RDF.type CUDS.GraphId .
        #         {graph_id} RDF.type CUDS.RootNode .
        #     }}
        # }}
        # """
        #
        # s = self._kb.update(update_query)
        #we could add a function: fuseki_graph which returns a method that makes any query to be one on this graph.
        # now get all graphs already in teh system, and augment the _graphs, though this is not really needed in teh future, we need to make _graphs always query, as many users could be changing the databse at the same time.

        query = """
	            SELECT DISTINCT ?g WHERE {
	              GRAPH ?g { ?s ?p ?o }
	            }
	            """
        results = self._kb.query(query)
        print("results.josn()", results.json())
        print("status code:", results.status_code)

        """
        the results are of the form (example):
        
        results.josn(): 
        {'head': {'vars': ['g']}, 'results': {'bindings': [{'g': {'type': 'uri', 'value': 'http://dome40.io/dataset/data/platforms_dome_core_reasoned_Hermit'}}, {'g': {'type': 'uri', 'value': 'http://dome40.io/dataset/data/dome4.0_core_dataset_trial0_reasoned'}}]}}

        so essentially we should later enhance the loop to check the type of the graph. 
        """


        #graph_list = [result['g']['value'] for result in results['results']['bindings']]
        test=results.json()
        graph_list = [result['g']['value'] for result in test['results']['bindings']]
        print("Initialising the Fuseki Engine\n Found the following number of existing graphs", len(graph_list))
        print("The graphs found are: ", graph_list)
        self._graphs = {graph_id: graph_id for graph_id in graph_list}
        print("Updated the session engine with the available graphs\n")

    def create_graph(self, graph_id):
        """
        Parameters
        ----------
        graph_id

        """
        if graph_id is None:
            raise ValueError("We do not accept None as a name for named graph!")
        graph_id = to_iri(graph_id)
        g = graph_id
        update_query = f"""
        PREFIX RDF: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX MISO: <https://materials-discovery.org/miso#>
        PREFIX MIO: <https://materials-discovery.org/mio#>
        PREFIX CUDS: <https://materials-discovery.org/cuds#>
        PREFIX RDFS: <http://www.w3.org/2000/01/rdf-schema#>

        INSERT DATA {{
            GRAPH {g} {{
                {graph_id} RDF.type CUDS.GraphId .
                {graph_id} RDF.type CUDS.RootNode .
                {graph_id} CUDS.hasGraphId, graph_id .
                
            }}
        }}
        """

        s = self._kb.update(update_query)
        self._graphs[graph_id] = g
        return graph_id

    def remove_graph(self, graph_id):  # fixme, we need a type for graph_id and then do Union[g_id or Graph]
        try:
            graph_id = to_iri(graph_id)
            g = self._graphs[graph_id]
            from discomat.cuds.utils import prd
            prd(f"in remove graph deep inside the engine: {g}, {graph_id}")
            query = f"""
                DROP GRAPH <{graph_id}>
                """
            self._kb.update(query)

        except KeyError:
            raise ValueError(f"Graph '{graph_id}' does not exist in this engine or could not be deletet (dropped).")

        # todo:add log and provenance

    @property
    def graphs(self):
        """
        use https://docs.python.org/3/library/types.html#types.MappingProxyType
        give back a read only proxy of the dict, so the user cannot change the graphs directly,
        only the engine can manage its own graphs.
        """
        query = """
        SELECT DISTINCT ?g WHERE {
          GRAPH ?g { ?s ?p ?o }
        }
        """
        results=self._kb.update(query)
        graph_list = [result['g']['value'] for result in results['results']['bindings']]
        self._graphs = {graph_id: graph_id for graph_id in graph_list}

        return MappingProxyType(self._graphs)  # Return a read-only proxy to the dictionary

    def __iter__(self):
        return iter(self._graphs.values())

    def quads(self, s=None, p=None, o=None, g=None, /):
        # we construct the query based on what is not given,
        #it could be done more smartly but now I am focused on it working.

        query = "SELECT ?g ?s ?p ?o WHERE {"

        # If the g is not None, include the specific graph, otherwise its a query variable.
        if g is not None:
            query += f" GRAPH <{g}> {{"
        else:
            query += " GRAPH ?g {"

        # same for the triples
        query += f" {f'<{s}>' if s is not None else '?s'}"
        query += f" {f'<{p}>' if p is not None else '?p'}"
        query += f" {f'<{o}>' if o is not None else '?o'} ."

        # close brackets in query # see also utils/libs...
        query += " }"
        if g is not None:
         query += " }" #fixme add a check of we had one or two brackets.

        results = self._kb.query(query)

        # Iterate adn yield iterator
        for result in results['results']['bindings']:
            g = g if g is not None else result['g']['value']
            s = s if s is not None else result['s']['value']
            p = p if p is not None else result['p']['value']
            o = o if o is not None else result['o']['value']

            yield g, s, p, o

    def triples(self, s=None, p=None, o=None,/):
        for _, s, p, o in self.quads(s=s, p=p, o=o, g=None):
            yield s, p, o

    def query(self, query):  # need to make this aware of prefixes... simply by defining them in some method and using them in each query/update etc. could be part of kb.
        return self._kb.query(query)

    # @add_to_root
    def add_triple(self, s=None, p=None, o=None):
        query = f"""
            INSERT DATA {{
              <{s}> <{p}> {self.to_sparql_query(o)} .
            }}
            """
        self._kb.update(query)
        # for i, j, k in self._dataset.triples((None, None, None)):
        #     print(i, j, k)

    # @add_to_root
    def add_quad(self, s=None, p=None, o=None, g_id=None):
        query = f"""
        INSERT DATA {{
          GRAPH <{g_id}> {{
            <{s}> <{p}> {self.to_sparql_query(o)} .
          }}
        }}
        """
        self._kb.update(query)


    def remove_triple(self, s=None, p=None, o=None):
        query = f"""
        DELETE DATA {{
          <{s}> <{p}> {self.to_sparql_query(o)} .
        }}
        """
        self._kb.update(query)

    def remove_quad(self, s=None, p=None, o=None, g_id=None):
        query = f"""
        DELETE DATA {{
          GRAPH <{g_id}> {{
            <{s}> <{p}> {self.to_sparql_query(o)} .
          }}
        }}
        """

        self._kb.update(query)


    def get_cuds(self, iri):
        # This does not check if iri is a CUDS, we do not need this now, but in the future we may add a check
        # and augment the entity with the CUDS metadata (see ONTOMAP)
        query = f"""
         SELECT ?p ?o WHERE {{
           <{iri}> ?p ?o .
         }}
         """
        results=self._kb.update(query)
        #now we need to create a CUDS and return it, however, is it a proxy cuds or a real cuds?
        c=Cuds()
        # loop over the po and check what is in ONTOMAP, add it to, then add the rest, in effect we
        # do c.add(p, o) for all po pairs, but we first check the ontomap, so that we can add them as default if not defined.
        # for now, we add all:
        for result in results['results']['bindings']:
            p = result['p']['value']
            o = result['o']['value']
            c.add(p, o)

        return c

    def add_cuds(self, cuds):
        # loop over the cuds, and for each p and o add them
        pass

    def search_cuds(self, cuds):
        pass

    def get_cuds_region(self, cuds, radiud):
        pass


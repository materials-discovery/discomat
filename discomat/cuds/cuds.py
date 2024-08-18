import uuid, datetime
from collections import defaultdict
from urllib.parse import urlparse, urldefrag, urlsplit

from rdflib import Dataset, Graph, URIRef, Literal, RDF, RDFS
from rdflib.namespace import DC, DCTERMS, PROV, XSD
from discomat.ontology.namespaces import CUDS, MIO
# from .ontology_item import OntologyItem
# from .utils import SES # this should be defined.
from pyvis.network import Network
from IPython.display import display, HTML
from abc import ABC, abstractmethod
import os, sys, warnings, pickle
from types import MappingProxyType
from typing import Union

from rdflib import Namespace
from discomat.cuds.utils import to_iri, mnemonic_label


class Cuds:
    """
    Everything, when possible, is a CUDS!
    CUDS has built in support for provenance and persistent identifiers (PID) though we are not
    doing this with a "formal external authority yet".

    Unlike SimPhoNy, we do not aim to make every ontology entity (class or individual, or relation) etc
    as a python class, but keep its rdf nature. CUDS is simply a class that adds one more layer to any IRI
    so that we can trace it and add some bookkeeping, including translating between wengine backends and storing.
    the below implementation is the only one we need to keep in sync with the ontology (see mio.owl).



    """

    def __init__(self,
                 iri: Union[str, URIRef] = None,
                 pid: Union[str, URIRef] = None,
                 ontology_type=None,
                 description=None,
                 label=None):
        """
        iri: The iri should be unique, but default it is a uuid with MIO/CUDS as prefix.

        ontology_type: this is equivalent to RDF.type

        pid: a persistent identifier in the FAIR sense (locally managed for now)

        description:for human consumption
        label:for human consumption

        A Cuds will have an iri, which is unique for this instance of the CUDS.

        """
        # this is useful for errors, should actually re-evaluate if it should be used.

        self.path = sys.modules[__name__].__file__ if __name__ == "__main__" else __file__

        if description is not None and len(description) > 500:
            raise ValueError("in {self.path}: The description cannot exceed 500 characters")

        if label is not None and len(str(label)) > 20:
            raise ValueError("in {self.path}: The description cannot exceed 500 characters")

        self._graph = Graph()  # a CUDS is a little Graph Data Structure. This is the container concept.

        self.uuid = uuid.uuid4()  # Generate a unique UUID for each instance

        self.iri = iri if iri else f"http://www.ddmd.io/mio#cuds_iri_{self.uuid}"
        self.rdf_iri = URIRef(self.iri)  # make sure it is a URIRef

        self._graph.add((self.rdf_iri, CUDS.uuid, Literal(self.uuid)))

        # Should be unique for each CUDS, leave /none.
        # Defines a different version of the same CUDS if it has the same
        # PID

        self.ontology_type = ontology_type if ontology_type else MIO.Cuds
        # this is the RDF.type of the individual. Note: classes are not defined as Cuds, but only individuals
        self._graph.add((self.rdf_iri, RDF.type, URIRef(self.ontology_type)))

        self.description = description or f"This is CUDS version 1.0 - No description was given."
        # self._graph.add((self.rdf_iri, CUDS.description, Literal(description)))
        self.description = description or f"This is a CUDS without Description!"
        self._graph.add((self.rdf_iri, CUDS.description, Literal(str(self.description))))

        self.label = str(label) if label is not None else mnemonic_label(2)
        self._graph.add((self.rdf_iri, CUDS.label, Literal(str(self.label), datatype=XSD.string)))

        self.pid = pid or f"http://www.ddmd.io/mio#cuds_pid_{self.uuid}"
        # fixme use str(CUDS) or {str(MIO)}cuds_pid/... should stay the same for the same CUDS
        self._graph.add((self.rdf_iri, CUDS.Pid, Literal(str(self.pid), datatype=XSD.string)))

        self.creation_time = datetime.datetime.now()
        self._graph.set((self.rdf_iri, PROV.generatedAtTime, Literal(self.creation_time, datatype=XSD.dateTime)))

    # def __setattr__(self, name, value):
        """
        this (inactive) method enables adding automatically all attributes to teh internal graph, 
        but there is not yet much flexibility in changing the predicate, so keeping for future updates
        
        """
    #     if name.startswith('_'):
    #         super().__setattr__(name, value)
    #     else:
    #         super().__setattr__(name, value)
    #         if hasattr(self, 'rdf_iri'):
    #             self._graph.set((self.rdf_iri, CUDS[name], Literal(value)))

    # def __getattr__(self, name):
    #     """
    #     the opposite of setattr.
    #     """
    #     if name in self.__dict__:
    #         return self.__dict__[name]
    #     else:
    #         return self._graph.value(self.rdf_iri, CUDS[name])

    @property
    def properties(self):
        # Retrieve all properties (predicates) and objects for c.iri
        properties = defaultdict(list)
        for p, o in self._graph.predicate_objects(self.rdf_iri):
            namespace, fragment = self.split_uri2(p)
            properties[namespace].append((fragment, o))
        return properties

    def split_uri(self, uri):  # fixme move to utils
        # Split the URI into namespace and fragment
        parsed_uri = urlparse(uri)
        path = parsed_uri.path
        if "#" in path:
            namespace, fragment = path.split("#")
        elif "/" in path:
            namespace, fragment = path.rsplit("/", 1)
        else:
            namespace, fragment = path, ''
        return parsed_uri.scheme + "://" + parsed_uri.netloc + namespace + "/", fragment

    def print_graph(self):
        # Print the graph in a readable format (e.g., Turtle)
        print(self._graph.serialize(format="turtle"))

    def __repr__(self):
        # Pretty print format for the instance
        properties = self.properties
        output = [f"c.iri: {self.rdf_iri}\n"]
        for namespace, props in properties.items():
            output.append(f"Namespace: {namespace}")
            for fragment, obj in props:
                output.append(f"  {fragment}: {obj}")
            output.append("")  # Add a blank line between namespaces
        return "\n".join(output)

    def split_uri2(self, uri):  # fixme move to utils
        # Split the URI into namespace and fragment
        frag_split = urldefrag(uri)
        if frag_split[1]:  # If there's a fragment after #
            return frag_split[0] + "#", frag_split[1]
        else:  # Otherwise split at the last /
            split = urlsplit(uri)
            path_parts = split.path.rsplit('/', 1)
            if len(path_parts) > 1:
                return split.scheme + "://" + split.netloc + path_parts[0] + "/", path_parts[1]
            else:
                return uri, ''  # Fallback case

    @property
    def properties2(self):
        # Retrieve all properties (predicates) and objects for c.iri
        properties = {}
        for p, o in self._graph.predicate_objects(self.rdf_iri):
            properties[p] = o
        return properties

    def __repr__2(self):
        # Pretty print format for the instance
        properties = self.properties
        properties_str = "\n".join([f"  {p}: {o}" for p, o in properties.items()])
        return f"c.iri: {self.iri}\nProperties:\n{properties_str}"

    def add(self, p, o):
        try:
            self._graph.add((self.rdf_iri, to_iri(p), to_iri(o)))
            # fixme: use safe_uri from scigraph, as well as make this an utility function to get the proper iri from
            #  either an argument which is cuds, iri, or str.
        except TypeError as e:
            print(f"Wrong typ {e}")
            return None


    def remove(self, p, o):
        try:
            self._graph.remove((self.rdf_iri, to_iri(p), to_iri(o)))
            # fixme: use safe_uri from scigraph, as well as make this an utility function to get the proper iri from
            #  either an argument which is cuds, iri, or str.
        except TypeError as e:
            print(f"Wrong typ {e}")
            return None

    def __iter__(self):
        # Delegate the iteration to rdflib Graph
        return iter(self._graph)

    # def __getattr__(self, name):
    #     print(f"Delegating atttribute: {name}")
    #     # Delegate attribute access to self._graph
    #     # Avoid infinite recursion by checking if the attribute is _graph
    #     if name in ['_graph', '__deepcopy__']:
    #         raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
    #     return getattr(self._graph, name)
    @property
    def graph(self):
        return self._graph


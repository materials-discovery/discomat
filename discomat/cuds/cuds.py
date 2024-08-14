import uuid, datetime
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
        self._graph.add((self.rdf_iri, CUDS.description, Literal(description)))

        self.label = str(label) if label is not None else None
        self._graph.add((self.rdf_iri, CUDS.label, Literal(str(self.label))))

        self.pid = pid or f"http://www.ddmd.io/mio#cuds_pid_{self.uuid}"
        # fixme use str(CUDS) or {str(MIO)}cuds_pid/... should stay the same for the same CUDS

        def_str = f"http://www.ddmd.io/mio#cuds_pid_{self.uuid}"  # fixme use str(CUDS) or {str(MIO)}cuds_pid/..
        self.description = description or def_str
        self._graph.add((self.rdf_iri, CUDS.description, Literal(str(self.description))))

        self.creation_time = datetime.datetime.now()
        self._graph.set((self.rdf_iri, PROV.generatedAtTime, Literal(self.creation_time, datatype=XSD.dateTime)))

    @property
    def properties(self):
        # all the properties (predicates and other) and objects
        properties = {}
        for p, o in self._graph.predicate_objects(self.rdf_iri):
            properties[p] = o
        return properties

    def print(self):
        print(self._graph.serialize(format="turtle"))

    def __repr__(self):
        # Pretty print format for the instance
        properties = self.properties
        properties_str = "\n".join([f"  {p}: {o}" for p, o in properties.items()])
        return f"c.iri: {self.iri}\nProperties:\n{properties_str}"


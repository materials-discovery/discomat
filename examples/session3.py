from discomat.cuds.cuds import Cuds
from discomat.visualisation.cuds_vis import gvis
from discomat.cuds.utils import uuid_from_string, to_iri, pr, prd
from discomat.session .session import Session
from discomat.ontology.namespaces import CUDS, MIO, MISO

from rdflib import URIRef, Graph
from rdflib.namespace import RDF, RDFS
import copy
from discomat.ontology.namespaces import CUDS, MISO, MIO

session = Session()

session.create_graph("graph1")
session.create_graph("graph2")
# session.create_graph("graph3")

print(session)
print(session.engine)
# get default graph

def_g = session.graphs()

gvis(session, "session_example.html")
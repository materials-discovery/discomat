from discomat.cuds.cuds import Cuds
from discomat.visualisation.cuds_vis import gvis
from discomat.cuds.utils import uuid_from_string, to_iri, pr, prd
from discomat.session.session import Session
from discomat.ontology.namespaces import CUDS, MIO, MISO

from rdflib import URIRef, Graph
from rdflib.namespace import RDF, RDFS
import copy
from discomat.ontology.namespaces import CUDS, MISO, MIO
from discomat.session.engine import FusekiEngine, RdflibEngine

engine = FusekiEngine(description="test engine")
#engine=RdflibEngine()

# test session
session = Session(engine=engine)

list_of_graphs=[None]
for g in session:
    print(g)
    list_of_graphs.append(g)

print(list_of_graphs)

print(f"___________________\nAll Triple in the default Graph\n")
for t in session.triples():
    print(t)
print(f"___________________\nAll Triple in all named graphs\n")

for g in list_of_graphs:
    for t in session.triples('http://dome40.eu/semantics/pc#Accessed', None, None, g):
        print(t)
    print(f"___________________\n\n")
print(f"___________________\n\n")

prd(f"\nList_graphs:")
lg = session.list_graphs()
prd(lg)

gs = session.graphs()
print(f"type(gs): {type(gs)}, {gs}")
for i in gs:
    print(f"type(gs): {type(gs)}, {gs}")

prd("\n Print and count quads")
print(len(list(session.quads())))
for quad in session.quads():
    print('quad',quad)
    session.remove_quad(quad)

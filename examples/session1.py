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
#visualise the session.
gvis(session, "A_Session.html")
print(f"This session has an engine of type: {type(session.engine)}")
#visualise the engine of this session.
gvis(session.engine, "session_engine.html")

prd("add graphs")
session.create_graph("http://graph1.com")
session.create_graph("http://graph2.com")
session.create_graph("http://graph3.com")
gvis(session, "session_with_three_graphs.html")
print(session)

prd("remove graph2")
session.remove_graph("http://graph2.com")
print(session)
gvis(session, "session_removed_graph2.html")
session.print_graph()

# should loop over all graphs and the graph objects like and return something like
"""
<urn:x-rdflib:default> a rdfg:Graph;rdflib:storage [a rdflib:Store;rdfs:label 'Memory'].
<graph1> a rdfg:Graph;rdflib:storage [a rdflib:Store;rdfs:label 'Memory'].
<graph3> a rdfg:Graph;rdflib:storage [a rdflib:Store;rdfs:label 'Memory'].
"""
prd("-- iter over graphs")
for g in session:
    print(g)

prd(f"\nList_graphs:")
lg = session.list_graphs()
prd(f"\nList_graphs:")

prd(lg)

gs = session.graphs()
print(f"type(gs): {type(gs)}, {gs}")
for i in gs:
    print(f"type(gs): {type(gs)}, {gs}")

prd("\n Add  triples")
session.add_triple((MISO.Simulation, RDF.type, RDFS.Class))
session.add_triple((MISO.Simulation, RDFS.subClassOf, CUDS.Cuds))
session.add_triple((MISO.simulation, RDF.type, MISO.Simulation))

session.add_quad((MISO.simulation, RDF.type, MISO.Simulation, "http://graph1.com"))
session.add_quad((MISO.simulation, CUDS.has, MISO.SimulationEngine, "http://graph1.com"))


# add it again as we use it below:
session.create_graph("http://graph2.com")
session.create_graph("http://graph3.com")
session.create_graph("http://graph4.com")

prd(f"add quads")
session.add_quad((CUDS.root0, RDF.type, CUDS.RootNode, "http://graph1.com"))
session.add_quad((CUDS.root1, RDF.type, CUDS.RootNode, "http://graph1.com"))
session.add_quad((CUDS.root2, RDF.type, CUDS.RootNode, "http://graph2.com"))
session.add_quad((CUDS.root3, RDF.type, CUDS.RootNode, "http://graph3.com"))
session.add_quad((CUDS.root4, RDF.type, CUDS.RootNode, "http://graph4.com"))

session.add_quad( (URIRef("s1"), URIRef("p1"), URIRef("o1"), URIRef("http://graph1.com")))
session.add_quad((to_iri("s2"), to_iri("p2"), to_iri("o1"), "http://graph1.com"))
session.add_quad((to_iri("s3"), to_iri("p3"), to_iri("o3"), to_iri("http://graph1.com")))
session.add_quad((to_iri("o3"), to_iri("p4"), to_iri("o4"), "http://graph1.com"))
session.add_quad((to_iri("s3"), to_iri("p5"), to_iri("o4"), "http://graph1.com"))
session.add_quad((to_iri("s3"), to_iri("p5"), to_iri("o4"), "http://graph1.com"))
session.add_quad((to_iri("s3"), to_iri("p2"), to_iri("o3"), "http://graph1.com"))
session.add_quad((to_iri("s3"), to_iri("p3"), to_iri("o3"), "http://graph1.com"))
session.add_quad((to_iri("s3"), to_iri("p3"), to_iri("o3"), "http://graph1.com"))
session.add_quad((to_iri("s4"), to_iri("p4"), to_iri("o4"), "http://graph2.com"))
session.add_quad((to_iri("s5"), to_iri("p5"), to_iri("o5"), "http://graph2.com"))
session.add_quad((to_iri("s6"), to_iri("p6"), to_iri("o6"), "http://graph2.com"))

prd("\n Print and count quads")
print(len(list(session.quads())))
for quad in session.quads():
    print('quad',quad)
    session.remove_quad(quad)

# for s, p, o, g in session.quads():
#     print("quads:", s, p, o, g)
#
# prd("test quads ")
# for s, p, o, g in session.quads(None, None, None, "http://graph2.com"):
#     print(f"testing {s}, {p}, {o}, {g}")
#
# prd("test triples\n")
# for s, p, o, g in session.triples(None, None, None):
#     print("triples:", s, p, o, g)

prd("Delete a quad (s4, p4, o4, graph1)")

if (("s4", "p4", "o4")) in session:
    prd("its in")
else:
    prd("not in")
gvis(session, "session_all.html")

session.remove_triple(("s4", "p4", "o4"))
gvis(session, "session_after_remove.html")

if ("s4", "p4", "o4") in session:
    prd("its in")
else:
    prd("not in")

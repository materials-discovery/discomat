from lib2to3.fixes.fix_input import context

from discomat.cuds.cuds import Cuds
from discomat.visualisation.cuds_vis import gvis
from discomat.cuds.utils import uuid_from_string, to_iri, pr, prd
from discomat.session.session import Session
from discomat.ontology.namespaces import CUDS, MIO, MISO
import csv

from rdflib import URIRef, Graph
from rdflib.namespace import RDF, RDFS
import copy
from discomat.ontology.namespaces import CUDS, MISO, MIO

session = Session()

[session.create_graph(g) for g in ["https://graph.org/g1", "https://graph.org/g2", "https://graph.org/g3", "https://graph.org/g4", "https://graph.org/g5", "https://graph.org/MISO-ONTOLOGY"]]
quads=[]
with open('quads.csv', mode='r') as file:
    reader = csv.reader(file)
    next(reader)
    for row in reader:
        quads.append(tuple(row))

# assume the file has some text like NS.SomeObject, with NS some name space, we need to do the mapping here
# to the real name space


namespaces = {
    "MISO": MISO,
    "CUDS": CUDS,
    "RDF": RDF,
    "MIO": MIO
}

print(session)
for quad in quads:
    # session.add_quad(*quad[:4])  # unpack
    q=[]
    for i in quad[:4]:
        print(i)
        try:
            uri=URIRef(eval(i, {}, namespaces))
        except NameError:
            uri=i
        print(uri)
        q.append(uri)
    session.add_quad(tuple(q))
    print("quads", tuple(q))

print(session)
gvis(session, "session5.html")
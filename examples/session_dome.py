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

prd("remove graph2")
session.remove_graph("http://graph2.com")

for i in session.quads(g="http://dome40.io/provenance/", s="http://www.ddmd.io/mio/cuds#User_e5c615e4-35ff-43f0-acc5-35c39ff27c3c"):
    print (i) 

for i in session.quads(p="http://www.w3.org/ns/prov#wasAssociatedWith", g="http://dome40.io/provenance/"):
    print (i) 

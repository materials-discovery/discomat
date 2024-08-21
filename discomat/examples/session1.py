from discomat.cuds.cuds import Cuds
from discomat.visualisation.cuds_vis import gvis
from discomat.cuds.utils import uuid_from_string, to_iri
from discomat.cuds.session import Session
from rdflib import URIRef, Graph
import copy
from discomat.ontology.namespaces import CUDS, MISO, MIO

# test session
s = Session()
print(f"Session {50*'*'}")
print(s)
gvis(s, "cuds_session.html")

print(f"This session has an engine of type: {type(s.engine)}")
gvis(s.engine, "session_engine.html")

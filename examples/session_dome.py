from discomat.cuds.cuds import Cuds
from discomat.visualisation.cuds_vis import gvis
from discomat.cuds.utils import uuid_from_string, to_iri, pr, prd
from discomat.session.session import Session
from discomat.ontology.namespaces import CUDS, MIO, MISO
from discomat.cuds.utils import uuid_from_string, to_iri, QueryLib


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


query=QueryLib.all_triples()
q ="""
    PREFIX prov: <http://www.w3.org/ns/prov#>
    PREFIX PC: <http://dome40.eu/semantics/pc#>
    PREFIX CUDS: <http://www.ddmd.io/mio/cuds#>
    PREFIX MIO: <http://materials-discovery.org/semantics/mio#>
    PREFIX PROV: <http://www.w3.org/ns/prov#>
    PREFIX DOME: <http://dome40.eu/semantics/dome4.0_core#>
    PREFIX ADE: <http://dome40.eu/semantics/reasoned/ade_reasoned#>
    PREFIX PL: <https://dome40.eu/semantics/scenario/platforms#>

    SELECT ?s WHERE {

        ?s a PC:AccessGrant ;
        PROV:used <https://dome40.eu/semantics/scenario/platforms#CHEMEO> ;
        PROV:wasAttributedTo <http://dome40.eu/semantics/pc#User_e5c615e4-35ff-43f0-acc5-35c39ff27c3c> .
        }
"""

print(q)

res=session.query(q)
print(query)
print(res)
for i in res:
    print(i)

import itertools

from discomat.cuds.cuds import Cuds, ProxyCuds
from discomat.cuds.session_manager import SessionManager
from discomat.visualisation.cuds_vis import gvis
from discomat.cuds.utils import uuid_from_string, to_iri
from discomat.cuds.session import Session
from rdflib import URIRef, Graph, PROV, Literal

import copy

from discomat.ontology.namespaces import CUDS, MISO, MIO

session1 = Session(label="Session 1", description="session 2")


sim1 = Cuds(ontology_type=MISO.Simulation, description="simulation 1")
meth1 = Cuds(ontology_type=MISO.Method, description="method 1")
bc1=Cuds(ontology_type=MISO.BoundryCondition, description="boundary condition 1")
ms1 = Cuds(ontology_type=MISO.MaterialsSystem, description="some sort of materials system 1")

for i in [meth1, ms1, bc1]:
    sim1.add(MIO.has, i)

# since we have a whole cuds created in the base (None) session, adding it to the session object requirs adding each
# component:
prox={}
for i in [sim1, meth1, ms1, bc1]:
    prox[i]=session1.add_cuds(i)   # add all to the same session.

prox[sim1].description="sim1 created in base session, and moved with all its components later on to the specific " \
                       "session1"
# change the property of sim1 through the proxy

sim2 = Cuds(ontology_type=MISO.Simulation)
meth2 = Cuds(ontology_type=MISO.Method, description="method 2")
bc2=Cuds(ontology_type=MISO.BoundryCondition, description="boundary condition 2")
ms2 = Cuds(ontology_type=MISO.MaterialsSystem, description="some sort of materials system, part 2")

session2=Session(label="session 2", description="session 2")

prox2={}
for i in [sim2, meth1, ms2, bc2]:
    prox2[i]=session2.add_cuds(i)   # add all to the same session.

prox2[sim2].description="sim2 created similar to sim1"

test=Cuds(ontology_type=CUDS.Test) # test lives in the base session.
prox2[sim2].add(CUDS.hasTest, test)  # adding link across sessions is allowed.
# sim2prox.description="this is sim2"

print("iter over sessions")
g_session=Graph()
for i in  itertools.chain(session1.triples(), session2.triples()):
    g_session.add(i[:3])
gvis(g_session, "Session1_and_2.html")


import itertools

from discomat.cuds.cuds import Cuds, ProxyCuds
from discomat.session.session_manager import SessionManager
from discomat.visualisation.cuds_vis import gvis
from discomat.cuds.utils import uuid_from_string, to_iri, QueryLib
from discomat.session.session import Session
from rdflib import URIRef, Graph, PROV, Literal, RDF
from discomat.session.engine import FusekiEngine, RdflibEngine

import copy

from discomat.ontology.namespaces import CUDS, MISO, MIO
engine = FusekiEngine(description="test engine")

session1 = Session(label="Session 1", description="session 2",engine=engine)
sim1 = Cuds(ontology_type=MISO.Simulation, description="simulation 1")
meth1 = Cuds(ontology_type=MISO.Method, description="method 1")
bc1 = Cuds(ontology_type=MISO.BoundryCondition, description="boundary condition 1")
ms1 = Cuds(ontology_type=MISO.MaterialsSystem, description="some sort of materials system 1")

for i in [meth1, ms1, bc1]:
    sim1.add(MIO.has, i)

# since we have a whole cuds created in the base (None) session, adding it to the session object requirs adding each
# component:
prox = {}
for i in [sim1, meth1, ms1, bc1]:
    prox[i] = session1.add_cuds(i)  # add all to the same session.

# change the property of sim1 through the proxy
prox[sim1].description = "sim1 created in base session, and moved with all its components later on to the specific " \
                         "session1"

sim2 = Cuds(ontology_type=MISO.Simulation, description="this is sim2")
meth2 = Cuds(ontology_type=MISO.Method, description="method 2")
bc2 = Cuds(ontology_type=MISO.BoundryCondition, description="boundary condition 2")
ms2 = Cuds(ontology_type=MISO.MaterialsSystem, description="some sort of materials system, part 2")

session2 = Session(label="session 2", description="session 2")

prox2 = {}
for i in [sim2, meth1, ms2, bc2]:
    prox2[i] = session2.add_cuds(i)  # add all to the same session.

prox2[sim2].description = "sim2 created similar to sim1"

test = Cuds(ontology_type=CUDS.Test)  # test lives in the base session.
prox2[sim2].add(CUDS.hasTest, test)  # adding link across sessions is allowed.
# sim2prox.description="this is sim2"

print("iter over sessions")
g_session = Graph()
for i in itertools.chain(session1.triples(), session2.triples()):
    g_session.add(i[:3])
gvis(g_session, "Session1_and_2.html")

print(prox2[sim2].description)

query = QueryLib.all_triples()
print(query)

print(f"getting list of graphs in the session")
lg = session2.list_graphs()
for g in lg:
    print(g)
    aq = QueryLib.augment_graph_query(query, g)
    print(aq)
    res = session2.query(aq)
    # p=prox2[sim2].properties()

    print(f"loop over graphs and query them")
    for r in res:
        print(r)

# if we add the r to a new graph, we would replicate ht the same as the iter above.


# query to get the properties (p,o) of a specific subject

subj = sim2.iri  # lets fins all properties of the sim2 in the session2 and session1 (should be null! in session1)

for g in lg:
    query = QueryLib.subject_graph(subj)
    query = QueryLib.augment_graph_query(query, g)
    print(query)
    res1 = session1.query(query)

    # print(f"res1:{len(res1)}")
    # print(f"res2:{len(res2)}")
    i = 0
    for r in res1:
        print(f"i={i} r={r}")
        i + i + 1
    res2 = session2.query(query)
    for i in res2:
        print(i)

# lets test the new query for all triples :

query = QueryLib.all_triples(subj, None, None)  # should give the same result as above.
print(query)
query = QueryLib.all_triples(None, RDF.type, CUDS.Cuds)  # should give the same result as above.
print(query)

cuds_in_session=[]
for g in lg:
    query = QueryLib.all_triples(None, RDF.type, CUDS.Cuds)  # should give the same result as above.
    query = QueryLib.augment_graph_query(query, g)  # augment it with a graph
    print(query)
    # do the two sessions, we could also loop over sessions using the session manager singleton if desired.
    res1 = session1.query(query)
    res2 = session2.query(query)

    for r in itertools.chain(res1, res2):
        print(r['s'], r['p'] , r['o'])
        # store the cuds
        cuds_in_session.append(r['s'])

# now for each cuds, get all its properties
# starting from the first one
sub=cuds_in_session[0]
newCuds=Cuds(iri=sub, label="test Cuds")

print(f"sub={sub}")
for g in lg:
    query = QueryLib.all_triples(sub, None, None)  # should give the same result as above.
    query = QueryLib.augment_graph_query(query, g)  # augment it with a graph
    res1 = session1.query(query)
    res2 = session2.query(query)

    for r in itertools.chain(res1, res2):
        print(sub, r['p'] , r['o'])
        newCuds._graph.remove((None, r['p'], None)) # if we need to avoid duplication.
        newCuds.add(r['p'] , r['o'])


gvis(newCuds, "newCuds.html")


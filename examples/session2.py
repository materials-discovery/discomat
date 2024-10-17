from discomat.cuds.cuds import Cuds
from discomat.visualisation.cuds_vis import gvis
from discomat.cuds.utils import uuid_from_string, to_iri
from discomat.session.session import Session
from rdflib import URIRef, Graph
import copy
from discomat.ontology.namespaces import CUDS, MISO, MIO


sim = Cuds(MISO.Simulation)

bc=Cuds(MISO.BoundaryConditions)

sim.add(MIO.hasPart, bc)

g=Graph()
g = sim.graph + bc.graph

gvis(sim, "sim.html")

gvis(g, "g.html")


s = Session()
s.add_cuds(sim)


from discomat.cuds.cuds import Cuds
from discomat.visualisation.cuds_vis import gvis
from discomat.cuds.utils import uuid_from_string, to_iri
from discomat.cuds.session import Session
from rdflib import URIRef, Graph
import copy
from discomat.ontology.namespaces import CUDS, MISO, MIO


c1 = Cuds(MIO.Simulation)
c1.add

gvis(c1, "c1.html")


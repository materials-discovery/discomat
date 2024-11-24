from rdflib import Namespace

MIO = Namespace("http//materials-discovery.org/semantics/mio#") # we will standardise on this.
CUDS=Namespace("http://www.ddmd.io/mio/cuds#")
MISO=Namespace("http://www.ddmd.io/miso/")
PROV = Namespace("http://www.w3.org/ns/prov#")
PC = Namespace("http://dome40.eu/semantics/pc#")
DOME = Namespace("http://dome40.eu/semantics/dome4.0_core#")
ADE = Namespace("http://dome40.eu/semantics/reasoned/ade_reasoned#")
PL = Namespace("https://dome40.eu/semantics/scenario/platforms#")

# Export the CUDS namespace for direct import
__all__ = ["CUDS"]

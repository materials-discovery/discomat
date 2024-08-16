from rdflib import Namespace

MIO=Namespace("http://www.ddmd.io/mio#")
CUDS=Namespace("http://www.ddmd.io/mio/cuds#")
# Export the CUDS namespace for direct import
__all__ = ["CUDS"]

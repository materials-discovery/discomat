from discomat.cuds.cuds import Cuds
from discomat.visualisation.cuds_vis import gvis
from discomat.utils.uuid import uuid_from_string

c = Cuds()
print(c) # pretty print, organised to name spaces.

c.print_graph()

# test uuid_from_string
print(uuid_from_string(c.pid,4))

#generate_jshtml(c._graph, c.rdf_iri, "../visualisation/html_js_template_4.html", "./test4.html")

#generate_jshtml(c._graph, c.rdf_iri, "../visualisation/html_jsonld_vis.html", "./test_jsonld1.html")

gvis(c._graph)
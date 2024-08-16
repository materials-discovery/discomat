from discomat.cuds.cuds import Cuds
from discomat.visualisation.cuds import generate_jshtml, plot_graph

c = Cuds()
print(c)
c.print_graph()

generate_jshtml(c._graph, c.rdf_iri, "../visualisation/html_js_template_4.html", "./test4.html")

generate_jshtml(c._graph, c.rdf_iri, "../visualisation/html_jsonld_vis.html", "./test_jsonld1.html")

plot_graph(c._graph, c.rdf_iri)
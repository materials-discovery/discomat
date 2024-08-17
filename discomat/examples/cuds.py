from discomat.cuds.cuds import Cuds
from discomat.visualisation.cuds_vis import gvis
from discomat.cuds.utils import uuid_from_string, to_iri
from discomat.cuds.session import Session
from rdflib import URIRef

c = Cuds()
print(c)  # pretty print, organised to name spaces.

c.print_graph()  # simply print the serialised graph

# test uuid_from_string
print(uuid_from_string(c.pid, 4))
str = "http://www.ddmd.io/mio#cuds_iri_b1b9e5d0-2a03-4665-a073-8feb57742fb1"
expected_uuid = "b1b9e5d0-2a03-4665-a073-8feb57742fb1"
extracted_uuid = uuid_from_string(str)
assert extracted_uuid == expected_uuid, f"Expected {expected_uuid} but got {extracted_uuid}"

# generate_jshtml(c._graph, c.rdf_iri, "../visualisation/html_js_template_4.html", "./test4.html")
# generate_jshtml(c._graph, c.rdf_iri, "../visualisation/html_jsonld_vis.html", "./test_jsonld1.html")
# gvis(c._graph)
# test plot of Cuds
gvis(c, f"Cuds_graph.html")

print(f"TESTING to_iti {50 * '-'}")
original_iri = "https://predicate.org/predicate"
obtained_iri = to_iri(original_iri)
print(f"original_iri: {original_iri} of type {type(original_iri)}")
print(f"Testing to_iri: obtained_iri = {obtained_iri} is of type: {type(obtained_iri)}")
assert isinstance(obtained_iri, URIRef)

original_iri = URIRef("https://predicate.org/predicate")
obtained_iri = to_iri(original_iri)
print(f"original_iri: {original_iri} of type {type(original_iri)}")
print(f"Testing to_iri:  obtained_iri = {obtained_iri} is "
      f"of type:"
      f" {type(obtained_iri)}")
assert isinstance(obtained_iri, URIRef)

original_iri = c.iri
obtained_iri = to_iri(original_iri)
print(f"original_iri: {original_iri} of type {type(original_iri)}")
print(f"Testing to_iri: obtained_iri = {obtained_iri} is of type: {type(obtained_iri)}")
assert isinstance(obtained_iri, URIRef)

# test adding triplet to Cuds
#################################
# first adding using string (iri)
# c.add("https://predicate.org/predicate_str_iri", "https://subject.org/subject_str_iri")

# then adding using URIRef's
c.add(URIRef("https://predicate.org/predicate_uriref_iri"), URIRef("https://subject.org/subject_uriref_iri"))

#  adding using IRI (str) and URIRef's

c.add("https://predicate.org/1predicate_str_iri", URIRef("https://1subject.org/subject_uriref_iri"))

#  adding using Cuds
c.add("https://predicate.org/1predicate_str_iri",c) # fixme


gvis(c, f"Cuds_graph_add_test.html")
print(f"Printing C after adding {c}")
# test session


s = Session("http://example.org/mySession/1234",
            None,
            description="This is a simple Session",
            label="session_1",
            engine="walla")
print(f"Printing session  {s}")

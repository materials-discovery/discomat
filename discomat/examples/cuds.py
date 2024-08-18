from discomat.cuds.cuds import Cuds
from discomat.visualisation.cuds_vis import gvis
from discomat.cuds.utils import uuid_from_string, to_iri
from discomat.cuds.session import Session
from rdflib import URIRef, Graph
import copy

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

print(f"TESTING to_iri \n {50 * '-'}")
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
assert isinstance(obtained_iri, URIRef), f"Expected type URIRef but got {type(obtained_iri)}"

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


print(f"Testing the Cuds.remove Method")
# c1 = Graph().parse(data=c.serialize(format="turtle"), format="turtle")
c1=copy.deepcopy(c)
gvis(c1, "deep_copy_c.html")
c1.add("ThePredicate", "TheObject")
gvis(c1, "c1.html")
c2=copy.deepcopy(c1)
c2.remove("ThePredicate", "TheObject")
gvis(c2, "c2.html")

cdiff = c1.graph - c2.graph
gvis(cdiff, "cdiff.html") # gvis works both on Cuds and graph alike.



print(f"TESTING Iter on Cuds: \n{50*'-'}")
triple_count=0
for s, p, o in c.graph:
    triple_count=triple_count +1

print(f"c has  {len(c._graph)} == {triple_count} triples")
assert (len(c._graph) == triple_count), f"iterator is not working"

if (c.rdf_iri, None, None) in c.graph:
    print("Cuds contains triples about itself!")
else:
    print(f"Something is Wrong {c.rdf_iri}")

# test session
s = Session("http://example.org/mySession/1234",
            None,
            description="This is a simple Session",
            engine="SomeEngine")
print(f"TESTING Cuds Session {50*'*'}")
print(s)
gvis(s, "cuds_local_session.html")
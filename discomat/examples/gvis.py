"""
Visualisation of graphs using Javascript via NetworkX and Pyvis

This version works well, for now, I only need to figure out why the title comes up double (heading)!
 """


import networkx as nx
from pyvis.network import Network
from rdflib import Graph, URIRef, RDF, RDFS, OWL

from discomat.visualisation.cuds_vis import gvis

g = Graph()
g.parse(data='''
    @prefix ex: <http://example.org/> .
    @prefix foaf: <http://xmlns.com/foaf/0.1/> .
    @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
    @prefix prov: <http://www.w3.org/ns/prov#> .

    ex:Person a rdfs:Class;
             rdfs:subClassOf prov:Agent .

    ex:PersonA rdf:type ex:Person;
               foaf:knows ex:PersonB ;
               ex:worksAt ex:CompanyX ;
               foaf:name "Alice" .

    ex:PersonB rdf:type ex:Person;
               foaf:name "Bob" .

    ex:CompanyX ex:locatedIn "CityY" .
''', format='turtle')

pyvis_graph_to_js(g, 'rdf_graph.html')


#g2=Graph()
#g2.parse("/Users/adham/dev/materials-discovery/MIO/mio/mio.ttl")
#pyvis_graph_to_js(g2, 'rdf_graph3.html')
#
#
#n=Graph()
#n.parse("/Users/adham/Downloads/nasicon.ttl")
#pyvis_graph_to_js(n, 'nasicon_graph.html')
#

"""
Visualisation of cuds graphs using Javascript via NetworkX and Pyvis

This version works well, for now, I only need to figure out why the title comes up double (heading)!


The main purpose is to get a graph, assuming it is not huge, and focusing on showing the main class and individual relations with basic filtering. 

"""
import argparse, urllib.parse, os, re
from typing import Union
import networkx as nx
from pyvis.network import Network
from rdflib import Graph, URIRef, RDF, RDFS, OWL
from discomat.cuds.utils import uuid_from_string, short_uuid
from discomat.cuds.cuds import Cuds
from discomat.session.session import Session
from discomat.cuds.utils import extract_fragment
from discomat.ontology.namespaces import CUDS, MIO
from rdflib import URIRef, BNode, Literal


def gvis(graph: Union[Graph, Cuds], output_html_file: str = 'mygraph.html'):
    """
    Plot the RDF graph using NetworkX and Pyvis. 
    Showing only the fragments of IRIs and ignoring RDFS.comments.

    :param graph: The RDFLib graph to vizualize.

    Could be a single CUDS or a whole graph, though performance could be an issue.


    :param output_html_file: The HTML/JS output. Simply open in a browser!

    fixme: add option to support notebooks.
    """

    #G = nx.DiGraph()
    G = nx.MultiDiGraph()
    """
    A MultiDiGraph in Python's NetworkX library is a 
    directed graph that allows multiple edges between any pair of nodes. 
    """
    # if isinstance(graph, Session):
    #     # get all graphs in the session, including the default
    #     x=Graph()  # fix.
    #     for g in graph:  # i.e. g in session.
    #         x=x+g
    #     graph = x+graph._graph
    # elif isinstance(graph, Cuds):
    #     graph = graph._graph

    # this is a slight regression, the above took all graphs, but it works only for sessions with an engie which is rdflib one.

    if isinstance(graph, Cuds):
        graph = graph._graph

    for s, p, o in graph:

        # Ignore comments, as some are quite large.
        if p == RDFS.comment:
            continue

        if (p == RDF.type and o in {RDFS.Class, OWL.Class, OWL.DatatypeProperty, OWL.ObjectProperty,
                                    OWL.NamedIndividual}):
            continue

        if (p in {RDFS.range, RDFS.domain}):
            continue

        s_fragment = extract_fragment(str(s))
        p_fragment = extract_fragment(str(p))
        o_fragment = extract_fragment(str(o))

        # s_fragment = uuid_from_string(s_fragment, 5) or s_fragment
        # o_fragment = uuid_from_string(o_fragment, 5) or o_fragment
        if len(o_fragment)>8:
            o_fragment = short_uuid(o_fragment)

        if len(s_fragment) > 8:
            s_fragment = short_uuid(s_fragment)


        # fixme: quick code, it has duplication and not efficient...

        # Identify if the subject or object is a class
        if (s, None, RDFS.Class) in graph or (s, None, OWL.Class) in graph:
            G.add_node(s_fragment, title=str(s), color='orange')  # classes are RED
        elif (s, None, None) not in graph:
            G.add_node(s_fragment, title=str(s), color='green')
        else:
            G.add_node(s_fragment, title=str(s), color='red')

        if (o, None, RDFS.Class) in graph or (o, None, OWL.Class) in graph:
            G.add_node(o_fragment, title=str(o), color='orange')
        elif (o, None, None) not in graph:
            G.add_node(o_fragment, title=str(o), color='green')
        else:
            G.add_node(o_fragment, title=str(o), color='red')

            # Add edges, using thick orange for subclass relations
        edge_color = 'orange' if p == RDFS.subClassOf else 'red'
        edge_width = 5 if p == RDFS.subClassOf else 2

        G.add_edge(s_fragment, o_fragment, label=p_fragment, title=str(p), color=edge_color, width=edge_width)
        # edges = G.edges(data=True)
        # for edge in edges:
        #     print(edge)
    # Create a Pyvis network
    net = Network(
        height='850px',
        heading=f"Visualisation of {output_html_file}",
        neighborhood_highlight=True,
        directed=True,
        notebook=False,  # Ensure this is set to False for non-notebook environments
        select_menu=True,  # Optional: to select nodes and edges in the plot
        filter_menu=True

    )

    net.set_options("""
    var options = {
        "configure": {
    "enabled": true,
    "filter": ["physics"]
        },
        "physics": {
    "barnesHut": {
      "gravitationalConstant": -36200,
            "springLength": 40

    },
    "minVelocity": 0.75
  }
    }
    """)

    net.from_nx(G)  # Create directly from the NetworkX graph

    #net.show_buttons(filter_=['physics', 'nodes'])  # Show physics control in the UI
    # for edge in net.edges:
    #     print(edge)
    # Save the network to an HTML file
    net.write_html(output_html_file)  # Write HTML file

    file_uri = os.path.join(os.getcwd(), output_html_file)
    file_uri = f"file://{urllib.parse.quote(file_uri)}"

    print(f"Graph saved to {file_uri}")



def gvis2 (graph: Union[Graph, Cuds], output_html_file: str = 'mygraph.html'):
    """
    Plot the RDF graph using NetworkX and Pyvis.
    Showing only the fragments of IRIs and ignoring RDFS.comments.

    :param graph: The RDFLib graph to vizualize.

    Could be a single CUDS or a whole graph, though performance could be an issue.


    :param output_html_file: The HTML/JS output. Simply open in a browser!

    fixme: add option to support notebooks.
    """

    #G = nx.DiGraph()
    G = nx.MultiDiGraph()
    """
    A MultiDiGraph in Python's NetworkX library is a 
    directed graph that allows multiple edges between any pair of nodes. 
    """
    # if isinstance(graph, Session):
    #     # get all graphs in the session, including the default
    #     x=Graph()  # fix.
    #     for g in graph:  # i.e. g in session.
    #         x=x+g
    #     graph = x+graph._graph
    # elif isinstance(graph, Cuds):
    #     graph = graph._graph

    # this is a slight regression, the above took all graphs, but it works only for sessions with an engie which is rdflib one.

    if isinstance(graph, Cuds):
        graph = graph._graph



    for s, p, o in graph:

        # Ignore comments, as some are quite large.
        if p == RDFS.comment:
            continue

        if (o in {RDFS.Class, OWL.Class, OWL.DatatypeProperty, OWL.ObjectProperty,
                                    OWL.NamedIndividual, CUDS.Cuds}):
            continue

        if (p in {RDFS.range, RDFS.domain, CUDS.description}):
            continue

        s_fragment = extract_fragment(str(s))
        p_fragment = extract_fragment(str(p))
        o_fragment = extract_fragment(str(o))

        # s_fragment = uuid_from_string(s_fragment, 5) or s_fragment
        # o_fragment = uuid_from_string(o_fragment, 5) or o_fragment
        if len(o_fragment)>8:
            o_fragment = short_uuid(o_fragment)

        if len(s_fragment) > 8:
            s_fragment = short_uuid(s_fragment)


        # fixme: quick code, it has duplication and not efficient...

        # Identify if the subject or object is a class
        if (s, None, RDFS.Class) in graph or (s, None, OWL.Class) in graph:
            G.add_node(s_fragment, title=str(s), color='orange')  # classes are RED
        elif (s, None, None) not in graph:
            G.add_node(s_fragment, title=str(s), color='green')
        else:
            G.add_node(s_fragment, title=str(s), color='red')

        if (o, None, RDFS.Class) in graph or (o, None, OWL.Class) in graph:
            G.add_node(o_fragment, title=str(o), color='orange')
        elif (o, None, None) not in graph:
            G.add_node(o_fragment, title=str(o), color='green')
        else:
            G.add_node(o_fragment, title=str(o), color='red')

            # Add edges, using thick orange for subclass relations
        edge_color = 'orange' if p == RDFS.subClassOf else 'red'
        edge_width = 5 if p == RDFS.subClassOf else 2

        G.add_edge(s_fragment, o_fragment, label=p_fragment, title=str(p), color=edge_color, width=edge_width)
        # edges = G.edges(data=True)
        # for edge in edges:
        #     print(edge)
    # Create a Pyvis network
    net = Network(
        height='1200px',
        heading=f"Visualisation of {output_html_file}",
        neighborhood_highlight=True,
        directed=True,
        notebook=False,  # Ensure this is set to False for non-notebook environments
        select_menu=False,  # Optional: to select nodes and edges in the plot
        filter_menu=False

    )

  #   net.set_options("""
  #   var options = {
  #       "configure": {
  #   "enabled": true,
  #   "filter": ["physics"]
  #       },
  #       "physics": {
  #   "barnesHut": {
  #     "gravitationalConstant": -36200,
  #           "springLength": 40
  #
  #   },
  #   "minVelocity": 0.75
  # }
  #   }
  #   """)

    net.from_nx(G)  # Create directly from the NetworkX graph

    #net.show_buttons(filter_=['physics', 'nodes'])  # Show physics control in the UI
    # for edge in net.edges:
    #     print(edge)
    # Save the network to an HTML file
    net.write_html(output_html_file)  # Write HTML file

    file_uri = os.path.join(os.getcwd(), output_html_file)
    file_uri = f"file://{urllib.parse.quote(file_uri)}"

    print(f"Graph saved to {file_uri}")

# Usage example
# g = Graph()
# g.parse(data='''
#     @prefix ex: <http://example.org/> .
#     @prefix foaf: <http://xmlns.com/foaf/0.1/> .
#     @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
#     @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
#     @prefix prov: <http://www.w3.org/ns/prov#> .
# 
#     ex:Person a rdfs:Class;
#              rdfs:subClassOf prov:Agent .
# 
#     ex:PersonA rdf:type ex:Person;
#                foaf:knows ex:PersonB ;
#                ex:worksAt ex:CompanyX ;
#                foaf:name "Alice" .
# 
#     ex:PersonB rdf:type ex:Person;
#                foaf:name "Bob" .
# 
#     ex:CompanyX ex:locatedIn "CityY" .
# ''', format='turtle')
# 
# pyvis_graph_to_js(g, 'rdf_graph.html')
# 
# 
# g2=Graph()
# g2.parse("/Users/adham/dev/materials-discovery/MIO/mio/mio.ttl")
# pyvis_graph_to_js(g2, 'rdf_graph3.html')
# 
# 
# n=Graph()
# n.parse("/Users/adham/Downloads/nasicon.ttl")
# pyvis_graph_to_js(n, 'nasicon_graph.html')

###### gvis 3: If several subjects point to the same object, we clone the object node insteading of using the same point for visualization. ######
def gvis3(
    graph: Union[Graph, Cuds],
    output_html_file: str = 'mygraph.html',
    split_object_nodes_on_predicates=None,
    clean: bool = False,
    show_label: bool = False,
    core_predicates = None,
    clone_object_nodes_on_predicates: bool = True,   
):

    """
    choose to split (clone) Literal objects (labels/values) or not.
    Keep only CUDS-CUDS relationship for visualization.

    **** How to use it: ****
    gvis3(gall, output_html_file=" .html", clean=True) for clean view (no uuid, pid, description, creation time, LABLE etc)
    gvis3(gall, output_html_file=" .html", clean=True, show_label=True) for clean view WITH LABELS (labels are mnemonic by default)
    gvis3(gall, output_html_file=" .html") for full view
    gvis3(
        g,
        "custom.html",
        split_object_nodes_on_predicates={RDF.type, RDFS.subClassOf},
        clone_object_nodes_on_predicates=False,   # dont clone object nodes for the listed predicates
    )
    gvis3(g, "big.html", clean=True, clone_object_nodes_on_predicates=False)

    """



    G = nx.MultiDiGraph()
 

    # split RDF.type by default
    if split_object_nodes_on_predicates is None:
        split_object_nodes_on_predicates = {RDF.type}

    # Core view: keep only type/label/subClassOf edges unless user overrides
    if core_predicates is None:
        core_predicates = {RDF.type, RDFS.label, RDFS.subClassOf}

    if isinstance(graph, Cuds):
        graph = graph._graph

    clone_counter = 0

    def _short_label(term) -> str:

        if isinstance(term, Literal):
            return str(term)
        if isinstance(term, BNode):
            return short_uuid(str(term))
        frag = extract_fragment(str(term))
        return short_uuid(frag) if len(frag) > 8 else frag

    def _term_key(term) -> str:
       
        if isinstance(term, URIRef):
            return str(term) 
        if isinstance(term, BNode):
            return f"_:{str(term)}"  
        if isinstance(term, Literal):

            return term.n3()
        return str(term)

    def _node_id(term, *, force_clone: bool = False, clone_hint: str = "") -> str:

        nonlocal clone_counter
        base = _term_key(term)
        if not force_clone:
            return base
        clone_counter += 1
        return f"{base}__clone_{clone_counter}__{clone_hint}"

    def _add_node(node_id: str, *, label: str, title: str, color: str):
        if node_id not in G:
            G.add_node(node_id, label=label, title=title, color=color)



    for s, p, o in graph:
        p_name = extract_fragment(str(p)).lower()

        # Ignore comments, as some are quite large.
        if p == RDFS.comment:
            continue

        if clean:
            if p == CUDS.iri:
                continue

            if p_name in {"uuid", "pid", "creation_time", "creationtime"}:
                continue

            if (not show_label) and (p_name == "label"):
                continue

            if o in {
                RDFS.Class, OWL.Class, OWL.DatatypeProperty, OWL.ObjectProperty,
                OWL.NamedIndividual, CUDS.Cuds
            }:
                continue

            if p in {RDFS.range, RDFS.domain, CUDS.description}:
                continue



        s_label = _short_label(s)
        p_fragment = extract_fragment(str(p))
        o_label = _short_label(o)

        s_id = _node_id(s, force_clone=False)


        # split_obj = p in split_object_nodes_on_predicates
        # o_id = _node_id(o, force_clone=split_obj, clone_hint=f"{s_id}|{p_fragment}")

        # Always split Literal objects (e.g. labels/values), regardless of predicate.
        # Also split objects for predicates explicitly listed (e.g. rdf:type).
        split_obj = isinstance(o, Literal) or (clone_object_nodes_on_predicates and (p in split_object_nodes_on_predicates))

        o_id = _node_id(o, force_clone=split_obj, clone_hint=f"{s_id}|{p_fragment}")

        # Node styling (rough heuristic)
        if (s, None, RDFS.Class) in graph or (s, None, OWL.Class) in graph:
            _add_node(s_id, label=s_label, title=str(s), color='orange')
        elif (s, None, None) not in graph:
            _add_node(s_id, label=s_label, title=str(s), color='green')
        else:
            _add_node(s_id, label=s_label, title=str(s), color='red')

        if (o, None, RDFS.Class) in graph or (o, None, OWL.Class) in graph:
            _add_node(o_id, label=o_label, title=str(o), color='orange')
        elif (o, None, None) not in graph:
            _add_node(o_id, label=o_label, title=str(o), color='green')
        else:
            _add_node(o_id, label=o_label, title=str(o), color='red')

        edge_color = 'orange' if p == RDFS.subClassOf else 'red'
        edge_width = 5 if p == RDFS.subClassOf else 2

        G.add_edge(s_id, o_id, label=p_fragment, title=str(p), color=edge_color, width=edge_width)

    net = Network(
        height='1200px',
        heading="",
        neighborhood_highlight=True,
        directed=True,
        notebook=False,
        select_menu=False,
        filter_menu=False
    )

    net.from_nx(G)

    net.write_html(output_html_file)

    #  heading settings
    title_text = f"Visualisation of {os.path.basename(output_html_file)}"

    with open(output_html_file, "r", encoding="utf-8") as f:
        html = f.read()

    custom_h1 = f'\n<h1 style="text-align:center; font-weight:bold; margin: 20px 0;">{title_text}</h1>\n'

    if title_text not in html:
        html = re.sub(r"(<body[^>]*>)", r"\1" + custom_h1, html, count=1, flags=re.IGNORECASE)

    with open(output_html_file, "w", encoding="utf-8") as f:
        f.write(html)



    file_uri = os.path.join(os.getcwd(), output_html_file)
    file_uri = f"file://{urllib.parse.quote(file_uri)}"
    print(f"Graph saved to {file_uri}")




def main():
    parser = argparse.ArgumentParser(description="Visualize an ontology into a javascript/html file.")

    parser.add_argument('in_file', type=str, help='Input File Path  (e.g.; ontology.ttl).')
    parser.add_argument('out_file', type=str, nargs='?', default='mygraph.html', help='HTML File Path  (e.g.; '
                                                                                      'ontology.html).')

    args = parser.parse_args()

    g = Graph()
    g.parse(args.in_file)
    gvis(g, args.out_file)


# Check if the script is being run directly
if __name__ == "__main__":
    main()
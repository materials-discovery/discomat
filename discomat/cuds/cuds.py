from typing import Tuple, Union, Optional
import datetime
import inspect
import uuid
import warnings
from collections import defaultdict
from functools import wraps
from typing import Union
from urllib.parse import urlparse, urldefrag, urlsplit

from rdflib import Graph, URIRef, RDF

from discomat.session.session_manager import SessionManager
from discomat.cuds.utils import to_iri, mnemonic_label
from discomat.ontology.namespaces import CUDS, MIO
from discomat.ontology.ontomap import ONTOMAP

# todo: enhance and use pydntic or dataclass across the board.
Triple = Tuple[str, str, str]
Quad = Tuple[str, str, str, Optional[str]]
QuadOrTriple = Union[Triple, Quad]


def add_to_root(func):
    """
    decorator to add connection with root in a graph.
    """

    @wraps(func)
    def wrapper(*args):
        _self = args[0]
        s = args[1]
        p = args[2]
        o = args[3]

        if len(args) == 5:
            graph_id = args[4] or _self.default_graph_id
        else:
            graph_id = _self.default_graph_id

        # graph_id = graph_id or _self.default_graph_id
        print(f"in add_to_root: s={s}, p={p}, o={o}, gid={graph_id}")
        print(list(_self.graphs.keys()))
        try:
            graph = _self.graphs[graph_id]
        except KeyError:
            raise KeyError(f"Graph {graph_id} does not exist in this session. I cannot yet create graphs on teh fly.")

        # check if the graph has a root
        query = f"""
            SELECT ?subject WHERE {{
                ?subject <{RDF.type}> <{CUDS.RootNode}> .
            }}
        """
        res = graph.query(query)
        # for row in res:
        #     print(f"---> Result Row:", row)
        subjects = [str(row.subject) for row in res]
        has_root = subjects[0] if len(subjects) > 0 else None
        # print(f"---> has_root = {subjects}")
        # if not has_root:
        #     print("=====================================")
        #     print(f"No Root in Graph {graph}")
        #     print("=====================================")
        #     return func(*args, **kwargs)
        # else:
        #     print("We have a ROOT \n")
        # is this subject not connected to anything, connect to has_root.
        query = f"""
             ASK WHERE {{
                ?subject ?predicate <{s}> .
             }}
        """
        s_as_o = bool(graph.query(query).askAnswer)
        if s_as_o:
            # print(f"{s} is not orphan object")
            return func(*args)
        else:
            print(f"we are connecting {s} to {has_root}")

        graph.add((graph_id, CUDS.ConnectedTo, to_iri(s)))

        return func(*args)

    return wrapper


class Cuds:
    """

    CUDS the Common Universal Data Structures implementation in DiscoMat.

    Everything, when possible, is a CUDS (Common Universal data Structure)!
    CUDS has built in support for provenance and persistent identifiers (PID) though we are not
    doing this with a "formal external authority yet".

    Unlike SimPhoNy, we do not aim to make every ontology entity (class or individual, or relation) etc
    as a python class, but keep its rdf nature. CUDS is simply a class that adds one more layer to any IRI
    so that we can trace it and add some bookkeeping, including translating between wengine backends and storing.
    The below implementation is the only one we need to keep in sync with the ontology (see mio.owl).
    """

    # todo use pydantic and data structures instead of complex number of args

    def __init__(self,
                 ontology_type=None,
                 iri: Union[str, URIRef] = None,
                 description=None,
                 label=None,
                 pid: Union[str, URIRef] = None):  # fix me, we need to organise this using tying hints.
        """
        iri: The iri should be unique, but default it is a uuid with MIO/CUDS as prefix.

        Ontology_type: this is equivalent to RDF.type

        Pid: a persistent identifier in the FAIR sense (locally managed for now)

        Description:for human consumption

        Label:for human consumption, by default is a mnemonic

        A Cuds will have an iri, which is unique for this instance of the CUDS.

        Cuds has a modified __setattr_ which uses a rdf graph to store the properties
        of the CUDS, these are not limited to data properties. So doing:

        c=Cuds()
        c.foo, and if ONTOMAP[foo]=bar, then this translates to c._g.add(c.iri, foo, bar)
        otherwise it is a normal attribute (if already defined). 
        
        This is a step towards having an all ontology classes represented on the fly as classes without the
        need to load them in.
        """

        self._graph = Graph()  # A CUDS is a little Graph Data Structure. This is the container concept.

        _uuid = uuid.uuid4()
        self.iri = to_iri(iri) if iri else URIRef(f"https://www.ddmd.io/mio#cuds_iri_{_uuid}")
        self.add(CUDS.iri, to_iri(self.iri))
        self.add(RDF.type, CUDS.Cuds)

        self.uuid = _uuid
        self.rdf_iri = self.iri  # fixme this is probably not needed. can be factored out

        if description is not None and len(description) > 500:
            raise ValueError("in {self.path}: The description cannot exceed 500 characters")

        if label is not None and len(str(label)) > 20:
            raise ValueError("in {self.path}: The label cannot exceed 20 characters")

        self.description = description or None  # f"This is a CUDS without Description!"
        self.label = str(label) if label is not None else mnemonic_label(2)

        self.ontology_type = ontology_type if ontology_type else MIO.Cuds

        self.pid = pid or f"http://www.ddmd.io/mio#cuds_pid_{self.uuid}"
        # fixme use str(CUDS) or {str(MIO)}cuds_pid/... should stay the same for the same CUDS

        self.creation_time = datetime.datetime.now()

        # self.session = None
        """
        if session is not None, we have a proxy (in the session). 
        """

    def __setattr__(self, key, value):
        if key == 'iri':
            super().__setattr__(key, value)
            return
        elif key in ONTOMAP:
            if key != 'ontology_type':  # only one value is allowed, except the type.
                self._graph.remove((to_iri(self.iri), to_iri(ONTOMAP[key]), None))
            self._graph.add((to_iri(self.iri), to_iri(ONTOMAP[key]), to_iri(value)))
        else:
            super().__setattr__(key, value)  # fixme there should be no "normal attributes" apart from iri

    def __getattr__(self, key):
        if key in ONTOMAP:
            return self._graph.value(subject=to_iri(self.iri), predicate=to_iri(ONTOMAP[key]), any=True)
        else:
            super().__getattribute__(key)

    @property
    def properties(self):
        # Retrieve all properties (predicates) and objects for c.iri
        properties = defaultdict(list)
        for p, o in self._graph.predicate_objects(self.iri):
            namespace, fragment = self.split_uri2(p)
            properties[namespace].append((fragment, o))
        return properties

    def split_uri(self, uri):  # fixme move to utils
        # Split the URI into namespace and fragment
        parsed_uri = urlparse(uri)
        path = parsed_uri.path
        if "#" in path:
            namespace, fragment = path.split("#")
        elif "/" in path:
            namespace, fragment = path.rsplit("/", 1)
        else:
            namespace, fragment = path, ''
        return parsed_uri.scheme + "://" + parsed_uri.netloc + namespace + "/", fragment

    def print_graph(self):
        # Print the graph in a readable format (e.g., Turtle)
        print(self._graph.serialize(format="turtle"))

    def serialize(self):
        # serialise the CUDS and return a string (as ttl).
        return self._graph.serialize(format="turtle")

    def __repr__(self):
        # Pretty print format for the instance
        print("=============")
        properties = self.properties
        output = [f"\n============================\n Printing The CUDS with iri: {self.rdf_iri}"]
        for namespace, props in properties.items():
            output.append(f"- Namespace: {namespace}")
            for fragment, obj in props:
                output.append(f"  - {fragment}: {obj}")
            output.append("")  # Add a blank line between namespaces
        return "\n".join(output)

    def split_uri2(self, uri):  # fixme move to utils
        # Split the URI into namespace and fragment
        frag_split = urldefrag(uri)
        if frag_split[1]:  # If there's a fragment after #
            return frag_split[0] + "#", frag_split[1]
        else:  # Otherwise split at the last /
            split = urlsplit(uri)
            path_parts = split.path.rsplit('/', 1)
            if len(path_parts) > 1:
                return split.scheme + "://" + split.netloc + path_parts[0] + "/", path_parts[1]
            else:
                return uri, ''  # Fallback case

    @property
    def properties2(self):
        # Retrieve all properties (predicates) and objects for c.iri
        properties = {}
        for p, o in self._graph.predicate_objects(self.rdf_iri):
            properties[p] = o
        return properties

    def __repr__2(self):
        # Pretty print format for the instance
        properties = self.properties
        properties_str = "\n".join([f"  {p}: {o}" for p, o in properties.items()])
        return f"c.iri: {self.iri}\nProperties:\n{properties_str}"

    def add(self, p, o):
        if isinstance(o,Cuds):
            o=o.iri
        try:
            self._graph.add((self.iri, to_iri(p), to_iri(o)))
        except TypeError as e:
            print(f"Wrong typ {e}")
            return None

    def remove(self, p, o):
        try:
            self._graph.remove((self.rdf_iri, to_iri(p), to_iri(o)))
        except TypeError as e:
            print(f"Wrong typ {e}")
            return None

    def __iter__(self):
        # Delegate the iteration to rdflib Graph
        return iter(self._graph)

    @property
    def graph(self):
        return self._graph

class ProxyCuds():  # should be inheriting from ABC_CUDS rather form CUDS (so is CUDS)
    """
    A CUDS proxy, a way to handle a CUDS which is stored in a remote session and hence remote engine.
    To create it, we need a real CUDS, i.e., the assumption is to convert a real CUDS to a proxy one.


    if the CUDS is already in a remote session, but not in the local session,
    we need to use the session.get_cuds with
    the iri to get it as a proxy.

    c=Cuds()
    c_proxy=ProxyCuds(c)

    If it is in the session, and we need to create a proxy to it
    c_proxy = session.get_cuds(iri)

    i.e., if the cuds is in a remote session, get_cuds simply gets a proxy to it.
    """

    def __init__(self,
                 cuds: Cuds):

        ontology_type = CUDS.CudsProxy
        # note we cannot use super, as the self will still be an instance of this class, i.e., a proxy one.
        # and this will lead to recursion.
        # super().__init__(ontology_type=ontology_type, iri=cuds.iri, pid=cuds.pid, description=cuds.description,
        #                  label=cuds.label)
        object.__setattr__(self, 'session_id', cuds.session_id) # todo: raise error if no session id is defined.
        object.__setattr__(self, 'iri', cuds.iri)
        object.__setattr__(self, '_graph', Graph())

        for _ in cuds._graph:
            self._graph.add(_) #fixme delete this and keep only those attributes relevnt to the proxy.

        sm = SessionManager()
        s = sm.get_session(self.session_id)
        object.__setattr__(self, 'session', s)
        if isinstance(s, bool):
            print(f"cannot find session - fixme: critical proxy cuds fail!") # fixme: proxy cuds should fail if not session defined.
        else:
            print(f"ProxyCuds: Creating a CUDS proxy in the session  {s.session_id} \ n Note: graph support is WIP")

    def __setattr__(self, key, value):
        self.session.proxy_handler(self.iri, "setattr", key=key, value=value)

    def __getattr__(self, key):
        return self.session.proxy_handler(self.iri, "getattr", key=key)

    def properties(self):
        # Retrieve all properties (predicates) and objects for c.iri
        properties = self.session.proxy_handler(self.iri, "properties")
        return properties

    def print_graph(self):
        # Print the graph in a readable format (e.g., Turtle)
        print(self.session.proxy_handler(self.iri, "print_graph"))

    def serialize(self):
        # serialise the CUDS and return a string (as ttl).
        # a CUDS has only first neighbor relations, i.e, one edge only (depth =1)
        return self.session.proxy_handler(self.iri, "serialize")

    # def __repr__(self):
    #     # Pretty print format for the instance
    #     properties = self.properties
    #     output = [f"\n ** Printing The (Proxy) CUDS with iri: {self.iri}"]
    #     for namespace, props in properties.items():
    #         output.append(f"- Namespace: {namespace}")
    #         for fragment, obj in props:
    #             output.append(f"  - {fragment}: {obj}")
    #         output.append("")  # Add a blank line between namespaces
    #     return "\n".join(output)

    def add(self, p, o):
        self.session.proxy_handler(self.iri, "add", p=p, o=o) # we could have done proxy_handler.add too, but we do this way as it may be useful for even more network support.

    def remove(self, p, o):
        self.session.proxy_handler(self.iri, "remove", p, o)

    def __iter__(self):
        # Delegate the iteration to session proxy handler
        return self.session.proxy_handler(self.iri, "iter")

    @property
    def graph(self):
        warnings.warn(
            "cuds.graph is not available for proxy CUDS and is deprecated and will be removed in a future version from "
            "the real CUDS. "
            "Use iter method instead.",
            DeprecationWarning,
            stacklevel=2
        )
        return NotImplemented

import random
import re
import uuid
from functools import wraps
from typing import Union
from urllib.parse import urlparse

from mnemonic import Mnemonic
from rdflib import URIRef, Literal


def to_iri(e: Union[str, URIRef]):
    if isinstance(e, str) and (e.startswith("http://") or e.startswith("https://")):
            e = URIRef(e)
    elif isinstance(e, URIRef):
        pass
    elif isinstance(e, uuid.UUID):
        e = Literal(e)
    elif e is None:
        return Literal(None)
    else:
        e = Literal(str(e))
    return e


from rdflib import URIRef

def to_sparql_query(o):
    """
    If the object is an IRI (including URIRef), it is enclosed in angle brackets;
    if it is a literal, it is enclosed in double quotes.

    o: Object value, either an IRI (URIRef or string) or a literal.
    """
    if isinstance(o, URIRef):  #fixme, check if rdflib literal as well.
        return f"<{str(o)}>"
    elif isinstance(o, str) and (o.startswith("http://") or o.startswith("https://")):
        return f"<{o}>"
    else:
        return f'"{o}"'  # as a literal

def uuid_from_string(s: str = None, length: int = None):
    """

    scan string, identify a UUID part and either return it in whole, or the last length chars.
    """

    # Regular expression pattern for UUID
    # uuid_pattern = re.compile(r'\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b')
    uuid_pattern = re.compile(r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}')

    # Search for UUID in the string
    match = uuid_pattern.search(s)

    if match:
        # Extract the UUID
        uuid = match.group(0)
        return uuid if length is None else uuid[-5:]
    else:
        return None


def short_uuid(s: str) -> str:
    # Regular expression to find the UUID pattern in the string
    uuid_pattern = r'(\w{8}-\w{4}-\w{4}-\w{4}-\w{12})'

    match = re.search(uuid_pattern, s)
    if not match:
        if len(s) > 50:
            return (s[-12:])
        else:
            return (s)
    # Everything before the UUID is treated as the prefix
    prefix = s[:match.start()]
    uuid = match.group(1)

    # Get the last 4 characters of the UUID
    short_suffix = uuid[-4:]

    # Combine prefix with short suffix
    return f"{prefix}{short_suffix}".rstrip('_')  # Remove trailing underscore if no prefix


def extract_fragment(iri):  # we have this in so many versions and incarnations, should fixme move to utils
    """extract the fragment or the last part of an IRI."""
    return iri.split('#')[-1].split('/')[-1]


def mnemonic_label(number_of_words: int = 2):
    # word_site = "https://www.mit.edu/~ecprice/wordlist.10000"
    # response = requests.get(word_site)
    # WORDS = response.content.splitlines()
    # print (WORDS)

    mnemo = Mnemonic("english")
    words = mnemo.generate(strength=128)
    label = '_'.join(random.sample(list(words.split()), number_of_words))
    # seed = mnemo.to_seed(words, passphrase="")
    # entropy = mnemo.to_entropy(words)
    return label


def _arg_to_iri(func):
    def wrapper(*args, **kwargs):
        args = tuple(to_iri(arg) for arg in args)
        kwargs = {key: to_iri(value) for key, value in kwargs.items()}
        return func(*args, **kwargs)

    return wrapper


def arg_to_iri(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if args and hasattr(args[0], "__class__"):
            self, *new_args = args
            new_args = tuple(to_iri(arg) for arg in new_args)
            new_kwargs = {key: to_iri(value) for key, value in kwargs.items()}
            return func(self, *new_args, **new_kwargs)
        else:
            new_args = tuple(to_iri(arg) for arg in args)
            new_kwargs = {key: to_iri(value) for key, value in kwargs.items()}
            return func(*new_args, **new_kwargs)

    return wrapper


def pr(s):
    print(s.format(**locals()))


def prd(s):
    dashes = '-' * len(s)
    # print(dashes)
    print(s)
    print(dashes)


def split_uri(uri):  # fixme move to utils
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


"""
simple but often used sparql queries

"""


class QueryLib:
    @staticmethod
    def all_triples(s=None, p=None, o=None):
        """

        Returns
        -------
        return all triples in the default graph.
        <{s}>
        """
        s = f"<{s}>" if s else f"?s"
        p = f"<{p}>" if p else f"?p"
        o = f"<{o}>" if o else f"?o"

        return f"""
        SELECT ?s ?p ?o WHERE {{
          {s} {p} {o} .
        }}
        """

    @staticmethod
    def all_subjects():
        return """
        SELECT DISTINCT ?s WHERE {
          ?s ?p ?o .
        }"""

    @staticmethod
    def all_predicates():
        return """
        SELECT DISTINCT ?p WHERE {
          ?s ?p ?o .
        }"""

    @staticmethod
    def all_objects():
        return """
        SELECT DISTINCT ?o WHERE {
          ?s ?p ?o .
        }"""

    @staticmethod
    def subject_contains_string(substring):
        return f"""
        SELECT ?s ?p ?o WHERE {{
          ?s ?p ?o .
          FILTER(CONTAINS(LCASE(STR(?s)), "{substring.lower()}"))
        }}"""

    @staticmethod
    def objects_containing_string(substring):
        return f"""
        SELECT ?s ?p ?o WHERE {{
          ?s ?p ?o .
          FILTER(CONTAINS(LCASE(STR(?o)), "{substring.lower()}"))
        }}"""

    @staticmethod
    def predicates_containing_string(substring):
        return f"""
            SELECT ?s ?p ?o WHERE {{
              ?s ?p ?o .
              FILTER(CONTAINS(LCASE(STR(?p)), "{substring.lower()}"))
            }}"""

    @staticmethod
    def triples_with_literal_objects():
        return """
            SELECT ?s ?p ?o WHERE {
              ?s ?p ?o .
              FILTER(isLiteral(?o))
            }"""

    @staticmethod
    def triples_with_p_and_o_containing(pstr, ostr):
        return f"""
        SELECT ?s ?p ?o WHERE {{
          ?s ?p ?o .
          FILTER(CONTAINS(LCASE(STR(?p)), "{pstr.lower()}") && CONTAINS(LCASE(STR(?o)), "{ostr.lower()}"))
        }}"""

    @staticmethod
    def triples_with_p_and_o(pstr, ostr):
        return f"""
        SELECT ?s ?p ?o
        WHERE {{
          BIND (<{pstr}> AS ?p) .
          BIND (<{ostr}> AS ?o) .
          ?s ?p ?o .
          }}
        """

    @staticmethod
    def all_graphs_in_dataset():
        return """
        SELECT ?g ?s ?p ?o
        WHERE {
          {
            GRAPH ?g {
              ?s ?p ?o .
            }
          }
          UNION
          {
            VALUES ?g { UNDEF } .
            ?s ?p ?o .
          }
        }
        """

    @staticmethod
    def subject_as_graph(s, max_depth):
        # supposed to find al s, p, o related to s up to specific depth, downward.
        return """
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

            SELECT DISTINCT ?depth ?o WHERE {{
              VALUES ?subject {{ <{subject}> }}

              # Traverse up to depth n, capturing all intermediate objects
              ?subject (rdf:Property|!rdf:Property){{1,{depth}}} ?o .

              # Calculate depth by counting the properties traversed (optional)
              BIND((strlen(str(?propertyPath)) - strlen(replace(str(?propertyPath), "/", ""))) AS ?depth)
            }}
            """.format(subject=s, depth=max_depth)

    @staticmethod
    def subject_relation(s, properties):

        if properties:
            property_path = "|".join(f"<{prop}>" for prop in properties)
        else:
            return []
        return f"""
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

            SELECT DISTINCT ?o WHERE {{
            VALUES ?s {{ <{s}> }}
            ?s ({property_path}) ?o .
            }}
            """

    @staticmethod
    def subject_graph(s):
        return f"""
        SELECT ?p ?o
        WHERE {{
            <{s}> ?p ?o .
        }}
        """

    @staticmethod
    def augment_graph_query(query, graph_id):
        """
        tke a query and a named grap iri and retuen the query for the graph.
        useful when looping over graphs inclduing the default one and performing the same operation.
        Parameters
        ----------
        query
        graph

        Returns
        -------

        """
        graph_query = f"""
            SELECT ?s ?p ?o
            WHERE {{
              GRAPH <{graph_id}> {{
                {query}
              }}
            }}
            """

        return graph_query


class InsertLib:    # change to updateLib
    @staticmethod
    def add_triple_(s, p, o, g=None):
        """
        Return a SPARQL query to add a triple to a graph.

        :param s: The subject of the triple (URI or literal).
        :param p: The predicate of the triple (URI).
        :param o: The object of the triple (URI or literal).
        :param g: Optional graph URI to insert the triple into.
        :return: A proper SPARQL query string.
        """
        query = f"INSERT DATA {{\n"

        if g:
            query += f"  GRAPH <{g}> {{ <{s}> <{p}> <{o}> }}\n"
        else:
            query += f"  <{s}> <{p}> <{o}>\n"

        query += "}"

        return query

    @staticmethod
    def add_triple (s, p, o, graph_id=None, prefixes=None):
        """
        Build an INSERT DATA query, with optional graph (as iri) and prefixes (as dict).
        :param s: The subject of the triple
        :param p: The predicate of the triple
        :param o: The object of the triple
        :param graph_id: Optional, the graph iri where the data will be inserted
        :param prefixes: Optional, a dictionary of prefixes {short_name: full_URI}
        :return: The full SPARQL query as a string
        todo: we can add multiple inset liines (s p o) in one go, we can enhance so that the input is a list of s,o,p rather than just one.
        this will enhance performance.
        """

        prefix_section = ""

        # If prefixes are provided, expand them into the query
        if prefixes:
            for short_name, full_uri in prefixes.items():
                prefix_section += f"PREFIX {short_name}: <{full_uri}>\n"

        # query with  GRAPH section
        if graph_id:
            update_query = f"""
            {prefix_section}
            INSERT DATA {{
                GRAPH {graph_id} {{
                    {s} {p} {o} .  
                }}
            }}
            """
        else:
            update_query = f"""
            {prefix_section}
            INSERT DATA {{
                {s} {p} {o} .
            }}
            """

        return update_query


    @staticmethod
    def del_triple (subj=None, pred=None, obj=None, graph_id=None, prefixes=None):
            """
            Build a DELETE query to delete triples based on the provided parameters. If s, p, and o are specified,
            delete all, if one is omitted, delete all triplets having this specific value.
            E.g., del_triple(pred="some pred") will delete all triplets having this predicate,
            regardless of teh subject and object.
            If we leave all empty, it will delete everything in the specific graph, or the default graph.

            :param subj: Optional, subject
            :param pred: Optional, predicate
            :param obj: Optional, object
            :param graph_id: Optional, the graph where the data will be deleted
            :param prefixes: Optional, a dictionary of prefixes {short_name: full_URI}
            :return: The full SPARQL DELETE query as a string
            """

            # construct the prefix
            prefix_part = ""
            if prefixes:
                for short_name, full_uri in prefixes.items():
                    prefix_part += f"PREFIX {short_name}: <{full_uri}>\n"

            # The WHERE part
            conditions = []

            if subj:
                conditions.append(f"{subj}")    # use the given subj
            else:
                conditions.append("?s")

            if pred:
                conditions.append(f"{pred}")
            else:
                conditions.append("?p")

            if obj:
                conditions.append(f"{obj}")
            else:
                conditions.append("?o")

            triples = " ".join(conditions) + " ."

            # Build the query with or without the GRAPH section
            if graph_id:
                query = f"""
                {prefix_part}
                DELETE WHERE {{
                    GRAPH {graph_id} {{
                        {triples}
                    }}
                }}
                """
            else:
                query = f"""
                {prefix_part}
                DELETE WHERE {{
                    {triples}
                }}
                """

            return query


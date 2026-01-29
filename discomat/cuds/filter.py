from __future__ import annotations

from typing import Iterable, Optional, Set
from rdflib import Graph, URIRef
from rdflib.namespace import RDF


def graph_for_ml(
    g: Graph,
    *,
    # if user want to keep specific namespace prefixes only, e.g., only keep predicates/types under these namespaces, use this
    # see bottom for how to use
    keep_namespace_prefixes: Optional[Iterable[str]] = None,

    # cuds bookkeeping: whether to drop CUDS bookkeeping predicates/types
    drop_cuds_bookkeeping: bool = True,

    # decide whether to keep rdf:type (default: keep, but will drop system types like CUDS/MIO)
    keep_rdf_type: bool = True,
    keep_system_types: bool = False,

    # extra blacklist/whitelist（URIRef）
    extra_keep_predicates: Optional[Iterable[URIRef]] = None,
    extra_drop_predicates: Optional[Iterable[URIRef]] = None,
) -> Graph:
    """
    puropse: delete "training-unnecessary" triples like CUDS automatic metadata/root links, to get a cleaner KG for ML tasks.
    default: delete CUDS bookkeeping predicates + delete system types (CUDS/MIO) in rdf:type.
    optional: also support keep-only mode (keep_namespace_prefixes) to only keep predicates/types under your specified namespaces.
    """

    # 1. assemble keep-only prefixes
    keep_prefixes: Optional[tuple[str, ...]] = None
    if keep_namespace_prefixes:
        keep_prefixes = tuple(str(x) for x in keep_namespace_prefixes)

    # 2. assemble cuds bookkeeping predicate/type blacklist
    drop_predicates: Set[URIRef] = set(extra_drop_predicates or [])
    keep_predicates: Set[URIRef] = set(extra_keep_predicates or [])

    system_type_prefixes: tuple[str, ...] = ()
    if drop_cuds_bookkeeping:
        try:
            
            from discomat.ontology.namespaces import CUDS, MIO  # type: ignore
            from discomat.ontology.ontomap import ONTOMAP       # type: ignore

            # CUDS metadata 
            core_keys = {
                "iri", "pid", "description", "label",
                "uuid", "creation_time", "ontology_type",
            }

            # cuds bookkeeping predicates
            drop_predicates.add(CUDS.iri)

            # mapping specific predicate through ontomap (for example, CUDS.PID)
            for k in core_keys:
                if k in ONTOMAP:
                    drop_predicates.add(URIRef(str(ONTOMAP[k])))

            # common bookkeeping , while users are using session...
            for attr in ("ConnectedTo", "RootNode", "Cuds", "CudsProxy"):
                if hasattr(CUDS, attr):
                    pass

            # prefix of system types: CUDS/MIO
            system_type_prefixes = (str(CUDS), str(MIO))

        except Exception:
            # if we cannot import discomat, we do keep-only mode only (if prefix given)
            system_type_prefixes = ()

    # 3) filtering
    g2 = Graph()
    for prefix, ns in g.namespaces():
        g2.bind(prefix, ns)

    def _starts_with_any(uri: URIRef, prefixes: tuple[str, ...]) -> bool:
        s = str(uri)
        return any(s.startswith(p) for p in prefixes)

    for s, p, o in g:
        # keep only mode: only keep predicates/types under specified namespaces
        if keep_prefixes is not None:
            if p == RDF.type:
                if not keep_rdf_type:
                    continue
                if isinstance(o, URIRef) and _starts_with_any(o, keep_prefixes):
                    g2.add((s, p, o))
                continue

            if isinstance(p, URIRef) and _starts_with_any(p, keep_prefixes):
                g2.add((s, p, o))
            continue

        # default：drop CUDS bookkeeping
        if p in keep_predicates:
            g2.add((s, p, o))
            continue

        if p == RDF.type:
            if not keep_rdf_type:
                continue
            if (not keep_system_types) and isinstance(o, URIRef) and system_type_prefixes:
                if _starts_with_any(o, system_type_prefixes):
                    continue
            g2.add((s, p, o))
            continue

        if p in drop_predicates:
            continue

        # keep rest triples
        g2.add((s, p, o))

    return g2



    """
    how to use:

    from discomat.function.filter import graph_for_ml
    ttl_out = "xxx.ttl
    g_clean = graph_for_ml(gall)
    g_clean.serialize(destination=ttl_out, format="turtle")

    """


    """""
    if we want to keep specific namespace prefixes:
    
    from rdflib.namespace import RDF, RDFS, OWL

    g_clean = graph_for_ml(
        gall,
        keep_namespace_prefixes=[
            "https://www.ddmd.io/mio#",   # your prefixes, make sure the trailing '#' or '/' is included
            str(RDF), str(RDFS), str(OWL) # if you want to keep these...
        ]
    )

    
    """
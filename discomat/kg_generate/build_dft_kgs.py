from __future__ import annotations

import argparse
import pickle
from pathlib import Path
from typing import Tuple

from rdflib import Graph, Namespace, URIRef
from rdflib.namespace import RDF

from discomat.kg_generate.dftloader import dft_to_cuds_graph
from discomat.kg_generate.dftloader import MAT
from discomat.visualisation.cuds_vis import gvis3


CUDS = Namespace("http://www.ddmd.io/mio/cuds#")


def count_cuds_objects(graph: Graph) -> int:
    """
    Match the counting heuristic already used by the CIF KG loaders.
    """
    nodes_by_pred = set()
    for s, p, o in graph:
        if isinstance(s, URIRef) and isinstance(p, URIRef) and str(p).startswith(str(CUDS)):
            nodes_by_pred.add(s)

    nodes_by_type = set(graph.subjects(RDF.type, CUDS.Cuds))
    return len(nodes_by_pred | nodes_by_type)


def count_graph_nodes(graph: Graph) -> int:
    nodes = set()
    for s, p, o in graph:
        nodes.add(s)
        nodes.add(o)
    return len(nodes)


def save_graph_pickle(graph: Graph, out_path: Path) -> None:
    with open(out_path, "wb") as f:
        pickle.dump(graph, f)


def _build_light_dft_graph(graph: Graph) -> Graph:
    """
    Build a lighter ML-oriented graph while preserving the original full graph.

    Strategy:
    - keep the core material / calculation / structure backbone
    - keep unit-cell, atomic sites, k-point grid, key global DFT settings/results
    - drop dense Bond reification and run-environment metadata
    """
    drop_types = {
        MAT.Bond,
    }
    drop_predicates = {
        MAT.runDirectory,
        MAT.prefix,
        MAT.control_outdir,
        MAT.control_pseudo_dir,
        MAT.control_disk_io,
        MAT.control_verbosity,
        MAT.system_nosym,
        MAT.processor_cores,
        MAT.qe_version,
        MAT.start_time,
        MAT.end_time,
        MAT.total_cpu_time,
        MAT.total_wall_time,
    }

    dropped_nodes = set()
    for node_type in drop_types:
        dropped_nodes.update(graph.subjects(RDF.type, node_type))

    light = Graph()
    light.bind("MAT", MAT)

    for s, p, o in graph:
        if p in drop_predicates:
            continue
        if s in dropped_nodes or o in dropped_nodes:
            continue
        light.add((s, p, o))

    return light


def build_dft_graphs(
    *,
    input_root: Path,
    out_root: Path,
    iri_base: str = "http://www.ddmd.io/mio/kg",
    deterministic_iris: bool = True,
    make_neighbors: bool = True,
    max_neighbor_dist: float = 3.2,
    make_html: bool = True,
) -> Tuple[int, int]:
    out_root.mkdir(parents=True, exist_ok=True)

    n_ok = 0
    n_failed = 0

    for run_dir in sorted(p for p in input_root.iterdir() if p.is_dir()):
        pwi_path = run_dir / "scf.pwi"
        if not pwi_path.exists():
            continue

        target_dir = out_root / run_dir.name
        target_dir.mkdir(parents=True, exist_ok=True)

        try:
            calc, graph, _ = dft_to_cuds_graph(
                str(run_dir),
                iri_base=iri_base,
                deterministic_iris=deterministic_iris,
                make_neighbors=make_neighbors,
                max_neighbor_dist=max_neighbor_dist,
            )

            ttl_path = target_dir / f"{run_dir.name}.ttl"
            graph.serialize(destination=str(ttl_path), format="turtle")
            full_pkl_path = target_dir / f"{run_dir.name}.pkl"
            save_graph_pickle(graph, full_pkl_path)

            light_graph = _build_light_dft_graph(graph)
            light_ttl_path = target_dir / f"{run_dir.name}_light.ttl"
            light_graph.serialize(destination=str(light_ttl_path), format="turtle")
            light_pkl_path = target_dir / f"{run_dir.name}_light.pkl"
            save_graph_pickle(light_graph, light_pkl_path)

            if make_html:
                html_path = target_dir / f"{run_dir.name}.html"
                gvis3(graph, str(html_path), clean=True, clone_object_nodes_on_predicates=False)

                light_html_path = target_dir / f"{run_dir.name}_light.html"
                gvis3(light_graph, str(light_html_path), clean=True, clone_object_nodes_on_predicates=False)

            print(f"[OK] {run_dir.name} -> {calc.iri}")
            print(f"  Nodes (full): {count_graph_nodes(graph)}")
            print(f"  CUDS objects (full): {count_cuds_objects(graph)}")
            print(f"  Nodes (light): {count_graph_nodes(light_graph)}")
            print(f"  CUDS objects (light): {count_cuds_objects(light_graph)}")
            n_ok += 1
        except Exception as exc:
            (target_dir / f"{run_dir.name}.error.txt").write_text(str(exc), encoding="utf-8")
            print(f"[ERROR] {run_dir.name}: {exc}")
            n_failed += 1

    return n_ok, n_failed


def main() -> None:
    parser = argparse.ArgumentParser(description="Build knowledge graphs from DFT input/output folders.")
    parser.add_argument(
        "--input-root",
        type=Path,
        default=Path("examples/cifloader/DFT_input_output"),
        help="Root directory containing one subdirectory per DFT run.",
    )
    parser.add_argument(
        "--out-root",
        type=Path,
        default=Path("examples/cifloader/output_dft"),
        help="Output directory for generated TTL/HTML files.",
    )
    parser.add_argument("--iri-base", default="http://www.ddmd.io/mio/kg")
    parser.add_argument("--no-deterministic-iris", dest="deterministic_iris", action="store_false")
    parser.add_argument("--no-neighbors", dest="make_neighbors", action="store_false")
    parser.add_argument("--max-neighbor-dist", type=float, default=3.2)
    parser.add_argument("--no-html", dest="make_html", action="store_false")
    parser.set_defaults(deterministic_iris=True, make_neighbors=True, make_html=True)
    args = parser.parse_args()

    n_ok, n_failed = build_dft_graphs(
        input_root=args.input_root,
        out_root=args.out_root,
        iri_base=args.iri_base,
        deterministic_iris=args.deterministic_iris,
        make_neighbors=args.make_neighbors,
        max_neighbor_dist=args.max_neighbor_dist,
        make_html=args.make_html,
    )
    print(f"Done. Success: {n_ok}, Failed: {n_failed}")


if __name__ == "__main__":
    main()

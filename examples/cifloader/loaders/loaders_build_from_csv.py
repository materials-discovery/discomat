# loaders/build_from_csv.py
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

import pandas as pd
from rdflib import Namespace, RDF, URIRef, Literal

from discomat.kg_generate.cifloader import cif_to_cuds_graph
from discomat.visualisation.cuds_vis import gvis3


MAT = Namespace("http://www.ddmd.io/mio/materials#")
CUDS = Namespace("http://www.ddmd.io/mio/cuds#")


def count_cuds_objects(g) -> int:
    """
    count how many CUDS objects in the graph, by two heuristics:
    1) any subject that appears with a predicate in the CUDS namespace (cuds:*) is a CUDS node
    2) or rdf:type = cuds:Cuds
    finally take the union of these two sets to avoid missing nodes that only have one of the clues.
    """
    nodes_by_pred = set()
    for s, p, o in g:
        if isinstance(s, URIRef) and isinstance(p, URIRef) and str(p).startswith(str(CUDS)):
            nodes_by_pred.add(s)

    nodes_by_type = set(g.subjects(RDF.type, CUDS.Cuds))
    return len(nodes_by_pred | nodes_by_type)


def _pick_default_csv(csv_dir: Path) -> Optional[Path]:
    cands = sorted(csv_dir.glob("*.csv"))
    return cands[0] if cands else None


def _resolve_cif(cif_dir: Path, material_id: str) -> Optional[Path]:
    """
    seek mp-xxxx.cif for the given material_id (which is usually mp-xxxx).
    """
    #  1：mp-1234.cif
    p1 = cif_dir / f"{material_id}.cif"
    if p1.exists():
        return p1

    #  2：mp_1234.cif
    p2 = cif_dir / f"{material_id.replace('-', '_')}.cif"
    if p2.exists():
        return p2

    # 
    # fuzzy matches
    hits = list(cif_dir.glob(f"*{material_id}*.cif"))
    if len(hits) == 1:
        return hits[0]

    return None


def _as_python_scalar(v: Any) -> Optional[Any]:
    # make pandas/numpy scalars into python scalars, and convert NaN/NaT to None
    if v is None:
        return None
    try:
        if pd.isna(v):
            return None
    except Exception:
        pass
    # pandas / numpy scalar -> python
    if hasattr(v, "item"):
        try:
            return v.item()
        except Exception:
            pass
    return v


def _add_properties_to_graph(root_cuds, g, row: Dict[str, Any], *, ns: Namespace = MAT) -> None:
    """
    add all columns from the CSV (except material_id) as properties to the material (root) node in the graph.
    we can still add more later:
    1. unit / data types
    ...
    """
    # 1) write the material_id into the graph even CIF doesnt have it.
    mid = str(row.get("material_id"))
    if mid:
        # use CUDS.add will be converted to Literal((str(...))) by to_iri(), which loses the type...
        root_cuds.add(ns.materialId, mid)


    # 2) other properties
    for k, v in row.items():
        if k == "material_id":
            continue
        v = _as_python_scalar(v)
        if v is None:
            continue
        # all add to the material： <material> ns:<colname> "value"
        # Namespace support underlying，such as  ns.energy_per_atom
        try:
            pred = getattr(ns, k)
        except Exception:
            pred = URIRef(str(ns) + k)

        #  use graph.add to write ，try to keep the valuds/bools as they are, instead of converting to string by to_iri() in CUDS.add
        if isinstance(v, bool):
            lit = Literal(v)
        elif isinstance(v, int):
            lit = Literal(v)
        elif isinstance(v, float):
            lit = Literal(v)
        else:
            lit = Literal(str(v))

        g.add((URIRef(str(root_cuds.iri)), pred, lit))


def build_one(
    *,
    material_id: str,
    cif_path: Path,
    out_dir: Path,
    iri_base: str,
    deterministic_iris: bool,
    expand_symmetry: bool,
    make_neighbors: bool,
    max_neighbor_dist: float,
    clone_object_nodes_on_predicates: bool,
    row: Dict[str, Any],
) -> None:
    # generate KG
    root, g, nodes = cif_to_cuds_graph(
        str(cif_path),
        iri_base=iri_base,
        deterministic_iris=deterministic_iris,
        expand_symmetry=expand_symmetry,
        make_neighbors=make_neighbors,
        max_neighbor_dist=max_neighbor_dist,
    )

    # add properties to the graph
    _add_properties_to_graph(root, g, row, ns=MAT)

    # create output dir and save TTL + HTML
    out_dir.mkdir(parents=True, exist_ok=True)
    ttl_path = out_dir / f"{material_id}.ttl"
    html_path = out_dir / f"{material_id}.html"

    g.serialize(destination=str(ttl_path), format="turtle")

    gvis3(
        g,
        str(html_path),
        clean=True,
        clone_object_nodes_on_predicates=clone_object_nodes_on_predicates,
    )

    print("Material:", material_id)
    print("  CIF:", cif_path)
    print("  Root:", root.iri)
    print("  Triples:", len(g))
    print("  CUDS objects:", count_cuds_objects(g))
    print("  Saved TTL:", ttl_path)
    print("  Saved HTML:", html_path)
    print()


def main():
    here = Path(__file__).resolve().parent
    project_dir = here.parent  

    ap = argparse.ArgumentParser(
        description="Read CSV + CIF files, build per-material knowledge graphs (TTL + HTML)."
    )
    ap.add_argument("--csv", dest="csv_path", default=None, help="CSV file path (default: pick first under ./csv/)")
    ap.add_argument("--cif-dir", dest="cif_dir", default=str(project_dir / "cif_files"), help="Directory containing CIFs")
    ap.add_argument("--out-root", dest="out_root", default=str(project_dir / "output"), help="Output root directory")
    ap.add_argument("--iri-base", dest="iri_base", default="http://www.ddmd.io/kg", help="Base IRI for minted nodes")

    ap.add_argument("--deterministic-iris", action="store_true", default=True, help="Use deterministic IRIs (default: true)")
    ap.add_argument("--no-deterministic-iris", dest="deterministic_iris", action="store_false", help="Disable deterministic IRIs")

    ap.add_argument("--expand-symmetry", action="store_true", default=True, help="Expand symmetry (default: true)")
    ap.add_argument("--no-expand-symmetry", dest="expand_symmetry", action="store_false")

    ap.add_argument("--make-neighbors", action="store_true", default=True, help="Build neighbors/bonds (default: true)")
    ap.add_argument("--no-make-neighbors", dest="make_neighbors", action="store_false")

    ap.add_argument("--max-neighbor-dist", type=float, default=3.2, help="Max neighbor distance (default: 3.2 Å)")
    ap.add_argument("--clone", action="store_true", default=False, help="Clone object nodes in HTML visualization (default: false)")

    ap.add_argument("--limit", type=int, default=None, help="Only process first N rows")
    ap.add_argument("--only", type=str, default=None, help="Comma-separated material_id list to process")

    args = ap.parse_args()

    csv_dir = project_dir / "csv"
    cif_dir = Path(args.cif_dir)
    out_root = Path(args.out_root)

    csv_path = Path(args.csv_path) if args.csv_path else _pick_default_csv(csv_dir)
    if not csv_path or not csv_path.exists():
        print(f"[ERROR] CSV not found. Provide --csv, or put a .csv under: {csv_dir}", file=sys.stderr)
        sys.exit(1)

    df = pd.read_csv(csv_path)

    only_set = None
    if args.only:
        only_set = {x.strip() for x in args.only.split(",") if x.strip()}

    n_total = 0
    n_ok = 0
    n_missing = 0

    for idx, row in df.iterrows():
        if args.limit is not None and n_total >= args.limit:
            break

        material_id = str(row.get("material_id", "")).strip()
        if not material_id or material_id == "nan":
            continue

        if only_set is not None and material_id not in only_set:
            continue

        n_total += 1

        cif_path = _resolve_cif(cif_dir, material_id)
        if cif_path is None:
            n_missing += 1
            print(f"[WARN] CIF not found for {material_id} under {cif_dir}")
            continue

        # every material has its own foldler for outputs：output/mp_1234/
        out_dir = out_root / material_id.replace("-", "_")
        try:
            build_one(
                material_id=material_id,
                cif_path=cif_path,
                out_dir=out_dir,
                iri_base=args.iri_base,
                deterministic_iris=args.deterministic_iris,
                expand_symmetry=args.expand_symmetry,
                make_neighbors=args.make_neighbors,
                max_neighbor_dist=args.max_neighbor_dist,
                clone_object_nodes_on_predicates=args.clone,
                row=row.to_dict(),
            )
            n_ok += 1
        except Exception as e:
            err_path = out_dir / f"{material_id}.error.txt"
            out_dir.mkdir(parents=True, exist_ok=True)
            err_path.write_text(str(e), encoding="utf-8")
            print(f"[ERROR] Failed for {material_id}: {e}")
            print(f"        See: {err_path}")

    print("Done.")
    print(f"  CSV: {csv_path}")
    print(f"  CIF dir: {cif_dir}")
    print(f"  Output: {out_root}")
    print(f"  Total selected: {n_total}")
    print(f"  Success: {n_ok}")
    print(f"  CIF missing: {n_missing}")


if __name__ == "__main__":
    main()



# how to run it:
# cd to cifloader
# python loaders/loaders_build_from_csv.py --csv "csv/nasicon copy.csv" --cif-dir "cif_files" --out-root "output"
"""
Build per-material knowledge graphs by joining:
  - Structure triples from CIF (via cif_to_cuds_graph)
  - Property triples from a CSV (one row per material)

Default property modelling:
  Material --hasProperty--> MaterialProperty
    MaterialProperty propertyKey   "density"
    MaterialProperty propertyValue 2.84^^xsd:double
    MaterialProperty unit          "g/cm3" (if known)

Optionally also attach direct data properties on Material:
  Material density 2.84^^xsd:double

Usage (example):
  python build_material_kgs.py \
      --csv "nasicon copy.csv" \
      --cif-dir "./cifs" \
      --out-dir "./out_ttl" \
      --mode both
"""

from __future__ import annotations

import argparse
import uuid
from pathlib import Path
from typing import Dict, Optional, Iterable, Tuple, Any

import pandas as pd
from rdflib import Graph, Literal, URIRef
from rdflib.namespace import RDF, XSD

# import your CIF loader (patched to accept material_id/material_label)
from discomat.kg_generate.cifloader import cif_to_cuds_graph, MAT


# -------------------------
# helpers
# -------------------------

def _mint_iri(base: str, kind: str, ident: str, deterministic: bool = True) -> URIRef:
    """Stable URI minting, compatible with the CIF loader style."""
    base = base.rstrip("/") + "/"
    if deterministic:
        u = uuid.uuid5(uuid.NAMESPACE_URL, f"{kind}:{ident}")
    else:
        u = uuid.uuid4()
    return URIRef(f"{base}{kind}/{u}")


_UNITS: Dict[str, str] = {
    # These are common Materials Project conventions (adjust if your CSV differs)
    "volume": "Å^3",
    "density": "g/cm3",
    "energy_per_atom": "eV/atom",
    "formation_energy_per_atom": "eV/atom",
    "energy_above_hull": "eV/atom",
    "band_gap": "eV",
    "efermi": "eV",
}

_SKIP_COLS = {"material_id"}  # always skip as a property key (we store it separately)


def _typed_literal(v: Any) -> Optional[Literal]:
    """Convert pandas scalars to typed rdflib Literal."""
    if v is None:
        return None
    # pandas NA
    try:
        if pd.isna(v):
            return None
    except Exception:
        pass

    # normalize numpy scalars to python
    if hasattr(v, "item") and callable(getattr(v, "item")):
        try:
            v = v.item()
        except Exception:
            pass

    if isinstance(v, bool):
        return Literal(v, datatype=XSD.boolean)
    if isinstance(v, int):
        return Literal(v, datatype=XSD.integer)
    if isinstance(v, float):
        return Literal(v, datatype=XSD.double)

    # default string
    return Literal(str(v), datatype=XSD.string)


def resolve_cif_path(material_id: str, cif_dir: Path) -> Path:
    """Find the CIF for a given material_id."""
    candidates = [
        cif_dir / f"{material_id}.cif",
        cif_dir / f"{material_id}.CIF",
        cif_dir / f"{material_id}.mcif",
    ]
    for p in candidates:
        if p.exists():
            return p

    # fallback: search in directory (non-recursive first)
    hits = list(cif_dir.glob(f"*{material_id}*.cif")) + list(cif_dir.glob(f"*{material_id}*.CIF"))
    if hits:
        return hits[0]

    # recursive fallback
    hits = list(cif_dir.rglob(f"*{material_id}*.cif")) + list(cif_dir.rglob(f"*{material_id}*.CIF"))
    if hits:
        return hits[0]

    raise FileNotFoundError(f"No CIF found for {material_id} under {cif_dir}")


def attach_properties(
    *,
    g: Graph,
    material_iri: URIRef,
    row: Dict[str, Any],
    ns=MAT,
    iri_base: str = "http://www.ddmd.io/mio/kg",
    deterministic_iris: bool = True,
    mode: str = "nodes",  # "nodes" | "literals" | "both"
) -> None:
    """
    Attach CSV properties to the existing CIF-derived graph.

    mode:
      - nodes: create MaterialProperty nodes and connect via hasProperty
      - literals: add data properties directly on material (material ns[col] literal)
      - both: do both
    """
    assert mode in {"nodes", "literals", "both"}, f"Unknown mode={mode}"

    # always store material_id as a literal identifier
    if "material_id" in row and row["material_id"] is not None:
        g.add((material_iri, ns.materialId, Literal(str(row["material_id"]), datatype=XSD.string)))

    for key, val in row.items():
        if key in _SKIP_COLS:
            continue
        lit = _typed_literal(val)
        if lit is None:
            continue

        pred = ns[key]  # supports underscores etc.

        if mode in {"literals", "both"}:
            g.add((material_iri, pred, lit))

        if mode in {"nodes", "both"}:
            prop_ident = f"{row.get('material_id','unknown')}|{key}"
            prop_iri = _mint_iri(iri_base, "property", prop_ident, deterministic_iris)

            g.add((prop_iri, RDF.type, ns.MaterialProperty))
            g.add((material_iri, ns.hasProperty, prop_iri))

            g.add((prop_iri, ns.propertyKey, Literal(key, datatype=XSD.string)))
            g.add((prop_iri, ns.propertyValue, lit))

            unit = _UNITS.get(key)
            if unit:
                g.add((prop_iri, ns.unit, Literal(unit, datatype=XSD.string)))


def build_per_material_graphs(
    *,
    csv_path: Path,
    cif_dir: Path,
    out_dir: Path,
    iri_base: str = "http://www.ddmd.io/mio/kg",
    deterministic_iris: bool = True,
    mode: str = "both",
    keep_combined: bool = True,
) -> Tuple[int, int, Optional[Path]]:
    """
    Returns (n_ok, n_failed, combined_path)
    """
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(csv_path)
    combined = Graph()
    combined.bind("MAT", MAT)

    n_ok = 0
    n_failed = 0

    for _, r in df.iterrows():
        row = r.to_dict()
        mid = str(row.get("material_id") or "").strip()
        if not mid:
            n_failed += 1
            continue

        try:
            cif_path = resolve_cif_path(mid, cif_dir)
            # Use material_id as the join key so CIF formula changes don't break your graph identity
            material, g, _ = cif_to_cuds_graph(
                str(cif_path),
                material_id=mid,
                material_label=str(row.get("formula_pretty") or mid),
                iri_base=iri_base,
                deterministic_iris=deterministic_iris,
            )
            # attach properties
            attach_properties(
                g=g,
                material_iri=material.iri,
                row=row,
                ns=MAT,
                iri_base=iri_base,
                deterministic_iris=deterministic_iris,
                mode=mode,
            )

            # save per material
            out_path = out_dir / f"{mid}.ttl"
            g.serialize(destination=str(out_path), format="turtle")

            if keep_combined:
                for s, p, o in g:
                    combined.add((s, p, o))

            n_ok += 1

        except Exception as e:
            # write a small log file per failure for debugging
            (out_dir / f"{mid}.error.txt").write_text(str(e))
            n_failed += 1

    combined_path = None
    if keep_combined:
        combined_path = out_dir / "ALL_materials.ttl"
        combined.serialize(destination=str(combined_path), format="turtle")

    return n_ok, n_failed, combined_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True, type=Path, help="CSV with material properties (one row per material_id).")
    ap.add_argument("--cif-dir", required=True, type=Path, help="Directory containing CIF files named by material_id.")
    ap.add_argument("--out-dir", required=True, type=Path, help="Output directory for per-material TTL files.")
    ap.add_argument("--mode", default="both", choices=["nodes", "literals", "both"], help="How to attach properties.")
    ap.add_argument("--iri-base", default="http://www.ddmd.io/mio/kg", help="Base IRI for minted nodes.")
    ap.add_argument("--no-combined", action="store_true", help="Do not write ALL_materials.ttl")
    args = ap.parse_args()

    n_ok, n_failed, combined = build_per_material_graphs(
        csv_path=args.csv,
        cif_dir=args.cif_dir,
        out_dir=args.out_dir,
        iri_base=args.iri_base,
        mode=args.mode,
        keep_combined=(not args.no_combined),
    )

    print(f"Done. ok={n_ok}, failed={n_failed}")
    if combined:
        print(f"Combined graph: {combined}")


if __name__ == "__main__":
    main()

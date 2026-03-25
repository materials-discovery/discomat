from __future__ import annotations

import math
import re
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, XSD

from discomat.cuds.cuds import Cuds


MAT = Namespace("http://www.ddmd.io/mio/materials#")


_ASSIGN_RE = re.compile(r"^\s*([A-Za-z_]\w*)\s*=\s*(.+?)\s*$")
_ENERGY_RE = re.compile(r"!\s+total energy\s+=\s+([+-]?\d+(?:\.\d+)?)\s+Ry", re.IGNORECASE)
_FERMI_RE = re.compile(r"the Fermi energy is\s+([+-]?\d+(?:\.\d+)?)\s+ev", re.IGNORECASE)
_SMEAR_RE = re.compile(r"smearing contrib\. \(-TS\)\s+=\s+([+-]?\d+(?:\.\d+)?)\s+Ry", re.IGNORECASE)
_KPOINTS_RE = re.compile(
    r"number of k points=\s*(\d+)\s+(.+?)smearing,\s+width \(Ry\)=\s*([+-]?\d+(?:\.\d+)?)",
    re.IGNORECASE,
)
_ITER_RE = re.compile(r"convergence has been achieved in\s+(\d+)\s+iterations", re.IGNORECASE)
_WALL_RE = re.compile(r"PWSCF\s+:\s+(.+?)CPU\s+(.+?)WALL", re.IGNORECASE)
_START_RE = re.compile(r"Program PWSCF v\.([^\s]+)\s+starts on\s+(.+)", re.IGNORECASE)
_END_RE = re.compile(r"This run was terminated on:\s+(.+)", re.IGNORECASE)
_CORES_RE = re.compile(r"running on\s+(\d+)\s+processor cores", re.IGNORECASE)


def _clean_str(v: Optional[str]) -> Optional[str]:
    if v is None:
        return None
    v = str(v).strip().rstrip(",")
    if v in {"", ".", "?"}:
        return None
    if (v.startswith("'") and v.endswith("'")) or (v.startswith('"') and v.endswith('"')):
        v = v[1:-1].strip()
    return v or None


def _parse_scalar(v: Optional[str]) -> Any:
    v = _clean_str(v)
    if v is None:
        return None
    low = v.lower()
    if low in {".true.", "true"}:
        return True
    if low in {".false.", "false"}:
        return False
    try:
        if any(ch in v.lower() for ch in [".", "e", "d"]):
            return float(v.replace("d", "e").replace("D", "E"))
        return int(v)
    except ValueError:
        return v


def _typed_literal(v: Any) -> Optional[Literal]:
    if v is None:
        return None
    if isinstance(v, bool):
        return Literal(v, datatype=XSD.boolean)
    if isinstance(v, int):
        return Literal(v, datatype=XSD.integer)
    if isinstance(v, float):
        return Literal(v, datatype=XSD.double)
    return Literal(str(v), datatype=XSD.string)


def _mint_iri(base: str, kind: str, ident: str, deterministic: bool = True) -> URIRef:
    base = base.rstrip("/") + "/"
    token = uuid.uuid5(uuid.NAMESPACE_URL, f"{kind}:{ident}") if deterministic else uuid.uuid4()
    return URIRef(f"{base}{kind}/{token}")


def _normalise_name(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "_", name.strip()).strip("_")
    if not cleaned:
        return "value"
    if cleaned[0].isdigit():
        cleaned = f"v_{cleaned}"
    return cleaned


def _attach_literals(node: Cuds, values: Dict[str, Any], ns: Namespace = MAT) -> None:
    for key, value in values.items():
        lit = _typed_literal(value)
        if lit is None:
            continue
        node.add(ns[_normalise_name(key)], lit)


def _parse_namelists(lines: List[str]) -> Dict[str, Dict[str, Any]]:
    sections: Dict[str, Dict[str, Any]] = {}
    current: Optional[str] = None
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("&"):
            current = stripped[1:].strip().upper()
            sections[current] = {}
            continue
        if stripped == "/":
            current = None
            continue
        if current is None:
            continue
        match = _ASSIGN_RE.match(stripped)
        if not match:
            continue
        key, value = match.groups()
        sections[current][key] = _parse_scalar(value)
    return sections


def _block_after(lines: List[str], header: str) -> Tuple[Optional[str], List[str]]:
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if not stripped.upper().startswith(header.upper()):
            continue
        rest = stripped[len(header):].strip()
        block: List[str] = []
        for inner in lines[idx + 1:]:
            if not inner.strip():
                break
            if inner.lstrip().startswith("&"):
                break
            if re.match(r"^[A-Z_]+\b", inner.strip()) and inner.strip().upper() == inner.strip():
                break
            block.append(inner.rstrip())
        return (_clean_str(rest) or None), block
    return None, []


def parse_qe_input(pwi_path: str) -> Dict[str, Any]:
    text = Path(pwi_path).read_text(encoding="utf-8")
    lines = text.splitlines()
    namelists = _parse_namelists(lines)

    species_header, species_lines = _block_after(lines, "ATOMIC_SPECIES")
    positions_header, positions_lines = _block_after(lines, "ATOMIC_POSITIONS")
    cell_header, cell_lines = _block_after(lines, "CELL_PARAMETERS")
    k_header, k_lines = _block_after(lines, "K_POINTS")

    species = []
    for line in species_lines:
        parts = line.split()
        if len(parts) >= 3:
            species.append(
                {
                    "element": parts[0],
                    "mass": _parse_scalar(parts[1]),
                    "pseudo_file": parts[2],
                }
            )

    positions = []
    for idx, line in enumerate(positions_lines):
        parts = line.split()
        if len(parts) >= 4:
            positions.append(
                {
                    "index": idx,
                    "element": parts[0],
                    "coords": [float(parts[1]), float(parts[2]), float(parts[3])],
                }
            )

    cell = []
    for line in cell_lines[:3]:
        parts = line.split()
        if len(parts) >= 3:
            cell.append([float(parts[0]), float(parts[1]), float(parts[2])])

    k_points: Dict[str, Any] = {"mode": k_header or "automatic"}
    if (k_header or "").lower() == "automatic" and k_lines:
        parts = k_lines[0].split()
        if len(parts) >= 6:
            k_points.update(
                {
                    "grid_x": int(parts[0]),
                    "grid_y": int(parts[1]),
                    "grid_z": int(parts[2]),
                    "shift_x": int(parts[3]),
                    "shift_y": int(parts[4]),
                    "shift_z": int(parts[5]),
                }
            )

    control = namelists.get("CONTROL", {})
    system = namelists.get("SYSTEM", {})
    electrons = namelists.get("ELECTRONS", {})

    return {
        "namelists": namelists,
        "prefix": control.get("prefix"),
        "calculation": control.get("calculation"),
        "cell_unit": cell_header or "angstrom",
        "position_unit": positions_header or "angstrom",
        "cell_vectors": cell,
        "atomic_species": species,
        "atomic_positions": positions,
        "k_points": k_points,
        "control": control,
        "system": system,
        "electrons": electrons,
    }


def parse_qe_output(pwo_path: str) -> Dict[str, Any]:
    text = Path(pwo_path).read_text(encoding="utf-8")
    out: Dict[str, Any] = {}

    start = _START_RE.search(text)
    if start:
        out["qe_version"] = start.group(1)
        out["start_time"] = start.group(2).strip()

    end = _END_RE.search(text)
    if end:
        out["end_time"] = end.group(1).strip()

    cores = _CORES_RE.search(text)
    if cores:
        out["processor_cores"] = int(cores.group(1))

    energy = _ENERGY_RE.search(text)
    if energy:
        out["total_energy_ry"] = float(energy.group(1))

    fermi = _FERMI_RE.search(text)
    if fermi:
        out["fermi_energy_ev"] = float(fermi.group(1))

    smear = _SMEAR_RE.search(text)
    if smear:
        out["smearing_contribution_ry"] = float(smear.group(1))

    kpts = _KPOINTS_RE.search(text)
    if kpts:
        out["num_k_points"] = int(kpts.group(1))
        out["smearing_scheme"] = kpts.group(2).strip()
        out["smearing_width_ry"] = float(kpts.group(3))

    iterations = _ITER_RE.search(text)
    if iterations:
        out["scf_iterations"] = int(iterations.group(1))
        out["converged"] = True

    wall = _WALL_RE.search(text)
    if wall:
        out["total_cpu_time"] = wall.group(1).strip()
        out["total_wall_time"] = wall.group(2).strip()

    return out


def _dot(a: List[float], b: List[float]) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _norm(v: List[float]) -> float:
    return _dot(v, v) ** 0.5


def _det3(m: List[List[float]]) -> float:
    return (
        m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1])
        - m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0])
        + m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0])
    )


def _invert3(m: List[List[float]]) -> Optional[List[List[float]]]:
    det = _det3(m)
    if abs(det) < 1e-12:
        return None
    inv = [[0.0] * 3 for _ in range(3)]
    inv[0][0] = (m[1][1] * m[2][2] - m[1][2] * m[2][1]) / det
    inv[0][1] = (m[0][2] * m[2][1] - m[0][1] * m[2][2]) / det
    inv[0][2] = (m[0][1] * m[1][2] - m[0][2] * m[1][1]) / det
    inv[1][0] = (m[1][2] * m[2][0] - m[1][0] * m[2][2]) / det
    inv[1][1] = (m[0][0] * m[2][2] - m[0][2] * m[2][0]) / det
    inv[1][2] = (m[0][2] * m[1][0] - m[0][0] * m[1][2]) / det
    inv[2][0] = (m[1][0] * m[2][1] - m[1][1] * m[2][0]) / det
    inv[2][1] = (m[0][1] * m[2][0] - m[0][0] * m[2][1]) / det
    inv[2][2] = (m[0][0] * m[1][1] - m[0][1] * m[1][0]) / det
    return inv


def _mat_vec(m: List[List[float]], v: List[float]) -> List[float]:
    return [
        m[0][0] * v[0] + m[0][1] * v[1] + m[0][2] * v[2],
        m[1][0] * v[0] + m[1][1] * v[1] + m[1][2] * v[2],
        m[2][0] * v[0] + m[2][1] * v[1] + m[2][2] * v[2],
    ]


def _angle_deg(a: List[float], b: List[float]) -> float:
    denom = _norm(a) * _norm(b)
    if denom == 0:
        return 0.0
    value = max(-1.0, min(1.0, _dot(a, b) / denom))
    return math.degrees(math.acos(value))


def _build_unit_cell(cell_vectors: List[List[float]], unit: str) -> Optional[Dict[str, Any]]:
    if len(cell_vectors) != 3:
        return None
    if (unit or "").lower() != "angstrom":
        return None
    inverse = _invert3(cell_vectors)
    if inverse is None:
        return None
    a_vec, b_vec, c_vec = cell_vectors
    return {
        "vectors": cell_vectors,
        "inverse": inverse,
        "a": _norm(a_vec),
        "b": _norm(b_vec),
        "c": _norm(c_vec),
        "alpha": _angle_deg(b_vec, c_vec),
        "beta": _angle_deg(a_vec, c_vec),
        "gamma": _angle_deg(a_vec, b_vec),
    }


def _cart_to_frac(cell: Dict[str, Any], coords: List[float]) -> Tuple[float, float, float]:
    frac = _mat_vec(cell["inverse"], coords)
    return float(frac[0]), float(frac[1]), float(frac[2])


def _frac_to_cart(cell: Dict[str, Any], frac: Tuple[float, float, float]) -> Tuple[float, float, float]:
    vectors = cell["vectors"]
    cart = [
        frac[0] * vectors[0][0] + frac[1] * vectors[1][0] + frac[2] * vectors[2][0],
        frac[0] * vectors[0][1] + frac[1] * vectors[1][1] + frac[2] * vectors[2][1],
        frac[0] * vectors[0][2] + frac[1] * vectors[1][2] + frac[2] * vectors[2][2],
    ]
    return float(cart[0]), float(cart[1]), float(cart[2])


def _infer_neighbor_edges(cell: Dict[str, Any], fracs: List[Tuple[float, float, float]], max_dist: float) -> List[Tuple[int, int, float]]:
    edges: List[Tuple[int, int, float]] = []
    for i, fi in enumerate(fracs):
        for j in range(i + 1, len(fracs)):
            fj = fracs[j]
            dx = fj[0] - fi[0]
            dy = fj[1] - fi[1]
            dz = fj[2] - fi[2]
            dx -= round(dx)
            dy -= round(dy)
            dz -= round(dz)
            dcart = _frac_to_cart(cell, (dx, dy, dz))
            dist = (dcart[0] ** 2 + dcart[1] ** 2 + dcart[2] ** 2) ** 0.5
            if 1e-6 < dist <= max_dist:
                edges.append((i, j, dist))
    return edges


def dft_to_cuds_graph(
    run_dir: str,
    *,
    pwi_name: str = "scf.pwi",
    pwo_name: str = "scf.pwo",
    material_id: Optional[str] = None,
    calculation_id: Optional[str] = None,
    iri_base: str = "http://www.ddmd.io/mio/kg",
    deterministic_iris: bool = True,
    make_neighbors: bool = True,
    max_neighbor_dist: float = 3.2,
    ns: Namespace = MAT,
) -> Tuple[Cuds, Graph, Dict[str, Any]]:
    run_path = Path(run_dir)
    pwi_path = run_path / pwi_name
    pwo_path = run_path / pwo_name

    input_data = parse_qe_input(str(pwi_path))
    output_data = parse_qe_output(str(pwo_path)) if pwo_path.exists() else {}

    calc_ident = calculation_id or run_path.name
    prefix = _clean_str(input_data.get("prefix"))
    mat_ident = material_id or (prefix.split("_scf_")[0] if prefix and "_scf_" in prefix else prefix) or run_path.name

    all_cuds: List[Cuds] = []
    nodes: Dict[str, Any] = {}

    material = Cuds(
        ontology_type=ns.Material,
        iri=_mint_iri(iri_base, "material", mat_ident, deterministic_iris),
        description=f"Imported from DFT inputs/outputs in {run_path.name}",
        label=str(mat_ident)[:20],
    )
    all_cuds.append(material)
    nodes["material"] = material
    material.add(ns.materialId, Literal(str(mat_ident), datatype=XSD.string))

    calculation = Cuds(
        ontology_type=ns.DFTCalculation,
        iri=_mint_iri(iri_base, "dft_calculation", calc_ident, deterministic_iris),
        label=str(calc_ident)[:20],
    )
    all_cuds.append(calculation)
    nodes["calculation"] = calculation
    material.add(ns.hasCalculation, calculation)
    calculation.add(ns.calculationId, Literal(str(calc_ident), datatype=XSD.string))
    calculation.add(ns.runDirectory, Literal(str(run_path), datatype=XSD.string))

    if prefix:
        calculation.add(ns.prefix, Literal(prefix, datatype=XSD.string))

    input_node = Cuds(
        ontology_type=ns.DFTInput,
        iri=_mint_iri(iri_base, "dft_input", calc_ident, deterministic_iris),
        label="dft_input",
    )
    output_node = Cuds(
        ontology_type=ns.DFTOutput,
        iri=_mint_iri(iri_base, "dft_output", calc_ident, deterministic_iris),
        label="dft_output",
    )
    all_cuds.extend([input_node, output_node])
    nodes["input"] = input_node
    nodes["output"] = output_node
    calculation.add(ns.hasInput, input_node)
    calculation.add(ns.hasOutput, output_node)

    structure = Cuds(
        ontology_type=ns.CrystalStructure,
        iri=_mint_iri(iri_base, "structure", calc_ident, deterministic_iris),
        label="structure",
    )
    unit_cell = Cuds(
        ontology_type=ns.UnitCell,
        iri=_mint_iri(iri_base, "unitcell", calc_ident, deterministic_iris),
        label="unitcell",
    )
    all_cuds.extend([structure, unit_cell])
    nodes["structure"] = structure
    calculation.add(ns.hasStructure, structure)
    structure.add(ns.hasUnitCell, unit_cell)

    cell_vectors = input_data.get("cell_vectors", [])
    cell_unit = input_data.get("cell_unit", "angstrom")
    qe_cell = _build_unit_cell(cell_vectors, cell_unit)

    if len(cell_vectors) == 3:
        for axis, vec in zip(["aVector", "bVector", "cVector"], cell_vectors):
            unit_cell.add(ns[axis], Literal(" ".join(str(x) for x in vec), datatype=XSD.string))
        unit_cell.add(ns.cellVectorUnit, Literal(str(cell_unit), datatype=XSD.string))

    if qe_cell is not None:
        _attach_literals(
            unit_cell,
            {
                "a": qe_cell["a"],
                "b": qe_cell["b"],
                "c": qe_cell["c"],
                "alpha": qe_cell["alpha"],
                "beta": qe_cell["beta"],
                "gamma": qe_cell["gamma"],
            },
            ns=ns,
        )

    _attach_literals(
        input_node,
        {
            "calculation": input_data.get("calculation"),
            "position_unit": input_data.get("position_unit"),
            "cell_unit": cell_unit,
            **{f"control_{k}": v for k, v in input_data.get("control", {}).items()},
            **{f"system_{k}": v for k, v in input_data.get("system", {}).items()},
            **{f"electrons_{k}": v for k, v in input_data.get("electrons", {}).items()},
        },
        ns=ns,
    )

    k_points = input_data.get("k_points", {})
    if k_points:
        kgrid = Cuds(
            ontology_type=ns.KPointGrid,
            iri=_mint_iri(iri_base, "kpoint_grid", calc_ident, deterministic_iris),
            label="kgrid",
        )
        all_cuds.append(kgrid)
        nodes["kgrid"] = kgrid
        input_node.add(ns.hasKPointGrid, kgrid)
        _attach_literals(kgrid, k_points, ns=ns)

    element_nodes: Dict[str, Cuds] = {}
    species_nodes: List[Cuds] = []
    for idx, species in enumerate(input_data.get("atomic_species", [])):
        element = str(species["element"])
        element_node = element_nodes.get(element)
        if element_node is None:
            element_node = Cuds(
                ontology_type=ns.Element,
                iri=_mint_iri(iri_base, "element", element, deterministic_iris),
                label=element[:20],
            )
            all_cuds.append(element_node)
            element_nodes[element] = element_node

        species_node = Cuds(
            ontology_type=ns.AtomicSpecies,
            iri=_mint_iri(iri_base, "atomic_species", f"{calc_ident}:{idx}:{element}", deterministic_iris),
            label=f"{element}_spec"[:20],
        )
        all_cuds.append(species_node)
        species_nodes.append(species_node)
        input_node.add(ns.hasAtomicSpecies, species_node)
        species_node.add(ns.hasElement, element_node)
        _attach_literals(species_node, species, ns=ns)

    position_unit = (input_data.get("position_unit") or "angstrom").lower()
    site_nodes: List[Cuds] = []
    fracs: List[Tuple[float, float, float]] = []
    positions = input_data.get("atomic_positions", [])

    for site_data in positions:
        element = str(site_data["element"])
        coords = site_data["coords"]
        frac_coords: Optional[Tuple[float, float, float]] = None

        if position_unit == "crystal":
            frac_coords = (float(coords[0]), float(coords[1]), float(coords[2]))
        elif position_unit == "angstrom" and qe_cell is not None:
            frac_coords = _cart_to_frac(qe_cell, coords)

        element_node = element_nodes.get(element)
        if element_node is None:
            element_node = Cuds(
                ontology_type=ns.Element,
                iri=_mint_iri(iri_base, "element", element, deterministic_iris),
                label=element[:20],
            )
            all_cuds.append(element_node)
            element_nodes[element] = element_node

        site_ident = f"{calc_ident}:site:{site_data['index']}:{element}"
        site_node = Cuds(
            ontology_type=ns.AtomicSite,
            iri=_mint_iri(iri_base, "site", site_ident, deterministic_iris),
            label=f"{element}{site_data['index']}"[:20],
        )
        all_cuds.append(site_node)
        site_nodes.append(site_node)
        structure.add(ns.hasAtomicSite, site_node)
        site_node.add(ns.hasElement, element_node)
        site_node.add(ns.positionUnit, Literal(position_unit, datatype=XSD.string))
        site_node.add(ns.cartX, Literal(float(coords[0]), datatype=XSD.double))
        site_node.add(ns.cartY, Literal(float(coords[1]), datatype=XSD.double))
        site_node.add(ns.cartZ, Literal(float(coords[2]), datatype=XSD.double))

        if frac_coords is not None:
            site_node.add(ns.fractX, Literal(frac_coords[0], datatype=XSD.double))
            site_node.add(ns.fractY, Literal(frac_coords[1], datatype=XSD.double))
            site_node.add(ns.fractZ, Literal(frac_coords[2], datatype=XSD.double))
            fracs.append(frac_coords)
        else:
            fracs.append((0.0, 0.0, 0.0))

    if make_neighbors and qe_cell is not None and len(fracs) == len(site_nodes) and site_nodes:
        for i, j, distance in _infer_neighbor_edges(qe_cell, fracs, max_neighbor_dist):
            site_nodes[i].add(ns.neighborOf, site_nodes[j])
            site_nodes[j].add(ns.neighborOf, site_nodes[i])
            bond = Cuds(
                ontology_type=ns.Bond,
                iri=_mint_iri(iri_base, "bond", f"{calc_ident}:{i}:{j}", deterministic_iris),
                label=f"b{i}_{j}"[:20],
            )
            all_cuds.append(bond)
            structure.add(ns.hasBond, bond)
            bond.add(ns.bondAtom1, site_nodes[i])
            bond.add(ns.bondAtom2, site_nodes[j])
            bond.add(ns.bondDistance, Literal(distance, datatype=XSD.double))

    _attach_literals(output_node, output_data, ns=ns)

    g = Graph()
    g.bind("MAT", ns)
    for cuds in all_cuds:
        for triple in cuds.graph:
            g.add(triple)

    nodes["elements"] = element_nodes
    nodes["sites"] = {f"site_{i}": site for i, site in enumerate(site_nodes)}
    nodes["species"] = species_nodes
    nodes["input_data"] = input_data
    nodes["output_data"] = output_data

    return calculation, g, nodes

# this function can read cif files and filter out unnecessary triples for ML tasks

from __future__ import annotations

import os, re, math, uuid
from typing import Dict, List, Tuple, Optional

import gemmi
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS, XSD 

from discomat.cuds.cuds import Cuds


MAT = Namespace("http://www.ddmd.io/mio/materials#")

_NUM_RE = re.compile(r"^\s*([+-]?\d+(?:\.\d+)?)(?:\(\d+\))?\s*$")

def _clean_str(v: Optional[str]) -> Optional[str]:
    if v is None:
        return None
    v = str(v).strip()
    if v in (".", "?", ""):
        return None
    # strip CIF quotes
    if (v.startswith("'") and v.endswith("'")) or (v.startswith('"') and v.endswith('"')):
        v = v[1:-1].strip()
    return v or None

def _parse_float(v: Optional[str]) -> Optional[float]:
    v = _clean_str(v)
    if v is None:
        return None
    m = _NUM_RE.match(v)
    if not m:
        return None
    return float(m.group(1))


def _lit_float(x: Optional[float]) -> Optional[Literal]:
    if x is None:
        return None
    return Literal(float(x), datatype=XSD.double)


def _lit_int(x: Optional[int]) -> Optional[Literal]:
    if x is None:
        return None
    return Literal(int(x), datatype=XSD.integer)

def _mint_iri(base: str, kind: str, ident: str, deterministic: bool = True) -> str:
    """
    生成稳定 IRI（对同一个 CIF/同一个 site/bond，重复导入可得到同样 IRI，方便去重/增量更新）
    """
    base = base.rstrip("/") + "/"
    if deterministic:
        u = uuid.uuid5(uuid.NAMESPACE_URL, f"{kind}:{ident}")
    else:
        u = uuid.uuid4()
    return f"{base}{kind}/{u}"

def _extract_pairs_and_loops(block: gemmi.cif.Block) -> Tuple[Dict[str, str], List[gemmi.cif.Loop]]:
    pairs: Dict[str, str] = {}
    loops: List[gemmi.cif.Loop] = []
    for item in block:
        if item.pair is not None:
            tag, val = item.pair
            # 如果有 duplicate tag，后者覆盖前者（你也可以改成保留 list）
            pairs[tag] = val
        elif item.loop is not None:
            loops.append(item.loop)
    return pairs, loops


def _find_atom_site_loop(loops: List[gemmi.cif.Loop]) -> Optional[gemmi.cif.Loop]:
    for lp in loops:
        tags = [t.lower() for t in lp.tags]
        if all(t in tags for t in ["_atom_site_fract_x", "_atom_site_fract_y", "_atom_site_fract_z"]):
            return lp
        if all(t in tags for t in ["_atom_site_cartn_x", "_atom_site_cartn_y", "_atom_site_cartn_z"]):
            return lp
    return None


def _find_symop_strings(loops: List[gemmi.cif.Loop]) -> List[str]:
    """
    兼容老式 CIF: _symmetry_equiv_pos_as_xyz
    也兼容新式 CIF: _space_group_symop_operation_xyz
    """
    for lp in loops:
        tags = [t.lower() for t in lp.tags]
        if "_symmetry_equiv_pos_as_xyz" in tags:
            idx = tags.index("_symmetry_equiv_pos_as_xyz")
        elif "_space_group_symop_operation_xyz" in tags:
            idx = tags.index("_space_group_symop_operation_xyz")
        else:
            continue

        w = lp.width()
        L = lp.length()
        vals = lp.values
        ops: List[str] = []
        for i in range(L):
            row = vals[i * w : (i + 1) * w]
            ops.append(_clean_str(row[idx]) or "x,y,z")
        return ops
    return []


def _rows_from_loop(lp: gemmi.cif.Loop) -> List[Dict[str, str]]:
    tags = list(lp.tags)
    w = lp.width()
    L = lp.length()
    vals = lp.values
    out: List[Dict[str, str]] = []
    for i in range(L):
        row = vals[i * w : (i + 1) * w]
        out.append({tags[j]: row[j] for j in range(w)})
    return out


def _wrap01(x: float) -> float:
    return x - math.floor(x)


def _expand_sites_with_symmetry(
    raw_sites: List[Dict[str, str]],
    sym_ops: List[str],
    tol: float = 1e-6
) -> List[Dict[str, object]]:
    """
    将 asymmetric unit 展开为 full unit cell，并去重（按 element + frac coords）
    """
    ops = [gemmi.Op(s) for s in sym_ops] if sym_ops else [gemmi.Op("x,y,z")]

    expanded: List[Dict[str, object]] = []
    for site in raw_sites:
        typ = _clean_str(site.get("_atom_site_type_symbol")) or _clean_str(site.get("_atom_site_label")) or "X"
        label = _clean_str(site.get("_atom_site_label")) or typ

        fx = _parse_float(site.get("_atom_site_fract_x"))
        fy = _parse_float(site.get("_atom_site_fract_y"))
        fz = _parse_float(site.get("_atom_site_fract_z"))

        if fx is None or fy is None or fz is None:
            # 如果是 Cartn 坐标，这里先跳过（也可以加：Cartn→Frac 的转换）
            continue

        occ = _parse_float(site.get("_atom_site_occupancy"))
        wyck = _clean_str(site.get("_atom_site_Wyckoff_symbol"))

        for op in ops:
            nx, ny, nz = op.apply_to_xyz([fx, fy, fz])  # gemmi 支持这个用法
            nx, ny, nz = _wrap01(nx), _wrap01(ny), _wrap01(nz)

            expanded.append({
                "element": typ,
                "label": label,
                "fract": (nx, ny, nz),
                "occupancy": occ,
                "wyckoff": wyck,
            })

    # 去重：同元素且 frac 坐标足够接近就认为同一原子
    uniq: List[Dict[str, object]] = []
    for s in expanded:
        e = s["element"]
        fx, fy, fz = s["fract"]
        hit = False
        for t in uniq:
            if t["element"] != e:
                continue
            gx, gy, gz = t["fract"]
            if max(abs(fx - gx), abs(fy - gy), abs(fz - gz)) < tol:
                hit = True
                break
        if not hit:
            uniq.append(s)

    return uniq



def _infer_neighbor_edges(
    cell: gemmi.UnitCell,
    fracs: List[Tuple[float, float, float]],
    max_dist: float = 3.2
) -> List[Tuple[int, int, float]]:
    """
    简单距离阈值邻接（PBC：在 fractional space 取最小像）
    """
    edges: List[Tuple[int, int, float]] = []
    n = len(fracs)

    for i in range(n):
        fi = fracs[i]
        for j in range(i + 1, n):
            fj = fracs[j]
            dx = fj[0] - fi[0]
            dy = fj[1] - fi[1]
            dz = fj[2] - fi[2]

            # minimum image in fractional
            dx -= round(dx)
            dy -= round(dy)
            dz -= round(dz)

            dcart = cell.orthogonalize(gemmi.Fractional(dx, dy, dz))
            dist = math.sqrt(dcart.x * dcart.x + dcart.y * dcart.y + dcart.z * dcart.z)

            if 1e-6 < dist <= max_dist:
                edges.append((i, j, dist))

    return edges

def cif_to_cuds_graph(
    cif_path: str,
    *,
    material_id: Optional[str] = None,
    material_label: Optional[str] = None,
    ns: Namespace = MAT,
    iri_base: str = "http://www.ddmd.io/mio/kg",
    deterministic_iris: bool = True,
    expand_symmetry: bool = True,
    make_neighbors: bool = True,
    max_neighbor_dist: float = 3.2,
    keep_material_literals: bool = False,
    keep_spacegroup_it_number: bool = False,
    keep_bond_distance: bool = False,
    minimal_if_symops: bool = True,
) -> Tuple[Cuds, Graph, Dict[str, Cuds]]:
    """
    读取 CIF → 创建/连接 CUDS → 合并为一个 rdflib.Graph

    返回:
      - root_material_cuds
      - merged_graph
      - nodes dict（可用于后续查找：例如 element nodes / site nodes）
    """
    doc = gemmi.cif.read_file(cif_path, check_level=0)  # 容忍 duplicate tags
    block = doc.sole_block()

    pairs, loops = _extract_pairs_and_loops(block)

    formula = _clean_str(pairs.get("_chemical_formula_sum"))
    common_name = _clean_str(pairs.get("_chemical_name_common"))

    a = _parse_float(pairs.get("_cell_length_a"))
    b = _parse_float(pairs.get("_cell_length_b"))
    c = _parse_float(pairs.get("_cell_length_c"))
    alpha = _parse_float(pairs.get("_cell_angle_alpha")) or 90.0
    beta = _parse_float(pairs.get("_cell_angle_beta")) or 90.0
    gamma = _parse_float(pairs.get("_cell_angle_gamma")) or 90.0

    # space group (尽量兼容不同 tag)
    sg_hm = _clean_str(pairs.get("_symmetry_space_group_name_H-M")) or _clean_str(pairs.get("_space_group_name_H-M_alt"))
    sg_it = _parse_float(pairs.get("_space_group_IT_number"))
    sg_it_int = int(sg_it) if sg_it is not None else None

    sg_hall = (
        _clean_str(pairs.get("_space_group_name_Hall"))
        or _clean_str(pairs.get("_symmetry_space_group_name_Hall"))
        or _clean_str(pairs.get("_space_group.name_Hall"))
    )


    # atom sites
    atom_lp = _find_atom_site_loop(loops)
    raw_sites = _rows_from_loop(atom_lp) if atom_lp is not None else []


    # symmetry ops
    sym_ops = _find_symop_strings(loops)

    has_symops = bool(sym_ops)
    if minimal_if_symops and has_symops:
        expand_symmetry = False
        make_neighbors = False
    if expand_symmetry:
        sites = _expand_sites_with_symmetry(raw_sites, sym_ops)
    else:
        # 不展开就只用原 loop
        sites = []
        for s in raw_sites:
            typ = _clean_str(s.get("_atom_site_type_symbol")) or _clean_str(s.get("_atom_site_label")) or "X"
            label = _clean_str(s.get("_atom_site_label")) or typ
            fx = _parse_float(s.get("_atom_site_fract_x"))
            fy = _parse_float(s.get("_atom_site_fract_y"))
            fz = _parse_float(s.get("_atom_site_fract_z"))
            occ = _parse_float(s.get("_atom_site_occupancy"))
            if occ is None:
                occ = 1.0
            if fx is None or fy is None or fz is None:
                continue
            sites.append({"element": typ, "label": label, "fract": (fx, fy, fz), "occupancy": occ,})

    # ---------- Create CUDS and link via .add ----------
    all_cuds: List[Cuds] = []
    nodes: Dict[str, Cuds] = {}

    mat_ident = material_id or formula or os.path.splitext(os.path.basename(cif_path))[0]
    material = Cuds(
        ontology_type=ns.Material,
        iri=_mint_iri(iri_base, "material", mat_ident, deterministic_iris),
        description=f"Imported from CIF: {os.path.basename(cif_path)}",
        label=(material_label or formula or "Material")[:20],
    )
    all_cuds.append(material)
    nodes["material"] = material

    if material_id:
        # keep an explicit identifier so CIF-based label/formula changes won't break joins
        material.graph.add((material.iri, ns.materialId, Literal(material_id, datatype=XSD.string)))

    structure = Cuds(
        ontology_type=ns.CrystalStructure,
        iri=_mint_iri(iri_base, "structure", mat_ident, deterministic_iris),
        label="structure",
    )
    all_cuds.append(structure)
    nodes["structure"] = structure
    material.add(ns.hasStructure, structure)





    unit_cell = Cuds(
        ontology_type=ns.UnitCell,
        iri=_mint_iri(iri_base, "unitcell", mat_ident, deterministic_iris),
        label="unitcell",
    )
    all_cuds.append(unit_cell)
    structure.add(ns.hasUnitCell, unit_cell)

    for pred, val in [
        (ns.a, _lit_float(a)),
        (ns.b, _lit_float(b)),
        (ns.c, _lit_float(c)),
        (ns.alpha, _lit_float(alpha)),
        (ns.beta, _lit_float(beta)),
        (ns.gamma, _lit_float(gamma)),
    ]:
        if val is not None:
            unit_cell.add(pred, val)

    if sg_hm or sg_it_int is not None:
        sg = Cuds(
            ontology_type=ns.SpaceGroup,
            iri=_mint_iri(iri_base, "spacegroup", f"{mat_ident}:{sg_hm}:{sg_it_int}", deterministic_iris),
            label="spacegroup",
        )
        all_cuds.append(sg)
        structure.add(ns.hasSpaceGroup, sg)
        if sg_hm:
            sg.add(ns.hmSymbol, Literal(sg_hm))
        if sg_hall:
            sg.add(ns.hallSymbol, Literal(sg_hall))
        # if sg_it_int is not None:
        #     sg.add(ns.itNumber, _lit_int(sg_it_int))

    # element nodes (去重)
    element_nodes: Dict[str, Cuds] = {}

    site_nodes: List[Cuds] = []
    fracs: List[Tuple[float, float, float]] = []

    for idx, s in enumerate(sites):
        el = str(s["element"])
        fx, fy, fz = s["fract"]
        fracs.append((float(fx), float(fy), float(fz)))

        if el not in element_nodes:
            e_node = Cuds(
                ontology_type=ns.Element,
                iri=_mint_iri(iri_base, "element", el, deterministic_iris),
                label=el[:20],
            )
            all_cuds.append(e_node)
            element_nodes[el] = e_node
        else:
            e_node = element_nodes[el]


        site_ident = f"{mat_ident}:site:{idx}:{el}:{fx:.6f},{fy:.6f},{fz:.6f}"
        site = Cuds(
            ontology_type=ns.AtomicSite,
            iri=_mint_iri(iri_base, "site", site_ident, deterministic_iris),
            label=f"{el}{idx}"[:20],
        )
        all_cuds.append(site)
        site_nodes.append(site)

        structure.add(ns.hasAtomicSite, site)
        site.add(ns.hasElement, e_node)
        site.add(ns.fractX, _lit_float(fx))
        site.add(ns.fractY, _lit_float(fy))
        site.add(ns.fractZ, _lit_float(fz))

        if "occupancy" in s and s["occupancy"] is not None:
            site.add(ns.occupancy, _lit_float(float(s["occupancy"])))
        if "wyckoff" in s and s["wyckoff"]:
            site.add(ns.wyckoff, Literal(str(s["wyckoff"])))
        if "label" in s and s["label"]:
            site.add(ns.siteLabel, Literal(str(s["label"])))


    nodes["elements"] = element_nodes  # type: ignore
    nodes["sites"] = {f"site_{i}": n for i, n in enumerate(site_nodes)}  # type: ignore

    # neighbors / bonds
    if make_neighbors and a and b and c:
        cell = gemmi.UnitCell(float(a), float(b), float(c), float(alpha), float(beta), float(gamma))
        edges = _infer_neighbor_edges(cell, fracs, max_neighbor_dist)

        for i, j, dist in edges:
            # 方案A：直接用关系连（最像你 DOME40 的 add 方式）
            site_nodes[i].add(ns.neighborOf, site_nodes[j])
            site_nodes[j].add(ns.neighborOf, site_nodes[i])

            # 方案B（可选）：reify 一个 Bond 结点存 distance（如果你想把 distance 也进 KG）
            bond_ident = f"{mat_ident}:bond:{i}-{j}:{dist:.4f}"
            bond = Cuds(
                ontology_type=ns.Bond,
                iri=_mint_iri(iri_base, "bond", bond_ident, deterministic_iris),
                label=f"b{i}_{j}"[:20],
            )
            all_cuds.append(bond)
            structure.add(ns.hasBond, bond)
            bond.add(ns.bondAtom1, site_nodes[i])
            bond.add(ns.bondAtom2, site_nodes[j])

    # merge to one rdflib graph (按你 workflow1.6 的套路)
    g = Graph()
    g.bind("MAT", ns)
    for cuds in all_cuds:
        for s, p, o in cuds.graph:
            g.add((s, p, o))

    return material, g, nodes
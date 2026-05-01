from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import trimesh

from npa.exp_preprocessing.wrl_io import load_vrml_meshes, to_trimesh_list


@dataclass(frozen=True)
class ExpFilteredLineage:
    lineage_idx: int
    lineage_mesh: trimesh.Trimesh
    dpn_meshes: list[trimesh.Trimesh]
    pros_meshes: list[trimesh.Trimesh]

    @property
    def n_dpn(self) -> int:
        return len(self.dpn_meshes)

    @property
    def n_pros(self) -> int:
        return len(self.pros_meshes)


@dataclass(frozen=True)
class ExpRejectedLineage:
    lineage_idx: int
    lineage_mesh: trimesh.Trimesh
    dpn_meshes: list[trimesh.Trimesh]
    pros_meshes: list[trimesh.Trimesh]
    rejection_reason: str

    @property
    def n_dpn(self) -> int:
        return len(self.dpn_meshes)

    @property
    def n_pros(self) -> int:
        return len(self.pros_meshes)


@dataclass(frozen=True)
class ExpFilteredLobe:
    genotype: str
    lobe: str
    kept: list[ExpFilteredLineage]
    rejected: list[ExpRejectedLineage]
    n_rejected_disconnected: int
    n_rejected_no_dpn: int
    n_lineages_total: int
    n_unassigned_dpn: int
    n_unassigned_pros: int


def mesh_bbox(mesh: trimesh.Trimesh) -> tuple[np.ndarray, np.ndarray]:
    vertices = np.asarray(mesh.vertices)
    return vertices.min(axis=0), vertices.max(axis=0)


def fraction_vertices_inside_bbox(
    vertices: np.ndarray,
    bbox_min: np.ndarray,
    bbox_max: np.ndarray,
) -> float:
    if vertices.size == 0:
        return 0.0
    inside = np.logical_and(vertices >= bbox_min, vertices <= bbox_max).all(axis=1)
    return float(inside.mean())


def assign_cells_to_lineages_by_vertex_bbox(
    cell_meshes: list[trimesh.Trimesh],
    lineage_meshes: list[trimesh.Trimesh],
    min_fraction: float = 0.95,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Assign cells by the old WRL helper rule: fraction of cell vertices inside
    each lineage bounding box.
    """
    lineage_bboxes = [mesh_bbox(mesh) for mesh in lineage_meshes]
    assignments: list[int] = []
    scores: list[float] = []

    for cell in cell_meshes:
        vertices = np.asarray(cell.vertices)
        best_idx = -1
        best_score = -1.0
        for idx, (bbox_min, bbox_max) in enumerate(lineage_bboxes):
            score = fraction_vertices_inside_bbox(vertices, bbox_min, bbox_max)
            if score > best_score:
                best_score = score
                best_idx = idx
        assignments.append(best_idx if best_score >= min_fraction else -1)
        scores.append(best_score)

    return np.asarray(assignments, dtype=np.int32), np.asarray(scores, dtype=np.float32)


def assign_cells_to_lineages_by_containment(
    cell_meshes: list[trimesh.Trimesh],
    lineage_meshes: list[trimesh.Trimesh],
    min_fraction: float = 0.60,
    n_sample: int = 20,
    seed: int = 0,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Assign cells using sampled mesh containment against lineage meshes.

    A bounding-box overlap prefilter avoids unnecessary containment calls.
    """
    lineage_bboxes = [mesh_bbox(mesh) for mesh in lineage_meshes]
    rng = np.random.default_rng(seed)
    assignments: list[int] = []
    scores: list[float] = []

    for cell in cell_meshes:
        vertices = np.asarray(cell.vertices)
        if vertices.size == 0:
            assignments.append(-1)
            scores.append(0.0)
            continue

        cell_min = vertices.min(axis=0)
        cell_max = vertices.max(axis=0)
        if len(vertices) > n_sample:
            sample_idx = rng.choice(len(vertices), size=n_sample, replace=False)
            sample_vertices = vertices[sample_idx]
        else:
            sample_vertices = vertices

        best_idx = -1
        best_score = -1.0
        for idx, lineage_mesh in enumerate(lineage_meshes):
            bbox_min, bbox_max = lineage_bboxes[idx]
            if np.any(cell_min > bbox_max) or np.any(cell_max < bbox_min):
                continue
            score = float(lineage_mesh.contains(sample_vertices).mean())
            if score > best_score:
                best_score = score
                best_idx = idx

        assignments.append(best_idx if best_score >= min_fraction else -1)
        scores.append(max(best_score, 0.0))

    return np.asarray(assignments, dtype=np.int32), np.asarray(scores, dtype=np.float32)


def lineage_is_connected(
    mesh: trimesh.Trimesh,
    min_faces: int = 50,
    max_secondary_volume: float = 5.0,
) -> bool:
    """
    Return False when a lineage has a substantial disconnected component.

    Small secondary components are tolerated as reconstruction artifacts.
    """
    components = mesh.split(only_watertight=False, repair=False)
    if len(components) <= 1:
        return True

    main_idx = max(range(len(components)), key=lambda idx: len(components[idx].faces))
    for idx, component in enumerate(components):
        if idx == main_idx or len(component.faces) < min_faces:
            continue
        if abs(float(component.volume)) >= max_secondary_volume:
            return False
    return True


def load_exp_filtered_lobe(
    lineage_wrl: Path,
    pros_wrl: Path,
    dpn_wrl: Path,
    genotype: str,
    lobe: str,
    *,
    min_pros_fraction: float = 0.95,
    min_dpn_fraction: float = 0.60,
    dpn_sample_size: int = 20,
    min_lineage_faces: int = 50,
    max_secondary_volume: float = 5.0,
) -> ExpFilteredLobe:
    lineage_meshes = to_trimesh_list(load_vrml_meshes(lineage_wrl))
    pros_meshes = to_trimesh_list(load_vrml_meshes(pros_wrl))
    dpn_meshes = to_trimesh_list(load_vrml_meshes(dpn_wrl))

    pros_assignments, _ = assign_cells_to_lineages_by_vertex_bbox(
        pros_meshes, lineage_meshes, min_fraction=min_pros_fraction
    )
    dpn_assignments, _ = assign_cells_to_lineages_by_containment(
        dpn_meshes,
        lineage_meshes,
        min_fraction=min_dpn_fraction,
        n_sample=dpn_sample_size,
    )

    kept: list[ExpFilteredLineage] = []
    rejected: list[ExpRejectedLineage] = []
    n_rejected_disconnected = 0
    n_rejected_no_dpn = 0

    for lineage_idx, lineage_mesh in enumerate(lineage_meshes):
        dpn_indices = np.where(dpn_assignments == lineage_idx)[0]
        pros_indices = np.where(pros_assignments == lineage_idx)[0]
        lineage_dpn_meshes = [dpn_meshes[idx] for idx in dpn_indices]
        lineage_pros_meshes = [pros_meshes[idx] for idx in pros_indices]

        if not lineage_is_connected(
            lineage_mesh,
            min_faces=min_lineage_faces,
            max_secondary_volume=max_secondary_volume,
        ):
            n_rejected_disconnected += 1
            rejected.append(
                ExpRejectedLineage(
                    lineage_idx=lineage_idx,
                    lineage_mesh=lineage_mesh,
                    dpn_meshes=lineage_dpn_meshes,
                    pros_meshes=lineage_pros_meshes,
                    rejection_reason="disconnected",
                )
            )
            continue

        if dpn_indices.size == 0:
            n_rejected_no_dpn += 1
            rejected.append(
                ExpRejectedLineage(
                    lineage_idx=lineage_idx,
                    lineage_mesh=lineage_mesh,
                    dpn_meshes=lineage_dpn_meshes,
                    pros_meshes=lineage_pros_meshes,
                    rejection_reason="no_dpn",
                )
            )
            continue

        kept.append(
            ExpFilteredLineage(
                lineage_idx=lineage_idx,
                lineage_mesh=lineage_mesh,
                dpn_meshes=lineage_dpn_meshes,
                pros_meshes=lineage_pros_meshes,
            )
        )

    return ExpFilteredLobe(
        genotype=genotype,
        lobe=lobe,
        kept=kept,
        rejected=rejected,
        n_rejected_disconnected=n_rejected_disconnected,
        n_rejected_no_dpn=n_rejected_no_dpn,
        n_lineages_total=len(lineage_meshes),
        n_unassigned_dpn=int((dpn_assignments == -1).sum()),
        n_unassigned_pros=int((pros_assignments == -1).sum()),
    )

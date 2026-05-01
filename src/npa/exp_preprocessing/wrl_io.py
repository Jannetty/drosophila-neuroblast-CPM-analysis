from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import trimesh

COORDINATE_PATTERN = re.compile(r"Coordinate\s*\{[^}]*?point\s*\[([^\]]*)\]", re.S)
COORD_INDEX_PATTERN = re.compile(r"coordIndex\s*\[([^\]]*)\]", re.S)
NUMBER_PATTERN = re.compile(r"[-+]?\d*\.\d+|[-+]?\d+")


def _parse_vertices(pts_block: str) -> np.ndarray:
    values = np.array(NUMBER_PATTERN.findall(pts_block), dtype=np.float32)
    if values.size % 3 != 0:
        values = values[: values.size // 3 * 3]
    return values.reshape(-1, 3)


def _parse_faces(idx_block: str) -> np.ndarray:
    indices = [int(s) for s in re.findall(r"-?\d+", idx_block)]
    faces: list[list[int]] = []
    current: list[int] = []

    def flush_face() -> None:
        if len(current) >= 3:
            for k in range(1, len(current) - 1):
                faces.append([current[0], current[k], current[k + 1]])

    for idx in indices:
        if idx == -1:
            flush_face()
            current = []
        else:
            current.append(idx)
    flush_face()

    return np.asarray(faces, dtype=np.int32).reshape(-1, 3)


def load_vrml_meshes(path: Path) -> list[tuple[np.ndarray, np.ndarray]]:
    """
    Parse a VRML2 file and return a list of (vertices, faces) meshes.

    The parser supports both files with one shared Coordinate block and files
    with one Coordinate block per IndexedFaceSet. Polygonal faces are converted
    to triangles by fan triangulation.
    """
    text = Path(path).read_text(errors="ignore")
    coord_matches = list(COORDINATE_PATTERN.finditer(text))
    index_matches = list(COORD_INDEX_PATTERN.finditer(text))

    if not coord_matches:
        raise ValueError(f"No Coordinate {{ point [...] }} block found in {path}")

    coords = [
        {"pos": match.end(), "vertices": _parse_vertices(match.group(1))}
        for match in coord_matches
    ]
    meshes: list[tuple[np.ndarray, np.ndarray]] = []

    if len(coords) == 1:
        shared_vertices = coords[0]["vertices"]
        for match in index_matches:
            faces = _parse_faces(match.group(1))
            if faces.size:
                meshes.append((shared_vertices, faces))
        return meshes

    coords_sorted = sorted(coords, key=lambda item: int(item["pos"]))
    coord_idx = 0
    for match in index_matches:
        while (
            coord_idx + 1 < len(coords_sorted)
            and match.start() > int(coords_sorted[coord_idx + 1]["pos"])
        ):
            coord_idx += 1
        faces = _parse_faces(match.group(1))
        if faces.size:
            meshes.append((coords_sorted[coord_idx]["vertices"], faces))

    return meshes


def to_trimesh_list(
    meshes: list[tuple[np.ndarray, np.ndarray]],
) -> list[trimesh.Trimesh]:
    """Convert shared-index (vertices, faces) pairs to compact Trimesh objects."""
    tm_list: list[trimesh.Trimesh] = []
    for vertices, faces in meshes:
        used, inverse = np.unique(faces, return_inverse=True)
        vertices_local = np.asarray(vertices[used], dtype=np.float32)
        faces_local = inverse.reshape(faces.shape).astype(np.int32)
        tm_list.append(
            trimesh.Trimesh(vertices=vertices_local, faces=faces_local, process=False)
        )
    return tm_list


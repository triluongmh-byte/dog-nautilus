"""Render documentation pictures from the exported, assembled CAD meshes (CPU only)."""
from pathlib import Path
import json
import struct

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np
import vtk
from vtk.util.numpy_support import vtk_to_numpy

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/images"


def triangles(path):
    reader = vtk.vtkSTLReader()
    reader.SetFileName(str(path))
    reader.Update()
    poly = reader.GetOutput()
    if poly.GetNumberOfCells() > 3500:
        dec = vtk.vtkQuadricDecimation()
        dec.SetInputData(poly)
        dec.SetTargetReduction(1 - 3500 / poly.GetNumberOfCells())
        dec.Update()
        poly = dec.GetOutput()
    points = vtk_to_numpy(poly.GetPoints().GetData())
    faces = vtk_to_numpy(poly.GetPolys().GetConnectivityArray()).reshape(-1, 3)
    return points[faces].copy()


def colour(name):
    if name == "lid": return "#e7eceb"
    if name == "frame": return "#405567"
    if name.startswith("gear_"): return "#e2a23a"
    if name.startswith("foot_"): return "#df745b"
    if name.startswith("pin_"): return "#bec6cc"
    if name.endswith(("holder", "cradle", "clip")): return "#819d9f"
    return "#36a99c"


def render(parts, filename, title, elev, azim, opened=False, side=False):
    ts, cs = [], []
    for name, tri in parts:
        tri = tri.copy()
        if opened and name in ("lid", "pigtail_clip"):
            tri[:, :, 2] += 34
        normals = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
        normals /= np.maximum(np.linalg.norm(normals, axis=1, keepdims=True), 1e-12)
        light = np.array([0.35, -0.5, 0.8]); light /= np.linalg.norm(light)
        # Double-sided CAD display: imported STL winding can vary by face.
        shade = 0.57 + 0.43 * np.abs(normals @ light)
        base = np.array(matplotlib.colors.to_rgb(colour(name)))
        ts.append(tri); cs.append(np.clip(base[None, :] * shade[:, None], 0, 1))
    alltri, allcol = np.concatenate(ts), np.concatenate(cs)
    fig = plt.figure(figsize=(14, 9), dpi=140, facecolor="#f1f4f5")
    ax = fig.add_axes([0.01, 0.03, 0.98, 0.89], projection="3d", facecolor="#f1f4f5")
    ax.add_collection3d(Poly3DCollection(alltri, facecolors=allcol, edgecolors="none", zsort="average"))
    pts = alltri.reshape(-1, 3); lo, hi = pts.min(0), pts.max(0)
    center = (lo + hi) / 2; span = hi - lo
    for dim, setter in enumerate((ax.set_xlim, ax.set_ylim, ax.set_zlim)):
        setter(center[dim] - span[dim] * .56, center[dim] + span[dim] * .56)
    ax.set_box_aspect(span)
    ax.set_proj_type("ortho")
    ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off()
    fig.text(.055, .94, "NAUTILUS DOG  /  V0", fontsize=23, color="#203443", weight="bold")
    fig.text(.055, .902, title, fontsize=13, color="#526571")
    fig.text(.055, .035, "Actual CAD geometry  ·  Hardware fit and walking remain untested", fontsize=10, color="#647782")
    fig.savefig(OUT / filename, facecolor=fig.get_facecolor(), metadata={"Software": "Nautilus CAD documentation renderer"})
    plt.close(fig)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((ROOT / "case/out/parts.json").read_text())
    parts = [(p["name"], triangles(ROOT / "case/out" / p["stl"])) for p in manifest["parts"] if p.get("role") != "coupon" and p.get("printable") is not False]
    render(parts, "dog-isometric.png", "Four nautilus gear pairs + Jansen legs", 24, -58)
    render(parts, "dog-side.png", "Side inspection · gear and linkage layers", 9, -90, side=True)
    render(parts, "dog-open.png", "Lid lifted for inspection · unchanged assembly geometry", 30, -60, opened=True)
    print("README images:", OUT)

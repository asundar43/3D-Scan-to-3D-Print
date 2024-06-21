import open3d as o3d
import numpy as np
import os
import pymeshfix
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import logging
import threading


def convert_ply_to_stl(ply_files, output_dir, min_triangles, progress_bar, status_label):
    total_files = len(ply_files)
    for index, ply_file in enumerate(ply_files):
        if not ply_file.lower().endswith('.ply'):
            logging.warning(f'Skipping "{ply_file}" because it is filetype: "{os.path.splitext(ply_file)[1]}"')
            continue

        try:
            mesh = o3d.io.read_triangle_mesh(ply_file)
            mesh.compute_vertex_normals()

            while len(mesh.triangles) < min_triangles:
                mesh = mesh.subdivide_midpoint(number_of_iterations=1)

            mesh.remove_duplicated_vertices()
            mesh.remove_duplicated_triangles()
            mesh.remove_degenerate_triangles()
            mesh.remove_non_manifold_edges()

            vertices = np.asarray(mesh.vertices)
            faces = np.asarray(mesh.triangles)

            meshfix = pymeshfix.MeshFix(vertices, faces)
            meshfix.repair()

            watertight_mesh = o3d.geometry.TriangleMesh()
            watertight_mesh.vertices = o3d.utility.Vector3dVector(meshfix.v)
            watertight_mesh.triangles = o3d.utility.Vector3iVector(meshfix.f)

            watertight_mesh.compute_vertex_normals()

            stl_file = os.path.join(output_dir, os.path.basename(ply_file).replace('.ply', '.stl'))
            o3d.io.write_triangle_mesh(stl_file, watertight_mesh)
            logging.info(f"Converted {ply_file} to {stl_file} with {len(watertight_mesh.triangles)} triangles")
        except Exception as e:
            logging.error(f"Failed to process {ply_file}: {str(e)}")

        progress = (index + 1) / total_files * 100
        progress_bar["value"] = progress
        status_label.config(text=f"Processing file {index + 1} of {total_files}...")
        progress_bar.update_idletasks()
        status_label.update_idletasks()

    status_label.config(text="Conversion completed!")
    messagebox.showinfo("Info", "Finished converting all PLY files to STL files.")


def select_ply_files():
    global ply_files
    ply_files = filedialog.askopenfilenames(filetypes=[("PLY files", "*.ply")])
    if ply_files:
        status_label.config(text=f"Selected {len(ply_files)} PLY file(s).")
    else:
        status_label.config(text="No PLY files selected.")


def select_output_directory():
    global output_dir
    output_dir = filedialog.askdirectory()
    if output_dir:
        status_label.config(text=f"Selected output directory: {output_dir}")
    else:
        status_label.config(text="No output directory selected.")


def start_conversion():
    if ply_files and output_dir:
        min_triangles = min_triangles_var.get()
        threading.Thread(target=convert_ply_to_stl,
                         args=(ply_files, output_dir, min_triangles, progress_bar, status_label)).start()
    else:
        messagebox.showwarning("Input Required", "Please select PLY files and an output directory")


def setup_logging():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger()
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    return logger


if __name__ == "__main__":
    logger = setup_logging()
    ply_files = []
    output_dir = ""

    root = tk.Tk()
    root.title("PLY to STL Converter")

    frame = tk.Frame(root)
    frame.pack(padx=10, pady=10)

    select_ply_button = tk.Button(frame, text="Select PLY Files", command=select_ply_files)
    select_ply_button.pack(pady=5)

    select_output_button = tk.Button(frame, text="Select Output Directory", command=select_output_directory)
    select_output_button.pack(pady=5)

    min_triangles_label = tk.Label(frame, text="Minimum Triangles:")
    min_triangles_label.pack(pady=5)

    min_triangles_var = tk.IntVar(value=10000)
    min_triangles_entry = tk.Entry(frame, textvariable=min_triangles_var)
    min_triangles_entry.pack(pady=5)

    convert_button = tk.Button(frame, text="Convert", command=start_conversion)
    convert_button.pack(pady=10)

    progress_bar = ttk.Progressbar(frame, orient="horizontal", length=300, mode="determinate")
    progress_bar.pack(pady=10)

    status_label = tk.Label(frame, text="No conversion in progress")
    status_label.pack(pady=5)

    root.mainloop()

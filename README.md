# Voxel Engine

A lightweight voxel engine built with Python, ModernGL, Pygame, and GLSL — inspired by Minecraft.

![Voxel Engine showcase](https://res.cloudinary.com/dyez98wtv/image/upload/v1791219642/2026-10-06_01-51_odt8t4.webp)

*And yes, that screenshot is from this project — not Minecraft. The blocks are innocent.*

## Run it

```bash
pip install pygame moderngl PyGLM numpy numba opensimplex
python main.py
```

Run the command from the project root. A Python installation with OpenGL 3.3 support is recommended.

## Controls

- **W / S** — move forward / backward
- **A / D** — move left / right
- **Q / E** — move up / down
- **Mouse** — look around
- **Left click** — remove a voxel
- **Right click** — switch between remove and add mode

## Highlights

- Chunk-based voxel world with procedural terrain, caves, trees, water, and clouds.
- Frustum culling skips chunks outside the camera view.
- Numba-compiled terrain and mesh generation speeds up CPU-heavy work.
- Binary greedy meshing combines compatible visible faces while preserving materials and ambient occlusion.
- Ambient occlusion adds depth to voxel corners.
- Vertex data is packed into a single `uint32`, storing position, voxel, face, AO, and triangle-flip data efficiently.
- Shared NumPy voxel storage keeps chunk data compact and fast to access.
- OpenGL depth testing, face culling, texture arrays, mipmaps, and nearest-neighbor filtering improve rendering performance while keeping the pixel-art look.

## Tech

See [the file-by-file meshing integration guide](docs/meshing-integration.md) for the
world, mesh, shader, and editing data flow.

For repeatable CPU meshing timings and binary greedy meshing integration notes,
see [the meshing benchmark](benchmarks/README.md).

- Python
- GLSL
- Pygame
- ModernGL
- NumPy / Numba

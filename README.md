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
- **Esc** — quit

## Highlights

- Chunk-based voxel world with procedural terrain, caves, trees, water, and clouds.
- Frustum culling skips chunks outside the camera view.
- Numba-compiled terrain and mesh generation speeds up CPU-heavy work.
- Visible-face meshing avoids generating hidden cube faces.
- Ambient occlusion adds depth to voxel corners.
- Vertex data is packed into a single `uint32`, storing position, voxel, face, AO, and triangle-flip data efficiently.
- Shared NumPy voxel storage keeps chunk data compact and fast to access.
- OpenGL depth testing, face culling, texture arrays, mipmaps, and nearest-neighbor filtering improve rendering performance while keeping the pixel-art look.

## Tech

- Python
- GLSL
- Pygame
- ModernGL
- NumPy / Numba

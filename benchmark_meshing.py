"""Camera-independent CPU benchmark for the engine's packed-vertex mesh API."""

import argparse
from datetime import datetime, timezone
import hashlib
import importlib
import json
import platform
from pathlib import Path
from random import seed as seed_random
from time import perf_counter_ns

import numba
import numpy as np

from settings import CHUNK_SIZE as N, CHUNK_VOL, SEED, WORLD_W, WORLD_H, WORLD_D, WORLD_VOL
from world_objects.chunk import Chunk


# Bind the dispatcher at module scope so Numba can call the existing terrain code.
generate_chunk_terrain = Chunk.generate_terrain


@numba.njit
def generate_terrain(voxels, position, seed):
    # Numba's RNG has separate state from Python's random module.
    seed_random(seed)
    generate_chunk_terrain(voxels, position[0] * N, position[1] * N, position[2] * N)


def chunk_index(position):
    x, y, z = position
    return x + WORLD_W * z + WORLD_W * WORLD_D * y


def neighborhood(position):
    x, y, z = position
    for cy in range(max(0, y - 1), min(WORLD_H, y + 2)):
        for cz in range(max(0, z - 1), min(WORLD_D, z + 2)):
            for cx in range(max(0, x - 1), min(WORLD_W, x + 2)):
                yield cx, cy, cz


def make_case(name, world, position, seed):
    world.fill(0)
    voxels = world[chunk_index(position)].reshape(N, N, N)  # y, z, x
    y, z, x = np.indices((N, N, N))
    if name == 'solid':
        voxels.fill(4)
    elif name == 'enclosed':
        for neighbor in neighborhood(position):
            world[chunk_index(neighbor)].fill(4)
    elif name == 'slab':
        voxels[:N // 2] = 4
    elif name == 'checkerboard':
        voxels[:] = ((x + y + z) % 2 == 0) * 4
    elif name == 'mixed':
        rng = np.random.default_rng(seed)
        voxels[:] = rng.integers(1, 8, size=voxels.shape, dtype=np.uint8)
        voxels[rng.random(voxels.shape) < 0.5] = 0
    elif name == 'terrain':
        for neighbor in neighborhood(position):
            generate_terrain(world[chunk_index(neighbor)], neighbor,
                             seed + chunk_index(neighbor))
    elif name != 'empty':
        raise ValueError(name)
    return world[chunk_index(position)]


def exposed_area(world, position):
    """Independent reference: a one-voxel halo, with out-of-world treated solid."""
    halo = np.ones((N + 2,) * 3, dtype=bool)
    coordinates = np.arange(-1, N + 1)
    # Assemble only the 27 small pieces needed for cross-chunk face checks.
    for oy in (-1, 0, 1):
        for oz in (-1, 0, 1):
            for ox in (-1, 0, 1):
                p = tuple(a + b for a, b in zip(position, (ox, oy, oz)))
                if not (0 <= p[0] < WORLD_W and 0 <= p[1] < WORLD_H and 0 <= p[2] < WORLD_D):
                    continue
                source = world[chunk_index(p)].reshape(N, N, N)
                selections = [np.flatnonzero(coordinates // N == o) for o in (oy, oz, ox)]
                local = [coordinates[s] % N for s in selections]
                halo[np.ix_(*selections)] = source[np.ix_(*local)] != 0
    center = halo[1:-1, 1:-1, 1:-1]
    return sum(int(np.count_nonzero(center & ~adjacent)) for adjacent in (
        halo[:-2, 1:-1, 1:-1], halo[2:, 1:-1, 1:-1],
        halo[1:-1, :-2, 1:-1], halo[1:-1, 2:, 1:-1],
        halo[1:-1, 1:-1, :-2], halo[1:-1, 1:-1, 2:]))


def validate_mesh(mesh, expected_area):
    if mesh.dtype != np.uint32 or mesh.ndim != 1 or mesh.size % 6:
        raise ValueError('Expected six packed uint32 vertices per quad')
    xyz = np.column_stack((mesh >> 26, (mesh >> 20) & 63,
                           (mesh >> 14) & 63)).astype(np.int64)
    if np.any(xyz > N):
        raise ValueError('Vertex outside chunk')
    triangles = xyz.reshape(-1, 3, 3)
    cross = np.cross(triangles[:, 1] - triangles[:, 0],
                     triangles[:, 2] - triangles[:, 0])
    if np.any(np.count_nonzero(cross, axis=1) != 1):
        raise ValueError('Degenerate or non-axis-aligned triangle')
    area = int(np.abs(cross).sum()) / 2
    if area != expected_area:
        raise ValueError(f'Mesh area {area} != exposed voxel area {expected_area}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--builder', default='meshes.binary_greedy_mesh_builder:build_chunk_mesh')
    parser.add_argument('--iterations', type=int, default=50)
    parser.add_argument('--warmup', type=int, default=5)
    parser.add_argument('--seed', type=int, default=SEED)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.iterations < 1 or args.warmup < 1:
        parser.error('iterations and warmup must be positive')
    module, function = args.builder.split(':')
    builder = getattr(importlib.import_module(module), function)
    world = np.zeros((WORLD_VOL, CHUNK_VOL), dtype=np.uint8)
    position = (WORLD_W // 2, 0, WORLD_D // 2)
    report = {
        'timestamp_utc': datetime.now(timezone.utc).isoformat(),
        'builder': args.builder, 'python': platform.python_version(),
        'platform': platform.platform(), 'cpu': platform.processor(),
        'numpy': np.__version__, 'numba': numba.__version__,
        'chunk_size': N, 'world_shape': [WORLD_W, WORLD_H, WORLD_D],
        'chunk_position': position, 'seed': args.seed,
        'iterations': args.iterations, 'warmup': args.warmup, 'cases': [],
    }
    print(f'{N}³ chunks; {args.iterations} samples/case; CPU build only (includes allocation)')
    print(f'{"case":14} {"median ms":>10} {"p95 ms":>10} {"quads":>10} {"mesh KiB":>10}')
    for name in ('empty', 'solid', 'enclosed', 'slab', 'terrain', 'checkerboard', 'mixed'):
        voxels = make_case(name, world, position, args.seed)
        input_hash = hashlib.sha256(world).hexdigest()
        start = perf_counter_ns()
        mesh = builder(voxels, 1, position, world)
        first_call_ms = (perf_counter_ns() - start) / 1e6
        expected_area = exposed_area(world, position)
        validate_mesh(mesh, expected_area)
        digest = hashlib.sha256(mesh).hexdigest()
        for _ in range(args.warmup):
            mesh = builder(voxels, 1, position, world)
        samples = []
        for _ in range(args.iterations):
            # Discard the previous output before timing, so its deallocation is excluded.
            del mesh
            start = perf_counter_ns()
            mesh = builder(voxels, 1, position, world)
            samples.append((perf_counter_ns() - start) / 1e6)
        validate_mesh(mesh, expected_area)
        if hashlib.sha256(mesh).hexdigest() != digest:
            raise ValueError(f'{name}: output changed between identical builds')
        row = {
            'name': name, 'input_sha256': input_hash, 'mesh_sha256': digest,
            'solid_voxels': int(np.count_nonzero(voxels)), 'exposed_unit_faces': expected_area,
            'vertices': int(mesh.size), 'triangles': int(mesh.size // 3),
            'quads': int(mesh.size // 6), 'mesh_bytes': int(mesh.nbytes),
            'first_call_ms': first_call_ms, 'median_ms': float(np.median(samples)),
            'p95_ms': float(np.percentile(samples, 95)), 'min_ms': min(samples),
            'samples_ms': samples,
        }
        report['cases'].append(row)
        print(f'{name:14} {row["median_ms"]:10.3f} {row["p95_ms"]:10.3f}'
              f' {row["quads"]:10,d} {row["mesh_bytes"] / 1024:10.1f}')
        if name == 'empty':
            print(f'  First call (includes JIT if needed): {first_call_ms:.1f} ms; excluded above')
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + '\n')
        print(f'Saved {args.output}')


if __name__ == '__main__':
    main()

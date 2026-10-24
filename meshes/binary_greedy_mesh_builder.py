"""Binary visibility/rectangle mesher using the engine's packed vertex contract."""
from settings import CHUNK_SIZE as N, CHUNK_AREA, np, njit
from meshes.chunk_mesh_builder import get_ao, is_void, pack_data


@njit
def trailing_zeros(bits):
    count = 0
    while (bits & np.uint64(1)) == 0:
        bits >>= np.uint64(1)
        count += 1
    return count


@njit
def build_chunk_mesh(chunk_voxels, format_size, chunk_pos, world_voxels):
    if not 1 <= N <= 62:
        raise ValueError('Packed coordinates and padded uint64 rows require CHUNK_SIZE <= 62')
    if format_size != 1:
        raise ValueError('Expected one packed uint32 per vertex')
    if not np.any(chunk_voxels):
        return np.empty(0, dtype=np.uint32)
    cx, cy, cz = chunk_pos
    # Columns along Y, X, Z, with a solid halo outside the finite world.
    columns = np.zeros((3, N + 2, N + 2), dtype=np.uint64)
    for y in range(-1, N + 1):
        for z in range(-1, N + 1):
            for x in range(-1, N + 1):
                if 0 <= x < N and 0 <= y < N and 0 <= z < N:
                    solid = chunk_voxels[x + N * z + CHUNK_AREA * y] != 0
                else:
                    solid = not is_void((x, y, z), (cx*N+x, cy*N+y, cz*N+z), world_voxels)
                if solid:
                    columns[0, z+1, x+1] |= np.uint64(1) << np.uint64(y+1)
                    columns[1, z+1, y+1] |= np.uint64(1) << np.uint64(x+1)
                    columns[2, x+1, y+1] |= np.uint64(1) << np.uint64(z+1)

    # At most six faces per occupied voxel; trimmed copy owns only its output.
    output = np.empty(np.count_nonzero(chunk_voxels) * 36, dtype=np.uint32)
    index = 0
    inner_mask = (np.uint64(1) << np.uint64(N)) - np.uint64(1)
    for face in range(6):
        axis = face // 2
        positive = face == 0 or face == 2 or face == 5
        # Each slice holds keys and binary rows in the two face-plane axes.
        keys = np.zeros((N, N, N), dtype=np.uint32)
        rows = np.zeros((N, N), dtype=np.uint64)
        for v in range(N):
            for u in range(N):
                col = columns[axis, v+1, u+1]
                if positive:
                    visible = col & ~(col >> np.uint64(1))
                else:
                    visible = col & ~(col << np.uint64(1))
                visible = (visible >> np.uint64(1)) & inner_mask
                while visible:
                    depth = trailing_zeros(visible)
                    visible &= visible - np.uint64(1)
                    if axis == 0:
                        x, y, z = u, depth, v
                        normal = (0, 1 if positive else -1, 0)
                        plane = 'Y'
                    elif axis == 1:
                        x, y, z = depth, u, v
                        normal = (1 if positive else -1, 0, 0)
                        plane = 'X'
                    else:
                        x, y, z = v, u, depth
                        normal = (0, 0, 1 if positive else -1)
                        plane = 'Z'
                    dx, dy, dz = normal
                    ao = get_ao((x+dx, y+dy, z+dz),
                                (cx*N+x+dx, cy*N+y+dy, cz*N+z+dz), world_voxels, plane)
                    material = chunk_voxels[x + N*z + CHUNK_AREA*y]
                    key = (int(material) << 8) | ao[0] | (ao[1] << 2) | (ao[2] << 4) | (ao[3] << 6)
                    keys[depth, u, v] = key
                    rows[depth, u] |= np.uint64(1) << np.uint64(v)

        for depth in range(N):
            for u in range(N):
                while rows[depth, u]:
                    v = trailing_zeros(rows[depth, u])
                    key = keys[depth, u, v]
                    ao = (key & 3, (key >> 2) & 3, (key >> 4) & 3, (key >> 6) & 3)
                    width, height = 1, 1
                    # Constant AO guarantees the old per-unit interpolation survives merging.
                    if ao[0] == ao[1] == ao[2] == ao[3]:
                        while v + height < N and keys[depth, u, v+height] == key and (rows[depth, u] & (np.uint64(1) << np.uint64(v+height))):
                            height += 1
                    mask = ((np.uint64(1) << np.uint64(height)) - np.uint64(1)) << np.uint64(v)
                    if ao[0] == ao[1] == ao[2] == ao[3]:
                        while u + width < N:
                            if (rows[depth, u+width] & mask) != mask:
                                break
                            matches = True
                            for vv in range(v, v+height):
                                if keys[depth, u+width, vv] != key:
                                    matches = False
                                    break
                            if not matches:
                                break
                            width += 1
                    for uu in range(u, u+width):
                        rows[depth, uu] &= ~mask
                    d = depth + int(positive)
                    if axis == 0:
                        corners = ((u,d,v), (u+width,d,v), (u+width,d,v+height), (u,d,v+height))
                    elif axis == 1:
                        corners = ((d,u,v), (d,u+width,v), (d,u+width,v+height), (d,u,v+height))
                    else:
                        corners = ((v,u,d), (v,u+width,d), (v+height,u+width,d), (v+height,u,d))
                    flip = ao[1] + ao[3] > ao[0] + ao[2]
                    if face == 0:
                        order = (1,0,3,1,3,2) if flip else (0,3,2,0,2,1)
                    elif face == 1:
                        order = (1,3,0,1,2,3) if flip else (0,2,3,0,1,2)
                    elif face == 2 or face == 4:
                        order = (3,0,1,3,1,2) if flip else (0,1,2,0,2,3)
                    else:
                        order = (3,1,0,3,2,1) if flip else (0,2,1,0,3,2)
                    for corner in order:
                        x, y, z = corners[corner]
                        output[index] = pack_data(x,y,z,key >> 8,face,ao[corner],flip)
                        index += 1
    return output[:index].copy()

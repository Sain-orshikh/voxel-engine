from settings import *
from meshes.chunk_mesh_builder import get_chunk_index

class VoxelHandler:
    def __init__(self, world):
        self.app = world.app
        self.chunks = world.chunks

        #ray casting result
        self.chunk = None
        self.voxel_id = None
        self.voxel_index = None
        self.local_pos = None
        self.world_pos = None
        self.voxel_normal = None

        self.interaction_mode = 0 #0: remove, 1: add
        self.new_voxel_id = 1

    def add_voxel(self):
        if self.voxel_id:
            #check voxel id along normal
            result = self.get_voxel_id(self.voxel_world_pos + self.voxel_normal)

            #is the new place empty?
            if not result[0] and result[3]:
                _, voxel_index, _, chunk = result
                chunk.voxels[voxel_index] = self.new_voxel_id
                self.rebuild_affected_chunks(self.voxel_world_pos + self.voxel_normal)

    def rebuild_affected_chunks(self, world_pos):
        """Refresh visibility and AO consumers, including edge/corner neighbors."""
        wx, wy, wz = map(int, world_pos)
        affected = set()
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    index = get_chunk_index((wx + dx, wy + dy, wz + dz))
                    if index != -1:
                        affected.add(index)
        for index in sorted(affected):
            chunk = self.chunks[index]
            chunk.is_empty = not np.any(chunk.voxels)
            chunk.mesh.rebuild()

    def remove_voxel(self):
        if self.voxel_id:
            self.chunk.voxels[self.voxel_index] = 0
            self.rebuild_affected_chunks(self.voxel_world_pos)

    def set_voxel(self):
        if self.interaction_mode:
            self.add_voxel()
        else:
            self.remove_voxel()

    def switch_mode(self):
        self.interaction_mode = not self.interaction_mode

    def update(self):
        self.ray_cast()

    def ray_cast(self):
        # start point
        x1, y1, z1 = self.app.player.position
        # end point
        x2, y2, z2 = self.app.player.position + self.app.player.forward * MAX_RAY_DIST

        current_voxel_pos = glm.ivec3(x1, y1, z1)
        self.voxel_id = 0
        self.voxel_normal = glm.ivec3(0)
        step_dir = -1

        dx = glm.sign(x2 - x1)
        delta_x = min(dx / (x2 - x1), 10000000.0) if dx != 0 else 10000000.0
        max_x = delta_x * (1.0 - glm.fract(x1)) if dx > 0 else delta_x * glm.fract(x1)

        dy = glm.sign(y2 - y1)
        delta_y = min(dy / (y2 - y1), 10000000.0) if dy != 0 else 10000000.0
        max_y = delta_y * (1.0 - glm.fract(y1)) if dy > 0 else delta_y * glm.fract(y1)

        dz = glm.sign(z2 - z1)
        delta_z = min(dz / (z2 - z1), 10000000.0) if dz != 0 else 10000000.0
        max_z = delta_z * (1.0 - glm.fract(z1)) if dz > 0 else delta_z * glm.fract(z1)

        while not (max_x > 1.0 and max_y > 1.0 and max_z > 1.0):

            result = self.get_voxel_id(voxel_world_pos=current_voxel_pos)
            if result[0]:
                self.voxel_id, self.voxel_index, self.voxel_local_pos, self.chunk = result
                self.voxel_world_pos = current_voxel_pos

                if step_dir == 0:
                    self.voxel_normal.x = -dx
                elif step_dir == 1:
                    self.voxel_normal.y = -dy
                else:
                    self.voxel_normal.z = -dz
                return True

            if max_x < max_y:
                if max_x < max_z:
                    current_voxel_pos.x += dx
                    max_x += delta_x
                    step_dir = 0
                else:
                    current_voxel_pos.z += dz
                    max_z += delta_z
                    step_dir = 2
            else:
                if max_y < max_z:
                    current_voxel_pos.y += dy
                    max_y += delta_y
                    step_dir = 1
                else:
                    current_voxel_pos.z += dz
                    max_z += delta_z
                    step_dir = 2
        return False

    def get_voxel_id(self, voxel_world_pos):
        wx, wy, wz = map(int, voxel_world_pos)
        chunk_index = get_chunk_index((wx, wy, wz))
        if chunk_index == -1:
            return 0, 0, 0, 0
        chunk = self.chunks[chunk_index]
        local_pos = glm.ivec3(wx % CHUNK_SIZE, wy % CHUNK_SIZE, wz % CHUNK_SIZE)
        lx, ly, lz = local_pos
        voxel_index = lx + CHUNK_SIZE * lz + CHUNK_AREA * ly
        return chunk.voxels[voxel_index], voxel_index, local_pos, chunk

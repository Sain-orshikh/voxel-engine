from meshes.quad_mesh import QuadMesh


class Water:
    def __init__(self, app):
        self.mesh = QuadMesh(app)

    def render(self):
        self.mesh.render()
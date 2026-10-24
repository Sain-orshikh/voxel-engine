import numpy as np

class BaseMesh:
    def __init__(self):
        #OpenGl context
        self.ctx = None
        #shader program
        self.program = None
        #vertex buffer for data type format: "3f 3f"
        self.vbo_format = None
        #attribute names according to the format: ("in_position", "in_color")
        self.attrs: tuple[str, ...] = None
        #vertex array object    
        self.vao = None
        self.vbo = None

    def get_vertex_data(self) -> np.array: ...

    def get_vao(self):
        vertex_data = self.get_vertex_data()
        # OpenGL buffers need storage even when an empty/fully hidden chunk has
        # no vertices. Keep its draw count at zero instead of adding dummy data.
        vbo = (self.ctx.buffer(vertex_data) if vertex_data.nbytes
               else self.ctx.buffer(reserve=4))
        vao = self.ctx.vertex_array(
            self.program, [(vbo, self.vbo_format, *self.attrs)], skip_errors = True
        )
        if not vertex_data.nbytes:
            vao.vertices = 0
        self.vbo = vbo
        return vao

    def render(self):
        self.vao.render()

#version 330 core

layout (location = 0) in vec3 in_position;

uniform mat4 m_proj;
uniform mat4 m_view;
uniform int center;
uniform float u_time;
uniform float cloud_scale;

void main() {
    vec3 pos = in_position;
    pos.xz -= center;
    pos.xz *= cloud_scale;
    pos.xz += center;
    pos.xz += 300 * sin(0.01 * u_time);
    gl_Position = m_proj * m_view * vec4(pos, 1.0);
}
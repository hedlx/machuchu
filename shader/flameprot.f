#version 130

in vec2 p;
uniform float time;

vec2 V0(vec2 co) {
    return co;
}

vec2 V1(vec2 co) {
    return vec2(sin(co.x), sin(co.y));
}

vec2 V2(vec2 co) {
    return co / sqrt(dot(co, co));
}

vec2 V3(vec2 co) {
    float r = dot(co, co);
    return vec2(co.x * sin(r) - co.y * cos(r),
                co.x * cos(r) + co.y * sin(r));
}

#define V_N 4
vec2 V(int i, vec2 co) {
    switch(i) {
        case 0: return V0(co); break;
        case 1: return V1(co); break;
        case 2: return V2(co); break;
        case 3: return V3(co); break;
    }
}

float rand(vec2 co){
  return fract(sin(dot(co.xy ,vec2(12.9898,78.233))) * 43758.5453);
}

void main() {
    float c = .0;
    vec3 tx = vec3(1, 3, 2);
    vec3 ty = vec3(3, 2, 2);
    vec2 co = vec2(dot(tx, vec3(p, 1)),
                   dot(ty, vec3(p, 1)));
    gl_FragColor = vec4(V(1, co), 0, 0);
}

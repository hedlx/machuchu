#version 130

#include "color.h"

varying vec4 p;
uniform float time;

float speed = 0.001f;

float rand(vec2 co){
  return fract(sin(dot(co.xy ,vec2(12.9898,78.233))) * 43758.5453);
}

void main() {
    float ts = speed * time;

    float l = 0;

    vec3 c = lab2rgb(
        l * l,
        l * l * l,
        0);

    gl_FragColor = vec4(c, 0);
}
#version 150

in vec2 p;
out vec4 fragColor;

uniform float time;

#include "lib.h"
#include "color.h"

void main() {
    float x = p.x;
    float y = p.y;
    float t = time / 1000;

    float r = t / sqrt(t + sqr(x) + sqr(y));
    float f = atan(x, y) / TAU * 2 + .5;

    float a = TAU * mod(r + f, 1);
    vec3 c = lab2rgb(75, 50 * sin(a), 50 * cos(a));

    fragColor = vec4(c, 1);
}

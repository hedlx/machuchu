// Created by jerky in 2020-03-22
// https://www.shadertoy.com/view/WdlyDM
#include "preamble.h"

// This is free and unencumbered software released into the public domain.
// https://unlicense.org/UNLICENSE

#define RANK_1           6
#define RANK_2           7
#define RANK_3           9
#define ZOOM_SPEED_1     2.
#define ZOOM_SPEED_2     3.
#define ZOOM_SPEED_3     5.
#define ROTATE_SPEED_1  10.
#define ROTATE_SPEED_2  -5.
#define ROTATE_SPEED_3   3.
#define SATURATION_1     1.0
#define SATURATION_2     0.5
#define SATURATION_3     0.75
#define POINT_SIZE       0.0002

/* library */

const float PI = radians(180.f);
const float TAU = radians(360.f);

float length2(vec2 p) { return p.x * p.x + p.y * p.y; }
int idiv(int a, int b) { return (a + (a > 0 ? b - 1 : 0)) / b; }

vec3 hsv2rgb(float h, float s, float v) {
    h = fract(h) * 6.;
    float c = v * s;
    float x = c * (1. - abs(mod(h, 2.) - 1.));
    float m = v - c;
    switch (int(h)) {
        case 6:
        case 0: return m + vec3(c, x, 0);
        case 1: return m + vec3(x, c, 0);
        case 2: return m + vec3(0, c, x);
        case 3: return m + vec3(0, x, c);
        case 4: return m + vec3(x, 0, c);
        case 5: return m + vec3(c, 0, x);
    }
}

bool keyToggle(int key) {
    return texelFetch(iChannel0, ivec2(key, 2), 0).x > 0.;
}

/* voronoi */

float res_d = 1./0.;
vec3 res_color = vec3(0, 0, 0);
vec2 p;
int debug_rings = 0;

void add_point(vec2 pos, vec3 color) {
    float distance_from_center = length2(p);
    float d = length2(pos - p.xy);
    if (res_d < d)
        return;
    res_d = d;
    res_color = !keyToggle(80/*p*/) && d < distance_from_center * POINT_SIZE
        ? color * 0.8
        : color * atan(distance_from_center / d / 2.) / PI * 2.;
}

// This function adds an infinity number of nested rings to the Voronoi Diagram.
// The ring is a group of points at the same radius. Each ring consists of
// `rank` points.
//
// The trick is, for each pixel, this function is checking only three possible
// points: one in the ring above, one in the ring bellow, and one in two rings
// bellow.
void endless(int rank, float zoom, float rotation, float sat) {
    if (rank <= 2) return;
    float ring_dist = (1. + sin(PI / float(rank))) / cos(PI / float(rank));
    zoom *= float(rank);

    int center_ring = int(floor(log(length2(p)) / 2. / log(ring_dist) - zoom));
    float alpha = (atan(p.y, p.x) / TAU - rotation) * float(rank);
    float alpha1 = floor(alpha + 0.5) / float(rank);
    float alpha2 = floor(alpha) / float(rank);

    debug_rings += center_ring;
    for (int ring = center_ring - 1; ring <= center_ring + 1; ring++) {
        float shift = float(abs(ring) % 2) / 2. / float(rank);
        float color_shift = float(idiv(3 * ring, 2)) / float(rank);
        float d = abs(ring) % 2 == 0 ? alpha1 : alpha2;
        float t = (rotation + shift + d) * TAU;
        vec2 pos = pow(ring_dist, float(ring) + zoom) * vec2(cos(t), sin(t));
        add_point(pos, hsv2rgb(d + color_shift, sat, 1.));
    }
}

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    p.xy = (fragCoord.xy - iResolution.xy / 2.) * pow(2., 20. * iMouse.x / iResolution.x);
    float rot = iTime / 1000.;
    float zoom = iTime / 100.;

    if (!keyToggle(49/*1*/))
        endless(RANK_1, zoom * ZOOM_SPEED_1, rot * ROTATE_SPEED_1, SATURATION_1);
    if (!keyToggle(50/*2*/))
        endless(RANK_2, zoom * ZOOM_SPEED_2, rot * ROTATE_SPEED_2, SATURATION_2);
    if (keyToggle(51/*3*/))
        endless(RANK_3, zoom * ZOOM_SPEED_3, rot * ROTATE_SPEED_3, SATURATION_3);

    float debug_shade = keyToggle(68/*d*/) ? float(debug_rings % 2) / 4. + 0.5 : 1.;

    fragColor = vec4(res_color, 1.) * debug_shade;
}

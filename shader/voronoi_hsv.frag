#version 150

out vec4 machuchu_FragColor;

in vec2 p;
uniform float time;

uniform bool draw_dots;
uniform bool draw_borders; // looks ok if ether rank1 or rank2 is zero

uniform int rank1 = 6, rank2 = 7;
uniform int rotate_speed1 = 10, rotate_speed2 = -5;
uniform int zoom_speed1 = 0, zoom_speed2 = 0;
#pragma machuchu slider rank1 2 10
#pragma machuchu slider rank2 2 10
#pragma machuchu slider rotate_speed1 -100 100
#pragma machuchu slider rotate_speed2 -100 100
#pragma machuchu slider zoom_speed1 -100 100
#pragma machuchu slider zoom_speed2 -100 100

#include "color.h"

#define POINT_SIZE 0.0002
uniform bool DEBUG_RINGS;

float res_d = 1./0.;
vec3 res_color = vec3(0);
bool in_border = false;
int debug_rings = 0;

void add_point(vec2 pos, vec3 color) {
    float distance_from_center = length2(p);
    float d = length2(pos - p);
    if(res_d < d)
        return;

    if (draw_borders &&
        res_d != 1./0. &&
        (res_d - d) / distance_from_center < 0.1)
        in_border = true;

    res_d = d;

    float shade = draw_dots && d < distance_from_center * POINT_SIZE
        ? 0.8
        : atan(distance_from_center / d / 2.) / PI * 2.;

    if (in_border)
        shade *= 0.5;

    res_color = color * shade;
}

void endless(int rank, float ring_dist, float zoom, float rotation, float sat) {
    if(rank <= 2) return;
    if(ring_dist == 0.)
        ring_dist = (1. + sin(PI / float(rank))) / cos(PI / float(rank));
    zoom *= float(rank);

    int center_ring = int(floor(log(length2(p)) / 2. / log(ring_dist) - zoom));
    float alpha = (atan(p.y, p.x)/TAU - rotation) * float(rank);
    float alpha1 = floor(alpha+0.5) / float(rank);
    float alpha2 = floor(alpha) / float(rank);

    debug_rings += center_ring;
    for(int ring = center_ring-1; ring <= center_ring+1; ring++) {
        float shift = float(abs(ring) % 2) / 2. / float(rank);
        float color_shift = float(idiv(3*ring, 2)) / float(rank);
        float d = abs(ring)%2 == 0? alpha1 : alpha2;
        float t = (rotation + shift + d)*TAU;
        vec2 pos = pow(ring_dist, float(ring) + zoom) * vec2(cos(t), sin(t));
        add_point(pos, hsv2rgb(d+color_shift,sat, 1.));
    }
}

void main() {
    float rot = time/1000000.;
    float zoom = time/100000.;
    endless(rank1, 0., zoom*float(zoom_speed1), rot*float(rotate_speed1), 1.0);
    endless(rank2, 0., zoom*float(zoom_speed2), rot*float(rotate_speed2), 0.5);

    float shade = 1.;
    if (DEBUG_RINGS)
        shade *= float(debug_rings % 2) / 2. + 0.5;

    machuchu_FragColor = vec4(res_color, 1) * shade;
}

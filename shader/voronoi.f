#version 130

varying vec4 p;
uniform float time;

uniform bool draw_dots = true;

uniform int rank1 = 6, rank2 = 7;
uniform int rotate_speed1 = 10, rotate_speed2 = -5;
uniform int zoom_speed1 = 0, zoom_speed2 = 0;
#pragma machachu slider rank1 2 10
#pragma machachu slider rank2 2 10
#pragma machachu slider rotate_speed1 -100 100
#pragma machachu slider rotate_speed2 -100 100
#pragma machachu slider zoom_speed1 -100 100
#pragma machachu slider zoom_speed2 -100 100

#include "lib.h"

#define BLACK_DOT_SIZE 0.0002
//#define DEBUG_RINGS 2

float res_d = 1/0.;
vec3 res_color = vec3(0,0,0);
float debug_rings = 0;

void add(vec2 pos, vec3 color, vec2 center)
{
    vec2 pos2 = pos;
    float distance_from_center = sqr(p.x-center.x) + sqr(p.y-center.y);
    pos -= p.xy;
    pos *= pos;
    float d = pos.x+pos.y;
    if(res_d > d) {

        #ifdef BLACK_DOT_SIZE
        if (draw_dots) {
            if(d < distance_from_center * BLACK_DOT_SIZE) {
                res_d = d;
                res_color = color*0.8;
                return;
            }
        }
        #endif

        res_d = d;
        res_color = color;
    }
}

int div_up(int a, int b) {
        return a/b + (a%b>0?1:0);
}

void endless(int rank, float ring_dist, float zoom, float rotation, vec2 center, float sat)
{
    if(rank <= 2) return;
    if(ring_dist == 0)
        ring_dist = (1 + sin(PI/rank)) / cos(PI/rank);
    zoom *= rank;
    vec2 p = p.xy - center;

    int center_ring = int(floor( log(sqr(p.x)+sqr(p.y))/2/log(ring_dist) - zoom));
    float alpha = (atan(p.y, p.x)/TAU - rotation)*rank;
    float alpha1 = floor(alpha+0.5) / rank;
    float alpha2 = floor(alpha) / rank;

    debug_rings += center_ring;
    for(int ring = center_ring-1; ring <= center_ring+1; ring++) {
      float shift = (ring%2==0?0:1)/2.0/rank;
      float color_shift = div_up(-3*ring, 2)/float(rank);
      float d = ring%2 == 0? alpha1 : alpha2;
      float t = (rotation + shift + d)*TAU;
      vec2 pos = pow(ring_dist, ring+zoom) * vec2(cos(t), sin(t)) + center;
      add(pos, hsv2rgb(d+color_shift,sat, 1), center);
    }
}

void main()
{
    float rot = time/1000000.;
    float zoom = time/100000.;
    endless(rank1, 0, zoom*zoom_speed1, rot*rotate_speed1, vec2(0), 1.0);
    endless(rank2, 0, zoom*zoom_speed2, rot*rotate_speed2, vec2(0), 0.5);
    #ifdef DEBUG_RINGS
    debug_rings = mod(1000+debug_rings, DEBUG_RINGS)/2/DEBUG_RINGS + 0.5;
    #else
    debug_rings = 1;
    #endif
    gl_FragColor = vec4(res_color, 1.) * debug_rings;
}

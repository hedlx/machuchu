#version 130

varying vec4 p;
uniform float time;

#include "lib.h"

#define BLACK_DOT_SIZE 0.0002
//#define DEBUG_RINGS 2

float res_d = 1/0.;
vec3 res_color = vec3(0,0,0);
float distance_from_center = sqr(p.x) + sqr(p.y);
float debug_rings = 0;

void add(vec2 pos, vec3 color)
{
    pos -= p.xy;
    pos *= pos;
    float d = pos.x+pos.y;
    #ifdef BLACK_DOT_SIZE
    if(d < distance_from_center * BLACK_DOT_SIZE) {
        res_d = d;
        res_color = color*0.8;
    } else
    #endif
    if(res_d > d) {
        res_d = d;
        res_color = color;
    }
}

void endless(int rank, float scale, float sat, float speed)
{
    if(scale == 0)
        scale = (1 + sin(PI/rank)) / cos(PI/rank);
    int center_ring = int(floor( log(sqr(p.x)+sqr(p.y))/2/log(scale)) );
    float base_shift = time/speed;
    int alpha = int(floor((atan(p.y, p.x)/TAU - base_shift)*rank));
    if(alpha < 0) alpha += rank;
    debug_rings += center_ring;
    for(int ring = center_ring-1; ring <= center_ring+1; ring++) {
      float size = pow(scale, ring);
      float shift = (ring%2)/2.0/rank;
      float color_shift = (-3*ring/2)/float(rank);
      for(int i = alpha; i <= alpha+1; i++) {
          float d = i / float(rank);
          float t = (base_shift + shift + d)*TAU;
          vec2 pos = size * vec2(cos(t), sin(t));
          add(pos, hsv2rgb(d+color_shift,sat, 1));
      }
    }
}

void main()
{
    endless(6, 0, 1.0, 100000);
    endless(7, 0, 0.5,  10000);
    #ifdef DEBUG_RINGS
    debug_rings = mod(1000+debug_rings, DEBUG_RINGS)/2/DEBUG_RINGS + 0.5;
    #else
    debug_rings = 1;
    #endif
    gl_FragColor = vec4(res_color, 1.) * debug_rings;
}

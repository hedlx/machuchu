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
        res_d = 0;
        res_color = vec3(0,0,0);
    }
    #endif
    if(res_d > d) {
        res_d = d;
        res_color = color;
    }
}

void endless(int rank, float scale, float sat, float speed)
{
    int center_ring = int(floor( log(sqr(p.x)+sqr(p.y))/log(scale)) );
    debug_rings += center_ring;
    for(int ring = center_ring-1; ring <= center_ring+1; ring++) {
      float size = pow(scale, ring/2.);
      for(int i = 0; i < rank; i++) {
          float d = i / float(rank);
          float t = (time/speed + (ring*1.5)/rank+d)*TAU;
          vec2 pos = size * vec2(cos(t), sin(t));
          add(pos,  hsv2rgb(d,sat,1));
      }
    }
}

void main()
{
    endless(6, 3, 1,     100000);
    endless(7, 3.5, 0.5, 10000);
    #ifdef DEBUG_RINGS
    debug_rings = mod(1000+debug_rings, DEBUG_RINGS)/2/DEBUG_RINGS + 0.5;
    #else
    debug_rings = 1;
    #endif
    gl_FragColor = vec4(res_color, 1.) * debug_rings;
}

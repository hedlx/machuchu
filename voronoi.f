#version 130

varying vec4 p;

uniform float time;

#include "lib.h"

float res_d = 1/0.;
vec3 res_color = vec3(0,0,0);

vec2 lissajous(float x, float y, float t)
{
    t *= TAU;
    return vec2(sin(x*t), cos(y*t));
}

void add(vec2 pos, vec3 color)
{
    pos -= p.xy;
    pos *= pos;
    float d = pos.x+pos.y;
    if(res_d > d && d > 0.001) {
        res_d = d;
        res_color = color;
    }
}

#define ADD(X,Y,RGB) add(vec2(X,Y), COLOR(RGB))

#define ADD_LISSAJOUS(COUNT,SIZE,X,Y,PERIOD, SHIFT, COLOR) \
  for(int i = 0; i < COUNT; i++) { \
     float d = i / float(COUNT); \
     add(SIZE*lissajous(X,Y,time/PERIOD+SHIFT+d), COLOR); \
  }

void endless(int rank, float scale, float sat, float speed)
{
    float d = log(sqrt(sqr(p.x)+sqr(p.y)))/log(pow(scale,0.5));
    for(int q = int(d-1); q < int(d+2); q++) {
      float a = pow(scale, q/2.);
      ADD_LISSAJOUS(rank, a, 1, 1, speed, (q*1.5)/rank, hsv2rgb(d,sat,1))
    }
}

void main()
{
    ADD(0, 0, 000000);

    //ADD_LISSAJOUS( 7, 15, 1.0, 1.0, 10000, 0, hsv2rgb(d,1,1))
    //ADD_LISSAJOUS( 9,  4, 7.0, 5.0, 80000, 0, vec3(d,d,d))
    //ADD_LISSAJOUS( 9,  7,10.0, 7.0, 90000, 0, vec3(d,d,d))

    endless(6, 3, 1,     100000);
    endless(7, 3.5, 0.5, 10000);

    gl_FragColor = vec4(res_color, 1.);
}

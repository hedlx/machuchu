#version 130

varying vec4 p;

uniform int depth = 64;
#pragma machachu slider depth 2 512

uniform float time;

#include "lib.h"

#define COLOR(RGB) vec3(\
  (0x##RGB>>16&0xFF)/255., \
  (0x##RGB>> 8&0xFF)/255., \
  (0x##RGB>> 0&0xFF)/255.)

vec3 gradient4(float f, vec3 c[4])
{
    f = fract(f)*4;
    float a = fract(f);
    #define case(n) case n: return c[n]*(1-a) + c[(n+1)%4]*a
    switch(int(f)) {
        case(0);
        case(1);
        case(2);
        case(3);
    }
    #undef ret
}

#define color(rgb) 4
vec3 select_color(float f)
{
    return gradient4(f, vec3[4](COLOR(000000),
                                COLOR(9700c8),
                                COLOR(ffffff),
                                COLOR(92d800)));
}

float striped_mandel(vec2 c, float shift, int strips, float strip_size, int n)
{
    float res_r = 0.0;
    float res_i = 0.0;
    float res_r_tmp;
    int i = 0;
    while ((sqr(res_r) + sqr(res_i) < 64) && (i < n))
    {
        res_r_tmp = res_r;
        res_r = sqr(res_r) - sqr(res_i) + c.x;
        res_i = 2.0 * res_r_tmp * res_i + c.y;
        ++i;
    }
    if (i < n) {
        float res = i+1-log2(log2(sqrt(sqr(res_r)+sqr(res_i))));
        res = (res+shift)/strip_size;
        return int(res)/float(strips);
    } else
        return 0.;
}

float q()
{return 0.;}

void main()
{
    vec4 pp = p;
    pp.x = p.x * 1.5 - 0.5;
    pp.y *= 1.5;
    float f = striped_mandel(pp.xy, -time/1000, 4, 1, depth);
    gl_FragColor = vec4(select_color(f), 1);
}
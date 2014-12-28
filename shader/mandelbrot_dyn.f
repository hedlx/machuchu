#version 130

varying vec4 p;

uniform float param1 = 128.;
uniform float param2 = 16.;
uniform float time;

#include "lib.h"

float mandel(vec2 c, int n)
{
    float res_r = time / 100000;
    float res_i = 0; // sin(time / 5000);
    float res_r_tmp;
    int i = 0;
    while ((sqr(res_r) + sqr(res_i) < param2) && (i < n))
    {
        res_r_tmp = res_r;
        res_r = sqr(res_r) - sqr(res_i) * sqr(res_i) + c.x;
        res_i = 2.0 * res_r_tmp * res_i + c.y;
        ++i;
    }
    if (i < n)
        return i+1-log2(log2(sqrt(sqr(res_r)+sqr(res_i))));
    return float(i);
}

void main()
{
    vec4 pp = p;
    pp.x = p.x * 1.5 - 0.5;
    pp.y *= 1.5;
    vec3 c = labhsv(sin(time/10000)+mandel(pp.xy, int(param1)) / param1, 0.75, 0.75);
    gl_FragColor = vec4(c, 1);
}

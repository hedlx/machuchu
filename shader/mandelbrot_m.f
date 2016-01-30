#version 130

varying vec4 p;

uniform float param1 = 128.;
uniform float param2 = 16.;
uniform float time;

#include "lib.h"
#include "color.h"

float mandel(vec2 c, int n)
{
    float res_r = 0.0;
    float res_i = 0.0;
    float res_r_tmp;
    int i = 0;
    while ((sqr(res_r) + sqr(res_i) < param2) && (i < n))
    {
        res_r_tmp = res_r;
        res_r = sqr(res_r) - sqr(res_i) + c.x;
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
    pp.x = (p.x * 1.5 - 0.5);
    pp.y *= 1.5;
    float m = mandel(pp.xy, int(param1)) / param1;
    int th = 40;
    m *= th;
    int i = int(m);
    float f = m - i;
    float hue = sin(atan(sin(pp.x), sin(pp.y) / 3) * 2 + i + f / 100) * 30;
    hue -= int(hue);
    vec3 c = vec3(0.);
    if(i != th)
    {
        c = labhsv(hue, 0.8, f / 1.1);
        #define compress(x) pow(x,1.6) - 0.05
        c = map3(compress, c);
        #undef compress
    }
    gl_FragColor = vec4(c, 1);
}

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
    float d = 0.00001;
    float mx = mandel(pp.xy + vec2(d, 0), int(param1)) / param1;
    float my = mandel(pp.xy + vec2(0, d), int(param1)) / param1;
    float grad = atan((m - mx) / d, (m - my) / d);
    m *= param1;
    int i = int(m);
    float f = m - i;
    float hue = sin(3 * (grad + tan(i * 1.1))) + pow(sin(0.006 * f) * 90, 2);
    hue -= int(hue);
    vec3 c = labhsv(hue, 1.0 /*pow((sin(9*grad)+1.0)/2.0,0.3) / 2 + 0.3*/, pow(f, 0.8) / 1.3 + 0.1);
    gl_FragColor = vec4(c, 1);
}

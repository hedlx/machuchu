#version 120

varying vec4 p;

uniform float time;

const float PI = 3.1415926535897932384626433832795;

float line(vec2 a1, vec2 a2, vec2 x)
{
    vec2 m = (a1 + a2) / 2.;
    vec2 d = (m - x) * (m - x);
    float r = d.x + d.y - distance(a1, m);
    if(r < 0)
    {
        r = 1;
    }
    else
    {
        r = exp(-r);
    }
    vec2 t = (x - a1) / (a2 - a1);
    return exp(-abs(t.x - t.y)) * r;
}

void main()
{
    float t = (time / 10000.) - int(time / 10000.);
#if 0
    float p = line(vec2(-t, -t), vec2(t, t), p.xy);
#else
    vec2 xy = vec2(sin(t * PI),cos(t * PI));
    float k = 0.7;
    float p = line(-xy * k, xy * k, p.xy);
#endif
    gl_FragColor = vec4(p, p, p, 1.);
}

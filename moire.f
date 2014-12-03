#version 120

varying vec4 p;

uniform float time;
//uniform float s = 1.;
uniform float c = 1.;

#define mod(x, k) (1 - abs((x) - int((x) / (k)) * (k) - 1))
#define div(x, k) (int((x) / (k)))
#define sqr(x) ((x) * (x))

vec4 hsv2rgb(float h, float s, float v)
{
    h *= 6;
    float c = v * s;
    float x = c * mod(h, 2);
    switch(int(h))
    {
        case 0: return vec4(c, x, 0, 1);
        case 1: return vec4(x, c, 0, 1);
        case 2: return vec4(0, c, x, 1);
        case 3: return vec4(0, x, c, 1);
        case 4: return vec4(x, 0, c, 1);
        default: return vec4(c, 0, x, 1);
    }
}

void main()
{
    vec4 pp = p;
    pp.x = -(pp.x + 1.) / 2.;
    float t = (time / 10000.);
    pp.y = (pp.y - 1.) / 2;
    float f = /*pow(t, 2) * abs(pp.x) / abs(pp.y); */(pow(t, 2) * (pp.x * pp.x + pp.y * pp.y));
//    f = (s == 0.) ? f : sin(2 * 3.14159265358979323846 * f);
//    f -= int(f);
    gl_FragColor = hsv2rgb(mod(f / t, 1.), mod(f / (t * t), 1.), 1.);//mod(f, 1.), 1./*mod((f - mod(f, 1.)) / 256., 1.)*/, 1.);
}
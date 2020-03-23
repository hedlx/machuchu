// Created by yqy in 2017-10-13
// https://www.shadertoy.com/view/ltSyRm
#version 130
#include "preamble.h"

const float param2 = 1024.f;
const float d = 0.00003f;
const float PI = radians(180.f);
const float TAU = radians(360.f);

#define div(a, b) int((a) / (b))
#define sqr(a) ((a) * (a))
#define cub(a) (sqr(a) * (a))

#define map3(f, v) vec3(f((v).x), f((v).y), f((v).z))

int   idiv (int a, int b) { return a/b + (a%b>0?1:0); }
int   imod (int a, int b) { return a>=0 ? a%b : b-1+(a+1)%b; }
float add2 (vec2 a) { return a.x + a.y; }
float sub2 (vec2 a) { return a.x - a.y; }
bool  bxor2(bvec2 a) { return a.x ^^ a.y; }
vec2  flip2(vec2 a) { return vec2(a.y, a.x); }

vec2 cx_conj(vec2 a) { return vec2(a.x, -a.y); }
vec2 cx_inv (vec2 a) { return cx_conj(a) / add2(a*a); }
vec2 cx_mul (vec2 a, vec2 b) { return vec2(sub2(a*b), add2(a*flip2(b))); }
vec2 cx_div (vec2 a, vec2 b) { return cx_mul(a, cx_conj(b)); }

vec3 hsv2rgb(float h, float s, float v) {
    h = fract(h) * 6.f;
    float c = v * s;
    float x = c * (1.f - abs(mod(h, 2.f) - 1.f));
    float m = v - c;

    #define ret(a, b, c)\
        return vec3(a + m, b + m, c + m)

    switch (int(h)) {
        case 0: ret(c, x, 0.f);
        case 1: ret(x, c, 0.f);                                                                                                          
        case 2: ret(0.f, c, x);                                                                                                          
        case 3: ret(0.f, x, c);                                                                                                          
        case 4: ret(x, 0.f, c);                                                                                                          
        case 5: ret(c, 0.f, x);                                                                                                          
    }                                                                                                                                  
                                                                                                                                       
    #undef ret                                                                                                                         
}                                                                                                                                      
                                                                                                                                       
vec3 lab2xyz(float l, float a, float b) {                                                                                              
    const vec3 w = vec3(0.95047f, 1.f, 1.08883f);                                                                                          
    vec3 c = vec3((l + 16.f) / 116.f)                                                                                                      
           + vec3(a / 500.f, 0.f, -b / 200.f);                                                                                               
    #define f(t)\
        t > 6.f / 29.f\
            ? cub(t)\
            : (116.f * t - 16.f) * 27.f / 24389.f
    return w * map3(f, c);                                                                                                             
    #undef f                                                                                                                           
}                                                                                                                                      
                                                                                                                                       
vec3 lab2rgb(float l, float a, float b) {
    const mat3 m = mat3(
         3.2404542f, -1.5371385f, -0.4985314f,
        -0.9692660f,  1.8760108f,  0.0415560f,
         0.0556434f, -0.2040259f,  1.0572252f
    );
    #define f(t)\
        t > 0.00304f\
            ? 1.055f * pow(t, 1.f / 2.4f) - 0.055f\
            : 12.92f * t
    vec3 c = lab2xyz(l, a, b) * m;
    return map3(f, c);
    #undef f
}

vec3 labhsv(float h, float s, float v) {
    h *= TAU;
    s *= 100.f;
    v *= 100.f;
    return lab2rgb(v, s * sin(h), s * cos(h));
}

float foo(vec2 v)
{
    return log2(abs(log2(sqr(v.x) + sqr(v.y))));
}

float mandel(vec2 c, float n)
{
    vec2 z = vec2(0.f);
    vec2 z_tmp;
    int i = 0;
    while (length(z) < param2 && (i < int(n) - 1))
    {
        z = cx_mul(z, z) + c;
        ++i;
    }
    float a = n - float(int(n));
    z = z * (1. - a) + (cx_mul(z, z) + c) * a;
    return float(i + 1) - foo(z);
}

void mainImage( out vec4 fragColor, in vec2 fragCoord )
{
	vec2 pp = fragCoord.xy / iResolution.xy;
    pp.x = pp.x * 4.f - 8.f/3.f;
    pp.y = pp.y * 8.f/3.f - 4.f/3.f;

    float param1 = pow(abs(sin(iTime / 10.f)), 1.6) * 32.f + 1.f;
    float m = mandel(pp, param1) / param1;
    float mx = mandel(pp + vec2(d, 0.f), param1) / param1;
    float my = mandel(pp + vec2(0.f, d), param1) / param1;
    float grad = atan((m - mx) / d, -(m - my) / d);

    fragColor = vec4(labhsv(m / 12.f, (m + 0.6f) / 2.3f, abs(grad)/PI), 1.f);
}

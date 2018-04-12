#pragma once

const float PI = radians(180);
const float TAU = radians(360);

#define div(a, b) int((a) / (b))
#define sqr(a) ((a) * (a))
#define cub(a) (sqr(a) * (a))

#define map3(f, v) vec3(f((v).x), f((v).y), f((v).z))

int   idiv (int a, int b) { return (a + (a>0?b-1:0))/b; }
int   imod (int a, int b) { return a>=0 ? a%b : b-1+(a+1)%b; }
float add2 (vec2 a) { return a.x + a.y; }
float sub2 (vec2 a) { return a.x - a.y; }
bool  bxor2(bvec2 a) { return a.x ^^ a.y; }
vec2  flip2(vec2 a) { return vec2(a.y, a.x); }

vec2 cx_conj(vec2 a) { return vec2(a.x, -a.y); }
vec2 cx_inv (vec2 a) { return cx_conj(a) / add2(a*a); }
vec2 cx_mul (vec2 a, vec2 b) { return vec2(sub2(a*b), add2(a*flip2(b))); }
vec2 cx_div (vec2 a, vec2 b) { return cx_mul(a, cx_conj(b)); }

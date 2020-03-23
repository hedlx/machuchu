#version 130

#include "lib.h"

varying vec4 p;

// misc functions {{{
vec3 bool2col(bool b) {
    return b? vec3(0.5, 0.5, 1.0): vec3(1.);
}

bool eq(float x, float y, float t) {
    return (x+t > y) && (x-t < y);
}

ivec2 hexagon(vec2 p) {
    p.y -= 1/sqrt(3);
    vec2 c = vec2(1,1/sqrt(3));

    ivec2 q = ivec2(floor(p/c));
    vec2 d = p - q*c;

    bool q1 = d.x*c.y + d.y*c.x >= c.x*c.y;
    bool q2 = (c.x-d.x)*c.y + d.y * c.x >= c.x*c.y;
    ivec2 r = ivec2(floor(q.x/2.),floor(q.y/3.));
    switch(imod(q.y, 6)) {
    case 0:
        if(q.x%2 == 0) {
            if(!q1) {r.x--;r.y--;}
        } else {
            if(!q2) r.y--;
        }
        break;
    case 3:
        if(q.x%2 == 0) {
            if(q2) r.x--;
            else r.y--;
        } else {
            if(!q1) r.y--;
        }
        break;
    case 4:case 5:
        r.x = int(floor((q.x+1)/2.))-1;
        break;
    }
    return r;
}
// }}}

// patterns {{{
float grid_f(float x, float period) {
    const float TRESHOLD = 0.99;
    float val = abs(sin(TAU*(x+1.0)*0.5*period));
    return val >= TRESHOLD ? 1.0 : 0.0;
}
vec3 pattern_grid(vec2 p) {
    float val = (grid_f(p.x, 8) + grid_f(p.y, 8))/2;
    return vec3(1.0-val, 1.0-val, 1.0);
}

uniform int px = 0, py = 0;
#pragma machuchu slider px -100 100
#pragma machuchu slider py -100 100
vec3 pattern_sight(vec2 p) {
    vec2 c = vec2(px, py)/100.;
    return bool2col(eq(p.x,c.x, 0.01) || eq(p.y,c.y, 0.01));
}

uniform int scale = 10;
#pragma machuchu slider scale 1 30

vec3 pattern_checkboard(vec2 p) {
    return bool2col(bxor2(lessThan(fract(p*scale), vec2(0.5))));
}

vec3 pattern_gingham(vec2 p) {
    ivec2 q = ivec2(floor(p*scale*2));
    int i = imod(q.x,2)+imod(q.y,2);
    switch(i){
    case 0: return vec3(1,1,1);
    case 1: return vec3(0.75,0.75,1);
    case 2: return vec3(0.5,0.5,1);
    }
}

vec3 pattern_hexagonal(vec2 p) {
    ivec2 q = hexagon(p*scale*3);
    int i = q.x - (q.y&1) + 1;
    switch(imod(i,3)){
    case 0: return vec3(1,1,1);
    case 1: return vec3(0.75,0.75,1);
    case 2: return vec3(0.5,0.5,1);
    }
}

uniform int pattern = 0;
#pragma machuchu slider pattern 0 4
vec3 pattern_(vec2 p) {
    switch(pattern) {
    case 0: return pattern_grid(p);
    case 1: return pattern_sight(p);
    case 2: return pattern_checkboard(p);
    case 3: return pattern_gingham(p);
    case 4: return pattern_hexagonal(p);
    }
}
// }}}

// transofrmations {{{
vec2 transform1(vec2 i) {
    return vec2(atan(i.x,i.y)/PI, log(sqr(i.x)+sqr(i.y))/PI/2 );
}

uniform int transform = 0;
#pragma machuchu slider transform 0 2
vec2 transform_(vec2 i) {
    switch(transform) {
    case 0: return i;
    case 1: return transform1(i);
    case 2: return cx_inv(i);
    }
}
// }}}

void main() {
    gl_FragColor = vec4(pattern_(transform_(p.xy)), 1.0);
}

#version 130

in vec2 p;

uniform int val1 = 0;
uniform int val2 = 3;
#pragma machuchu slider val1 -10 10
#pragma machuchu slider val2 1 10

#include "lib.h"
#include "color.h"
#include "text.h"

void main() {
    float c =
        + text_int(p*5. + vec2(0, 0), val1)
        + text_int(p*5. + vec2(0, 1), val2)
        + text_int(p*5. + vec2(0, 2), imod(val1, val2))
    ;
    gl_FragColor = vec4(c);
}

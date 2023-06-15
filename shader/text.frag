#version 150

in vec2 p;
in vec2 machuchu_pos;
out vec4 fragColor;

uniform int val1 = 0;
uniform int val2 = 3;
#pragma machuchu slider val1 -10 10
#pragma machuchu slider val2 1 10

#include "lib.h"
#include "color.h"
#include "text.h"

uniform sampler2D machuchu_tex;

void main() {
    float c =
        + text_int(p*5. + vec2(0, 0), val1)
        + text_int(p*5. + vec2(0, 1), val2)
        + text_int(p*5. + vec2(0, 2), imod(val1, val2))
    ;
    fragColor = vec4(c) +
        texture(
            machuchu_tex,
            machuchu_pos * vec2(1.1) - vec2(0.05)
        ) * vec4(0.5, 0.1, 0.1, 0.0);
}

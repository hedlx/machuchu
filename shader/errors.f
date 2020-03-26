//#version 130
#version 300 es
precision mediump float;
out vec4 machuchu_FragColor;
void main() { machuchu_FragColor = vec4(0); }

// foo
float errors_f_1() { return; }
// bar
#include "errors.h"
// baz
float errors_f_2() { return; }
// qux

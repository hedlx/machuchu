#version 300 es

precision mediump float;

in vec4 p;
uniform float time;
out vec4 machuchu_FragColor;

/* Shaydertoy uniforms */
const vec2 iResolution = vec2(640, 360);
#define iTime (time/1000.)
#define iMouse (vec4(0, 0, 0, 0))
uniform sampler2D iChannel0;
uniform sampler2D iChannel1;
uniform sampler2D iChannel2;
uniform sampler2D iChannel3;

void mainImage(out vec4 c, vec2 u);
void main() { mainImage(machuchu_FragColor, p.xy*360./2. + iResolution/2.); }

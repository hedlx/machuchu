#version 300 es

precision mediump float;

in vec2 p;
uniform vec4 machuchu_mouse;
uniform bool machuchu_click;
uniform float time;
out vec4 machuchu_FragColor;

/* Shaydertoy uniforms */
const vec2 iResolution = vec2(640, 360);
float iTime;
vec4 iMouse;
uniform sampler2D iChannel0;
uniform sampler2D iChannel1;
uniform sampler2D iChannel2;
uniform sampler2D iChannel3;

void mainImage(out vec4 c, vec2 u);
void main() {
	iTime = time / 1000.;
	iMouse = machuchu_mouse*360. / 2. + iResolution.xyxy / 2.;
	if (isnan(iMouse.x))
		iMouse = vec4(0);
	if (!machuchu_click)
		iMouse.zw = -iMouse.zw;
	mainImage(machuchu_FragColor, p.xy * 360. / 2. + iResolution / 2.);
}

#define p machuchu_p
#define time machuchu_time

#version 120

varying vec4 p;

uniform float time;
uniform float slider_x_period = 8;
uniform float slider_y_period = 8;

const float TRESHOLD = 0.99;
const float PI = 3.1415926535897932384626433832795;
const float TAU = 6.283185307179586;

float f(float x, float period)
{
    float val = abs(sin(TAU*(x+1.0)*0.5*period));
    return val >= TRESHOLD ? 1.0 : 0.0;
}

void main()
{
    float val = f(p.x, slider_x_period)
              + f(p.y, slider_y_period);
    val *= 0.5;
    gl_FragColor = vec4(1.0-val, 1.0-val, 1.0, 1.0);
}

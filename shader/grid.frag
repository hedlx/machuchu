#version 150

in vec2 p;

uniform bool transparent;

uniform float time;
uniform int x_period = 8;
#pragma machuchu slider x_period 1 30
uniform int y_period = 8;
#pragma machuchu slider y_period 1 30

out vec4 fragColor;

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
    float val = f(p.x, float(x_period))
              + f(p.y, float(y_period));
    if (transparent)
        val *= 0.5;
    fragColor = vec4(1.0-val, 1.0-val, 1.0, 1.0);
}

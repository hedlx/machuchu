#version 330

in vec2 p;

void main()
{
    float f = (floatBitsToUint(p.x) + floatBitsToUint(p.y)) % 2U;
    gl_FragColor = vec4(f, f, f, 1.);
}

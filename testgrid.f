#version 330

varying vec4 p;

void main()
{
    float f = (floatBitsToUint(p.x) + floatBitsToUint(p.y)) % 2U;
    gl_FragColor = vec4(f, f, f, 1.);
}

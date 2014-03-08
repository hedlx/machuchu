varying vec4 p;

uniform float param = 128.;

int mandel(vec2 c, int n)
{
    float res_r = 0.0;
    float res_i = 0.0;
    float res_r_tmp;
    int i = 0;
    while ((res_r * res_r + res_i * res_i < 4) && (i < n))
    {
        res_r_tmp = res_r;
        res_r = res_r * res_r - res_i * res_i + c.x;
        res_i = 2.0 * res_r_tmp * res_i + c.y;
        ++i;
    }
    return i;
}

void main()
{
    p.x = p.x * 1.5 - 0.5;
    gl_FragColor = 1. - mandel(p.xy, int(param)) / param;
}
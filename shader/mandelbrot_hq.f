#version 120

varying vec2 p;

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

#define KAHAN_ITER(I) \
    { \
        float y = I - c_; \
        float t = sum_ + y; \
        c_ = (t - sum_) - y; \
        sum_ = t; \
    }

float kahan_sum6(float i0, float i1, float i2, float i3, float i4, float i5)
{
    float sum_ = 0.0;
    float c_ = 0.0;
    KAHAN_ITER(i0)
    KAHAN_ITER(i1)
    KAHAN_ITER(i2)
    KAHAN_ITER(i3)
    KAHAN_ITER(i4)
    KAHAN_ITER(i5)
    return sum_;
}

#define KAHAN_SUM7(O1, O2, I0, I1, I2, I3, I4, I5, I6)\
{\
    float sum_ = 0.0;\
    float c_ = 0.0;\
    KAHAN_ITER(I0)\
    KAHAN_ITER(I1)\
    KAHAN_ITER(I2)\
    KAHAN_ITER(I3)\
    KAHAN_ITER(I4)\
    KAHAN_ITER(I5)\
    KAHAN_ITER(I6)\
    O1 = sum_; O2 = c_;\
}

#define KAHAN_SUM5(O1, O2, I0, I1, I2, I3, I4)\
{\
    float sum_ = 0.0;\
    float c_ = 0.0;\
    KAHAN_ITER(I0)\
    KAHAN_ITER(I1)\
    KAHAN_ITER(I2)\
    KAHAN_ITER(I3)\
    KAHAN_ITER(I4)\
    O1 = sum_; O2 = c_;\
}

#define SUM_SQR(A,B) A*A, 2*A*B, B*B

int mandel2(vec2 c, int n)
{
    float res_r0 = 0.0, res_r1 = 0.0;
    float res_i0 = 0.0, res_i1 = 0.0;

    float res_r0_tmp, res_r1_tmp;
    int i = 0;
    while ((kahan_sum6(SUM_SQR(res_r0,res_r1), SUM_SQR(res_i0,res_i1)) < 4) && (i < n))
    {
        res_r0_tmp = res_r0;
        res_r1_tmp = res_r1;

        KAHAN_SUM7(res_r0, res_r1,
            res_r0*res_r0, 2*res_r0*res_r1, res_r1*res_r1,
            -res_i0*res_i0, -2*res_i0*res_i1, -res_i1*res_i1,
            c.x);

        KAHAN_SUM5(res_i0, res_i1,
            2.0*res_r0_tmp*res_i0, 2.0*res_r1_tmp*res_i0, 2.0*res_r0_tmp*res_i1, 2.0*res_r1_tmp*res_i1,
            c.y);

        ++i;
    }
    return i;
}

void main()
{
    vec2 pp = p;
    pp.x = p.x * 1.5 - 0.5;
    pp.y *= 1.5;
    float color1 = 1. - mandel(pp, int(param)) / param;
    float color2 = 1. - mandel2(pp, int(param)) / param;
    gl_FragColor = vec4(color1, color2, 0.0, 1.);
}

const float PI = 3.14159265;
const float TAU = 2 * PI;

#define div(a, b) int((a) / (b))
#define mod(a, b) ((a) - div(a, b) * (b))
#define sqr(a) ((a) * (a))
#define cub(a) (sqr(a) * (a))

#define map3(f, v) vec3(f((v).x), f((v).y), f((v).z))

vec3 hsv2rgb(float h, float s, float v) {
    h = fract(h) * 6;
    float c = v * s;
    float x = c * (1 - abs(mod(h, 2) - 1));
    float m = v - c;

    #define ret(a, b, c)\
        return vec3(a + m, b + m, c + m)

    switch (int(h)) {
        case 0: ret(c, x, 0);
        case 1: ret(x, c, 0);
        case 2: ret(0, c, x);
        case 3: ret(0, x, c);
        case 4: ret(x, 0, c);
        case 5: ret(c, 0, x);
    }

    #undef ret
}

vec3 lab2xyz(float l, float a, float b) {
    const vec3 w = vec3(0.95047, 1, 1.08883);
    vec3 c = vec3((l + 16) / 116)
           + vec3(a / 500, 0, -b / 200);
    #define f(t)\
        t > 6 / 29\
            ? cub(t)\
            : (116 * t - 16) * 27 / 24389
    return w * map3(f, c);
    #undef f
}

vec3 lab2rgb(float l, float a, float b) {
    const mat3 m = mat3(
         3.2404542, -1.5371385, -0.4985314,
        -0.9692660,  1.8760108,  0.0415560,
         0.0556434, -0.2040259,  1.0572252
    );
    #define f(t)\
        t > 0.00304\
            ? 1.055 * pow(t, 1 / 2.4) - 0.055\
            : 12.92 * t
    vec3 c = lab2xyz(l, a, b) * m;
    return map3(f, c);
    #undef f
}
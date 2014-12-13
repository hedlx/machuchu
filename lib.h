#define div(a, b) int((a) / (b))
#define mod(a, b) ((a) - div(a, b) * (b))
#define sqr(a) ((a) * (a))
#define cub(a) (sqr(a) * (a))
#define map3(f, v) vec3(f((v).x), f((v).y), f((v).z))

const float PI = 3.14159265;
const float TAU = 2 * PI;

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

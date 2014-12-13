#define div(a, b) int((a) / (b))
#define mod(a, b) ((a) - div(a, b) * (b))
#define sqr(a) ((a) * (a))

#define PI 3.14159265
#define TAU (2 * PI)

vec4 hsv2rgb(float h, float s, float v) {
    h *= 6;

    float c = v * s;
    float x = c * (1 - abs(mod(h, 2) - 1));
    float m = v - c;

    #define ret(a, b, c)\
        return vec4(a + m, b + m, c + m, 1)

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

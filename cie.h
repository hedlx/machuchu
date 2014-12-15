const vec3 E   = vec3(1, 1, 1);
const vec3 D50 = vec3(0.96422, 1, 0.82521);
const vec3 D65 = vec3(0.95047, 1, 1.08883);

const mat3 ADOBE_M = mat3(
     2.0413690, -0.5649464, -0.3446944,
    -0.9692660,  1.8760108,  0.0415560,
     0.0134474, -0.1183897,  1.0154096
);
const vec3 ADOBE_W = D65;

const mat3 APPLE_M = mat3(
     2.9515373, -1.2894116, -0.4738445,
    -1.0851093,  1.9908566,  0.0372026,
     0.0854934, -0.2694964,  1.0912975
);
const vec3 APPLE_W = D65;

const mat3 SRGB_M = mat3(
     3.2404542, -1.5371385, -0.4985314,
    -0.9692660,  1.8760108,  0.0415560,
     0.0556434, -0.2040259,  1.0572252
);
const vec3 SRGB_W = D65;

const mat3 CIE_M = mat3(
     2.3706743, -0.9000405, -0.4706338,
    -0.5138850,  1.4253036,  0.0885814,
     0.0052982, -0.0146949,  1.0093968
);
const vec3 CIE_W = E;

const mat3 ECI_M = mat3(
     1.7827618, -0.4969847, -0.2690101,
    -0.9593623,  1.9477962, -0.0275807,
     0.0859317, -0.1744674,  1.3228273
);
const vec3 ECI_W = D50;

const mat3 MATCH_M = mat3(
     2.6422874, -1.2234270, -0.3930143,
    -1.1119763,  2.0590183,  0.0159614,
     0.0821699, -0.2807254,  1.4559877
);
const vec3 MATCH_W = D50;

const mat3 BRUCE_M = mat3(
     2.7454669, -1.1358136, -0.4350269,
    -0.9692660,  1.8760108,  0.0415560,
     0.0112723, -0.1139754,  1.0132541
);
const vec3 BRUCE_W = D65;

vec3 gamma_correction(vec3 rgb, float gamma) {
   #define f(t)\
       t <= 0.00304\
         ? 12.92*t\
         : 1.055*pow(t, 1/gamma)-0.055
   return map3(f, rgb);
   #undef f
}

vec3 lab2xyz(float l, float a, float b) {
    vec3 _ = vec3((l + 16) / 116)
           + vec3(a / 500, 0, -b / 200);

    #define f(t)\
        t > 6 / 29\
            ? cub(t)\
            : (116 * t - 16) * 27 / 24389

    return map3(f, _);

    #undef f
}

#define lab2rgb(ws, l, a, b)\
   gamma_correction(ws ## _W * lab2xyz(l, a, b) * ws ## _M, 2.4)

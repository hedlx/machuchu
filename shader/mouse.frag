#version 300 es

precision mediump float;

in vec2 p;
uniform vec4 machuchu_mouse;
uniform bool machuchu_click;
out vec4 machuchu_FragColor;

float min2(vec2 v) { return min(v.x, v.y); }

bool in_rect(vec2 p, vec2 a, vec2 b) {
    return all(greaterThan(p, min(a, b))) && all(lessThan(p, max(a, b)));
}

void main() {
    if (isnan(machuchu_mouse.x) && length(p) < 0.1)
        machuchu_FragColor = vec4(1, 1, 0, 1);
    else if (min2(abs(p)) < 0.01)
        machuchu_FragColor = vec4(0.5);
    else
        machuchu_FragColor = vec4(0);

    if (in_rect(p, machuchu_mouse.xy, machuchu_mouse.zw))
        machuchu_FragColor = mix(machuchu_FragColor, vec4(1), machuchu_click ? 0.5 : 0.25);
}


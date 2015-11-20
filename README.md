☆ MACHUCHU ☆
============

Synopsis
--------
Machuchu — a GLSL (OpenGL Shading Language) viewer.

---

![animated screenshot](http://i.imgur.com/KfJQcR2.gif)

**Fig. 1.** Machuchu with `shader/voronoi_hsv.f` loaded.

---

Machuchu loads GLSL shader source code and renders it, producing animated live image. 
Depends on shader, resulting image may be very trippy (see fig. 1).

Shaders may be parametrized using so-called uniforms (uniform variables) inside GLSL code.
Machuchu let you edit value of uniforms using GUI controls.

We called it machuchu because we love Miyamoto-sensei. [\[1\]](http://z0r.de/2430)

Usage
----- 
* Run `./machuchu`.
* Click a "Load" button or press Ctrl+O and choose a shader file (.f).
  Example shaders can be found inside `shader/` directory.
* Controls:
    * `w`, `a`, `s`, `d`, Middle/Right mouse button — pan a view
    * `c` — position reset
    * `,` — zoom out
    * `.` — zoom in 
    * Mouse wheel — zoom in/out
    * `v` — zoom reset
    * `p` — pause
    * `f` — toggle a shader panel
    * `F10` — timer reset
    * `ESC` — quit
* Machuchu automatically reloads shader's code on file change.

Language extensions
-------------------

Machuchu extends Shading Language in following way:

* `#include "FILENAME"` and `#pragma once` — as in C language.
* `#pragma machuchu slider VAR FROM TO` — use slider with range `FROM ≤ value ≤ TO` to control variable named `VAR`. Otherwise it will be controlled by editable text field (non-bool uniforms) or checkbox (bool uniforms).
☆ MACHUCHU ☆
============

Synopsis
--------
Machuchu - a GLSL viewer.

Machuchu fetches uniforms in your a fragment shader code (.f files) and displays it as a text field on a panel.

We called it machuchu because we love Miyamoto-sensei.
http://z0r.de/2430

Usage
-----
1. Run ./machuchu.
2. Click a "Load" button or press Ctrl+O and choose a shader file (.f).
3. Controls
    Key binding                 | Action
    ----------------------------| ---------------------
    W,A,S,D                     | Pan a view
    Middle/Right mouse button   | Pan a view
    C                           | Position reset
    .                           | Zoom in
    ,                           | Zoom out
    Mouse wheel                 | Zoom in/out
    V                           | Zoom reset
    P                           | Pause
    F                           | Toggle a shader panel
    F10                         | Timer reset
    ESC                         | Quit
4. The shader's code will be reloaded automatically if it changed.

const uint text_font_data[] = uint[](0x10e100u,0x104100u,0x20000u,0x1e86185eu,0x83f880u,0x22969c62u,0x1a965852u,0x3f20820fu,0x19965957u,0x1896595eu,0x3149461u,0x1a96595au,0x1ea69a46u);

float text_int(vec2 c, int value) {
  const int LEN = 6;
  const int WIDTH = 5;
  const int HEIGHT = 6;

  c *= HEIGHT + 2.;

  if (c.x < 0 || c.y < 0 || c.x >= 1 + (WIDTH + 1) * LEN || c.y >= 2 + HEIGHT)
    return 0.;

  ivec2 ic = ivec2(c);

  int pos = ic.x / (WIDTH + 1);
  ic.x = (ic.x + WIDTH) % (WIDTH + 1);

  if (ic.x == WIDTH || ic.y == 0 || ic.y == HEIGHT + 1)
    return 1. / 8.;
  ic.y -= 1;

  int chr;
  switch (pos) {
  case 0:
    chr = value < 0 ? 1 : 0;
    break;
  case 1:
    chr = 3 + abs(value) / 10000 % 10;
    break;
  case 2:
    chr = 3 + abs(value) / 1000 % 10;
    break;
  case 3:
    chr = 3 + abs(value) / 100 % 10;
    break;
  case 4:
    chr = 3 + abs(value) / 10 % 10;
    break;
  case 5:
    chr = 3 + abs(value) / 1 % 10;
    break;
  }

  if (((text_font_data[chr] >> (ic.x * HEIGHT + HEIGHT - 1 - ic.y)) & 1u) == 1u)
    return 1.;

  return 1. / 8.;
}

#pragma once

#define MAX_RENDER_TEX_LEN  4096

int render_tex_to_html_file(const char*, const char*);
int render_steps_to_html_file(struct Step*, int, int);

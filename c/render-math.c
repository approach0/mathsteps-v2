#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <assert.h>

#include "optr.h"
#include "step.h"
#include "render-math.h"

int render_tex_to_html_file(const char *tex, const char *output)
{
	char* const argv[] = {
		"node",
		"../render-math.js",
		(char*)output,
		(char*)tex,
		NULL
	};

	return execvp(argv[0], argv);
}

#define STRING_APPEND(_p, _left, _fmt, ...) \
	({ \
		int tmp; \
		tmp = snprintf(_p, _left, _fmt, ## __VA_ARGS__); \
		assert(tmp >= 0); \
		_left -= tmp; \
		if (_left < 0) _left = 0; \
		p = p + tmp; \
	})

int render_steps_to_html_file(struct Step *steps, int n, int show_index)
{
	char display_str[MAX_RENDER_TEX_LEN];
	size_t left = MAX_RENDER_TEX_LEN;
	char *p = display_str;

	STRING_APPEND(p, left, "\\begin{align}");
	for (int i = 0; i < n; i++) {
		char tex[MAX_TEX_LEN];
		struct Step *step = steps + i;
		optr_write_tex(tex, step->tree);

		if (show_index) {
			if (i == 0)
				STRING_APPEND(p, left, " ");
			else
				STRING_APPEND(p, left, "\\text{step %d}", i);
		}

		if (i == 0)
			STRING_APPEND(p, left, "& %s", tex);
		else
			STRING_APPEND(p, left, "=& %s", tex);

		if (step->axiom) {
			STRING_APPEND(p, left, "& \\text{(axiom%d: %s)}", step->axiom_idx, step->axiom->name);
		} else {
			STRING_APPEND(p, left, "& \\text{(%s)}", "initial");
		}

		STRING_APPEND(p, left, "\\\\ ");
	}

	STRING_APPEND(p, left, "\\end{align}");
	render_tex_to_html_file(display_str, "./output.html");
}

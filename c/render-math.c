#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

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

#include "mhook.h"
#include "parser.h"

int main()
{
	void *scanner = parser_new_scanner();

	struct optr_node *root;
	root = parser_parse(scanner, "a + 1 + 0");

	if (root) {
		optr_print(root);
		optr_release(root);
	}

	parser_dele_scanner(scanner);

	mhook_print_unfree();
	return 0;
}

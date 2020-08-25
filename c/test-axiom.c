#include "mhook.h"
#include "parser.h"
#include "axiom.h"

int main()
{
	void *scanner = parser_new_scanner();

	struct optr_node *root1, *root2;
	root1 = parser_parse(scanner, "a + b + b + *{z}");
	root2 = parser_parse(scanner, "a + \\frac{1}{2} + \\frac{1}{2} + a + b + c");

	if (root1 && root2) {
		printf("tree1:\n");
		optr_print(root1);
		printf("tree2:\n");
		optr_print(root2);

		//int res = test_optr_identical(root1, root2);
		//printf("res=%d\n", res);

		struct optr_node **map = test_alpha_equiv(root1, root2);
		printf("alpha equiv = %d\n", (map != NULL));

		alpha_map_print(map);

		struct optr_node *root3 = rewrite_by_alpha(root1, map);
		printf("tree3:\n");
		optr_print(root3);

		alpha_map_free(map);

		optr_release(root1);
		optr_release(root2);
		optr_release(root3);
	}

	parser_dele_scanner(scanner);

	mhook_print_unfree();
	return 0;
}

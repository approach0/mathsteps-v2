#include <stdio.h>
#include <stdlib.h>

#include "mhook.h"
#include "parser.h"

int test_node_identical(struct optr_node *n1, struct optr_node *n2)
{
	if (n1->type != n2->type ||
	    n1->sign != n2->sign)
		return 0;

	switch (n1->type) {
	case OPTR_NODE_VAR:
		return n1->var == n2->var;
	case OPTR_NODE_NUM:
		return n1->num == n2->num;
	case OPTR_NODE_TOKEN:
		return n1->token == n2->token;
	default:
		fprintf(stderr, "invalid node type\n");
		abort();
	}
	return 0;
}

int test_optr_identical(struct optr_node *e1, struct optr_node *e2)
{
	if (!test_node_identical(e1, e2))
		return 0;
	else if (e1->n_children != e2->n_children)
		return 0;

	for (int i = 0; i < e1->n_children; i++) {
		struct optr_node *c1, *c2;
		c1 = e1->children[i];
		c2 = e2->children[i];
		if (!test_optr_identical(c1, c2))
			return 0;
	}

	return 1;
}

int alphabet_order(int var, int is_wildcards)
{
	int base = is_wildcards ? 26 * 2 : 0;
	if ('A' <= var && var <= 'Z') {
		return base + 26 + var - 'a';

	} else if ('a' <= var && var <= 'z') {
		return base + var - 'a';

	} else {
		fprintf(stderr, "invalid var value\n");
		abort();
		return 0;
	}
}

int __test_alpha_equiv(struct optr_node *e1, struct optr_node *e2, struct optr_node *map[])
{
	float type1 = e1->type, type2 = e2->type;
	float sign1 = e1->sign, sign2 = e2->sign;

	if (type1 == OPTR_NODE_NUM) {
		return test_node_identical(e1, e2);

	} else if (type1 == OPTR_NODE_VAR) {
		int key = alphabet_order(e1->var, e1->is_wildcards);
		struct optr_node *e_map;

		//e2->sign *= sign1;
		if ((e_map = map[key])) {
			return test_optr_identical(e_map, e2);

		} else {
			map[key] = e2;
			return 1;
		}
	}

	int length_unmatch = 0;
	for (int i = 0; i < e1->n_children; i++) {
		struct optr_node *c1, *c2;
		c1 = e1->children[i];

		if (i >= e2->n_children) {
			length_unmatch = 1;
			break;
		} else {
			c2 = e2->children[i];
		}

		if (c1->is_wildcards) {
			int key = alphabet_order(c1->var, 1);
			/* allocate placeholder operator */
			struct optr_node *placeholder = optr_alloc(OPTR_NODE_TOKEN);
			*placeholder = *e2;
			placeholder->n_children = 0;

			for (int j = i; j < e2->n_children; j++)
				optr_attach(placeholder, e2->children[j]);

			map[key] = placeholder;
			length_unmatch = 0;
			break;
		}

		if (!__test_alpha_equiv(c1, c2, map))
			return 0;
	}

	return !length_unmatch;
}

int test_alpha_equiv(struct optr_node *e1, struct optr_node *e2)
{
	struct optr_node *map[26 * 2 * 2] = {0};

	int is_equiv = __test_alpha_equiv(e1, e2, map);

#define DEBUG
	for (int i = 0; i < 26 * 2 * 2; i++) {
		struct optr_node *nd;
#ifdef DEBUG
		if ((nd = map[i])) {
			printf("[%d] => \n", i);
			optr_print(nd);
		}
#endif

		if (i >= 26 * 2)
			free(map[i]);
	}
	return is_equiv;
}

int main()
{
	void *scanner = parser_new_scanner();

	struct optr_node *root1, *root2;
	root1 = parser_parse(scanner, "a + b + b + *{z}");
	root2 = parser_parse(scanner, "a + \\frac{1}{2} + \\frac{1}{2} + a + b + c");

	if (root1 && root2) {
		optr_print(root1);
		optr_print(root2);

		//int res = test_optr_identical(root1, root2);
		//printf("res=%d\n", res);

		int alpha = test_alpha_equiv(root1, root2);
		printf("alpha = %d\n", alpha);

		optr_release(root1);
		optr_release(root2);
	}

	parser_dele_scanner(scanner);

	mhook_print_unfree();
	return 0;
}

#include <stdio.h>
#include <stdlib.h>

#include "parser.h"

int test_node_identical(struct optr_node *n1, struct optr_node *n2)
{
	if (n1->type != n2->type ||
	    (n1->sign != n2->sign && n1->pound_ID > 0 && n2->pound_ID > 0))
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

struct optr_node *shallow_copy(struct optr_node *src)
{
	struct optr_node *dest = optr_alloc(OPTR_NODE_TOKEN);
	*dest = *src;
	dest->n_children = 0;
	return dest;
}

struct optr_node *deep_copy(struct optr_node *src)
{
	if (src->type == OPTR_NODE_VAR || src->type == OPTR_NODE_NUM)
		return shallow_copy(src);

	struct optr_node *copy_root = shallow_copy(src);
	for (int i = 0; i < src->n_children; i++) {
		struct optr_node *child = src->children[i];
		struct optr_node *copy_child = deep_copy(child);

		optr_attach(copy_root, copy_child);
	}

	return copy_root;
}

int __test_alpha_equiv(struct optr_node *e1, struct optr_node *e2, struct optr_node *map[])
{
	int   type1 = e1->type, type2 = e2->type;
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

	} else if (!test_node_identical(e1, e2)) {
		return 0;
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
			struct optr_node *placeholder = shallow_copy(e2);

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

struct optr_node **test_alpha_equiv(struct optr_node *e1, struct optr_node *e2)
{
	struct optr_node **map = calloc(26 * 2 * 2, sizeof(struct optr_node*));

	int is_equiv = __test_alpha_equiv(e1, e2, map);
	if (is_equiv) {
		return map;
	} else {
		free(map);
		return NULL;
	}
}

void alpha_map_print(struct optr_node *map[])
{
	if (NULL == map)
		return;

	for (int i = 0; i < 26 * 2 * 2; i++) {
		struct optr_node *nd;
		if ((nd = map[i])) {
			printf("[%d] => \n", i);
			optr_print(nd);
		}
	}
}

void alpha_map_free(struct optr_node *map[])
{
	if (NULL == map)
		return;

	for (int i = 0; i < 26 * 2 * 2; i++) {
		struct optr_node *nd;
		if ((nd = map[i]) && i >= 26 * 2)
			free(map[i]);
	}

	free(map);
}

struct optr_node *rewrite_by_alpha(struct optr_node *root, struct optr_node *map[])
{
	if (NULL == map)
		return deep_copy(root);

	float sign = root->sign;
	if (root->type == OPTR_NODE_VAR) {
		int key = alphabet_order(root->var, root->is_wildcards);
		struct optr_node *subst = map[key] ? map[key] : root;
		subst = deep_copy(subst);

		subst->sign *= sign;
		return subst;

	} else if (root->type == OPTR_NODE_NUM) {
		return shallow_copy(root);
	}

	struct optr_node *new_tr = shallow_copy(root);
	for (int i = 0; i < root->n_children; i++) {
		struct optr_node *child = root->children[i];
		struct optr_node *subst = rewrite_by_alpha(child, map);

		optr_pass_children(new_tr, subst);
	}

	return new_tr;
}

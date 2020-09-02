#include <stdio.h>
#include <stdlib.h>

#include "parser.h"

int test_node_identical(struct optr_node *n1, struct optr_node *n2, float signs[])
{
	if (n1->type != n2->type ||
	    (n1->sign != n2->sign && n1->pound_ID == 0))
		return 0;

	int is_match = 0;
	switch (n1->type) {
	case OPTR_NODE_VAR:
		is_match = (n1->var == n2->var);
		break;
	case OPTR_NODE_NUM:
		is_match = (n1->num == n2->num);
		break;
	case OPTR_NODE_TOKEN:
		is_match = (n1->token == n2->token);
		break;
	default:
		fprintf(stderr, "invalid node type\n");
		abort();
	}

	if (is_match) {
		signs[n1->pound_ID] = n2->sign;
		return 1;
	} else {
		return 0;
	}
}

int test_optr_identical(struct optr_node *e1, struct optr_node *e2, float signs[])
{
	if (!test_node_identical(e1, e2, signs))
		return 0;
	else if (e1->n_children != e2->n_children)
		return 0;

	for (int i = 0; i < e1->n_children; i++) {
		struct optr_node *c1, *c2;
		c1 = e1->children[i];
		c2 = e2->children[i];
		if (!test_optr_identical(c1, c2, signs))
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

static int plug_sign_apply(struct optr_node *e, float sign)
{
	if (e->sign < 0) {
		e->sign *= sign;

	} else if (e->type == OPTR_NODE_TOKEN || e->token == TOK_HEX_ADD) {
		for (int i = 0; i < e->n_children; i++) {
			struct optr_node *child = e->children[i];
			child->sign *= sign;
		}

	} else {
		e->sign *= sign;
	}

	return 0;
}

static int __test_alpha_equiv(
	struct optr_node *e1, struct optr_node *e2,
	struct optr_node *map[], float signs[])
{
	int   type1 = e1->type, type2 = e2->type;
	float sign1 = e1->sign, sign2 = e2->sign;


	if (type1 == OPTR_NODE_NUM) {
		return test_node_identical(e1, e2, signs);

	} else if (type1 == OPTR_NODE_VAR) {
		int key = alphabet_order(e1->var, e1->is_wildcards);
		struct optr_node *e_map_old, *e_map_new = deep_copy(e2);

		/* if for example `-x' matches `a+b', then `x=-a-b' */
		plug_sign_apply(e_map_new, sign1);

		if ((e_map_old = map[key])) {
			int save = test_optr_identical(e_map_old, e_map_new, signs);
			optr_release(e_map_new);
			return save;

		} else {
			map[key] = e_map_new;
			return 1;
		}

	} else if (!test_node_identical(e1, e2, signs)) {
		return 0;
	}

	int length_unmatch = !(e1->n_children == e2->n_children);

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

			/*
			 * Wildcard matches should not include root sign,
			 * e.g., pattern `# 1 \cdot *{x}' and `- 1 \cdot 2 \cdot 3'
			 * will map `*{x} = 2 \cdot 3', not `*{x} = - 2 \cdot 3'.
			 */
			placeholder->sign = +1.f;

			for (int j = i; j < e2->n_children; j++) {
				struct optr_node *copy = deep_copy(e2->children[j]);
				optr_attach(placeholder, copy);
			}

			map[key] = placeholder;
			length_unmatch = 0;
			break;
		}

		if (!__test_alpha_equiv(c1, c2, map, signs))
			return 0;
	}

	return !length_unmatch;
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
		if ((nd = map[i])) {
			optr_release(map[i]);
		}
	}

	free(map);
}

struct optr_node
**test_alpha_equiv(struct optr_node *e1, struct optr_node *e2, float signs[])
{
	struct optr_node **map = calloc(26 * 2 * 2, sizeof(struct optr_node*));

	int is_equiv = __test_alpha_equiv(e1, e2, map, signs);
	if (is_equiv) {
		return map;
	} else {
		alpha_map_free(map);
		return NULL;
	}
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

		/* if for example `x=a+b' plugs into `-x` will become `-a-b' */
		plug_sign_apply(subst, sign);
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

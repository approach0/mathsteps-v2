#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "parser.h"
#include "alpha-equiv.h"

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
		return base + 26 + var - 'A';

	} else if ('a' <= var && var <= 'z') {
		return base + var - 'a';

	} else {
		fprintf(stderr, "invalid var value\n");
		abort();
		return 0;
	}
}

char order2alphabet(int order)
{
	int is_wildcards = 0;
	if (order >= 26 * 2) {
		is_wildcards = 1;
		order = order - 26;
	}

	if (order >= 26) {
		return 'A' + order - 26;
	} else {
		return 'a' + order;
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
		/* since this case outter sign is negative, just reverse it to positive */
		e->sign *= sign;

	} else if (e->type == OPTR_NODE_TOKEN && e->token == TOK_HEX_ADD) {
		/* this case we need to distribute signs */
		for (int i = 0; i < e->n_children; i++) {
			struct optr_node *child = e->children[i];
			child->sign *= sign;
		}

	} else {
		/* otherwise just apply the sign */
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

			if (e2->n_children - i == 1) {
				/* wildcards only wrap one operand, use it directly */
				map[key] = deep_copy(e2->children[i]);

			} else {
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
			}

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
			printf("[%c] => ", order2alphabet(i));
			optr_print_tex(nd);
			printf("\n");
		}
	}
}

static void alpha_map_free__items(struct optr_node *map[])
{
	for (int i = 0; i < 26 * 2 * 2; i++) {
		struct optr_node *nd;
		if ((nd = map[i])) {
			printf("free item @ %d\n", i);
			optr_release(nd);
		}
	}
}

static void alpha_map_refcnt(struct optr_node *map[], int cnt)
{
	for (int i = 0; i < 26 * 2 * 2; i++) {
		struct optr_node *nd;
		if ((nd = map[i])) {
			nd->refcnt += cnt;
			if (nd->refcnt <= 0) {
				printf("garbage free @ %d\n", i);
				optr_release(nd);
			}
		}
	}
}

void alpha_map_free(struct optr_node *map[])
{
	if (NULL == map)
		return;

	alpha_map_free__items(map);
	free(map);
}

#define MAX_UNIVERSE 10

typedef struct optr_node* (*map_universe_t)[26 * 2 * 2];
typedef float (*signs_universe_t)[MAX_NUM_POUNDS];

int test_node_identical__wildcards(
	struct optr_node *n1, struct optr_node *n2, signs_universe_t su, int nu)
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
		for (int i = 0; i < nu; i++)
			su[i][n1->pound_ID] = n2->sign;
		return 1;
	} else {
		return 0;
	}
}

int test_optr_identical__wildcards(
	struct optr_node *e1, struct optr_node *e2, signs_universe_t su, int nu)
{
	if (!test_node_identical__wildcards(e1, e2, su, nu))
		return 0;
	else if (e1->n_children != e2->n_children)
		return 0;

	for (int i = 0; i < e1->n_children; i++) {
		struct optr_node *c1, *c2;
		c1 = e1->children[i];
		c2 = e2->children[i];
		if (!test_optr_identical__wildcards(c1, c2, su, nu))
			return 0;
	}

	return 1;
}

void print_map_universe(map_universe_t mu, int nu)
{
	for (int i = 0; i < nu; i++) {
		struct optr_node** map = mu[i];
		printf("Universe #%d\n", i);
		alpha_map_print(map);
	}
}

int universe_add_constraint(int key, struct optr_node* map_new,
	map_universe_t mu, signs_universe_t su, int nu)
{
	for (int i = 0; i < nu; i++) {
		struct optr_node **map = mu[i];

		struct optr_node *map_old = map[key];
		if (map_old) {
			int identical = test_optr_identical__wildcards(map_old, map_new, su, nu);
			optr_release(map_new);

			if (!identical) {
				if (i + 1 < nu) {
					alpha_map_refcnt(map, -1);
					memcpy(mu[i], mu[i + 1], (nu - i - 1) * (26 * 2 * 2) * sizeof(struct optr_node*));
					memcpy(su[i], su[i + 1], (nu - i - 1) * MAX_NUM_POUNDS * sizeof(float));
				}
				nu = nu - 1;
			}

		} else {
			map[key] = map_new;
			map_new->refcnt += 1;
		}
	}

	return nu;
}

static int __test_alpha_equiv__wildcards(
	struct optr_node *e1, struct optr_node *e2,
	map_universe_t mu, signs_universe_t su, int nu)
{
	int   type1 = e1->type, type2 = e2->type;
	float sign1 = e1->sign, sign2 = e2->sign;

	//printf("LINE %d\n", __LINE__);
	printf("=========\n");
	optr_print(e1);
	printf("---------\n");
	optr_print(e2);
	print_map_universe(mu, nu);
	printf("\n");

	if (type1 == OPTR_NODE_NUM) {
		int identical = test_node_identical__wildcards(e1, e2, su, nu);

		return identical ? nu : 0;

	} else if (type1 == OPTR_NODE_VAR) {
		int key = alphabet_order(e1->var, e1->is_wildcards);
		struct optr_node *map_new = deep_copy(e2);

		/* if for example `-x' matches `a+b', then `x=-a-b' */
		plug_sign_apply(map_new, sign1);

		return universe_add_constraint(key, map_new, mu, su, nu);

	} else if (!test_node_identical__wildcards(e1, e2, su, nu)) {
		return 0;
	}

	struct optr_node *_1__[26 * 2 * 2 * MAX_UNIVERSE];
	float             _2__[MAX_NUM_POUNDS * MAX_UNIVERSE];
	int nu_new = 0;

	map_universe_t   mu_new = (map_universe_t)_1__;
	signs_universe_t su_new = (signs_universe_t)_2__;

	for (int t = 0; t < e2->n_children; t++) {
		/* make a copy */
		struct optr_node *_1[26 * 2 * 2 * MAX_UNIVERSE];
		float             _2[MAX_NUM_POUNDS * MAX_UNIVERSE];
		int nu_copy = nu;
		memcpy(_1, mu, 26 * 2 * 2 * sizeof(struct optr_node*) * nu);
		memcpy(_2, su, MAX_NUM_POUNDS * sizeof(float) * nu);
		map_universe_t  mu_copy = (map_universe_t)_1;
		signs_universe_t su_copy = (signs_universe_t)_2;

		/* switch a case */
		struct optr_node hanger, sub_hanger;
		hanger = *e2;
		hanger.n_children = 0;

		optr_attach(&hanger, e2->children[t]);
		for (int i = 0; i < e2->n_children; i++) {
			if (i != t)
				optr_attach(&hanger, e2->children[i]);
		}

		/* matching */
		int i;
		for (i = 0; i < e1->n_children; i++) {
			struct optr_node *c1, *c2;
			c1 = e1->children[i];

			if (i >= hanger.n_children) {
				break;

			} else if (c1->is_wildcards && hanger.n_children - i != 1) {
				/* allocate placeholder operator */
				sub_hanger = hanger;
				sub_hanger.n_children = 0;
				c2 = &sub_hanger;

				/*
				 * Wildcard matches should not include root sign,
				 * e.g., pattern `# 1 \cdot *{x}' and `- 1 \cdot 2 \cdot 3'
				 * will map `*{x} = 2 \cdot 3', not `*{x} = - 2 \cdot 3'.
				 */
				c2->sign = +1.f;

				for (int j = i; j < hanger.n_children; j++) {
					optr_attach(c2, hanger.children[j]);
				}

				i = e1->n_children;
				break;

			} else {
				c2 = hanger.children[i];
			}

			int nu_tmp = __test_alpha_equiv__wildcards(c1, c2, mu_copy, su_copy, nu_copy);
			if (!nu_tmp)
				break;
			else
				nu_copy = nu_tmp;
		}

		if (i == e1->n_children) {
			// append
			memcpy(mu_new[nu_new], mu_copy, 26 * 2 * 2 * sizeof(struct optr_node*) * nu_copy);
			memcpy(su_new[nu_new], su_copy, MAX_NUM_POUNDS * sizeof(float) * nu_copy);
			nu_new += nu_copy;
		}
	}

	memcpy(mu, mu_new, 26 * 2 * 2 * sizeof(struct optr_node*) * nu_new);
	memcpy(su, su_new, MAX_NUM_POUNDS * sizeof(float) * nu_new);
	return nu_new;
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

struct optr_node
**test_alpha_equiv__wildcards(struct optr_node *e1, struct optr_node *e2, float signs[])
{
	struct optr_node *_1[26 * 2 * 2 * MAX_UNIVERSE] = {0};
	float             _2[MAX_NUM_POUNDS * MAX_UNIVERSE];
	map_universe_t   mu = (map_universe_t)_1;
	signs_universe_t su = (signs_universe_t)_2;

	int is_equiv = __test_alpha_equiv__wildcards(e1, e2, mu, su, 1);
	print_map_universe(mu, is_equiv);
	abort();
	if (is_equiv) {
//		for (int i = 0; i < is_equiv; i++) {
//			alpha_map_free__items(mu[i]);
//		}
		struct optr_node **map = calloc(26 * 2 * 2, sizeof(struct optr_node*));
		memcpy(map, mu[0], 26 * 2 * 2 * sizeof(struct optr_node*));
		memcpy(signs, su[0], MAX_NUM_POUNDS * sizeof(float));
		return map;
	} else {
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

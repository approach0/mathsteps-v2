#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>

#include "parser.h"
#include "alpha-equiv.h"

typedef struct optr_node* (*map_universe_t)[26 * 2 * 2];
typedef float (*signs_universe_t)[MAX_NUM_POUNDS];

#define MAX_SIGNS_SPACE_SZ  (MAX_NUM_POUNDS * sizeof(float))
#define MAX_MAP_SPACE       (26 * 2 * 2)
#define MAX_MAP_SPACE_SZ    (MAX_MAP_SPACE * sizeof(struct optr_node*))

#define CAST(_to, _type, _from) \
	_type _to = (_type)(_from)

#define UNIVERSE_MAP_REFCNT(_mu, _start, _end, _cnt) \
	do { \
		for (int __k = _start; __k < _end; __k++) \
			alpha_map_refcnt(_mu[__k], _cnt); \
	} while (0)

#define UNIVERSE_ASSIGN_POUND_SIGNS(_su, _nu, _poundID, _sign) \
	do { \
		for (int __i = 0; __i < _nu; __i++) \
			_su[__i][_poundID] = _sign; \
	} while (0)

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

static struct optr_node *pre_plugin_sign_apply(struct optr_node *e, float sign)
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

	return e;
}

void alpha_map_print(struct optr_node *map[])
{
	if (NULL == map)
		return;

	for (int i = 0; i < MAX_MAP_SPACE; i++) {
		struct optr_node *nd;
		if ((nd = map[i])) {
			printf("[%c] => ", order2alphabet(i));
			optr_print_tex(nd);
			printf("\t(refcnt = %d)\n", nd->refcnt);
		}
	}
}

static void alpha_map_refcnt(struct optr_node *map[], int cnt)
{
	for (int i = 0; i < MAX_MAP_SPACE; i++) {
		struct optr_node *nd;
		if ((nd = map[i])) {
			nd->refcnt += cnt;
			if (nd->refcnt <= 0) {
				//printf("garbage collect @ %d\n", i);
				optr_release(nd);
				map[i] = NULL;
			}
		}
	}
}

void alpha_map_free(struct optr_node *map[])
{
	if (NULL == map)
		return;

	for (int i = 0; i < MAX_MAP_SPACE; i++) {
		struct optr_node *nd;
		if ((nd = map[i])) {
			optr_release(nd);
			map[i] = NULL;
		}
	}
	free(map);
}

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
		UNIVERSE_ASSIGN_POUND_SIGNS(su, nu, n1->pound_ID, n2->sign);
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

static void print_map_universe(map_universe_t mu, int nu)
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
			if (!test_optr_identical__wildcards(map_old, map_new, su, nu)) {
				/* now, unref and delete this possibility */
				alpha_map_refcnt(mu[i], -1);

				/* overwrite i by following items (if any) */
				if (i + 1 < nu) {
					memcpy(mu[i], mu[i + 1], (nu - i - 1) * MAX_MAP_SPACE_SZ);
					memcpy(su[i], su[i + 1], (nu - i - 1) * MAX_SIGNS_SPACE_SZ);
					/* redo this loop iteration */
					i = i - 1;
				}

				/* update universe number */
				nu = nu - 1;
			}

		} else {
			/* insert into this possibility */
			map[key] = map_new;
			map_new->refcnt += 1;
		}
	}

#if 0
	printf("\n");
	printf("insert [%c] ==> ", order2alphabet(key));
	optr_print_tex(map_new);
	printf("\n");
	printf("AFTER universe_add_constraint()\n");
	print_map_universe(mu, nu);
	printf("\n");
#endif

	/* release `map_new' if it has not ever been inserted */
	if (map_new->refcnt == 0)
		optr_release(map_new);

	return nu;
}

static struct optr_node
permute_children_by_one_leader(struct optr_node *T, int t)
{
	struct optr_node perm_T = *T;
	/* t == 0 indicates no permutation needed */
	if (t == 0)
		goto skip;
	/* construct a new tree with permuted children led by child at t */
	perm_T.n_children = 0;
	optr_attach(&perm_T, T->children[t]);
	for (int i = 0; i < T->n_children; i++) {
		if (i != t) optr_attach(&perm_T, T->children[i]);
	}
skip:
	return perm_T;
}

static struct optr_node
children_following(struct optr_node *T, int i)
{
	struct optr_node cf = *T;
	cf.n_children = 0;

	/*
	 * Wildcard matches should not include root sign,
	 * e.g., pattern `# 1 \cdot *{x}' and `- 1 \cdot 2 \cdot 3'
	 * will map `*{x} = 2 \cdot 3', not `*{x} = - 2 \cdot 3'.
	 */
	cf.sign = +1.f;

	for (int j = i; j < T->n_children; j++) {
		optr_attach(&cf, T->children[j]);
	}

	return cf;
}

static int
test_alpha_equiv__recur(struct optr_node *T1, struct optr_node *T2,
                        map_universe_t mu, signs_universe_t su, int nu)
{
	/* testing on this node ... */
	if (T1->type == OPTR_NODE_VAR) {
		int key = alphabet_order(T1->var, T1->is_wildcards);
		struct optr_node *map_new = deep_copy(T2);

		if (T1->pound_ID > 0) {
			/* the pound will absorb T2 sign */
			UNIVERSE_ASSIGN_POUND_SIGNS(su, nu, T1->pound_ID, T2->sign);
			if (T2->sign < 0)
				pre_plugin_sign_apply(map_new, -1);
		} else {
			/* if for example `-x' matches `a+b', then `x=-a-b' */
			pre_plugin_sign_apply(map_new, T1->sign);
		}
#if 0
		optr_print_node(T1);
		optr_print_node(T2);
		optr_print(map_new);
#endif
		return universe_add_constraint(key, map_new, mu, su, nu);

	} else {
		/* NUMBER or OPERATOR (TOKEN) */
		int identical = test_node_identical__wildcards(T1, T2, su, nu);

		if (!identical) {
			/* stop at umatched node */
			UNIVERSE_MAP_REFCNT(mu, 0, nu, -1);
			return 0;
		} else if (T1->type == OPTR_NODE_NUM) {
			/* stop at terminal */
			return nu;
		}
	}

	/* allocate possibilities space to be returned */
	struct optr_node *_mu[MAX_MAP_SPACE * MAX_UNIVERSE];
	float             _su[MAX_NUM_POUNDS * MAX_UNIVERSE];
	CAST(mu_new, map_universe_t, _mu);
	CAST(su_new, signs_universe_t, _su);
	int nu_new = 0;

	/* testing on permuted children ... */
	int child_perm_end = (T1->n_wildcards_children > 0) ? T2->n_children : 1;
	for (int t = 0; t < child_perm_end; t++) {

		/* allocate inherited (copied) sub-universe to be appended to `new' universe */
		struct optr_node *__mu[MAX_MAP_SPACE * MAX_UNIVERSE];
		float             __su[MAX_NUM_POUNDS * MAX_UNIVERSE];
		CAST(mu_copy, map_universe_t, __mu);
		CAST(su_copy, signs_universe_t, __su);
		int nu_copy = nu;
		/* make a copy */
		memcpy(__mu, mu, MAX_MAP_SPACE_SZ * nu);
		memcpy(__su, su, MAX_SIGNS_SPACE_SZ * nu);
		UNIVERSE_MAP_REFCNT(mu_copy, 0, nu_copy, +1);

		/* make a permuted T2 to be matched against */
		struct optr_node perm_T2 = permute_children_by_one_leader(T2, t);

		/* matching T1 against permuted T2 */
		int match_failed = 0;
		for (int i = 0; i < T1->n_children; i++) {
			/* test matching between each child pair from this T1-perm_T2 pair */
			struct optr_node *c1, *c2, cf;

			/* choose child from T1 */
			c1 = T1->children[i];

			/* choose child from permuted T2 */
			if (i >= perm_T2.n_children) {
				/* permuted T2 has not enough children to match T1 */
				match_failed = 1;
				break;

			} else if (c1->is_wildcards && perm_T2.n_children - i != 1) {
				/* followed here are multiple number of children (not single) */
				cf = children_following(&perm_T2, i);
				c2 = &cf;

				/* no need to go further */
				i = perm_T2.n_children;

			} else {
				c2 = perm_T2.children[i];
			}

			/* append new constraints to (copied) sub-universe */
			nu_copy = test_alpha_equiv__recur(c1, c2, mu_copy, su_copy, nu_copy);

			/* if this T1-perm_T2 pair does not match ... */
			if (nu_copy == 0) {
				match_failed = 1;
				break;
			}
		}

		/* this T1-perm_T2 pair can be matched? */
		if (match_failed) {
			UNIVERSE_MAP_REFCNT(mu_copy, 0, nu_copy, -1);
		} else {
			/* append (and spill possible overflow) */
			int nu_fill = (nu_new + nu_copy > MAX_UNIVERSE) ? MAX_UNIVERSE - nu_new: nu_copy;
			memcpy(mu_new[nu_new], mu_copy, MAX_MAP_SPACE_SZ * nu_fill);
			memcpy(su_new[nu_new], su_copy, MAX_SIGNS_SPACE_SZ * nu_fill);
			UNIVERSE_MAP_REFCNT(mu_copy, nu_fill, nu_copy, -1);
			nu_new += nu_fill;
		}
	}

	/* write back to original universe */ 
	UNIVERSE_MAP_REFCNT(mu, 0, nu, -1);
	memcpy(mu, mu_new, MAX_MAP_SPACE_SZ * nu_new);
	memcpy(su, su_new, MAX_SIGNS_SPACE_SZ * nu_new);
	nu = nu_new;

#if 0
	printf("=== test_alpha_equiv ===\n");
	optr_print(T1);
	printf("---\n");
	optr_print(T2);
	print_map_universe(mu, nu);
	printf("\n");
#endif
	return nu;
}

struct optr_node
**test_alpha_equiv(struct optr_node *T1, struct optr_node *T2, float signs[])
{
	/* allocate node-mapping and sign-mapping possibilities */
	struct optr_node *_mu[MAX_MAP_SPACE * MAX_UNIVERSE] = {0};
	float             _su[MAX_NUM_POUNDS * MAX_UNIVERSE];
	CAST(mu, map_universe_t, _mu);
	CAST(su, signs_universe_t, _su);

	/* invoke the recursive version */
	int nu = test_alpha_equiv__recur(T1, T2, mu, su, 1);
	if (nu > 0) {
		/* only return the first one */
		struct optr_node **map = calloc(MAX_MAP_SPACE, sizeof(struct optr_node*));
		memcpy(map, mu[0], MAX_MAP_SPACE_SZ);
		memcpy(signs, su[0], MAX_SIGNS_SPACE_SZ);

		/* free other possibilities */
		UNIVERSE_MAP_REFCNT(mu, 1, nu, -1);

		//printf("pound#1 = %f\n", signs[1]);
		//printf("pound#2 = %f\n", signs[2]);
		//printf("pound#3 = %f\n", signs[3]);
		return map;
	} else {
		return NULL;
	}
}

struct optr_node *rewrite_by_alpha(struct optr_node *root, struct optr_node *map[])
{
	if (NULL == map)
		return deep_copy(root);

	if (root->type == OPTR_NODE_VAR) {
		int key = alphabet_order(root->var, root->is_wildcards);
		struct optr_node *subst = map[key];
		assert(subst != NULL);
		subst = deep_copy(subst);

		/* if for example `x=a+b' plugs into `-x` will become `-a-b' */
		pre_plugin_sign_apply(subst, root->sign);
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

#include <stdlib.h>
#include <stdio.h>
#include <locale.h>

#include "optr.h"
#include "mhook.h"

struct optr_node *optr_alloc(int type)
{
	struct optr_node *nd = malloc(sizeof(struct optr_node));
	nd->type = type;
	nd->sign = +1.f;
	nd->is_wildcards = 0;
	nd->n_children = 0;
	return nd;
}

void optr_release(struct optr_node *root)
{
	for (int i = 0; i < root->n_children; i++) {
		struct optr_node *c = root->children[i];
		optr_release(c);
	}

	free(root);
}

struct optr_node *optr_attach(struct optr_node *f, struct optr_node *s)
{
	if (s == NULL)
		return f;

	if (f->n_children + 1 < MAX_OPTR_NUM_CHILDREN)
		f->children[f->n_children++] = s;
	else
		optr_release(s);

	return f;
}

void __print_node(struct optr_node *nd)
{
	if (nd->sign < 0)
		printf(" -");

	#define W 4
	char    dst[W + 1] = {0};
	wchar_t src[2] = {0};

	switch (nd->type) {
	case OPTR_NODE_VAR:
		printf("%c", nd->var);
		break;
	case OPTR_NODE_NUM:
		printf("%g", nd->num);
		break;
	case OPTR_NODE_TOKEN:
		src[0] = nd->token;
		setlocale(LC_ALL, "en_US.UTF-8");
		wcstombs(dst, src, W);
		printf("`%s'", dst);
		break;
	}

	if (nd->is_wildcards)
		printf(" (wildcards)");

	printf("\n");
}

void __optr_print(struct optr_node *nd, int level, int *depth_flags)
{
	enum {
		DEPTH_END,
		DEPTH_BEGIN,
		DEPTH_ALMOST_END
	};

	for (int i = 0; i < level; i++) {
		switch (depth_flags[i]) {
		case DEPTH_END:
			printf("    ");
			break;
		case DEPTH_BEGIN:
			if (i + 1 == level)
				printf(" ├──");
			else
				printf(" │  ");
			break;
		case DEPTH_ALMOST_END:
			printf(" └──");
			depth_flags[i] = DEPTH_END;
			break;
		default:
			fprintf(stderr, "invalid depth flag.\n");
			break;
		}
	}

	__print_node(nd);

	for (int i = 0; i < nd->n_children; i++) {
		struct optr_node *c = nd->children[i];

		if (i == nd->n_children - 1) {
			depth_flags[level] = DEPTH_ALMOST_END;
		} else if (i == 0) {
			depth_flags[level] = DEPTH_BEGIN;
		}

		__optr_print(c, level + 1, depth_flags);
	}
}

void optr_print(struct optr_node *root)
{
	int depth_flags[MAX_OPTR_PRINT_DEPTH] = {0};

	if (root == NULL) {
		printf("(empty optr)\n");
		return;
	}

	__optr_print(root, 0, depth_flags);
}

/*
 *  Pass grand-children to root if children and root have the same operator.
 *  Otherwise, attach children to root (only reduce signs).

 *      root (+)
 *    /   ^           <—— *
 *  ...  children (+)     |
 *        |               *
 *       grand-children _/
 */
struct optr_node *optr_pass_children(struct optr_node *rot, struct optr_node *sub)
{
	if (sub == NULL)
		return rot;

	if (rot->type == OPTR_NODE_TOKEN &&
		sub->type == OPTR_NODE_TOKEN &&
		rot->token == sub->token) {

		if (rot->token == TOK_TIMES_HEX)
			/* initialize by the sign of multiplication node bing destroyed */
			rot->sign *= sub->sign;

		for (int i = 0; i < sub->n_children; i++) {
			if (rot->n_children + 1 >= MAX_OPTR_NUM_CHILDREN)
				break;

			struct optr_node *grand = sub->children[i];
			switch (sub->token) {
			case TOK_ADD_HEX:
				/* distribute sign */
				grand->sign *= sub->sign;
				break;
			case TOK_TIMES_HEX:
				/* reduce sign */
				rot->sign *= grand->sign;
				grand->sign = 1.f;
				break;
			default:
				;
			}

			/* pass grand-child */
			optr_attach(rot, grand);
		}

		/* release single `sub' operator node */
		sub->n_children = 0;
		optr_release(sub);

	} else {
		/* pass child */
		if (rot->token == TOK_TIMES_HEX && sub->sign < 0) {
			rot->sign *= sub->sign;
			sub->sign = 1.f;
		}

		optr_attach(rot, sub);
	}

	return rot;
}

int optr_test()
{
	struct optr_node *root = optr_alloc(OPTR_NODE_VAR);
	struct optr_node *root2 = optr_alloc(OPTR_NODE_TOKEN);

	struct optr_node *nodes[] = {
		optr_alloc(OPTR_NODE_VAR),   // 0
		optr_alloc(OPTR_NODE_TOKEN), // 1
		optr_alloc(OPTR_NODE_NUM),   // 2
		optr_alloc(OPTR_NODE_TOKEN), // 3
		optr_alloc(OPTR_NODE_NUM),   // 4
		optr_alloc(OPTR_NODE_TOKEN), // 5
		optr_alloc(OPTR_NODE_NUM),   // 6
		optr_alloc(OPTR_NODE_TOKEN)    // 7
	};

	optr_attach(root, nodes[1]);
	optr_attach(root, nodes[2]);
	optr_attach(nodes[1], nodes[0]);
	optr_attach(nodes[1], nodes[3]);
	optr_attach(nodes[2], nodes[4]);

	optr_attach(root2, nodes[5]);
	optr_attach(root2, nodes[6]);
	optr_attach(nodes[5], nodes[7]);

	optr_print(root);
	optr_print(root2);

	root = optr_pass_children(root, root2);
	optr_print(root);

	optr_release(root);
	//optr_release(root2);

	mhook_print_unfree();
	return 0;
}

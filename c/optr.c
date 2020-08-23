#include <stdlib.h>
#include <stdio.h>

#include "optr.h"
#include "mhook.h"

struct optr_node *optr_alloc(int type)
{
	struct optr_node *nd = malloc(sizeof(struct optr_node));
	nd->type = type;
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
	if (f->n_children + 1 < MAX_OPTR_NUM_CHILDREN)
		f->children[f->n_children ++] = s;
	else
		optr_release(s);

	return f;
}

void __print_node(struct optr_node *nd)
{
	switch (nd->type) {
	case OPTR_NODE_VAR:
		printf(" %c", nd->var);
		break;
	case OPTR_NODE_NUM:
		printf(" %g", nd->num);
		break;
	case OPTR_NODE_TOKEN:
		printf("`%c`", nd->token);
		break;
	}
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
	__optr_print(root, 0, depth_flags);
}

struct optr_node *optr_pass_children(struct optr_node *rot, struct optr_node *sub)
{
	if (rot == NULL || sub == NULL)
		return NULL;

	for (int i = 0; i < sub->n_children; i++) {
		if (rot->n_children + 1 < MAX_OPTR_NUM_CHILDREN)
			rot->children[rot->n_children ++] = sub->children[i];
	}

	sub->n_children = 0;
	optr_release(sub);
	return rot;
}

int _main()
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

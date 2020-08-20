#include <stdlib.h>
#include <stdio.h>

#include "optr.h"

struct optr_node *optr_alloc(int type)
{
	struct optr_node *nd = malloc(sizeof(struct optr_node));
	nd->type = type;
	nd->n_children = 0;
	return nd;
}

struct optr_node *optr_attach(struct optr_node *f, struct optr_node *s)
{
	f->children[f->n_children ++] = s;
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
			break;
		default:
			fprintf(stderr, "invalid depth flag.\n");
			break;
		}
	}

	printf("[%d]\n", nd->type);

	for (int i = 0; i < nd->n_children; i++) {
		struct optr_node *c = nd->children[i];

		if (i == nd->n_children - 1) {
			depth_flags[level] = DEPTH_ALMOST_END;
		} else if (i == 0) {
			depth_flags[level] = DEPTH_BEGIN;
		}

		__optr_print(c, level + 1, depth_flags);

		if (depth_flags[level] == DEPTH_ALMOST_END)
			depth_flags[level] = DEPTH_END;
	}
}

void optr_print(struct optr_node *root)
{
	int depth_flags[MAX_OPTR_PRINT_DEPTH] = {0};
	__optr_print(root, 0, depth_flags);
}


//struct optr_node *optr_pass_children(struct optr_node *, struct optr_node *);

int main()
{
	struct optr_node *root = optr_alloc(OPTR_NODE_VAR);
	struct optr_node *nodes[] = {
		optr_alloc(OPTR_NODE_VAR),
		optr_alloc(OPTR_NODE_NUM),
		optr_alloc(OPTR_NODE_TOKEN)
	};

	optr_attach(root, nodes[1]);
	optr_attach(root, nodes[2]);
	optr_attach(nodes[1], nodes[0]);

	optr_print(root);

	return 0;
}

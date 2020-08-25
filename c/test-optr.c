#include "mhook.h"
#include "optr.h"

int main()
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

	mhook_print_unfree();
	return 0;
}

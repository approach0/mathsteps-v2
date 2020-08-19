#define MAX_OPTR_NUM_CHILDREN 128

struct optr_node {
	union {
		char  var;
		float num;
		int token;
	};

	int n_children;
	struct optr_node *children[MAX_OPTR_NUM_CHILDREN];
};

struct optr_node *optr_alloc(void);
struct optr_node *optr_pass_children(struct optr_node *, struct optr_node *);
struct optr_node *optr_attach(struct optr_node *, struct optr_node *);

void optr_print(struct optr_node *);
void optr_release(struct optr_node *);

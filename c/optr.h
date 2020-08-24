#define MAX_OPTR_NUM_CHILDREN 128
#define MAX_OPTR_PRINT_DEPTH  128

#define TOK_ADD_HEX   0x2b
#define TOK_TIMES_HEX 0xd7

enum optr_node_type {
	OPTR_NODE_VAR,
	OPTR_NODE_NUM,
	OPTR_NODE_TOKEN
};

struct optr_node {
	int type;
	union {
		int      var;
		float    num;
		wchar_t  token;
	};
	float sign;
	int is_wildcards;

	int n_children;
	struct optr_node *children[MAX_OPTR_NUM_CHILDREN];
};

struct optr_node *optr_alloc(int);
struct optr_node *optr_pass_children(struct optr_node *, struct optr_node *);
struct optr_node *optr_attach(struct optr_node *, struct optr_node *);

void optr_print(struct optr_node*);
void optr_release(struct optr_node *);

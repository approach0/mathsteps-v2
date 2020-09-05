#pragma once

#define MAX_OPTR_NUM_CHILDREN 128
#define MAX_OPTR_PRINT_DEPTH  128
#define MAX_TEX_LEN           2048

#define TOK_HEX_EQ    0x3d
#define TOK_HEX_ADD   0x2b /* commutative */
#define TOK_HEX_DIV   0xf7
#define TOK_HEX_TIMES 0xd7 /* commutative */
#define TOK_HEX_SUP   0x5e
#define TOK_HEX_FRAC  0x2f
#define TOK_HEX_SQRT  0x221a
#define TOK_HEX_ABS   0x1c1

#define IS_OF_OPERATOR(_nd, _code) \
	(_nd->type == OPTR_NODE_TOKEN && _nd->token == _code)

enum optr_node_type {
	OPTR_NODE_VAR,
	OPTR_NODE_NUM,
	OPTR_NODE_TOKEN
};

#include <wchar.h>

struct optr_node {
	int type;
	union {
		int      var;
		float    num;
		wchar_t  token;
	};
	float sign;

	int is_wildcards;
	int pound_ID;

	int n_children;
	struct optr_node *children[MAX_OPTR_NUM_CHILDREN];
	int n_wildcards_children;

	int refcnt;
};

struct optr_node *optr_alloc(int);
struct optr_node *optr_pass_children(struct optr_node *, struct optr_node *);
struct optr_node *optr_attach(struct optr_node *, struct optr_node *);

void optr_print_node(struct optr_node*);
void optr_print(struct optr_node*);
void optr_release(struct optr_node *);

float            optr_get_node_val(struct optr_node*);
struct optr_node optr_gen_val_node(float);

int  optr_write_tex(char*, struct optr_node*);
void optr_print_tex(struct optr_node*);

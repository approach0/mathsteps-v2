#pragma once
#include <stdlib.h>
#include <stdatomic.h>

struct state;

struct attach {
	int             n_children;
	struct state   *children;
};

struct state {
	_Atomic float   q;
	_Atomic float   n;

	struct expr_tr *expr_tr;
	struct state   *father;

	_Atomic struct attach attach;
};

struct sample_args {
	struct state *root;
	int n_samples;
	int n_threads;
	int worker_ID;
	int debug;
	int max_depth;
};

void state_init(struct state*, struct expr_tr*);
void mcts(struct state*, int, int, int, int);
void state_free(struct state*);

/* test */
struct expr_tr {
	float val;
};

static inline struct expr_tr **__possible_steps__(struct expr_tr *expr_tr, int *n_children)
{
	int c = (float)(expr_tr->val);
	*n_children = (c % 5) + 1;

	struct expr_tr **ret = malloc(*n_children * sizeof(uintptr_t));
	for (int i = 0; i < *n_children; i++) {
		ret[i] = malloc(sizeof(struct expr_tr));
		ret[i]->val = (float)((c + i) % 4 + 1.f) + rand() / (float)RAND_MAX;
	}

	return ret;
}

static inline void __print_expr__(struct expr_tr *expr_tr)
{
	printf("%.2f\n", expr_tr->val);
}

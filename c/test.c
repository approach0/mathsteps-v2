#include <pthread.h>
#include <stdint.h>
#include <stdatomic.h>
#include <unistd.h>
#include <stdlib.h>
#include <stdio.h>

#include "mhook.h"

#define PTR_CAST(_to, _type, _from) \
	_type* _to = (_type*)(_from)

struct expr_tr {
	int val;
};

struct expr_tr **__possible_steps__(struct expr_tr *expr_tr, int *n_children)
{
	int c = expr_tr->val;
	*n_children = (c % 5) + 1;

	struct expr_tr **ret = malloc(*n_children * sizeof(uintptr_t));
	for (int i = 0; i < *n_children; i++) {
		ret[i] = malloc(sizeof(struct expr_tr));
		ret[i]->val = c + 1 + i;
	}

	return ret;
}

void __print_expr__(struct expr_tr *expr_tr)
{
	printf("%d\n", expr_tr->val);
}

struct state {
	_Atomic float   q;
	_Atomic int     n;

	struct expr_tr *expr_tr;
	struct state   *father;

	_Atomic int     n_children;
	struct state   *children;
};

void state_init(struct state *state, struct expr_tr *expr_tr)
{
	state->q = 0.f;
	state->n = 0;
	state->expr_tr = expr_tr;
	state->father = NULL;
	state->n_children = 0;
	state->children = NULL;
}

void state_print(struct state *state, int level)
{
	for (int i = 0; i < level; i++)
		printf("  ");

	__print_expr__(state->expr_tr);

	for (int i = 0; i < state->n_children; i++)
		state_print(&state->children[i], level + 1);
}

void state_free(struct state *state)
{
	for (int i = 0; i < state->n_children; i++)
		state_free(&state->children[i]);

	if (state->children) {
		printf("free children\n");
		free(state->children);
	}

	printf("free tree\n");
	free(state->expr_tr);
}

void state_fully_expand(struct state *state)
{
	if (state->n_children != 0)
		return;

	int n_children;
	struct expr_tr **steps = __possible_steps__(state->expr_tr, &n_children);

	state->n_children = n_children;
	state->children = malloc(n_children * sizeof(struct state));
	for (int i = 0; i < n_children; i++)
		state_init(&state->children[i], steps[i]);
	printf("free steps\n");
	free(steps);

	state_print(state, 0);
}

void *worker(void *arg)
{
	PTR_CAST(root, struct state, arg);

	state_fully_expand(root);
}

int main()
{
    const int n_processors = sysconf(_SC_NPROCESSORS_ONLN);
	//const int n_threads = n_processors - 1;
	const int n_threads = 1;

	printf("Number of threads: %u\n", n_threads);
	pthread_t threads[n_threads];

	struct expr_tr *root_tr = malloc(sizeof(struct expr_tr));
	struct state root;
	root_tr->val = 123;
	state_init(&root, root_tr);

	for (int i = 0; i < n_threads; i++)
		pthread_create(threads + i, NULL, worker, &root);

	for (int i = 0; i < n_threads; i++)
		pthread_join(threads[i], NULL);

	state_free(&root);
	mhook_print_unfree();
}

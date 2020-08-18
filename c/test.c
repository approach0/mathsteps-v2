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

struct expr_tr *__possible_steps__(struct expr_tr *expr_tr, int *n_children)
{
	int c = expr_tr->val;
	*n_children = (c % 5) + 1;

	struct expr_tr *ret = malloc(*n_children * sizeof expr_tr);
	for (int i = 0; i < *n_children; i++)
		ret[i].val = c + 1 + i;

	return ret;
}

struct state {
	_Atomic float    q;
	_Atomic uint32_t n;

	struct expr_tr *expr_tr;
	struct state   *father;

	_Atomic uint32_t        n_children;
	struct state   *children;
};

struct state *state_new(struct expr_tr *expr_tr)
{
	struct state *state = malloc(sizeof(struct state));
	state->q = 0.f;
	state->n = 0;
	state->expr_tr = expr_tr;
	state->father = NULL;
	state->n_children = 0;
	state->children = NULL;
	return state;
}

void state_fully_expand(struct state *state)
{
	if (state->n_children != 0)
		return;

	int n_children;
	struct expr_tr *steps = __possible_steps__(state->expr_tr, &n_children);

	printf("%d\n", n_children);
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

	struct expr_tr root_tr = {123};
	struct state *root = state_new(&root_tr);

	for (int i = 0; i < n_threads; i++)
		pthread_create(threads + i, NULL, worker, root);

	for (int i = 0; i < n_threads; i++)
		pthread_join(threads[i], NULL);

	free(root);
	mhook_print_unfree();
}

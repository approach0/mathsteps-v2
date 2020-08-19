#include <pthread.h>
#include <stdint.h>
#include <stdatomic.h>
#include <unistd.h>
#include <stdlib.h>
#include <stdio.h>
#include <float.h>
#include <math.h>
#include <time.h>

#include "mhook.h"

#define PTR_CAST(_to, _type, _from) \
	_type* _to = (_type*)(_from)

struct expr_tr {
	float val;
};

struct expr_tr **__possible_steps__(struct expr_tr *expr_tr, int *n_children)
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

void __print_expr__(struct expr_tr *expr_tr)
{
	printf("%.2f\n", expr_tr->val);
}

struct state {
	_Atomic float   q;
	_Atomic float   n;

	struct expr_tr *expr_tr;
	struct state   *father;

	_Atomic int     n_children;
	struct state   *children;
};

void state_init(struct state *state, struct expr_tr *expr_tr)
{
	state->q = 0.f;
	state->n = 0.f;
	state->expr_tr = expr_tr;
	state->father = NULL;
	state->n_children = 0;
	state->children = NULL;
}

void state_print(struct state *state, int level, int print_all)
{
	for (int i = 0; i < level; i++)
		printf("  ");

	printf("q=%.2f, n=%.0f, ", state->q, state->n);
	__print_expr__(state->expr_tr);

	if (!print_all)
		return;

	for (int i = 0; i < state->n_children; i++)
		state_print(&state->children[i], level + 1, print_all);
}

void state_free(struct state *state)
{
	for (int i = 0; i < state->n_children; i++)
		state_free(&state->children[i]);

	if (state->n_children > 0) {
		free(state->children);
	}

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
	for (int i = 0; i < n_children; i++) {
		state_init(&state->children[i], steps[i]);
		state->children[i].father = state;
	}
	free(steps);
}

int state_best_child(struct state *state, float c_param)
{
	int n_children = state->n_children;
	int best_idx = -1;
	float N = state->n;
	float best = -FLT_MAX;

	for (int i = 0; i < n_children; i++) {
		float q = state->children[i].q;
		float n = state->children[i].n;
		float uct = q + c_param * sqrtf(logf(N + 1.f) / (n + 1.f));

		printf("uct[%d] = %.3f: ", i, uct);
		state_print(&state->children[i], 0, 0);

		if (uct > best) {
			best_idx = i;
			best = uct;
		}
	}

	return best_idx;
}

struct state *state_reward_backprop(struct state *state, float reward)
{
	while (state->father) {
		state->n += 1.f;
		if (state->q < reward) {
			state->q = reward;
		}
		state = state->father;
	}

	return state;
}

void state_rollout(struct state *state, int maxdepth)
{
	int cnt = 0;
	while (cnt < maxdepth) {
		printf("step#%d rollout: ", cnt);
		state_print(state, 0, 0);

		state_fully_expand(state);

		int n_children = state->n_children;
		if (n_children == 0)
			break;

		int child_idx = rand() % n_children;

		state = &state->children[child_idx];
		cnt++;
	}

	float reward = state->expr_tr->val;
	printf("reward: %.2f\n", reward);

	struct state *root = state_reward_backprop(state, reward);
	//printf("after backprop:\n");
	//state_print(root, 0, 1);
}

struct sample_args {
	struct state *root;
	int n_samples;
	int n_threads;
	int worker_ID;
};

void *sample_worker(void *_args)
{
	PTR_CAST(args, struct sample_args, _args);
	struct state *root = args->root;
	int n_samples = args->n_samples;
	int worker_ID = args->worker_ID;

	state_fully_expand(root);

	printf("fully expand: \n");
	state_print(root, 0, 1);

	for (int i = 0; i < n_samples; i++) {
		printf("\n");
		printf("Woker#%d sample#%d rollout root: ", worker_ID, i);
		state_print(root, 0, 0);

		int best_idx = state_best_child(root, 2.f);
		if (best_idx < 0)
			break;

		struct state *best_child = &root->children[best_idx];
		state_rollout(best_child, 4);
	}
}

void sample(struct sample_args args)
{
	const int n_threads = args.n_threads;

	printf("Number of threads: %u\n", n_threads);
	pthread_t threads[n_threads];

	for (int i = 0; i < n_threads; i++) {
		args.worker_ID = i;
		pthread_create(threads + i, NULL, sample_worker, &args);
	}

	for (int i = 0; i < n_threads; i++)
		pthread_join(threads[i], NULL);
}

int main()
{
	const int n_processors = sysconf(_SC_NPROCESSORS_ONLN);
	//const int n_threads = n_processors - 1;

	srand(time(NULL));

	struct expr_tr *root_tr = malloc(sizeof(struct expr_tr));
	struct state root;
	root_tr->val = 123.f;
	state_init(&root, root_tr);

	struct sample_args args = {&root, 3, 1};
	sample(args);

	printf("after sampling:\n");
	state_print(&root, 0, 1);

	state_free(&root);
	mhook_print_unfree();
}

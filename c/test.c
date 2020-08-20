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

/*
 * MCTS parallel sampling
 */
struct state {
	_Atomic float   q;
	_Atomic float   n;

	struct expr_tr *expr_tr;
	struct state   *father;

	int             n_children;
	struct state   *children;
	pthread_mutex_t lock;
};

struct sample_args {
	struct state *root;
	int n_samples;
	int n_threads;
	int worker_ID;
	int debug;
	int max_depth;
};

void state_init(struct state *state, struct expr_tr *expr_tr)
{
	state->q = ATOMIC_VAR_INIT(0.f);
	state->n = ATOMIC_VAR_INIT(0.f);
	state->expr_tr = expr_tr;
	state->father = NULL;
	state->n_children = 0;
	state->children = NULL;
	pthread_mutex_init(&state->lock, NULL);
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
	pthread_mutex_destroy(&state->lock);
}

void state_fully_expand(struct state *state)
{
	pthread_mutex_lock(&state->lock);
	if (state->n_children != 0) {
		pthread_mutex_unlock(&state->lock);
		return;
	}

	int n_children;
	struct expr_tr **steps = __possible_steps__(state->expr_tr, &n_children);

	state->n_children = n_children;
	state->children = malloc(n_children * sizeof(struct state));
	for (int i = 0; i < n_children; i++) {
		state_init(&state->children[i], steps[i]);
		state->children[i].father = state;
	}

	pthread_mutex_unlock(&state->lock);
	free(steps);
}

int state_best_child(struct state *state, float c_param, int debug)
{
	int n_children = state->n_children;
	int best_idx = -1;
	float N = state->n;
	float best = -FLT_MAX;

	for (int i = 0; i < n_children; i++) {
		float q = state->children[i].q;
		float n = state->children[i].n;
		float uct = q + c_param * sqrtf(logf(N + 1.f) / (n + 1.f));

		if (debug) {
			printf("uct[%d] = %.3f: ", i, uct);
			state_print(&state->children[i], 0, 0);
		}

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
		/* atomic increment */
		float _n = atomic_load(&state->n);
		while(!atomic_compare_exchange_weak(&state->n, &_n, _n + 1.f));

		/* atomic max-update */
		float update, _q = atomic_load(&state->q);
		do {
			update = (_q < reward) ? reward : _q;
		} while (!atomic_compare_exchange_weak(&state->q, &_q, update));

		/* backtrace until root */
		state = state->father;
	}

	return state;
}

void state_rollout(struct state *state, int maxdepth, int debug)
{
	int cnt = 0;
	while (cnt < maxdepth) {
		if (debug) {
			printf("step#%d rollout: ", cnt);
			state_print(state, 0, 0);
		}

		state_fully_expand(state);

		int n_children = state->n_children;
		if (n_children == 0)
			break;

		int child_idx = rand() % n_children;

		state = &state->children[child_idx];
		cnt++;
	}

	float reward = state->expr_tr->val;
	if (debug)
		printf("reward: %.2f\n", reward);

	struct state *root = state_reward_backprop(state, reward);
	(void)root;

	//printf("after backprop:\n");
	//state_print(root, 0, 1);
}

void *sample_worker(void *_args)
{
	PTR_CAST(args, struct sample_args, _args);
	struct state *root = args->root;
	int n_samples = args->n_samples;
	int worker_ID = args->worker_ID;
	int debug = args->debug;
	int max_depth = args->max_depth;

	state_fully_expand(root);

	for (int i = 0; i < n_samples; i++) {
		if (debug) {
			printf("\n");
			printf("Woker#%d sample#%d rollout root: ", worker_ID, i);
			state_print(root, 0, 0);
		}

		int best_idx = state_best_child(root, 2.f, debug);
		if (best_idx < 0)
			break; /* leaf */

		struct state *best_child = &root->children[best_idx];
		state_rollout(best_child, max_depth, debug);
	}
}

void sample(struct sample_args args)
{
	const int n_threads = args.n_threads;

	printf("Sampling (number of threads: %u)\n", n_threads);
	pthread_t threads[n_threads];

	for (int i = 0; i < n_threads; i++) {
		args.worker_ID = i;
		pthread_create(threads + i, NULL, sample_worker, &args);
	}

	for (int i = 0; i < n_threads; i++)
		pthread_join(threads[i], NULL);
}

void mcts(struct state *root, int n_threads, int sample_times, int maxsteps, int max_depth)
{
	struct state *cur = root;
	int cnt = 0;

	while ((cnt++) < maxsteps) {
		printf("\n[current cnt=%d/%d] ", cnt, maxsteps);
		state_print(cur, 0, 0);

		struct sample_args args = {
			cur,
			sample_times,
			n_threads,
			0,
			n_threads == 1,
			max_depth
		};
		sample(args);

		printf("\n[after sampling]\n");
		state_print(cur, 0, 1);

		printf("\n[moving to best child]\n");
		int best_idx = state_best_child(cur, 0, 0);
		if (best_idx < 0)
			break; /* leaf */

		cur = &cur->children[best_idx];
	}
}

int main()
{
	srand(time(NULL));

	struct expr_tr *root_tr = malloc(sizeof(struct expr_tr));
	struct state root;
	root_tr->val = 123.f;
	state_init(&root, root_tr);

	const int n_processors = sysconf(_SC_NPROCESSORS_ONLN);
	const int n_threads = n_processors - 1;
	mcts(&root, n_threads, 440, 10, 4);

	state_free(&root);
	mhook_print_unfree();
}

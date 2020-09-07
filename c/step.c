#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <math.h>

#include "parser.h"
#include "step.h"

#define ABS(x)  ( (x < 0) ? -(x) : (x) )

enum value_factors {
	RIGHT_SIDE_OF_EQ,
	NEGATIVE_SIGNS,
	NUMBER_LEVEL_CNT,
	NUMBER_SUM,
	NUMBER_IN_SQRT,
	NUMBER_ONE_ZERO,
	NUMBER_OTHER_INTS,
	NUMBER_PAD_ZEROS,
	NUMBER_DECIMALS,
	VAR_LEVEL_CNT,
	VAR_MAX_LEVEL,

	N_VALUE_FACTORS
};

struct collect_args {
	int level;
	int right_side_of_eq;
	int num_under_sqrt;
};

static int right_padding_zeros(int Int)
{
	int digit, cnt = 0;
	if (Int == 0)
		return 1;

	while (Int > 0) {
		digit = Int % 10;
		if (digit != 0)
			break;
		else
			cnt += 1;

		Int /= 10;
	}
	return cnt;
}

static void collect_stats(struct optr_node *tree, int *stats, struct collect_args args)
{
	if (tree->sign < 0)
		stats[NEGATIVE_SIGNS] += 1;

	if (tree->type != OPTR_NODE_TOKEN) {
		if (args.right_side_of_eq)
			stats[RIGHT_SIDE_OF_EQ] += 1;

		if (tree->type == OPTR_NODE_NUM) {
			float num = tree->num;

			stats[NUMBER_LEVEL_CNT] += args.level + 1;
			stats[NUMBER_SUM] += ABS(num);

			if (args.num_under_sqrt) {
				stats[NUMBER_IN_SQRT] += ABS(num);
				args.num_under_sqrt = 0;
			}

			if (num == (int)num) {
				int abs_num = ABS(num);
				if (abs_num == 0) {
					if (stats[RIGHT_SIDE_OF_EQ] > 0)
						stats[RIGHT_SIDE_OF_EQ] -= 1;

					stats[NUMBER_ONE_ZERO] += 1;
				} else if (abs_num == 1) {
					stats[NUMBER_ONE_ZERO] += 1;
				} else {
					stats[NUMBER_OTHER_INTS] += 1;
				}

                int n_pad_zeros = right_padding_zeros(abs_num);
                stats[NUMBER_PAD_ZEROS] += n_pad_zeros;

			} else {
				stats[NUMBER_DECIMALS] += 1;
			}
		} else {
			if (args.level > stats[VAR_MAX_LEVEL])
				stats[VAR_MAX_LEVEL] = args.level;

			stats[VAR_LEVEL_CNT] += args.level + 1;
		}

	} else {
		/* dive deeper */
		if (tree->token == TOK_HEX_FRAC)
			args.level += 4;
		else
			args.level += 1;

		for (int i = 0; i < tree->n_children; i++) {
			struct optr_node *child = tree->children[i];

			if (tree->token == TOK_HEX_EQ && i > 0)
				args.right_side_of_eq = 1;
			else if (tree->token == TOK_HEX_SQRT)
				args.num_under_sqrt = 1;

			collect_stats(child, stats, args);
		}
	}
}

float state_value__neg_complexity(struct optr_node *tree)
{
	int stats[N_VALUE_FACTORS] = {0};
	struct collect_args args = {0};

	collect_stats(tree, stats, args);

#if 0
	#define PRINT(_field) \
		printf("%s = %d\n", # _field, stats[_field]);

	PRINT(RIGHT_SIDE_OF_EQ);
	PRINT(NEGATIVE_SIGNS);
	PRINT(NUMBER_LEVEL_CNT);
	PRINT(NUMBER_SUM);
	PRINT(NUMBER_IN_SQRT);
	PRINT(NUMBER_ONE_ZERO);
	PRINT(NUMBER_OTHER_INTS);
	PRINT(NUMBER_PAD_ZEROS);
	PRINT(NUMBER_DECIMALS);
	PRINT(VAR_LEVEL_CNT);
	PRINT(VAR_MAX_LEVEL);
#endif

	float complexity =
		powf(2.f * stats[RIGHT_SIDE_OF_EQ], 3.f) +
		1.f * logf(1.f + logf(1.f + stats[RIGHT_SIDE_OF_EQ])) +
		5.f * logf(1.f + stats[NUMBER_IN_SQRT]) +
		1.f * (
			 0.9f * stats[NUMBER_ONE_ZERO] +
			 1.0f * stats[NUMBER_OTHER_INTS] +
			 0.1f * stats[NEGATIVE_SIGNS] +
			 3.0f * stats[NUMBER_DECIMALS] +
			-0.2f * stats[NUMBER_PAD_ZEROS] +
			 3.0f * stats[VAR_LEVEL_CNT] +
			 1.0f * stats[NUMBER_LEVEL_CNT]
		) +
		powf(2.f * stats[VAR_MAX_LEVEL], 2.f)
	;

	return -complexity;
}

static int _prior_than(struct Step *s1, struct Step *s2)
{
	if (s1->axiom_idx != s2->axiom_idx) {
		return s1->axiom_idx < s2->axiom_idx;
	} else {
		return s1->value > s2->value;
	}
}

static int quicksort_parition(struct Step *steps, int lo, int hi)
{
	struct Step tmp, *pivot = steps + hi;
	int i = lo; /* separator of smaller elements */
	for (int j = lo; j < hi; j++) {
		if (_prior_than(steps + j, pivot)) {
			tmp = steps[i];
			steps[i] = steps[j];
			steps[j] = tmp;
			i += 1;
		}
	}

	tmp = steps[i];
	steps[i] = steps[hi];
	steps[hi] = tmp;
	return i;
}

/* sort steps by (axiom_idx, value) tuple */
static void sort_steps(struct Step *steps, int lo, int hi)
{
	if (lo < hi) {
		int pivot =  quicksort_parition(steps, lo, hi);
		sort_steps(steps, lo, pivot - 1);
		sort_steps(steps, pivot + 1, hi);
	}
}

int possible_next_steps(
	struct optr_node *tree, struct Axiom *axioms[], int m,
	struct Step *steps, int max_steps)
{
	int n_steps = 0;
	float v0 = state_value__neg_complexity(tree);

	if (max_steps <= 0)
		goto skip;

	for (int i = 0; i < m; i++) {
		struct Axiom *a = axioms[i];

		struct optr_node *output[MAX_AXIOM_OUTPUTS];
		int n = axiom_apply(a, tree, output);

		for (int j = 0; j < n; j++) {
			struct optr_node *out = output[j];

			if (n_steps + 1 <= max_steps) {
				float value = state_value__neg_complexity(out);

				if (!a->is_allow_complication) {
					if ((a->is_strict_simplify && value <= v0) ||
					    value < v0)
						continue;
				}

				steps[n_steps].axiom     = a;
				steps[n_steps].axiom_idx = i;
				steps[n_steps].tree      = out;
				steps[n_steps].value     = value;
				n_steps += 1;
			} else {
				optr_release(out);
			}
		}
	}

	sort_steps(steps, 0, n_steps - 1);
skip:
	return n_steps;
}

int mathsteps_baseline(
	struct optr_node *tree, struct Axiom *axioms[], int m,
	struct Step *steps, int max_steps)
{
	int n, n_steps = 1;
	steps[0].axiom     = NULL;
	steps[0].axiom_idx = -1;
	steps[0].tree      = deep_copy(tree);
	steps[0].value     = state_value__neg_complexity(tree);

	if (max_steps <= 0)
		goto skip;

	do {
		struct Step cur = steps[n_steps - 1];
		n = possible_next_steps(cur.tree, axioms, m, steps + n_steps, max_steps - n_steps);
		for (int j = n_steps + 1; j < n_steps + n; j++) {
			optr_release(steps[j].tree);
		}
		n_steps += (n > 0) ? 1 : 0;
	} while (n > 0);

skip:
	return n_steps;
}

void print_step(struct Step *step, int print_tree)
{
	if (NULL == step || NULL == step->tree)
		printf("(empty step)\n");

	char tex[MAX_TEX_LEN];
	optr_write_tex(tex, step->tree);
	printf("%s", tex);
	if (step->axiom) {
		printf("\t (by axiom#%d `%s')", step->axiom_idx, step->axiom->name);
	} else {
		printf("\t (initial)");
	}
	printf("\n");

	if (print_tree)
		optr_print(step->tree);
}

struct Step tex2step(const char *tex)
{
	struct Step step = {0};

	void *scanner = parser_new_scanner();
	if (NULL == scanner)
		return step;

	struct optr_node *root = parser_parse(scanner, tex);
	step.tree = root;

	parser_dele_scanner(scanner);
	return step;
}

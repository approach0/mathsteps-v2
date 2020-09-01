#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <math.h>

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

int possible_next_steps(
	struct optr_node *tree, struct Axiom *axioms[], int m,
	struct Step **results)
{
	int n_results = 0;
	for (int i = 0; i < m; i++) {
		struct Axiom *a = axioms[i];

		struct optr_node *output[MAX_AXIOM_OUTPUTS];
		int n = axiom_apply(a, tree, output);
	}
	return 0;
}

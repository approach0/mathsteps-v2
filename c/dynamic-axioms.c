#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <math.h>

#include "mhook.h"
#include "parser.h"
#include "axiom.h"
#include "dynamic-axioms.h"

#define MAP_NODE(_map, _var) \
	_map[alphabet_order(_var, 0)]

#define CALLBK_ARGS \
	struct Rule *rule, struct optr_node *subject, \
	struct optr_node **map, float *signs, int signbits

#define ABS(x)  ( (x < 0) ? -(x) : (x) )

static inline int is_integer(float num)
{
	return (ABS(num) == (int)ABS(num));
}

/*
 * axiom_add
 */
static struct optr_node *_calc_add(CALLBK_ARGS)
{
//	/* print everything */
//	printf("Rule: \n");
//	rule_print(rule);
//	printf("\n");
//
//	printf("subject:\n");
//	optr_print(subject);
//	printf("\n");
//
//	printf("alpha map: \n");
//	alpha_map_print(map);
//	printf("\n");
//
//	printf("sign[1] = %g\n", signs[1]);
//	printf("sign bits: 0x%x\n", signbits);
//	printf("\n");

	struct optr_node *a = MAP_NODE(map, 'a');
	struct optr_node *b = MAP_NODE(map, 'b');

	if (a->type == OPTR_NODE_NUM &&
	    b->type == OPTR_NODE_NUM) {
		struct optr_node c, *rewritten;
		c = optr_gen_val_node(optr_get_node_val(a) + optr_get_node_val(b));
		MAP_NODE(map, 'c') = &c;
		rewritten = rewrite_by_alpha(rule->output_cache[signbits][0], map);
		MAP_NODE(map, 'c') = NULL;
		return rewritten;
	}
	return NULL;
}

struct Axiom *axiom_add()
{
	struct Axiom *a = axiom_new("Addition");

	axiom_add_rule(a, "# (a + b)", "c", &_calc_add);
	a->is_symmetric_reduce = 1;
	//axiom_print(a);

	axiom_add_test(a, "-(1 + 3 - 2)");
	axiom_add_test(a, "-(1 - 2)");
	axiom_add_test(a, "\\sqrt{3(1 - 2 + 3)x}");

	return a;
}

/*
 * axiom_mul
 */
static struct optr_node *_calc_mul(CALLBK_ARGS)
{
	struct optr_node *a = MAP_NODE(map, 'a');
	struct optr_node *b = MAP_NODE(map, 'b');

	if (a->type == OPTR_NODE_NUM &&
	    b->type == OPTR_NODE_NUM) {
		struct optr_node c, *rewritten;
		c = optr_gen_val_node(optr_get_node_val(a) * optr_get_node_val(b));
		MAP_NODE(map, 'c') = &c;
		rewritten = rewrite_by_alpha(rule->output_cache[signbits][0], map);
		MAP_NODE(map, 'c') = NULL;
		return rewritten;
	}
	return NULL;
}

struct Axiom *axiom_mul()
{
	struct Axiom *a = axiom_new("Multiplication");

	axiom_add_rule(a, "# ab", "#1 c", &_calc_mul);
	a->is_root_sign_reduce = 1;
	a->is_symmetric_reduce = 1;

	axiom_add_test(a, "3(-2)");
	axiom_add_test(a, "-(3 \\cdot 4)");
	axiom_add_test(a, "-(3 \\cdot (-2))");
	axiom_add_test(a, "-(-3)(-2)4");

	return a;
}

/*
 * axiom_pow
 */
static struct optr_node *_calc_pow(CALLBK_ARGS)
{
	struct optr_node *a = MAP_NODE(map, 'a');
	struct optr_node *b = MAP_NODE(map, 'b');

	if (a->type == OPTR_NODE_NUM &&
	    b->type == OPTR_NODE_NUM) {
		struct optr_node c, *rewritten;

		float a_val = optr_get_node_val(a);
		float b_val = optr_get_node_val(b);
		float c_val = powf(a_val, b_val);
		if (c_val > 2000)
			return NULL;

		c = optr_gen_val_node(c_val);

		MAP_NODE(map, 'c') = &c;
		rewritten = rewrite_by_alpha(rule->output_cache[signbits][0], map);
		MAP_NODE(map, 'c') = NULL;
		return rewritten;
	}
	return NULL;
}

struct Axiom *axiom_pow()
{
	struct Axiom *a = axiom_new("Calculate Power");

	axiom_add_rule(a, "# a^{b}", "#1 c", &_calc_pow);
	a->is_root_sign_reduce = 1;

	axiom_add_test(a, "2^{3}");
	axiom_add_test(a, "-2^{3}");
	axiom_add_test(a, "-2^{-2}");
	axiom_add_test(a, "-(-2)^{2}");
	axiom_add_test(a, "(-2)^{2}");

	return a;
}

/*
 * axiom_sqrt
 */
#define MAX_FACTORS 16

int factorizations(int num, int *factors)
{
	int p = 2, cnt = 0;
	num = ABS(num);
	while (num >= p) {
		if (num % p == 0) {
			num = num / p;
			factors[cnt++] = p;
		} else {
			p += 1;
		}
	}

	return cnt;
}

int sqrt_draw(int num, int *_n, int *_m)
{
    int m = 1, n = 1;
	int factors[MAX_FACTORS];
    int n_factors = factorizations(num, factors);

    while (n_factors > 0) {
		int a = factors[--n_factors];
		int b = (n_factors > 0) ? factors[n_factors - 1] : -1;
		if (a == b) {
			--n_factors;
			m = m * a;
		} else {
			n = n  * a;
		}
	}

	*_m = m;
	*_n = n;
	return n_factors;
}

static struct optr_node *_calc_sqrt(CALLBK_ARGS)
{
	struct optr_node *x = MAP_NODE(map, 'x');
	struct optr_node *rewritten;

	if (x->type == OPTR_NODE_NUM) {
		float x_val = optr_get_node_val(x);

		if (x_val >= 0 && is_integer(x_val)) {
			int n_val, m_val;

			if (x_val == 0) {
				struct optr_node c = optr_gen_val_node(0);
				MAP_NODE(map, 'c') = &c;
				rewritten = rewrite_by_alpha(rule->output_cache[signbits][0], map);
				MAP_NODE(map, 'c') = NULL;
				return rewritten;
			}

			sqrt_draw(x_val, &n_val, &m_val);

			if (n_val == 1) {
				struct optr_node c = optr_gen_val_node(m_val);
				MAP_NODE(map, 'c') = &c;
				rewritten = rewrite_by_alpha(rule->output_cache[signbits][0], map);
				MAP_NODE(map, 'c') = NULL;
				return rewritten;

			} else if (m_val > 1) {
				struct optr_node m = optr_gen_val_node(m_val);
				struct optr_node n = optr_gen_val_node(n_val);
				MAP_NODE(map, 'm') = &m;
				MAP_NODE(map, 'n') = &n;
				rewritten = rewrite_by_alpha(rule->output_cache[signbits][1], map);
				MAP_NODE(map, 'm') = NULL;
				MAP_NODE(map, 'n') = NULL;
				return rewritten;
			}
		}
	}

	return NULL;
}

struct Axiom *axiom_sqrt()
{
	struct Axiom *a = axiom_new("Calculate square root");

	axiom_add_rule(a, "#\\sqrt{x}", "#1 c \n #1 m \\sqrt{n}", &_calc_sqrt);
	a->is_root_sign_reduce = 1;

	axiom_add_test(a, "-\\sqrt{2}");
	axiom_add_test(a, "-\\sqrt{27}");
	axiom_add_test(a, "-\\sqrt{59049}");
	axiom_add_test(a, "-\\sqrt{0}");
	axiom_add_test(a, "-\\sqrt{1}");
	axiom_add_test(a, "-\\sqrt{-1}");
	axiom_add_test(a, "-\\sqrt{9}");
	axiom_add_test(a, "-\\sqrt{8}");
	axiom_add_test(a, "\\sqrt{16}");

	return a;
}

/*
 * axiom_abs
 */
static struct optr_node *_calc_abs(CALLBK_ARGS)
{
	struct optr_node *x = MAP_NODE(map, 'x');
	struct optr_node *rewritten;

	if (x->type == OPTR_NODE_NUM) {
		float x_val = optr_get_node_val(x);
		float c_val = ABS(x_val);
		struct optr_node c = optr_gen_val_node(c_val);

		MAP_NODE(map, 'c') = &c;
		rewritten = rewrite_by_alpha(rule->output_cache[signbits][0], map);
		MAP_NODE(map, 'c') = NULL;
		return rewritten;
	}
	return NULL;
}

struct Axiom *axiom_abs()
{
	struct Axiom *a = axiom_new("Calculate Power");

	axiom_add_rule(a, "#\\left| #x \\right|", "#1 c", &_calc_abs);
	a->is_root_sign_reduce = 1;

	axiom_add_test(a, "\\left| 8 \\right|");
	axiom_add_test(a, "-\\left| 8 \\right|");
	axiom_add_test(a, "\\left| -8 \\right|");
	axiom_add_test(a, "-\\left| -8 \\right|");

	return a;
}

/*
 * axiom_simplify_fraction
 */
int Euclidean_gcd(int x, int y)
{
    while (y) {
		int save = y;
		y = x % y;
		x = save;
	}

    return x;
}

static struct optr_node *_simplify_fraction(CALLBK_ARGS)
{
	struct optr_node *rewritten;
	struct optr_node *a = MAP_NODE(map, 'a');
	struct optr_node *b = MAP_NODE(map, 'b');

	if (a->type == OPTR_NODE_NUM &&
	    b->type == OPTR_NODE_NUM) {
		float a_val = optr_get_node_val(a);
		float b_val = optr_get_node_val(b);

		if (is_integer(a_val) && is_integer(b_val)) {
			int gcd = Euclidean_gcd(a_val, b_val);
			if (gcd != 0 && gcd != 1) {
				a_val = a_val / gcd;
				b_val = b_val / gcd;
				if (b_val == 1) {
					struct optr_node c = optr_gen_val_node(a_val);
					MAP_NODE(map, 'c') = &c;
					rewritten = rewrite_by_alpha(rule->output_cache[signbits][0], map);
					MAP_NODE(map, 'c') = NULL;
					return rewritten;
				} else if (b != 0) {
					struct optr_node c = optr_gen_val_node(a_val);
					struct optr_node d = optr_gen_val_node(b_val);
					MAP_NODE(map, 'c') = &c;
					MAP_NODE(map, 'd') = &d;
					rewritten = rewrite_by_alpha(rule->output_cache[signbits][1], map);
					MAP_NODE(map, 'c') = NULL;
					MAP_NODE(map, 'd') = NULL;
					return rewritten;
				}
			}
		}

	}

	return NULL;
}

struct Axiom *axiom_simplify_fraction()
{
	struct Axiom *a = axiom_new("Simplify fraction");

	axiom_add_rule(a, "#\\frac{a}{b}", "#1 c \n #1 \\frac{c}{d}", &_simplify_fraction);
	a->is_root_sign_reduce = 1;

	axiom_add_test(a, "-\\frac{-14}{-4}");
	axiom_add_test(a, "\\frac{9}{-6}");
	axiom_add_test(a, "-\\frac{-12}{6}");
	axiom_add_test(a, "\\frac{-12}{6}");

	return a;
}

/*
 * axiom_fraction_add
 */
static struct optr_node *_fraction_numerator_add(CALLBK_ARGS)
{
	struct optr_node *rewritten;
	struct optr_node *a = MAP_NODE(map, 'a');
	struct optr_node *b = MAP_NODE(map, 'b');

	if (a->type == OPTR_NODE_NUM &&
	    b->type == OPTR_NODE_NUM) {
		float a_val = optr_get_node_val(a);
		float b_val = optr_get_node_val(b);

		if (is_integer(a_val) && is_integer(b_val)) {
			struct optr_node *c = MAP_NODE(map, 'c');
			a_val = a_val * signs[2];
			b_val = b_val * signs[3];
			float z_val = a_val + b_val;

			if (c->type == OPTR_NODE_NUM) {
				float c_val = c->num;
				if (is_integer(c_val) && c_val != 0 && is_integer(z_val / c_val)) {
					struct optr_node z = optr_gen_val_node(z_val / c_val);
					MAP_NODE(map, 'z') = &z;
					rewritten = rewrite_by_alpha(rule->output_cache[signbits][0], map);
					MAP_NODE(map, 'z') = NULL;
					return rewritten;
				}
			}

			struct optr_node z = optr_gen_val_node(z_val);
			MAP_NODE(map, 'z') = &z;
			rewritten = rewrite_by_alpha(rule->output_cache[signbits][1], map);
			MAP_NODE(map, 'z') = NULL;
			return rewritten;
		}

	}

	return NULL;
}

struct Axiom *axiom_fraction_add()
{
	struct Axiom *a = axiom_new("Fraction addition in numerator");

	axiom_add_rule(a, "#(#\\frac{a}{c} #\\frac{b}{c})", "z \n \\frac{z}{c}",
	               &_fraction_numerator_add);
	axiom_add_rule(a, "#\\frac{a}{b} #\\frac{c}{d}", "\\frac{#1 ad #2 cb}{bd}", NULL);

	a->is_allow_complication = 1;
	a->is_symmetric_reduce = 1;

	axiom_add_test(a, "-(\\frac{4}{3} - \\frac{1}{3})");
	axiom_add_test(a, "\\frac{4}{3} - \\frac{1}{3}");
	axiom_add_test(a, "-\\frac{1}{3} - \\frac{5}{3}");
	axiom_add_test(a, "-\\frac{1}{3} + \\frac{5}{3}");
	axiom_add_test(a, "\\frac{1}{3a} - \\frac{5}{3a}");
	axiom_add_test(a, "-\\frac{1}{-2} - \\frac{-2}{3}");

	return a;
}

/*
 * axiom_fraction_add_int
 */
static struct optr_node *_fraction_add_int(CALLBK_ARGS)
{
	struct optr_node *rewritten;
	struct optr_node *a = MAP_NODE(map, 'a');
	struct optr_node *b = MAP_NODE(map, 'b');

	if (a->type == OPTR_NODE_NUM) {
		float a_val = optr_get_node_val(a);
		/* the key is to test whether a is an integer */
		if (is_integer(a_val)) {
			rewritten = rewrite_by_alpha(rule->output_cache[signbits][0], map);
			return rewritten;
		}

	}

	return NULL;
}

struct Axiom *axiom_fraction_add_int()
{
	struct Axiom *a = axiom_new("Fraction adds integer");

	axiom_add_rule(a, "#(#a # \\frac{b}{c})", "\\frac{#2 ac #3 b}{c}", &_fraction_add_int);

	a->is_allow_complication = 1;

	axiom_add_test(a, "-(\\frac{1}{3} - \\frac{2}{3} + 2)");
	axiom_add_test(a, "- 1 - \\frac{-1}{2}");
	axiom_add_test(a, "- \\frac{-1}{2} + 1");
	axiom_add_test(a, "\\left| -(5 + \\frac{1}{2})  \\right|");

	return a;
}

/*
 * collapse_fraction (collapse fraction containing decimals)
 */
static struct optr_node *_fraction_collapse(CALLBK_ARGS)
{
	struct optr_node *rewritten;
	struct optr_node *a = MAP_NODE(map, 'a');
	struct optr_node *b = MAP_NODE(map, 'b');

	if (a->type == OPTR_NODE_NUM &&
	    b->type == OPTR_NODE_NUM) {
		float a_val = optr_get_node_val(a);
		float b_val = optr_get_node_val(b);
		if (b_val == 0) goto skip;

		if (!is_integer(a_val) || !is_integer(b_val)) {
			struct optr_node c = optr_gen_val_node(a_val / b_val);
			MAP_NODE(map, 'c') = &c;
			rewritten = rewrite_by_alpha(rule->output_cache[signbits][0], map);
			MAP_NODE(map, 'c') = NULL;
			return rewritten;
		}

	} else if (b->type == OPTR_NODE_NUM) {
		float b_val = optr_get_node_val(b);
		if (b_val == 0) goto skip;

		if (!is_integer(b_val)) {
			struct optr_node c = optr_gen_val_node(1 / b_val);
			MAP_NODE(map, 'k') = &c;
			rewritten = rewrite_by_alpha(rule->output_cache[signbits][1], map);
			MAP_NODE(map, 'k') = NULL;
			return rewritten;
		}
	}

skip:
	return NULL;
}

struct Axiom *axiom_fraction_collapse()
{
	struct Axiom *a = axiom_new("Fraction collapse");

	axiom_add_rule(a, "#\\frac{a}{b}", "#1 c \n #1 ka", &_fraction_collapse);

	a->is_root_sign_reduce = 1;

	axiom_add_test(a, "-\\frac{-6.4}{3.2}");
	axiom_add_test(a, "\\frac{9}{-2.5}");
	axiom_add_test(a, "-\\frac{-10.2}{-6}");
	axiom_add_test(a, "-\\frac{x}{-0.5}");

	return a;
}

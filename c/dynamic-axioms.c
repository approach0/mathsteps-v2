#include <stdlib.h>
#include <stdio.h>
#include <string.h>

#include "mhook.h"
#include "parser.h"
#include "axiom.h"
#include "dynamic-axioms.h"

#define MAP_NODE(_map, _var) \
	_map[alphabet_order(_var, 0)]

#define CALLBK_ARGS \
	struct Rule *rule, struct optr_node *subject, \
	struct optr_node **map, float *signs, int signbits

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

	return a;
}

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

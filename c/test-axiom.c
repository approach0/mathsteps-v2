#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <ctype.h>

#include "mhook.h"
#include "parser.h"
#include "axiom.h"
#include "dynamic-axioms.h"

static struct optr_node *test_addition(
	struct Rule *rule, struct optr_node *subject,
	struct optr_node **map, float *signs, int signbits)
{
	/* print everything */
	printf("Rule: \n");
	rule_print(rule);
	printf("\n");

	printf("subject:\n");
	optr_print(subject);
	printf("\n");

	printf("alpha map: \n");
	alpha_map_print(map);
	printf("\n");

	printf("sign[1] = %g\n", signs[1]);
	printf("sign bits: 0x%x\n", signbits);
	printf("\n");

	/* mock-up implementation */
	struct optr_node *a = MAP_NODE(map, 'a');
	struct optr_node *b = MAP_NODE(map, 'b');

	if (a->type == OPTR_NODE_NUM &&
	    b->type == OPTR_NODE_NUM) {
		struct optr_node c;
		c = optr_gen_val_node(optr_get_node_val(a) + optr_get_node_val(b));
		MAP_NODE(map, 'x') = &c;

        return rewrite_by_alpha(rule->output_cache[signbits][0], map);
	}
	return NULL;
}

int main()
{
	struct Axiom *a = axiom_new("distribute rules");

	axiom_add_rule(a, "a # 0", "a", NULL);
	axiom_add_rule(a, "# \\frac{a}{c} # \\frac{b}{c}", "\\frac{x}{c}", &test_addition);
	//axiom_print(a);

	void *scanner = parser_new_scanner();
	struct optr_node *tree = parser_parse(scanner, "\\frac{1}{zz} + \\frac{3}{zz}");
	parser_dele_scanner(scanner);

	struct optr_node *output = exact_rule_apply(a->rules + 1, tree);

	printf("applied? %d \n", output != NULL);
	optr_print(output);

	optr_release(tree);
	optr_release(output);
	axiom_free(a);
	mhook_print_unfree();
	return 0;
}

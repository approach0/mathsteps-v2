#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <ctype.h>

#include "mhook.h"
#include "parser.h"
#include "axiom.h"

int main()
{
	struct Axiom *a = axiom_new("distribute rules");

	axiom_add_rule(a, "a # 0", "a", NULL);
	//axiom_add_rule(a, "\\frac{a}{b}", "a \n \\frac{c}{d}", NULL);
	//axiom_add_rule(a, "#\\frac{a}{b} # 1 # 0", "#1 x #2 1 = #0 1", NULL);
	//axiom_print(a);

	void *scanner = parser_new_scanner();
	struct optr_node *tree = parser_parse(scanner, "\\frac{1}{2} + 0 + xx");
	parser_dele_scanner(scanner);

	struct optr_node *output = exact_rule_apply(a->rules + 0, tree);

	printf("applied? %d \n", output != NULL);
	optr_print(output);

	optr_release(tree);
	optr_release(output);
	axiom_free(a);
	mhook_print_unfree();
	return 0;
}

#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <ctype.h>

#include "mhook.h"
#include "axiom.h"

int main()
{
	struct Axiom *a = axiom_new("distribute rules");

	axiom_add_static_rule(a, "a + 0", "a", NULL);
	axiom_add_static_rule(a, "\\frac{a}{b}", "a \n \\frac{c}{d}", NULL);

	axiom_print(a);

	axiom_free(a);
	mhook_print_unfree();
	return 0;
}

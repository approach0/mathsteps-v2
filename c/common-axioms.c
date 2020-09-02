#include <stdio.h>
#include <stdlib.h>

#include "dynamic-axioms.h"
#include "common-axioms.h"

struct Axiom **common_axioms(int *n)
{
	struct Axiom **ret = malloc(sizeof(struct Axiom*) * MAX_AXIOMS);
	int cnt = 0;

	{
		struct Axiom *a = axiom_new("Remove zero term");

		axiom_add_rule(a, "# (n - n)", "0", NULL);
		axiom_add_rule(a, "# (a - \\frac{a}{1})", "0", NULL);
		axiom_add_rule(a, "# (-a + \\frac{a}{1})", "0", NULL);

		axiom_add_test(a, "-(2 - 2)");
		axiom_add_test(a, "\\frac{a^{2}}{1} - a^{2}");

		ret[cnt++] = a;
	}

	{
		struct Axiom *a = axiom_new("Multiplying zero result in zero");

		axiom_add_rule(a, "# 0 \\cdot *{a}", "0", NULL);
		axiom_add_rule(a, "#\\frac{#0}{x}", "0", NULL);

		axiom_add_test(a, "\\frac{0 \\times b^{2} \\times a}{2}");
		axiom_add_test(a, "a \\times b^{2} \\times 0");
		axiom_add_test(a, "a \\times 0 \\times b^{2}");

		ret[cnt++] = a;
	}

	{
		struct Axiom *a = axiom_add();
		ret[cnt++] = a;
	}

	{
		struct Axiom *a = axiom_mul();
		ret[cnt++] = a;
	}

	*n = cnt;
	return ret;
}

void common_axioms_free(struct Axiom *axioms[], int n)
{
	for (int i = 0; i < n; i++)
		axiom_free(axioms[i]);
	free(axioms);
}

#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <ctype.h>

#include "mhook.h"
#include "parser.h"
#include "axiom.h"
#include "dynamic-axioms.h"
#include "common-axioms.h"

int main()
{
	//struct Axiom *a = axiom_add();
	//axiom_test(a);
	//axiom_free(a);

	int m;
	struct Axiom **axioms = common_axioms(&m);

	for (int i = 0; i < m; i++) {
		struct Axiom *a = axioms[i];
		if (strcmp(a->name, "Multiplying zero result in zero") == 0) {
			axiom_test(a);
		}
	}

	common_axioms_free(axioms, m);
	mhook_print_unfree();
	return 0;
}

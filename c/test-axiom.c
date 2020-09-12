#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <ctype.h>

#include "mhook.h"
#include "parser.h"
#include "axiom.h"
#include "dynamic-axioms.h"
#include "common-axioms.h"
#include "vt100-code.h"

int main()
{
	//struct Axiom *a = axiom_add();
	//axiom_test(a);
	//axiom_free(a);

	int m;
	struct Axiom **axioms = common_axioms(&m);
	printf("There are %d axioms in total.\n", m);

	for (int i = 0; i < m; i++) {
		struct Axiom *a = axioms[i];
		//if (1) {
		//if (strcmp(a->name, "Square-power cancels out") == 0) {
		if (i + 1 == m) {
			printf(C_BLUE "Testing axiom `%s'\n" C_RST, a->name);
			axiom_test(a);
		}
	}

	common_axioms_free(axioms, m);
	mhook_print_unfree();
	return 0;
}

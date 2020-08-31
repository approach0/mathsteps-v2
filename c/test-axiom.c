#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <ctype.h>

#include "mhook.h"
#include "parser.h"
#include "axiom.h"
#include "dynamic-axioms.h"

int main()
{
	struct Axiom *a = axiom_addition();
	axiom_test(a);
	axiom_free(a);

	mhook_print_unfree();
	return 0;
}

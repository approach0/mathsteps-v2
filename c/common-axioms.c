#include <stdio.h>
#include <stdlib.h>

#include "dynamic-axioms.h"
#include "common-axioms.h"

struct Axiom **common_axioms(int *n)
{
	struct Axiom **ret = malloc(sizeof(struct Axiom*) * MAX_AXIOMS);
	int cnt = 0;

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

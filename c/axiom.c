#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "axiom.h"

struct Axiom *axiom_new(const char *name)
{
	struct Axiom *a = malloc(sizeof(struct Axiom));
	strcpy(a->name, name);

	a->n_rules = 0;
	a->n_tests = 0;

	a->is_root_sign_reduce = 0;
	a->is_recursive_apply = 0;
	a->is_allow_complication = 0;
	a->is_strict_simplify = 0;
	a->is_disabled = 0;

	a->max_output_num = 10;
}

void axiom_free(struct Axiom *a)
{
	free(a);
}

struct Axiom *axiom_add_rule(
	struct Axiom *a,
	const char *pattern,
	const char *output,
	void *dynamic_procedure)
{
	return NULL;
}

#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "parser.h"
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
	for (int i = 0; i < a->n_rules; i++) {
		struct Rule *rule = &a->rules[i];
		optr_release(rule->pattern_cache);
		optr_release(rule->output_cache[0]);
	}
	free(a);
}

struct Axiom *axiom_add_static_rule(
	struct Axiom *a,
	const char *pattern,
	const char *output,
	void *dynamic_procedure)
{
	int i = a->n_rules ++;
	strcpy(a->rules[i].pattern, pattern);
	strcpy(a->rules[i].output, output);

	void *scanner = parser_new_scanner();
	assert(scanner != NULL);

	struct optr_node *root_pattern = NULL;
	struct optr_node *root_output = NULL;

	root_pattern = parser_parse(scanner, pattern);
	if (NULL == root_pattern) {
		fprintf(stderr, "cannot add rule due to parser error.\n");

		optr_release(root_pattern);
		optr_release(root_output);
		a->n_rules -= 1;

		goto skip;
	}

	root_output = parser_parse(scanner, output);
	if (NULL == root_output) {
		fprintf(stderr, "cannot add rule due to parser error.\n");

		optr_release(root_pattern);
		optr_release(root_output);
		a->n_rules -= 1;

		goto skip;
	}

	a->rules[i].pattern_cache = root_pattern;
	a->rules[i].output_cache[0] = root_output;

skip:
	parser_dele_scanner(scanner);
	return a;
}

void axiom_print(struct Axiom *a)
{
	printf("Axiom `%s':\n", a->name);
	for (int i = 0; i < a->n_rules; i++) {
		struct Rule *rule = &a->rules[i];
		printf("#%d rule:\n", i);

		printf("[pattern] %s\n", rule->pattern);
		optr_print(rule->pattern_cache);

		printf("[output] %s\n", rule->output);
		optr_print(rule->output_cache[0]);
	}
	printf("\n");
}

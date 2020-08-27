#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

#include "parser.h"
#include "axiom.h"

char *_ltrim(char *s)
{
    while(isspace(*s)) s++;
    return s;
}

char *_rtrim(char *s)
{
    char* back = s + strlen(s);
    while(isspace(*--back));
    *(back+1) = '\0';
    return s;
}

char *trim(char *s)
{
    return _rtrim(_ltrim(s));
}

int cnt_outputs(char *s)
{
	int count = 0;
	while ((s = strchr(s, '\n')) != NULL) {
		count++;
		s++;
	}
	return count + 1;
}

struct Axiom *axiom_new(const char *name)
{
	struct Axiom *a = calloc(1, sizeof(struct Axiom));
	strcpy(a->name, name);
	a->max_output_num = 10;
}

void _free_rule(struct Rule *rule)
{
	char *pattern = rule->pattern;

	if (rule->pattern_cache) {
		optr_release(rule->pattern_cache);
		rule->pattern_cache = NULL;
	}

	for (int j = 0; j < MAX_RULE_OUTPUTS; j++) {
		if (rule->output_cache[j]) {
			optr_release(rule->output_cache[j]);
			rule->output_cache[j] = NULL;
		}
	}
}

void axiom_free(struct Axiom *a)
{
	for (int i = 0; i < a->n_rules; i++) {
		struct Rule *rule = &a->rules[i];
		_free_rule(rule);
	}
	free(a);
}

struct Axiom *axiom_add_rule(
	struct Axiom *a,
	const char *pattern,
	const char *output,
	void *dynamic_procedure)
{
	struct optr_node *root = NULL;
	int i = a->n_rules ++;
	struct Rule *rule = &a->rules[i];

	/* copy pattern/output string */
	strcpy(rule->pattern, pattern);
	strcpy(rule->output, output);

	/* allocate scanner */
	void *scanner = parser_new_scanner();
	assert(scanner != NULL);

	/* create pattern cache */
	root = parser_parse(scanner, pattern);
	if (NULL == root) {
		fprintf(stderr, "cannot add rule due to parser error.\n");

		_free_rule(rule);
		a->n_rules -= 1;

		goto skip;
	} else {
		rule->pattern_cache = root;
	}

	/* create output cache */
	char *all, *now, *field;
	int cnt = 0;
	all = now = strdup(output);
	while ((field = strsep(&now, "\n"))) {
		char *subout = trim(field);
		root = parser_parse(scanner, subout);
		if (NULL == root) {
			fprintf(stderr, "cannot add rule due to parser error: %s\n", subout);

			_free_rule(rule);
			a->n_rules -= 1;

			free(all);
			goto skip;
		} else {
			rule->output_cache[cnt++] = root;
		}
	}
	free(all);

skip:
	/* de-allocate scanner */
	parser_dele_scanner(scanner);
	return a;
}

void axiom_print(struct Axiom *a)
{
	printf("Axiom `%s':\n", a->name);
	for (int i = 0; i < a->n_rules; i++) {
		struct Rule *rule = &a->rules[i];
		printf("--- #%d rule ---\n", i);

		printf("[pattern]\n%s\n", rule->pattern);
		optr_print(rule->pattern_cache);

		printf("[output]\n%s\n", rule->output);
		for (int j = 0; j < MAX_RULE_OUTPUTS; j++) {
			if (rule->output_cache[j]) {
				printf("{%d}:\n", j);
				optr_print(rule->output_cache[j]);
			}
		}
	}
}

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

int cnt_char_occurrence(const char *s, char t)
{
	int count = 0;
	while ((s = strchr(s, t)) != NULL) {
		count++;
		s++;
	}
	return count;
}

int ipow(int base, int exp)
{
	int result = 1;
	for (;;)
	{
		if (exp & 1)
			result *= base;
		exp >>= 1;
		if (!exp)
			break;
		base *= base;
	}

	return result;
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

	for (int i = 0; i < ipow(2, rule->n_pounds); i++) {
		for (int j = 0; j < MAX_RULE_OUTPUTS; j++) {
			if (rule->output_cache[i][j]) {
				optr_release(rule->output_cache[i][j]);
				rule->output_cache[i][j] = NULL;
			}
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

int pound2signed(char *dest, const char *src, int bits, int n_pounds)
{
	int reduce_sign = 1;
	strcpy(dest, src);
	for (int i = 1; i <= n_pounds; i++) {
		/* find named pound... */
		char named_pound[16];
		sprintf(named_pound, "#%d", i);
		char *pound_pos = strstr(dest, named_pound);
		if (NULL == pound_pos)
			continue;

		/* replace named pound */
		*(pound_pos + 0) = ' ';
		*(pound_pos + 1) = (bits & 0x1) ? '+' : '-';

		/* reduce sign */
		reduce_sign *= (bits & 0x1) ? +1 : -1;

		/* continue to get next sign bit */
		bits = bits >> 1;
	}

	char *pound_pos = strstr(dest, "#0");
	if (pound_pos) {
		*(pound_pos + 0) = ' ';
		*(pound_pos + 1) = (reduce_sign == 1) ? '+' : '-';
	}
}

struct Axiom *axiom_add_rule(
	struct Axiom *a,
	const char *pattern,
	const char *output,
	apply_callbk_t dynamic_procedure)
{
	struct optr_node *root = NULL;
	int i = a->n_rules ++;
	struct Rule *rule = &a->rules[i];

	/* set properties */
	strcpy(rule->pattern, pattern);
	strcpy(rule->output, output);
	int n_pounds = cnt_char_occurrence(pattern, '#');
	rule->n_pounds = n_pounds;
	rule->dynamic_procedure = dynamic_procedure;

	/* allocate scanner */
	void *scanner = parser_new_scanner();
	assert(scanner != NULL);

	/* setup pattern cache */
	root = parser_parse(scanner, pattern);
	if (NULL == root) {
		fprintf(stderr, "cannot add rule due to parser error.\n");

		_free_rule(rule);
		a->n_rules -= 1;

		goto skip;
	} else {
		rule->pattern_cache = root;
	}

	/* setup output cache */
	for (int k = 0; k < ipow(2, n_pounds); k++) {
		char tmp[MAX_RULE_STR_LEN];
		pound2signed(tmp, output, k, n_pounds);
		//printf("%s => %s => %s\n", pattern, output, tmp);

		/* create output cache */
		char *all, *now, *field;
		int cnt = 0;
		all = now = strdup(tmp);
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
				rule->output_cache[k][cnt++] = root;
			}
		}
		free(all);
	}

skip:
	/* de-allocate scanner */
	parser_dele_scanner(scanner);
	return a;
}

void rule_print(struct Rule *rule)
{
	printf("[pattern]\n%s\n", rule->pattern);
	optr_print(rule->pattern_cache);

	printf("[output]\n%s\n", rule->output);
	for (int k = 0; k < ipow(2, rule->n_pounds); k++) {
		for (int j = 0; j < MAX_RULE_OUTPUTS; j++) {
			if (rule->output_cache[k][j]) {
				printf("{%d, %d}:\n", k, j);
				optr_print(rule->output_cache[k][j]);
			}
		}
	}
}

void axiom_print(struct Axiom *a)
{
	printf("Axiom `%s':\n", a->name);
	for (int i = 0; i < a->n_rules; i++) {
		struct Rule *rule = &a->rules[i];
		printf("--- #%d rule ---\n", i);
		rule_print(rule);
	}
}

struct optr_node *exact_rule_apply(struct Rule *rule, struct optr_node *tree)
{
	float signs[MAX_NUM_POUNDS];
	struct optr_node **map = test_alpha_equiv(rule->pattern_cache, tree, signs);

	if (NULL == map) {
		return NULL;
	}

	int k = 0;
	for (int i = 0; i < rule->n_pounds; i++) {
		int pound_ID = i + 1;
		if (signs[pound_ID] > 0) {
			k = k | (0x1 << i);
		}
	}

	struct optr_node **outputs = rule->output_cache[k];
	struct optr_node *output;
	if (rule->dynamic_procedure) {
		output = (*rule->dynamic_procedure)(rule, tree, map, signs, k);
	} else {
		output = rewrite_by_alpha(outputs[0], map);
	}

	alpha_map_free(map);
	return output;
}

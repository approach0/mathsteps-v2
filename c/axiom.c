#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <stdint.h>

#include "vt100-code.h"
#include "parser.h"
#include "axiom.h"

static char *_ltrim(char *s)
{
    while(isspace(*s)) s++;
    return s;
}

static char *_rtrim(char *s)
{
    char* back = s + strlen(s);
    while(isspace(*--back));
    *(back+1) = '\0';
    return s;
}

static char *trim(char *s)
{
    return _rtrim(_ltrim(s));
}

static int cnt_char_occurrence(const char *s, char t)
{
	int count = 0;
	while ((s = strchr(s, t)) != NULL) {
		count++;
		s++;
	}
	return count;
}

static int ipow(int base, int exp)
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

int axiom_add_test(struct Axiom* a, const char* test_str)
{
	if (a->n_tests + 1 < MAX_AXIOM_TESTS) {
		strcpy(a->tests[a->n_tests ++], test_str);
		return 0;
	}

	return 1;
}

int axiom_test(struct Axiom* a)
{
	int n_failed = 0;
	struct optr_node *output[MAX_AXIOM_OUTPUTS];

	void *scanner = parser_new_scanner();

	for (int i = 0; i < a->n_tests; i++) {
		const char *test_str = a->tests[i];
		struct optr_node *tree = parser_parse(scanner, test_str);
		printf("[testing] `%s':\n", test_str);

		if (NULL == tree) {
			n_failed ++;
			break;
		}

		/* do testing */
		int n_output = axiom_apply(a, tree, output);
		printf("%d applied results:\n", n_output);

		for (int i = 0; i < n_output; i++) {
			struct optr_node *out = output[i];

			printf(C_CYAN "#%d: " C_RST, i);

			optr_print_tex(out);
			printf("\n");

			//optr_print(out);

			optr_release(out);
		}

		optr_release(tree);
		printf("\n");
	}

	parser_dele_scanner(scanner);
	return n_failed;
}

struct Axiom *axiom_new(const char *name)
{
	struct Axiom *a = calloc(1, sizeof(struct Axiom));
	strcpy(a->name, name);
	a->max_output_num = DEFAULT_AXIOM_OUTPUTS;
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

int pound2signed(char *dest, const char *src, uint64_t bits, int n_pounds)
{
	int reduce_sign = 1;
	strcpy(dest, src);
	for (int i = 1; i <= n_pounds; i++) {
		/* find named pound... */
		char named_pound[16];
		sprintf(named_pound, "#%d", i);
		char *pound_pos = strstr(dest, named_pound);
		if (NULL == pound_pos)
			goto skip;

		/* replace named pound */
		*(pound_pos + 0) = ' ';
		*(pound_pos + 1) = (bits & 0x1) ? '+' : '-';
skip:
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

	return 0;
}

struct Rule *axiom_add_rule(
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
		rule->contain_toplevel_wildcards = root->n_wildcards_children;
	}

	/* setup output cache */
	for (uint64_t k = 0; k < ipow(2, n_pounds); k++) {
		/* create output cache */
		char *all, *now, *field;
		int cnt = 0;
		all = now = strdup(output);
		while ((field = strsep(&now, "\n"))) {
			char subout[MAX_RULE_STR_LEN];
			pound2signed(subout, trim(field), k, n_pounds);
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
	return rule;
}

void rule_print(struct Rule *rule)
{
	printf("[pattern]\n%s\n", rule->pattern);
	optr_print(rule->pattern_cache);

	printf("[template]\n%s\n", rule->output);
	for (uint64_t k = 0; k < ipow(2, rule->n_pounds); k++) {
		for (int j = 0; j < MAX_RULE_OUTPUTS; j++) {
			if (rule->output_cache[k][j]) {
				struct optr_node *c = rule->output_cache[k][j];
				printf(C_GRAY "{%lu, %d} " C_RST, k, j);
				optr_print_tex(c);
				printf("\n");
				optr_print(c);
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

	uint64_t k = 0;
	for (int i = 0; i < rule->n_pounds; i++) {
		int pound_ID = i + 1;
		if (signs[pound_ID] > 0) {
			k = k | (0x1 << i);
		}
	}

	struct optr_node *output;
	if (rule->dynamic_procedure) {
		output = (*rule->dynamic_procedure)(rule, tree, map, signs, k);
	} else {
		struct optr_node **outputs = rule->output_cache[k];
		output = rewrite_by_alpha(outputs[0], map);

		//alpha_map_print(map);
		//optr_print(outputs[0]);
		//optr_print(output);
	}

	alpha_map_free(map);
	return output;
}

struct optr_node *ij_replaced(
	struct optr_node *tree, struct optr_node *subst,
	int i, int j, int is_root_sign_reduce)
{
	struct optr_node *new_tree = shallow_copy(tree);

	/* new sign depends on reduction, e.g., "-(-a)(-b)c => -abc" */
	if (is_root_sign_reduce)
		new_tree->sign = 1.f;

	for (int k = 0; k < tree->n_children; k++) {
		if (k != i && k != j) {
			optr_attach(new_tree, deep_copy(tree->children[k]));
		} else if (k == i) {
			optr_pass_children(new_tree, subst);
		}
	}
	return new_tree;
}

struct optr_node *merge_brothers(
	struct optr_node *tree, struct optr_node *reduced,
	int i, int j, int n, int is_root_sign_reduce)
{
	struct optr_node *new_tree = reduced;
	if (n > 2) {
		/* there are left brothers */
		new_tree = ij_replaced(tree, reduced, i, j, is_root_sign_reduce);

	} else {
		/* entire level gets reduced */
		;

		/* for non-reduce root sign, apply root sign in this case.
		 * e.g., "-(1 - 2) => 1" */
		if (!is_root_sign_reduce)
			new_tree->sign *= tree->sign;
	}

	return new_tree;
}

int axiom_level_apply(
	struct Axiom *axiom, struct optr_node *tree,
	struct optr_node **results, int max_outputs)
{
	int tok = tree->token;
	int n = tree->n_children;
	int cnt = 0;
	int rsr = axiom->is_root_sign_reduce;

	if (tree->type != OPTR_NODE_TOKEN || max_outputs <= 0)
		return 0;

	for (int i = 0; i < axiom->n_rules; i++) {
		struct Rule *rule = axiom->rules + i;
		struct optr_node *reduced, hanger;

		if (n == 1 || rule->contain_toplevel_wildcards) {
			/* in unary tree, invok exact_rule_apply() directly */
			reduced = exact_rule_apply(rule, tree);
			if (reduced) {
				results[cnt++] = merge_brothers(tree, reduced, 0, 0, 0, rsr);
				if (cnt == max_outputs) goto early_stop;
			}

		} else if (tok == TOK_HEX_ADD || tok == TOK_HEX_TIMES) {
			/* in commutative tree, make children pair permutations */
			for (int i = 0; i < n; i++) {
				for (int j = i + 1; j < n; j++) {
					//rule_print(rule);
					if (1) {
						hanger = *tree;
						hanger.n_children = 0;
						optr_attach(&hanger, tree->children[i]);
						optr_attach(&hanger, tree->children[j]);

						//printf("ij:\n");
						//optr_print(&hanger);

						reduced = exact_rule_apply(rule, &hanger);
						if (reduced) {
							results[cnt++] = merge_brothers(tree, reduced, i, j, n, rsr);
							if (cnt == max_outputs) goto early_stop;
						}
					}

					if (!axiom->is_symmetric_reduce && !rule->is_symmetric_reduce) {
						hanger = *tree;
						hanger.n_children = 0;
						optr_attach(&hanger, tree->children[j]);
						optr_attach(&hanger, tree->children[i]);

						//printf("ji:\n");
						//optr_print(&hanger);

						reduced = exact_rule_apply(rule, &hanger);
						if (reduced) {
							results[cnt++] = merge_brothers(tree, reduced, j, i, n, rsr);
							if (cnt == max_outputs) goto early_stop;
						}
					}
				}
			}
		} else {
			/* in non-commutative tree, make children pair in order */
			for (int i = 0; i + 1 < n; i++) {
				hanger = *tree;
				hanger.n_children = 0;
				optr_attach(&hanger, tree->children[i]);
				optr_attach(&hanger, tree->children[i + 1]);
				reduced = exact_rule_apply(rule, &hanger);
				if (reduced) {
					results[cnt++] = merge_brothers(tree, reduced, i, i + 1, n, rsr);
					if (cnt == max_outputs) goto early_stop;
				}
			}
		}
	}

early_stop:
	return cnt;
}

int axiom_onetime_apply(struct Axiom *axiom, struct optr_node *tree, struct optr_node **results)
{
	int max_outputs = axiom->max_output_num;
	int n_results = axiom_level_apply(axiom, tree, results, max_outputs);
	max_outputs -= n_results;
	results += n_results;

	for (int i = 0; i < tree->n_children; i++) {
		struct optr_node *child = tree->children[i];

		/* invoke this function recursively for each child */
		int n = axiom_onetime_apply(axiom, child, results);

		/* for each applied child, plug in back to original tree */
		for (int j = 0; j < n; j++) {
			struct optr_node *subst = results[j];
			struct optr_node *newtr = ij_replaced(tree, subst, i, -1, 0);
			results[j] = newtr;
		}

		/* update output pointer and counter */
		n_results += n;
		max_outputs -= n;
		results += n;
	}
	return n_results;
}

int axiom_apply(struct Axiom *axiom, struct optr_node *tree, struct optr_node **results)
{
	if (axiom->is_disabled)
		return 0;

	if (axiom->is_recursive_apply) {
		/* TODO */
		return 0;
	} else {
		return axiom_onetime_apply(axiom, tree, results);
	}
}


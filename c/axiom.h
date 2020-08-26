#pragma once
#define MAX_RULE_NAME_LEN  128
#define MAX_RULE_STR_LEN   1024
#define MAX_AXIOM_RULES    32
#define MAX_RULE_OUTPUTS   3

#include "optr.h"

struct Rule {
	char pattern[MAX_RULE_STR_LEN];
	char output[MAX_RULE_STR_LEN];

	struct optr_node *pattern_cache, *output_cache[MAX_RULE_OUTPUTS];
	float             signs_cache[MAX_RULE_STR_LEN];

	void *dynamic_output;
	int   is_wildcards;
};

struct Axiom {
	char name[MAX_RULE_NAME_LEN];

	int n_rules;
	struct Rule rules[MAX_AXIOM_RULES];

	int n_tests;
	struct Rule tests[MAX_AXIOM_RULES];

	int is_root_sign_reduce;
	int is_recursive_apply;
	int is_allow_complication;
	int is_strict_simplify;
	int is_disabled;

	int max_output_num;
};

struct Axiom *axiom_new(const char*);
void axiom_free(struct Axiom*);

struct Axiom *axiom_add_static_rule(struct Axiom*, const char*, const char*, void*);
void axiom_print(struct Axiom*);

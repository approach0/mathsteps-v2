#pragma once
#define MAX_RULE_NAME_LEN  128
#define MAX_RULE_STR_LEN   1024
#define MAX_AXIOM_RULES    32

#define MAX_SIGN_PERMUTATIONS 32 /* 2^5 */
#define MAX_NUM_POUNDS        5
#define MAX_RULE_OUTPUTS      3

#define MAX_AXIOM_TESTS    128
#define MAX_AXIOM_OUTPUTS  20

#include "alpha-equiv.h"

struct Rule;

typedef struct optr_node *
(*apply_callbk_t)(struct Rule*, struct optr_node*, struct optr_node **map, float *signs, int);

struct Rule {
	char pattern[MAX_RULE_STR_LEN];
	char output[MAX_RULE_STR_LEN];

	int n_pounds; /* number of pounds in pattern */
	apply_callbk_t    dynamic_procedure;

	struct optr_node *pattern_cache;
	struct optr_node *output_cache[MAX_SIGN_PERMUTATIONS][MAX_RULE_OUTPUTS];
};

struct Axiom {
	char name[MAX_RULE_NAME_LEN];

	int n_rules;
	struct Rule rules[MAX_AXIOM_RULES];

	int n_tests;
	char tests[MAX_AXIOM_TESTS][MAX_TEX_LEN];

	int is_root_sign_reduce;
	int is_symmetric_reduce;
	//int is_recursive_apply;
	//int is_allow_complication;
	//int is_strict_simplify;
	//int is_disabled;
	int max_output_num;
};

struct Axiom *axiom_new(const char*);
void          axiom_free(struct Axiom*);

struct Axiom *axiom_add_rule(struct Axiom*, const char*, const char*, apply_callbk_t);
int           axiom_add_test(struct Axiom*, const char*);
int           axiom_test(struct Axiom*);

void          rule_print(struct Rule*);
void          axiom_print(struct Axiom*);

struct optr_node *exact_rule_apply(struct Rule*, struct optr_node*);

int axiom_level_apply(struct Axiom*, struct optr_node*, struct optr_node **);

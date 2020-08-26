#pragma once
#include "optr.h"

#define MAX_NUM_POUNDS 16

int test_node_identical(struct optr_node*, struct optr_node*);
int test_optr_identical(struct optr_node*, struct optr_node*);

int alphabet_order(int, int);

struct optr_node *shallow_copy(struct optr_node*);
struct optr_node *deep_copy(struct optr_node*);

struct optr_node **test_alpha_equiv(struct optr_node*, struct optr_node*, float*);

void alpha_map_print(struct optr_node *map[]);
void alpha_map_free(struct optr_node *map[]);

struct optr_node *rewrite_by_alpha(struct optr_node*, struct optr_node *map[]);

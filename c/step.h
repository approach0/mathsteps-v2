#pragma once
#include "optr.h"
#include "axiom.h"

struct Step {
	struct Axiom     *axiom;
	int               axiom_idx;
	struct optr_node *tree;
	float             value;
};

float state_value__neg_complexity(struct optr_node*);

int   possible_next_steps(struct optr_node*, struct Axiom *axioms[], int, struct Step*, int);
int   mathsteps_baseline (struct optr_node*, struct Axiom *axioms[], int, struct Step*, int);

void  print_step(struct Step*, int);

#pragma once
#include "optr.h"
#include "axiom.h"

struct Step {
	struct Axiom     *axiom;
	int               axiom_idx;
	struct optr_node *tree;
	float             value;
};

#pragma once
#define MAX_AXIOMS 200
#define FULL_COMMON_AXIOMS

#include "axiom.h"

struct Axiom **common_axioms(int*);
void           common_axioms_free(struct Axiom *axioms[], int);

#pragma once
#include "optr.h"

void             *parser_new_scanner();
struct optr_node *parser_parse(void*, const char*);
void              parser_dele_scanner(void*);

%{
#include "y.tab.h"
#include "lex.yy.h"

#include "optr.h"

int yyerror(void *, const char*);

#define YYPARSE_PARAM yyscan_t scanner
#define YYLEX_PARAM scanner
%}

%union {
	struct optr_node *nd;
}

%destructor {
	if ($$) {
		optr_release($$);
		$$ = NULL;
	}
} <nd>

%define api.pure full
%define parse.error verbose

%lex-param {void *scanner}
%parse-param {void *scanner}
/*
 * Above statements will change yyparse() and yylex() from no arguments to these:
 * yyparse(yyscan_t *scanner)
 * yylex(YYSTYPE *yylval_param, yyscan_t yyscanner)
 */

%token _EOL
%token <nd> NUM
%token _ADD
%token _TIMES

%start doc
%type <nd> sum
%type <nd> product
%type <nd> factor
%type <nd> atom

%left _NULL_REDUCE
%left _ADD
%left _TIMES

%%
doc: sum

sum: %prec _NULL_REDUCE {
	$$ = NULL;
}
| product {
	$$ = $1;
}
| sum _ADD product {
	struct optr_node *op = optr_alloc(OPTR_NODE_TOKEN);
	op->token = '+';

	optr_attach(op, $1);
	optr_attach(op, $3);
	$$ = op;
}
;

product: factor {
	$$ = $1;
}
| product factor {
	struct optr_node *op = optr_alloc(OPTR_NODE_TOKEN);
	op->token = '*';

	optr_attach(op, $1);
	optr_attach(op, $2);
	$$ = op;
}
| product _TIMES factor {
	struct optr_node *op = optr_alloc(OPTR_NODE_TOKEN);
	op->token = '*';

	optr_attach(op, $1);
	optr_attach(op, $3);
	$$ = op;
}
;

factor: atom {
	$$ = $1;
}
;

atom: NUM {
	$$ = $1;
}
;
%%

int yyerror(void *scanner, const char *msg)
{
	fprintf(stderr, "%s\n", msg);
	return 0;
}

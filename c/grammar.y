%{
#define YY_DECL int yylex(YYSTYPE *yylval_param, void *yyscanner, int *pound_cnt)

#include "y.tab.h"
#include "lex.yy.h"

int yylex(YYSTYPE*, void*, int*);

#include "optr.h"

int yyerror(void*, struct optr_node**, int *, const char*);
wchar_t mbc2wc(const char*);

#define COMM_ATTACH(_root, _child) \
	optr_pass_children(_root, _child)
%}

%union {
	struct optr_node *nd;
	int pound_cnt;
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
%lex-param {int *pound_cnt}

%parse-param {void *scanner}
%parse-param {struct optr_node **root}
%parse-param {int *pound_cnt}
/*
 * Above statements will change yylex() and yyparse() from no arguments to these:
 * yylex(YYSTYPE *yylval_param, yyscan_t yyscanner, int *pound_cnt)
 * yyparse(yyscan_t *scanner, struct optr_node *root, int *pound_cnt)
 */

%token _EOL
%token <nd> NUM
%token <nd> VAR
%token _EQ
%token _ADD
%token _MINUS
%token <pound_cnt> POUND
%token _DIV
%right _SUP _SUB
%token _TIMES _CDOT
%token _STAR
%token _SQRT

%start start
%type <nd> doc
%type <nd> sum
%type <nd> term
%type <nd> product
%type <nd> factor
%type <nd> atom

%left _NULL_REDUCE
%left _ADD _MINUS POUND
%left _TIMES _CDOT

%right _FRAC
%nonassoc _L_BRACE        _R_BRACE
%nonassoc _L_PARENTHESIS  _R_PARENTHESIS
%nonassoc _L_BRACKET      _R_BRACKET
%nonassoc _L_BAR          _R_BAR

%%
start: doc {
	*root = $1;
}
;

doc: sum {
	$$ = $1;
}
| sum _EQ sum {
	struct optr_node *op = optr_alloc(OPTR_NODE_TOKEN);
	op->token = mbc2wc("=");

	optr_attach(op, $1);
	optr_attach(op, $3);
	$$ = op;
}
;

sum: %prec _NULL_REDUCE {
	$$ = NULL;
}
| term {
	$$ = $1;
}
| sum _ADD term {
	if (NULL != $1) {
		struct optr_node *op = optr_alloc(OPTR_NODE_TOKEN);
		op->token = mbc2wc("+");

		COMM_ATTACH(op, $1);
		COMM_ATTACH(op, $3);
		$$ = op;
	} else {
		$$ = $3;
	}
}
| sum _MINUS term {
	if ($3) $3->sign *= -1.f;

	if (NULL != $1) {
		struct optr_node *op = optr_alloc(OPTR_NODE_TOKEN);
		op->token = mbc2wc("+");

		COMM_ATTACH(op, $1);
		COMM_ATTACH(op, $3);
		$$ = op;
	} else {
		$$ = $3;
	}
}
| sum POUND term {
	if ($3) $3->pound_ID = $2;

	if (NULL != $1) {
		struct optr_node *op = optr_alloc(OPTR_NODE_TOKEN);
		op->token = mbc2wc("+");

		COMM_ATTACH(op, $1);
		COMM_ATTACH(op, $3);
		$$ = op;
	} else {
		$$ = $3;
	}
}
;

term: product {
	$$ = $1;
}
| term _DIV product {
	struct optr_node *op = optr_alloc(OPTR_NODE_TOKEN);
	op->token = mbc2wc("÷");

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
	op->token = mbc2wc("×");

	COMM_ATTACH(op, $1);
	COMM_ATTACH(op, $2);
	$$ = op;
}
| product _TIMES factor {
	struct optr_node *op = optr_alloc(OPTR_NODE_TOKEN);
	op->token = mbc2wc("×");

	COMM_ATTACH(op, $1);
	COMM_ATTACH(op, $3);
	$$ = op;
}
| product _CDOT factor {
	struct optr_node *op = optr_alloc(OPTR_NODE_TOKEN);
	op->token = mbc2wc("×");

	COMM_ATTACH(op, $1);
	COMM_ATTACH(op, $3);
	$$ = op;
}
;

factor: atom {
	$$ = $1;
}
| atom _SUP atom {
	struct optr_node *op = optr_alloc(OPTR_NODE_TOKEN);
	op->token = mbc2wc("^");

	COMM_ATTACH(op, $1);
	COMM_ATTACH(op, $3);
	$$ = op;
}
| atom _SUB atom {
	/* TODO */
	if ($3)
		optr_release($$);

	$$ = $1;
}
| _FRAC atom atom {
	struct optr_node *op = optr_alloc(OPTR_NODE_TOKEN);
	op->token = mbc2wc("/");

	optr_attach(op, $2);
	optr_attach(op, $3);
	$$ = op;
}
;

atom: NUM {
	$$ = $1;
}
| VAR {
	$$ = $1;
}
| _L_BRACE sum _R_BRACE {
	$$ = $2;
}
| _STAR _L_BRACE VAR _R_BRACE {
	$3->is_wildcards = 1;
	$$ = $3;
}
| _SQRT atom {
	struct optr_node *op = optr_alloc(OPTR_NODE_TOKEN);
	op->token = mbc2wc("√");
	optr_attach(op, $2);
	$$ = op;
}
| _L_PARENTHESIS sum _R_PARENTHESIS {
	$$ = $2;
}
| _L_BRACKET sum _R_BRACKET {
	$$ = $2;
}
| _L_BAR sum _R_BAR {
	struct optr_node *op = optr_alloc(OPTR_NODE_TOKEN);
	op->token = mbc2wc("ǁ");
	optr_attach(op, $2);
	$$ = op;
}
;
%%

int yyerror(void *scanner, struct optr_node **root, int *_, const char *msg)
{
	fprintf(stderr, "[Error] %s\n", msg);
	*root = NULL;
	return 0;
}

#include <locale.h>
wchar_t mbc2wc(const char *mb)
{
	static wchar_t retstr[2];
	setlocale(LC_ALL, "en_US.UTF-8");
	mbstowcs(retstr, mb, 2);

	//printf("mb=%s ==> 0x%x\n", mb, retstr[0]);
	return retstr[0];
}

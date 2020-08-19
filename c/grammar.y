%{

struct optr_node {
	int a;
};
%}

%union {
	struct optr_node *nd;
}

%destructor {
	if ($$) {
		$$ = NULL;
	}
} <nd>

%define parse.error verbose

%token _EOL
%token <nd> NUM
%token <nd> ADD
%token <nd> TIMES

%start doc
%type <nd> sum
%type <nd> product
%type <nd> factor
%type <nd> atom

%left NULL_REDUCE
%left ADD
%left TIMES

%%
doc: sum

sum: %prec NULL_REDUCE {
}
| product {
}
| sum ADD product {
}
;

product: factor {
}
| product factor {
}
| product TIMES factor {
}
;

factor: atom {
}
;

atom: NUM {
}
;
%%

int yyerror(const char *msg)
{
	fprintf(stderr, "%s\n", msg);
	return 0;
}

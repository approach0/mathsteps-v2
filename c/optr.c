#include <stdlib.h>
#include <stdio.h>
#include <locale.h>
#include <string.h>

#include "optr.h"

struct optr_node *optr_alloc(int type)
{
	struct optr_node *nd = malloc(sizeof(struct optr_node));
	nd->type = type;
	nd->sign = +1.f;
	nd->is_wildcards = 0;
	nd->pound_ID = 0;
	nd->n_children = 0;
	nd->n_wildcards_children = 0;
	return nd;
}

void optr_release(struct optr_node *root)
{
	if (root == NULL)
		return;

	for (int i = 0; i < root->n_children; i++) {
		struct optr_node *c = root->children[i];
		optr_release(c);
	}

	free(root);
}

struct optr_node *optr_attach(struct optr_node *f, struct optr_node *s)
{
	if (s == NULL)
		return f;

	if (f->n_children + 1 < MAX_OPTR_NUM_CHILDREN) {
		f->children[f->n_children++] = s;

		if (s->is_wildcards)
			f->n_wildcards_children += 1;
	} else {
		optr_release(s);
	}

	return f;
}

float optr_get_node_val(struct optr_node *nd)
{
	if (nd->type == OPTR_NODE_NUM)
		return nd->sign * nd->num;
	else
		return 0;
}

struct optr_node optr_gen_val_node(float val)
{
	struct optr_node ret;
	memset(&ret, 0, sizeof(ret));

	ret.type = OPTR_NODE_NUM;
	ret.sign = (val < 0) ? -1.f : 1.f;
	ret.num = (val < 0) ? -val : val;
	return ret;
}

static void __print_node(struct optr_node *nd)
{
	if (nd->sign < 0)
		printf(" -");

	#define W 4
	char    dst[W + 1] = {0};
	wchar_t src[2] = {0};

	switch (nd->type) {
	case OPTR_NODE_VAR:
		printf(" %c", nd->var);
		break;
	case OPTR_NODE_NUM:
		printf(" %g", nd->num);
		break;
	case OPTR_NODE_TOKEN:
		src[0] = nd->token;
		setlocale(LC_ALL, "en_US.UTF-8");
		wcstombs(dst, src, W);
		printf("`%s'", dst);
		break;
	default:
		fprintf(stderr, "invalid node type\n");
		abort();
	}

	if (nd->is_wildcards)
		printf(" (wildcards)");
	else if (nd->n_wildcards_children > 0)
		printf(" (has %d wildcards children)", nd->n_wildcards_children);

	if (nd->pound_ID)
		printf(" (pound sign #%d)", nd->pound_ID);

	printf("\n");
}

static void __optr_print(struct optr_node *nd, int level, int *depth_flags)
{
	enum {
		DEPTH_END,
		DEPTH_BEGIN,
		DEPTH_ALMOST_END
	};

	for (int i = 0; i < level; i++) {
		switch (depth_flags[i]) {
		case DEPTH_END:
			printf("    ");
			break;
		case DEPTH_BEGIN:
			if (i + 1 == level)
				printf(" ├──");
			else
				printf(" │  ");
			break;
		case DEPTH_ALMOST_END:
			printf(" └──");
			depth_flags[i] = DEPTH_END;
			break;
		default:
			fprintf(stderr, "invalid depth flag.\n");
			break;
		}
	}

	__print_node(nd);

	for (int i = 0; i < nd->n_children; i++) {
		struct optr_node *c = nd->children[i];

		if (i == nd->n_children - 1) {
			depth_flags[level] = DEPTH_ALMOST_END;
		} else if (i == 0) {
			depth_flags[level] = DEPTH_BEGIN;
		}

		__optr_print(c, level + 1, depth_flags);
	}
}

void optr_print(struct optr_node *root)
{
	int depth_flags[MAX_OPTR_PRINT_DEPTH] = {0};

	if (root == NULL) {
		printf("(empty optr)\n");
		return;
	}

	__optr_print(root, 0, depth_flags);
}

/*
 *  Pass grand-children to root if children and root have the same operator.
 *  Otherwise, attach children to root (only reduce signs).

 *      root (+)
 *    /   ^           <——-.
 *  ...  children (+)     |
 *        |               .
 *       grand-children _/
 */
struct optr_node *optr_pass_children(struct optr_node *rot, struct optr_node *sub)
{
	if (sub == NULL)
		return rot;

	if (rot->type == OPTR_NODE_TOKEN &&
		sub->type == OPTR_NODE_TOKEN &&
		rot->token == sub->token) {

		if (rot->token == TOK_HEX_TIMES)
			/* initialize by the sign of multiplication node bing destroyed */
			rot->sign *= sub->sign;

		for (int i = 0; i < sub->n_children; i++) {
			if (rot->n_children + 1 >= MAX_OPTR_NUM_CHILDREN)
				break;

			struct optr_node *grand = sub->children[i];
			switch (sub->token) {
			case TOK_HEX_ADD:
				/* distribute sign */
				grand->sign *= sub->sign;
				break;
			case TOK_HEX_TIMES:
				/* reduce sign */
				rot->sign *= grand->sign;
				grand->sign = 1.f;
				break;
			default:
				;
			}

			/* pass grand-child */
			optr_attach(rot, grand);
		}

		/* release single `sub' operator node */
		sub->n_children = 0;
		optr_release(sub);

	} else {
		/* pass child */
		if (rot->token == TOK_HEX_TIMES && sub->sign < 0) {
			rot->sign *= sub->sign;
			sub->sign = 1.f;
		}

		optr_attach(rot, sub);
	}

	return rot;
}

int need_inner_fence(struct optr_node *nd)
{
	if (nd->sign < 0 && nd->n_children > 1) {
		/* negative non-unary */
		if (nd->type == OPTR_NODE_TOKEN && (
			nd->token == TOK_HEX_TIMES ||
			nd->token == TOK_HEX_FRAC ||
			nd->token == TOK_HEX_SUP
		))
			return 0;
		else
			return 1;
	} else {
		return 0;
	}
}

int need_outter_fence(struct optr_node* nd, struct optr_node *parent)
{
	int ret = 0;
	if (parent == NULL)
		ret = -1;

	else if (IS_OF_OPERATOR(parent, TOK_HEX_ADD) && IS_OF_OPERATOR(nd, TOK_HEX_ADD))
		ret = 1;

	else if (
		IS_OF_OPERATOR(parent, TOK_HEX_FRAC) ||
		IS_OF_OPERATOR(parent, TOK_HEX_ABS) ||
		IS_OF_OPERATOR(parent, TOK_HEX_SQRT) ||
		IS_OF_OPERATOR(parent, TOK_HEX_EQ) ||
		IS_OF_OPERATOR(parent, TOK_HEX_ADD)
	)
		ret = -2;

	else if (
		IS_OF_OPERATOR(parent, TOK_HEX_SUP) &&
		IS_OF_OPERATOR(nd, TOK_HEX_SQRT)
	)
		ret = 2;

	else if (nd->sign > 0) {

		if (nd->n_children <= 1) /* unary */
			ret = -3;

		else if (IS_OF_OPERATOR(parent, TOK_HEX_SUP) && (
			IS_OF_OPERATOR(nd, TOK_HEX_FRAC) ||
			IS_OF_OPERATOR(nd, TOK_HEX_SUP)
		))
			ret = 3;

		else if (
			IS_OF_OPERATOR(nd, TOK_HEX_FRAC) ||
			IS_OF_OPERATOR(nd, TOK_HEX_SUP)
		)
			ret = -4;

		else if (IS_OF_OPERATOR(parent, TOK_HEX_TIMES) &&
			IS_OF_OPERATOR(nd, TOK_HEX_TIMES)
		)
			ret = -5;

		else
			ret = 4;

	} else {
		ret = 5;
	}

#if 0
	printf("need_outter_fence ?\n");
	__print_node(parent);
	__print_node(nd);
	printf("ret = %d!\n", ret);
#endif
	return (ret >= 0) ? 1 : 0;
}

static int __optr_write_tex(
	char* dest, struct optr_node* cur, struct optr_node *parent)
{
	wchar_t tok = cur->token;
	char inner_expr[MAX_TEX_LEN];
	char signed_expr[MAX_TEX_LEN];

	if (cur->type != OPTR_NODE_TOKEN) {
		/* terminal tokens */
		if (cur->is_wildcards) {
			/* wildcards */
			sprintf(inner_expr, "*{%c}", cur->var);
		} else if (cur->type == OPTR_NODE_NUM) {
			/* number */
			sprintf(inner_expr, "%g", cur->num);
		} else {
			/* variable */
			sprintf(inner_expr, "%c", cur->var);
		}

	} else if (tok == TOK_HEX_ADD || tok == TOK_HEX_TIMES) {
		/* commutative operators */
		char *p = inner_expr;
		for (int i = 0; i < cur->n_children; i++) {
			struct optr_node *operand = cur->children[i];
			char to_append[MAX_TEX_LEN];
			__optr_write_tex(to_append, operand, cur);

			if (i == 0) {
				p += sprintf(p, "%s", to_append);
			} else if (to_append[0] == '-') {
				p += sprintf(p, " - %s", to_append + 1);
			} else {
				if (tok == TOK_HEX_ADD)
					p += sprintf(p, " + %s", to_append);
				else
					p += sprintf(p, " \\times %s", to_append);
			}
		}

	} else {
		/* other operators */
		char op_expr[2][MAX_TEX_LEN];

		if (tok == TOK_HEX_EQ) {
			__optr_write_tex(op_expr[0], cur->children[0], cur);
			__optr_write_tex(op_expr[1], cur->children[1], cur);
			sprintf(inner_expr, "%s = %s", op_expr[0], op_expr[1]);

		} else if (tok == TOK_HEX_DIV) {
			__optr_write_tex(op_expr[0], cur->children[0], cur);
			__optr_write_tex(op_expr[1], cur->children[1], cur);
			sprintf(inner_expr, "%s \\div %s", op_expr[0], op_expr[1]);

		} else if (tok == TOK_HEX_SUP) {
			__optr_write_tex(op_expr[0], cur->children[0], cur);
			__optr_write_tex(op_expr[1], cur->children[1], cur);
			sprintf(inner_expr, "%s^{%s}", op_expr[0], op_expr[1]);

		} else if (tok == TOK_HEX_FRAC) {
			__optr_write_tex(op_expr[0], cur->children[0], cur);
			__optr_write_tex(op_expr[1], cur->children[1], cur);
			sprintf(inner_expr, "\\frac{%s}{%s}", op_expr[0], op_expr[1]);

		} else if (tok == TOK_HEX_SQRT) {
			__optr_write_tex(op_expr[0], cur->children[0], cur);
			sprintf(inner_expr, "\\sqrt{%s}", op_expr[0]);

		} else if (tok == TOK_HEX_ABS) {
			__optr_write_tex(op_expr[0], cur->children[0], cur);
			sprintf(inner_expr, "\\left| %s \\right|", op_expr[0]);

		} else {
			fprintf(stderr, "unexpected token: %u\n", (unsigned int)tok);
			abort();
		}
	}

	char *p = signed_expr;
	if (cur->sign < 0)
		p += sprintf(p, "-");

	if (need_inner_fence(cur))
		sprintf(p, "(%s)", inner_expr);
	else
		sprintf(p, "%s", inner_expr);

	if (need_outter_fence(cur, parent))
		sprintf(dest, "(%s)", signed_expr);
	else
		sprintf(dest, "%s", signed_expr);

	return 0;
}

int optr_write_tex(char* dest, struct optr_node* optr)
{
	return __optr_write_tex(dest, optr, NULL);
}

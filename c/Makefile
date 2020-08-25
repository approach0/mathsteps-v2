MHOOK_FLAGS := -Wl,--wrap,malloc -Wl,--wrap,free \
-Wl,--wrap,realloc -Wl,--wrap,calloc -Wl,--wrap,strdup

all:
	bison -v -d --report=itemset grammar.y -o y.tab.c
	flex lexer.l
	#gcc $(MHOOK_FLAGS) mhook.c optr.c parser.c y.tab.c lex.yy.c -lfl -o parser.out

	gcc -std=c11 -c mcts.c mhook.c optr.c axiom.c
	gcc -c parser.c y.tab.c lex.yy.c
	#gcc $(MHOOK_FLAGS) mhook.o optr.o -o optr.out

	gcc $(MHOOK_FLAGS) mhook.o mcts.o -lpthread -lm -latomic -o mcts.out

	gcc $(MHOOK_FLAGS) mhook.o optr.o y.tab.o lex.yy.o parser.o axiom.o -lfl -o axiom.out

clean:
	rm -f *.o *.out
	rm -f *.tab.[ch] lex.yy.[ch] *.dot y.output

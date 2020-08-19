MHOOK_FLAGS := -Wl,--wrap,malloc -Wl,--wrap,free \
-Wl,--wrap,realloc -Wl,--wrap,calloc -Wl,--wrap,strdup

all:
	bison -v -d --report=itemset grammar.y -o y.tab.c
	flex lexer.l
	gcc -std=c11 -c test.c mhook.c
	gcc $(MHOOK_FLAGS) mhook.o test.o -lpthread -lm -latomic

clean:
	rm -f *.o *.out
	rm -f *.tab.[ch] lex.yy.c *.dot y.output

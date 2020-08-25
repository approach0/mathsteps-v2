MHOOK_FLAGS := -Wl,--wrap,malloc -Wl,--wrap,free \
-Wl,--wrap,realloc -Wl,--wrap,calloc -Wl,--wrap,strdup

CC := gcc
CFLAGS := $(MHOOK_FLAGS)
LDFLAGS := -lfl -lpthread -lm -latomic

TEST_SRCS := $(wildcard test-*.c)
TEST_BINS := $(TEST_SRCS:.c=.out)

ALL_OBJS := mhook.o optr.o lex.yy.o y.tab.o parser.o axiom.o mcts.o
ALL_BINS := $(TEST_BINS)

all: $(ALL_OBJS) $(ALL_BINS)
	@echo 'Building finished.'

y.tab.c  y.tab.h:
	bison -v -d --report=itemset grammar.y -o y.tab.c

lex.yy.c  lex.yy.h:
	flex lexer.l

%.o: %.c y.tab.h lex.yy.h
	$(CC) -std=c11 -c $(CFLAGS) $(filter %.c, $^) -o $@

%.out: %.o
	$(CC) $(CFLAGS) $(LDFLAGS) $(ALL_OBJS) $(filter %.o, $^) -o $@

clean:
	rm -f *.o *.out
	rm -f *.tab.[ch] lex.yy.[ch] *.dot y.output

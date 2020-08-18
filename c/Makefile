MHOOK_FLAGS := -Wl,--wrap,malloc -Wl,--wrap,free \
-Wl,--wrap,realloc -Wl,--wrap,calloc -Wl,--wrap,strdup

all:
	gcc -std=c11 -c test.c mhook.c
	gcc $(MHOOK_FLAGS) mhook.o test.o -lpthread

clean:
	rm -f *.o *.out

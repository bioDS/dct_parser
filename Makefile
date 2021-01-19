tree.o: tree.c
	gcc -fPIC -Wall -c -g tree.c
	gcc -shared -o tree.so tree.o

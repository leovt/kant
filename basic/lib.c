#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int eq_str(char* a, char* b){
	return strcmp(a, b) == 0;
}

char* cat_str(char* a, char* b){
	int alen = strlen(a);
	int blen = strlen(b);
	char *s = malloc(alen+blen+1);
	memcpy(s, a, alen);
	memcpy(s+alen, b, blen);
	s[alen+blen]=0;
	return s;
}

void printi(int i){
	printf("%d", i);
}

void prints(char* s){
	printf("%s", s);
}

int inputi(){
	char s[150];
	gets(s);
	return atoi(s);
}

char* inputs(){
	char* s = (char*) malloc(150);
	gets(s);
	return s;
}

#include <stdlib.h>
#include <stdio.h>
#include "opcodes.h"
#include "bc_string.h"

typedef struct BCHead{
	unsigned short int code_length;
	unsigned short int nb_int;
	unsigned short int nb_str;
	unsigned short int nb_const_int;
	unsigned short int nb_const_str;
} BCHead;

void disassemble(unsigned char* code, unsigned short int code_length)
{
	for (int i=0; i<code_length; i++){
		if (code[i] >= sizeof(opnames) / sizeof(opnames[0]))
			exit(EXIT_FAILURE);
		if (code[i] > op_hasarg){
			unsigned short int arg = code[i+1] + 256*code[i+2];
			if (i+2 < code_length){
				printf("%3d: %s %hu\n", i, opnames[code[i]], arg);
			}
			else {
				exit(EXIT_FAILURE);
			}
			i += 2;
		}
		else{
			printf("%3d: %s\n", i, opnames[code[i]]);
		}
	}
}

void execute(BCHead *head, int* const_int, BCString** const_str, unsigned char *code){
	unsigned int ip = 0;
	int *istack = malloc(100*sizeof(int)); // TODO: magic stack space
	BCString **sstack = malloc(100*sizeof(BCString*));
	int *integers = malloc(head->nb_int * sizeof(int));
	BCString **strings = malloc(head->nb_str * sizeof(BCString*));
	int *itos = istack;
	BCString **stos = sstack;

	for(;;){
		unsigned char op = code[ip];
		unsigned int arg = 0;
		//puts(opnames[op]);
		if (op>op_hasarg){
			arg = code[ip+1] + 256*code[ip+2];
			ip += 3;
		}else{
			ip += 1;
		}
		int itmp;
		BCString *stmp;
		char buf[20];
		switch(op){
		case op_end:
			goto cleanup;
		case op_load_int:
			*itos = integers[arg];
			itos++;
			break;
		case op_load_str:
			*stos = strings[arg];
			stos++;
			break;
		case op_load_const_int:
			*itos = const_int[arg];
			itos++;
			break;
		case op_load_const_str:
			*stos = const_str[arg];
			stos++;
			break;
		case op_input_int:
			fgets(buf, 20, stdin);
			buf[19] = '\0';
			integers[arg] = strtol(buf, 0, 10);
			break;
		case op_input_str:
			strings[arg] = input_str(stdin);
			break;
		case op_save_int:
			itos--;
			integers[arg] = *itos;
			break;
		case op_save_str:
			stos--;
			strings[arg] = *stos;
			break;
		case op_print_str:
			stos--;
			//BCString *str = *stos;
			printf("%s ", (*stos)->data);
			break;
		case op_print_int:
			itos--;
			printf("%d ", *itos);
			break;
		case op_println:
			puts("");
			break;
		case op_add_int:
			itos--;
			itmp = *itos;
			itos--;
			*itos = *itos + itmp;
			itos++;
			break;
		case op_sub_int:
			itos--;
			itmp = *itos;
			itos--;
			*itos = *itos - itmp;
			itos++;
			break;
		case op_mul_int:
			itos--;
			itmp = *itos;
			itos--;
			*itos = *itos * itmp;
			itos++;
			break;
		case op_div_int:
			itos--;
			itmp = *itos;
			itos--;
			*itos = *itos / itmp;
			itos++;
			break;
		case op_eq_int:
			itos--;
			itmp = *itos;
			itos--;
			*itos = *itos == itmp;
			itos++;
			break;
		case op_cat_str:
			stos--;
			stmp = *stos;
			stos--;
			*stos = cat_str(*stos, stmp);
			stos++;
			break;
		case op_eq_str:
			stos--;
			stmp = *stos;
			stos--;
			*itos = eq_str(*stos, stmp);
			itos++;
			break;
		case op_jmp:
			ip = arg;
			break;
		case op_jmpz:
			itos--;
			if(*itos == 0)
				ip = arg;
			break;
		default:
			fprintf(stderr, "\nError: unknown opcode %s.\n", opnames[op]);
			exit(EXIT_FAILURE);
		}
	}

cleanup:
	free(integers);
	for(int i=0; i<head->nb_str; i++)
		free(strings[i]);
	for(;stos > sstack;){
		stos--;
		free(*stos);
	}
}

int main(int argc, char* argv[]){
	if (argc != 2){
		fputs("Usage: basic_vm FILENAME", stderr);
		return EXIT_FAILURE;
	}

	FILE* f = fopen(argv[1], "rb");
	struct BCHead head;
	fread(&head, sizeof(head), 1, f);
	printf("code_length = %hu\n", head.code_length);
	printf("nb_int = %hu\n", head.nb_int);
	printf("nb_str = %hu\n", head.nb_str);
	printf("nb_const_int = %hu\n", head.nb_const_int);
	printf("nb_const_str = %hu\n", head.nb_const_str);

	int *const_int = malloc(head.nb_const_int * sizeof(int));
	fread(const_int, sizeof(int), head.nb_const_int, f);


	BCString **const_str = malloc(head.nb_const_str * sizeof(BCString*));
	unsigned char *code = malloc(head.code_length);

	for (int i=0; i<head.nb_const_str; i++){
		unsigned int length = 0;
		fread(&length, sizeof(length), 1, f);
		const_str[i] = alloc_str(length);
		const_str[i]->length = length;
		fread(&const_str[i]->data, 1, length, f);
		const_str[i]->data[length] = '\0';
	}
	fread(code, head.code_length, 1, f);

	for (int i=0; i<head.nb_const_int; i++){
		printf("const_int[%d] = %d\n", i, const_int[i]);
	}
	for (int i=0; i<head.nb_const_str; i++){
		printf("const_str[%d] = %s\n", i, const_str[i]->data);
	}

	disassemble(code, head.code_length);
	execute(&head, const_int, const_str, code);


	for (int i=0; i<head.nb_const_str; i++){
		free(const_str[i]);
	}
	free(const_str);
	free(const_int);
	fclose(f);
}


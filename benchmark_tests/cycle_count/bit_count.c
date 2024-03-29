// C program to Count set 
// bits in an integer 
#include <stdio.h> 

unsigned long read_cycles(void)
{
  unsigned long cycles;
  asm volatile ("rdcycle %0" : "=r" (cycles));
  return cycles;
}

/* Function to get no of set bits in binary 
representation of positive integer n */
unsigned int countSetBits(unsigned int n) 
{ 
	unsigned int count = 0; 
	while (n) { 
		count += n & 1; 
		n >>= 1; 
	} 
	return count; 
} 

/* Program to test function countSetBits */
int main() 
{
	int cycle_count = read_cycles();
	int i = 923472389;
	printf("Number of bits = %d\n", countSetBits(i));
	cycle_count = read_cycles() - cycle_count;
	printf("cycle_count=%ld\n", cycle_count);
	return 0; 
}

#include<stdio.h>    
#include <time.h>

int main()    
{
	clock_t t;
        t = clock();

	int n1=0,n2=1,n3,i;    
	int number = 15;
	printf("\nFibonacci series of %d: ", number);
	printf("%d %d",n1,n2);//printing 0 and 1    
	for(i=2;i<number;++i)//loop starts from 2 because 0 and 1 are already printed    
	{    
		n3=n1+n2;    
		printf(" %d",n3);    
		n1=n2;    
		n2=n3;    
	}

	t = clock() - t;
        double time_taken = ((double)t)/CLOCKS_PER_SEC; // in seconds
        printf("Total Execution time: %f seconds\n", time_taken);	
	return 0;  
 }

#include<stdio.h>
#include <time.h>

void printFibonacci(int n){    
    static int n1=0,n2=1,n3;    
    if(n>0){    
         n3 = n1 + n2;    
         n1 = n2;    
         n2 = n3;    
         printf("%d ",n3);    
         printFibonacci(n-1);    
    }    
}    
int main(){    
    clock_t t;
     t = clock();

    int n = 15;
    printf("Fibonacci Series of number %d: ", n);    
    printf("%d %d ",0,1);    
    printFibonacci(n-2);//n-2 because 2 numbers are already printed    

    t = clock() - t;
    double time_taken = ((double)t)/CLOCKS_PER_SEC; // in seconds
    printf("Total Execution time: %f seconds\n", time_taken);
    return 0;  
 }    

#include<stdio.h>
#include <time.h>

int main()    
{
    clock_t t;
    t = clock();	

    int r,sum=0,temp;    
    int n = 15;
    printf("\nNumber= %d\n", n);
    temp=n;    
    while(n>0)    
    {    
    	r=n%10;    
        sum=(sum*10)+r;    
        n=n/10;    
    }    
    if(temp==sum)    
        printf("palindrome number \n");    
    else    
        printf("not palindrome\n");   

    t = clock() - t;
    double time_taken = ((double)t)/CLOCKS_PER_SEC; // in seconds
    printf("Total Execution time: %f seconds\n", time_taken);
    return 0;  
}

#include <stdio.h> 
#include <stdlib.h> 
#include <unistd.h> 
#include <string.h> 
#include <sys/types.h> 
#include <sys/socket.h> 
#include <arpa/inet.h> 
#include <netinet/in.h> 
  
#define PORT 8100
#define MAXLINE 1024 
  
// Driver code 
int main() { 
    int sockfd; 
    char buffer[MAXLINE];
    struct sockaddr_in servaddr, cliaddr; 
      
    // Creating socket file descriptor 
    if ( (sockfd = socket(AF_INET, SOCK_DGRAM, 0)) < 0 ) { 
        perror("socket creation failed"); 
        exit(EXIT_FAILURE); 
    } 
      
    memset(&servaddr, 0, sizeof(servaddr)); 
    memset(&cliaddr, 0, sizeof(cliaddr)); 
      
    // Filling server information 
    servaddr.sin_family    = AF_INET; // IPv4 
    servaddr.sin_addr.s_addr = INADDR_ANY; 
    servaddr.sin_port = htons(PORT); 
      
    // Bind the socket with the server address 
    if ( bind(sockfd, (const struct sockaddr *)&servaddr,  
            sizeof(servaddr)) < 0 ) 
    { 
        perror("bind failed");
        exit(EXIT_FAILURE); 
    }
    printf("\nNow accepting UDP Messages on Port : %d\n",PORT) ;
      
    int len, n;
    while(1)
    {
        n = recvfrom(sockfd, (char *)buffer, MAXLINE, MSG_WAITALL, ( struct sockaddr *) &cliaddr, &len); 
        buffer[n] = '\0'; 
        printf("%s\n", buffer);
        int choice = buffer[32];
        switch(choice){
                    
            case 50: if(buffer[42]==49)
                        printf("Bulb Status changed to : ON\n");
                     else printf("Bulb Status changed to : OFF\n");
                        break;
            case 51: if(buffer[42]==49)
                        printf("Thermostat Status changed to : ON\n");
                     else printf("Thermostat Status changed to : OFF\n");
                        break;
            case 52: if(buffer[42]==49) printf("Door Status changed to OPEN");
                     else printf("Door Status Changed to CLOSED");
                        break;
            default: printf("Command Not recognized. Please check the device type and try again.");
        }
    }
      
    return 0;
}
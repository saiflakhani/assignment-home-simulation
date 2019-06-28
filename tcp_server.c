#include <netdb.h>

#include <netinet/in.h>

#include <stdlib.h>

#include <string.h>

#include <sys/socket.h>

#include <sys/types.h>

#include <pthread.h>


#define MAX 1024
#define PORT_TCP 8099
#define SA struct sockaddr

// Function designed for chat between client and server. 
void tcp_func(int sockfd) {
    char buff[MAX];
    int n;
    // infinite loop for chat 
    bzero(buff, MAX);

    // read the message from client and copy it in buffer 
    read(sockfd, buff, sizeof(buff));
    // print buffer which contains the client contents 
    printf("%s\n", buff);
    int choice = buff[32];
    switch(choice){
                
        case 50: if(buff[42]==49)
                    printf("Bulb Status changed to : ON\n");
                 else printf("Bulb Status changed to : OFF\n");
                    break;
        case 51: if(buff[42]==49)
                    printf("Thermostat Status changed to : ON\n");
                 else printf("Thermostat Status changed to : OFF\n");
                    break;
        case 52: if(buff[42]==49) printf("Door Status changed to OPEN\n");
                 else printf("Door Status Changed to CLOSED\n");
                    break;
        default: printf("Command Not recognized. Please check the device type and try again.\n");
    }

    char ack_message[3] = "ACK";
    write(sockfd, ack_message, sizeof(ack_message));
    printf("Sent Acknowledgement\n");

    bzero(buff, MAX);

}
void * tcp_handler(void * args) {
    int sockfd, connfd, len;
    struct sockaddr_in servaddr, cli;
    // socket create and verification 
    sockfd = socket(AF_INET, SOCK_STREAM, 0);
    if (sockfd == -1) {
        printf("socket creation failed...\n");
        exit(0);
    } else
        printf("Socket successfully created..\n");
    bzero( & servaddr, sizeof(servaddr));
    // assign IP, PORT 
    servaddr.sin_family = AF_INET;
    servaddr.sin_addr.s_addr = htonl(INADDR_ANY);
    servaddr.sin_port = htons(PORT_TCP);

    // Binding newly created socket to given IP and verification 
    if ((bind(sockfd, (SA * ) & servaddr, sizeof(servaddr))) != 0) {
        printf("socket bind failed...\nPlease try a different Port.\n");
        exit(0);
    } else
        printf("Socket successfully bound..\n");

    // Now server is ready to listen and verification 
    while (1) {
        if ((listen(sockfd, 5)) != 0) {
            printf("Listen failed...\n");
            exit(0);
        } else
            printf("\nTCP Server listening on Port : %d\n",PORT_TCP);
        len = sizeof(cli);

        // Accept the data packet from client and verification 
        connfd = accept(sockfd, (SA * ) & cli, & len);
        if (connfd < 0) {
            printf("Server accept failed...\n");
            exit(0);
        } else
            printf("\nServer has accepted a TCP client...\n");

        // Function for chatting between client and server 
        tcp_func(connfd);
    }

    // After chatting close the socket 
    close(sockfd);
}

// Driver function 
int main() {
    pthread_t tcp_thread, udp_thread;
    int ret;
    ret = pthread_create( & tcp_thread, NULL, & tcp_handler, NULL);

    if (ret == 0) {
        printf("TCP Thread created successfully.\n");
    } else {
        printf("TCP Thread not created.\n");
        return 0; /*return from main*/
    }
    pthread_join(tcp_thread, NULL);
}
/* 	This program opens a connection to given DNS name (or IP address)
	and service (or port), writes a string to the socket, and reads a string back.

	The tcp_connect function is taken and modified from W.R. Stevens'
	"Unix Network Programming" book

	To compile: gcc simple-client.c
	To run: ./a.out <name/address> <service/port> <string>
*/

#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <stdlib.h>
#include <errno.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netdb.h>
#include <arpa/inet.h>

#define BUFLEN 160


/*  Resolves given name to IP address and tries to connect it. Note that name may result
    in multiple IPv4 or IPv6 address entries. If there are multiple entries, try them
    one at time until one succeeds.

    Parameters:
      * <host> is DNS name or IP address as a string
      * <serv> is service name or port number as a string

    Returns socket descriptor, or -1 if connection fails
*/
int tcp_connect(const char *host, const char *serv)
{
	int sockfd, n;
	struct addrinfo hints, *res, *ressave;

	bzero(&hints, sizeof(struct addrinfo));
	hints.ai_family = AF_UNSPEC;  // Either IPv4 or IPv6 are accepted
	hints.ai_socktype = SOCK_STREAM;  // We are only interested in stream sockets (TCP)

	// Try to resolv name into IP address and service into port.
	if ( (n = getaddrinfo(host, serv, &hints, &res)) != 0) {
		fprintf(stderr, "Failure in name resolution\n");
		return -1;
	}
	ressave = res; // so that we can release the memory afterwards

	do {
		sockfd = socket(res->ai_family, res->ai_socktype,
						res->ai_protocol);
		if (sockfd < 0)
				continue; // socket creation failed, try next address

		// Trying to connect socket address pointed by <res>
		if (connect(sockfd, res->ai_addr, res->ai_addrlen) == 0)
				break;          /* success */

		close(sockfd); // connect attempt failed, try next address
	} while ( (res = res->ai_next) != NULL);  // Find next address next in linked list

	if (res == NULL) {
		fprintf(stderr, "None of the addresses succeeded\n");
		sockfd = -1;
	} else {
		printf("Connection worked\n");
	}
	freeaddrinfo(ressave);
	return(sockfd);
}

	
int main(int argc, char *argv[])
{
	int sfd;

	if (argc < 3) {
		fprintf(stderr, "arguments: <host> <port> <message>\n");
		exit(EXIT_FAILURE);
	}

	if ((sfd = tcp_connect(argv[1], argv[2])) < 0) {
		perror("tcp_connect");
		exit(EXIT_FAILURE);
	}

	// Write string given in command line to socket
	char buf[BUFLEN];
	strncpy(buf, argv[3], BUFLEN - 1);
	buf[BUFLEN - 1] = 0;
	int n = write(sfd, buf, strlen(buf));
	if (n < 0) {
		perror("write");
	} else if (n < strlen(buf)) {
		printf("Not everything was written\n");
	}

	// Read from socket and print it to stdout
	n = read(sfd, buf, BUFLEN-1);
	if (n < 0) {
		perror("read");
	}
	buf[n] = 0;
	fputs(buf, stdout);
}

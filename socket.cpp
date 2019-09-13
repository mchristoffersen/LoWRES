#include <sys/socket.h> 
#include <arpa/inet.h>
#include <boost/date_time.hpp>
#include <uhd/usrp/multi_usrp.hpp>
#include <boost/algorithm/string.hpp>
#include <boost/filesystem.hpp>
#include <boost/format.hpp>
#include <boost/program_options.hpp>
#include <iostream>
#include <time.h>
#include "util.h"
#include "socket.h"

int initSocket() {
    int sock = 0, valread; 
    struct sockaddr_in serv_addr; 
    if ((sock = socket(AF_INET, SOCK_STREAM, 0)) < 0) {}
    serv_addr.sin_family = AF_INET; 
    serv_addr.sin_port = htons(1999); 
       
    // Convert IPv4 and IPv6 addresses from text to binary form 
    if(inet_pton(AF_INET, "127.0.0.1", &serv_addr.sin_addr)<=0)  
    {
        std::cout << "Conversion issue" << std::endl;
    } 
   
    if (connect(sock, (struct sockaddr *)&serv_addr, sizeof(serv_addr)) < 0) 
    {
        std::cout << "Connection issue" << std::endl;
    } 
    return sock;
}  

int guiSend(int sockfd, float *data, gpsData fix, int traceLen) {
    //FILE* recvDump;
    //recvDump = fopen("dumpFile.dat", "w");
    //if (recvDump != NULL) {
    //    fwrite(data, sizeof(float), traceLen, recvDump);
    //    fclose(recvDump);
    //}
    send(sockfd, data, traceLen*4, 0);
    send(sockfd, &fix, sizeof(gpsData), 0);

    return 0;
}

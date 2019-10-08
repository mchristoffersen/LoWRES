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

int initSocket(std::string ip) {
    int sock = 0, valread; 
    struct sockaddr_in serv_addr; 
    if ((sock = socket(AF_INET, SOCK_STREAM, 0)) < 0) {
        std::cout << "Socket creation issue" << std::endl;
    }
    serv_addr.sin_family = AF_INET; 
    serv_addr.sin_port = htons(1999); 

    // Convert IPv4 and IPv6 addresses from text to binary form 
    if(inet_pton(AF_INET, ip.c_str(), &serv_addr.sin_addr)<=0)  
    {
        std::cout << "IP conversion issue" << std::endl;
    } 

    if (connect(sock, (struct sockaddr *)&serv_addr, sizeof(serv_addr)) < 0) 
    {
        std::cout << "Connection issue" << std::endl;
    } 

    struct timeval timeout;
    timeout.tv_sec = 0;
    timeout.tv_usec = 500;

    if (setsockopt(sock, SOL_SOCKET, SO_SNDTIMEO, (char *)&timeout, sizeof(timeout)) < 0) {
        std::cout << "Couldn't set socket xmit timeout" << std::endl;
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
    //std::cout << "Pre send\n";
    //std::cout << sizeof(gpsData) << std::endl;
    fix.sanity = 0xBAADCAFEDEADBEEF;
    send(sockfd, &fix, sizeof(gpsData), 0);
    send(sockfd, data, traceLen*4, 0);
    //std::cout << "Post send\n";

    return 0;
}

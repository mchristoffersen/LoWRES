#pragma once

int initSocket(std::string ip);

int guiSend(int sockfd, float *data, gpsData fix, int traceLen);


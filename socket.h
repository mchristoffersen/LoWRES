#pragma once

int initSocket();

int guiSend(int sockfd, float *data, gpsData fix, int traceLen);


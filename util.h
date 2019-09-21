#pragma once

struct gpsData {
    double sanity;
    int64_t fullSec;
    double fracsec;
    unsigned long long int ntrace;
    float lat;
    float lon;
    float alt;
    float dop;
    unsigned int nsat;
};

gpsData parseNMEA(std::string nmea);

int saveTrace(FILE* dataFile, 
    float *data, gpsData fix, uhd::time_spec_t time, int traceLen);

int traceHandler(uhd::usrp::multi_usrp::sptr usrp, 
                  FILE* dataFile, int sockfd, int* p, int spt);

void generate_out_filename(
    char *filename, uhd::time_spec_t begin);

std::vector<std::complex<float>> generateChirp(
    float amp, int cf, int bw, float len, int fs, int prf);

std::vector<std::complex<float>> generateGate(
    float len, int fs, int prf);

// Generate and save header
int saveHdr(FILE* dataFile, double chirpBW, double chirpCF,
    double chirpLen, double chirpAmp, double prf, double traceLen,
    double rxFs, unsigned int stack, uhd::time_spec_t begin);

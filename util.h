#pragma once

struct gpsData {
    int64_t fullSec;
    double fracsec;
    float lat;
    float lon;
    float alt;
    float dop;
};

gpsData parseNMEA(std::string nmea);

gpsData saveTrace(FILE* dataFile, 
    float *data, std::string nmea, uhd::time_spec_t time, int traceLen);

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

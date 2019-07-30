#pragma once

std::string generate_out_filename(
    uhd::time_spec_t begin);

std::vector<std::complex<float>> generateChirp(
    float amp, int cf, int bw, float len, int fs, int prf);

std::vector<std::complex<float>> generateGate(
    float len, int fs, int prf);

// Generate and save header
int saveHdr(FILE* dataFile, double chirpBW, double chirpCF,
    double chirpLen, double chirpAmp, double prf, double traceLen,
    double rxFs, unsigned int stack);

#include <uhd/usrp/multi_usrp.hpp>
#include <boost/algorithm/string.hpp>
#include <boost/filesystem.hpp>
#include <boost/format.hpp>
#include <boost/program_options.hpp>
#include <iostream>
#include "util.h"

/***********************************************************************
 * Utilities
 **********************************************************************/
//! Generate filename from uhd::time_spec_t
std::string generate_out_filename(
    uhd::time_spec_t begin)
{
    /* Generate the filename... */
    return "datafile.dat";
}

std::vector<std::complex<float>> generateChirp(
    float amp, int cf, int bw, float len, int fs, int prf) 
{
    /* Function to generate a chirp
     * amp - amplitude of the chirp (integer dBm)
     * cf - center frequency of the chirp (int Hz)
     * bw - bandwidth of the chirp (integer percent of cf)
     * len - length of the chirp (microseconds)
     * fs - sampling frequency at which to generate chirp (int Hz)
     */

    float sample;
    float t;
    double pi = acos(-1.0);
    int nsamp = len*fs; // samples

    bw = bw/100;
    double initFreq = cf-((cf * bw) / 2); // Hz
    double freqSlope = (cf * bw) / len; // Hz/sec

    std::vector<std::complex<float>> chirp(nsamp);//fs/prf);

    for (size_t i = 0; i < nsamp; i++) {
      t = ((float)i) / fs;
      sample = pi/2 + 2*pi*(initFreq + (freqSlope/2) * t) * t;
      chirp[i] = std::complex<float>(amp*cos(sample), amp*sin(sample));
      //std::cout << chirp[i].real() << "," << chirp[i].imag() << std::endl;
    }

    //for (size_t i = nsamp; i < fs/prf; i++) {
    //  chirp[i] = 0;
    //}

    return chirp;
}

std::vector<std::complex<float>> generateGate(
    float len, int fs, int prf) 
{
    /* Function to generate a gate signal (square wave)
     * len - length of the chirp (microseconds)
     * fs - sampling frequency at which to generate chirp (int Hz)
     * prf - pulse repetition frequency
     */

    int nsamp = len*fs; // samples


    std::vector<std::complex<float>> gate(nsamp);//fs/prf);

    for (size_t i = 0; i < nsamp; i++) {
      gate[i] = std::complex<float>(0.3,0); // <0 dBm chirp
    }

    //for (size_t i = nsamp; i < fs/prf; i++) {
    //  gate[i] = std::complex<float>(0,0);
    //}

    return gate;
}


// Generate and save header
int saveHdr(FILE* dataFile, double chirpBW, double chirpCF,
    double chirpLen, double chirpAmp, double prf, double traceLen,
    double rxFs, unsigned int stack) {

    /* Function to write the data file header, includes information
       about chirp parameters and ...

       This makes the assumption that float = IEE754 binary32 and
       that double = IEEE754 binary64. This is not guaranteed by
       C++, but is true on x86-64 processors. 
    */

    // File Version 1.0
    float version = 1.0;

    char *header = (char*)malloc(68);
    
    // Magic bytes
    header[0] = 0xD0;
    header[1] = 0xD0;
    header[2] = 0xBE;
    header[3] = 0xEF;

    // Version num
    memcpy(header+4, &version, 4);

    // Chirp params
    memcpy(header+8, &chirpCF, 8);
    memcpy(header+16, &chirpBW, 8);
    memcpy(header+24, &chirpLen, 8);
    memcpy(header+32, &chirpAmp, 8);
    memcpy(header+40, &prf, 8);
    memcpy(header+48, &traceLen, 8);
    
    memcpy(header+56, &rxFs, 8);
    memcpy(header+64, &stack, 4);    

    // Initial time?
    // Notes?

    fwrite(header, 1, 68, dataFile);

    return 0;
}

// Save a trace
int saveTrace(FILE* dataFile, float *data, std::string nmea, int traceLen) {
  
    //Get todays date
    // std::stringstream date;
    // if (gmtm->tm_mday < 10) {
    //     date << '0';
    // }
    // date << gmtm->tm_mday << ':';
    // if (gmtm->tm_mon + 1 < 10) {
    //     date << '0';
    // }
    // date << gmtm->tm_mon + 1 << ':'
    //      << gmtm->tm_year + 1900 << '-';
    
    
    std::string temp;
    int sectStrt = 0;
    int cnt = 0;
    float lat = 0;
    float lon = 0;

    for (int j = 0; j < nmea.length(); ++j) {
        if (nmea[j] == ',') {
            if (cnt == 1) {
                temp = nmea.substr(sectStrt, j - sectStrt);
                if (temp.length() > 15) {
                    temp.erase(15, std::string::npos);
                }
                else {
                    while (temp.length() < 15) {
                        temp.append("0");
                    }
                }
                fwrite(temp.c_str(), sizeof(char), 15, dataFile);
            }
            else if (cnt == 2) {
                lat = stof(nmea.substr(sectStrt, j - sectStrt));
            }
            else if (cnt == 3) {
                if (nmea[j - 1] == 'S') {
                    lat = -lat;
                }
                fwrite(&lat, sizeof(float), 1, dataFile);
            }
            else if (cnt == 4) {
                lon = stof(nmea.substr(sectStrt, j - sectStrt));
            }
            else if (cnt == 5) {
                if (nmea[j-1] == 'W') {
                    lon = -lon;
                }
                fwrite(&lon, sizeof(float), 1, dataFile);
            }
            else if (cnt == 7) {
                int sats = stoi(nmea.substr(sectStrt, j - sectStrt));
                fwrite(&sats, sizeof(int), 1, dataFile);
            }
            else if (cnt == 9) {
                float altitude = stof(nmea.substr(sectStrt, j - sectStrt));
                fwrite(&altitude, sizeof(float), 1, dataFile);
            }
            ++cnt;
            sectStrt = j + 1;
        }
    }
    fwrite(data, sizeof(float), traceLen, dataFile);

    return 0;
}

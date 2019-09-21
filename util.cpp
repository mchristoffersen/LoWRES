#include <uhd/utils/thread.hpp>
#include <boost/date_time.hpp>
#include <uhd/usrp/multi_usrp.hpp>
#include <boost/algorithm/string.hpp>
#include <boost/filesystem.hpp>
#include <boost/format.hpp>
#include <boost/program_options.hpp>
#include <iostream>
#include <time.h>
#include "util.h"
#include "signal.h"
#include "socket.h"

/***********************************************************************
 * Utilities
 **********************************************************************/
//! Generate filename from uhd::time_spec_t
void generate_out_filename(
    char *filename, uhd::time_spec_t begin)
{
    // Generates a 19 character filename:
    // yyyymmdd-hhmmss.dat
    time_t timeval = begin.get_full_secs();
    timeval += begin.get_frac_secs();
    tm *utc = gmtime(&timeval);

    snprintf(filename, 20, "%4i%02i%02i-%02i%02i%02i.dat",
                utc->tm_year+1900, utc->tm_mon+1, utc->tm_mday,
                utc->tm_hour, utc->tm_min, utc->tm_sec);
 
    //std::cout << asctime(gmtime(&timeval)) << std::endl;
    //std::cout << fix.lat << "," << fix.lon << "," << fix.alt << std::endl;

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

    int pad = 30;
    bw = bw/100;
    double initFreq = cf-((cf * bw) / 2); // Hz
    double freqSlope = (cf * bw) / len; // Hz/sec

    std::vector<std::complex<float>> chirp(nsamp + pad, 0);

    for (size_t i = 0; i < nsamp; i++) {
      t = ((float)i) / fs;
      sample = -pi/2 + 2*pi*(initFreq + (freqSlope/2) * t) * t;
      chirp[i] = std::complex<float>(amp*cos(sample), amp*sin(sample));
      //std::cout << chirp[i].real() << "," << chirp[i].imag() << std::endl;
    }

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

int traceHandler(uhd::usrp::multi_usrp::sptr usrp, 
                  FILE* dataFile, int sockfd, int* p, int spt) {
    //uhd::set_thread_priority_safe(.9, true);
    gpsData fix;
    std::string nmea;
    uhd::time_spec_t time;
    size_t rb = 0;
    float* trace = (float*)malloc(spt*sizeof(float));
    unsigned long long int ntrace;

    while (not stop_signal_called) {
        nmea = usrp->get_mboard_sensor("gps_gpgga").value;
        fix = parseNMEA(nmea);
        rb = read(p[0], &time, sizeof(uhd::time_spec_t));
        if(rb != sizeof(uhd::time_spec_t)) {
            std::cout << "Failure reading time spec\n";
        }
        rb = read(p[0], trace, spt*sizeof(float));
        if(rb != spt*sizeof(float)) {
            std::cout << "Failure reading data\n";
        }
        rb = read(p[0], &ntrace, sizeof(unsigned long long int));
        if(rb != sizeof(unsigned long long int)) {
            std::cout << "Failure reading ntrace\n";
        }

        fix.ntrace = ntrace;

        saveTrace(dataFile, trace, fix, time, spt);
        guiSend(sockfd, trace, fix, spt);
    }
    return 0;
}
    


// Generate and save header
int saveHdr(FILE* dataFile, double chirpBW, double chirpCF,
    double chirpLen, double chirpAmp, double prf, double traceLen,
    double rxFs, unsigned int stack, uhd::time_spec_t begin) {

    /* Function to write the data file header, includes information
       about chirp parameters and ...

    */

    //time_t timeval = time.get_full_secs();
    //timeval += time.get_frac_secs();
    //std::cout << asctime(gmtime(&timeval)) << std::endl;
    //std::cout << fix.lat << "," << fix.lon << "," << fix.alt << std::endl;


    // File Version 1.0
    float version = 1.0;

    size_t size = 7*sizeof(double) + 2*sizeof(float) + 4;

    char *header = (char*)malloc(size);
    
    // Magic bytes
    header[0] = 0xD0;
    header[1] = 0xD0;
    header[2] = 0xBE;
    header[3] = 0xEF;

    // Version num
    memcpy(header+4, &version, sizeof(float));

    // Chirp params
    memcpy(header+8, &chirpCF, sizeof(double));
    memcpy(header+16, &chirpBW, sizeof(double));
    memcpy(header+24, &chirpLen, sizeof(double));
    memcpy(header+32, &chirpAmp, sizeof(double));
    memcpy(header+40, &prf, sizeof(double));
    memcpy(header+48, &traceLen, sizeof(double));
    
    memcpy(header+56, &rxFs, sizeof(double));
    memcpy(header+64, &stack, sizeof(float));    

    // Initial time?
    // Notes?
    fwrite(header, size, 1, dataFile);

    return 0;
}

// Save a trace
int saveTrace(FILE* dataFile, float *data, gpsData fix, uhd::time_spec_t time, int traceLen) {

    //gpsData fix = parseNMEA(nmea);

    fix.fullSec = time.get_full_secs();
    fix.fracsec = time.get_frac_secs();

    fwrite(&fix, sizeof(fix), 1, dataFile);
    fwrite(data, sizeof(float), traceLen, dataFile);
    
    return 0;
}

// Parse GGA NMEA strings for lat lon elev
gpsData parseNMEA(std::string nmea) {

    gpsData fix;

    char *tloc;    
    char *nmea_c = (char*)malloc(nmea.length()+1);
    std::strcpy(nmea_c, nmea.c_str());

    // Skip type and time
    strtok(nmea_c, ",");
    strtok(NULL, ",");

    // lat and lon
    tloc = strtok(NULL, ",");
    fix.lat = atof(tloc+2)/60;
    tloc[2] = 0;
    fix.lat += atof(tloc);
    if(strtok(NULL, ",")[0] == 'S') {
        fix.lat = -fix.lat;
    }

    tloc = strtok(NULL, ",");
    fix.lon = atof(tloc+3)/60;
    tloc[3] = 0;
    fix.lon += atof(tloc);
    if(strtok(NULL, ",")[0] == 'W') {
        fix.lon = -fix.lon;
    }

    // Skip quality
    strtok(NULL, ",");

    // Num sats
    fix.nsat = atoi(strtok(NULL, ","));

    // Dilution of precision
    fix.dop = atof(strtok(NULL, ","));

    // Altitude
    fix.alt = atof(strtok(NULL, ","));

    free(nmea_c);
    return fix;
}

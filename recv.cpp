#include <uhd/usrp/multi_usrp.hpp>
#include <boost/thread/thread.hpp>
#include <cstdio>
#include <iostream>
#include "recv.h"
#include "util.h"
#include "signal.h"
#include "socket.h"

/***********************************************************************
 * recv_to_file function
 **********************************************************************/
void recv_to_file(uhd::usrp::multi_usrp::sptr usrp,
    const std::string& cpu_format,
    const std::string& wire_format,
    size_t spb,
    size_t spt,
    int stack,
    double prf,
    uhd::time_spec_t begin,
    int *p)
{

    unsigned long long int ntrace = 0;
    int num_total_samps = 0;
    int stsend = 0;
    int sockfd = initSocket();
    std::string nmea;
    gpsData fix;

    // create a receive streamer
    uhd::stream_args_t stream_args(cpu_format, wire_format);
    stream_args.channels.push_back(0);
    uhd::rx_streamer::sptr rx_stream = usrp->get_rx_stream(stream_args);

    // Prepare buffers for received samples and metadata
    uhd::rx_metadata_t md;
    std::vector<std::vector<std::complex<float>>> buffs(
        1, std::vector<std::complex<float>>(spb));
 
   // create a vector of pointers to point to each of the channel buffers
    std::vector<std::complex<float>*> buff_ptrs;
    for (size_t i = 0; i < buffs.size(); i++) {
        buff_ptrs.push_back(&buffs[i].front());
    }

    bool overflow_message = true;

    double timeout = 5;
    // setup streaming
    uhd::stream_cmd_t stream_cmd(uhd::stream_cmd_t::STREAM_MODE_START_CONTINUOUS);
    stream_cmd.stream_now = false;
    stream_cmd.time_spec = uhd::time_spec_t(begin);
    rx_stream->issue_stream_cmd(stream_cmd); // stream command

    int st = 0;
    std::vector<float> acmltr(spt);

    for (size_t i = 0; i < spt; i++) {
        acmltr[i] = 0;
    }

    int count = 0;
    while (not stop_signal_called) {
        size_t num_rx_samps = rx_stream->recv(buff_ptrs, spb, md, timeout);
        timeout             = 1.0f; // small timeout for subsequent recv
        count++;
    
        if (md.error_code == uhd::rx_metadata_t::ERROR_CODE_TIMEOUT) {
            std::cout << boost::format("Timeout while streaming") << std::endl;
            break;
        }
        if (md.error_code == uhd::rx_metadata_t::ERROR_CODE_OVERFLOW) {
                stream_cmd.stream_mode = uhd::stream_cmd_t::STREAM_MODE_STOP_CONTINUOUS;
                rx_stream->issue_stream_cmd(stream_cmd); // stream command
                stream_cmd.stream_now = false;
                stream_cmd.time_spec = uhd::time_spec_t(usrp->get_time_now().get_full_secs() + 2) ;
                stream_cmd.stream_mode = uhd::stream_cmd_t::STREAM_MODE_START_CONTINUOUS;
                rx_stream->issue_stream_cmd(stream_cmd); // stream command
            if (overflow_message) {
                overflow_message = false;
                std::cerr
                    << boost::format(
                           "Got an overflow indication. Please consider the following:\n"
                           "  Your write medium must sustain a rate of %fMB/s.\n"
                           "  Dropped samples will not be written to the file.\n"
                           "  Please modify this example for yoSeur purposes.\n"
                           "  This message will not appear again.\n")
                           % (usrp->get_rx_rate() * sizeof(std::complex<float>) / 1e6);
            }
            continue;
        }
        //if (md.error_code != uhd::rx_metadata_t::ERROR_CODE_NONE) {
        //    throw std::runtime_error(
        //        str(boost::format("Receiver error %s") % md.strerror()));
        //}

        // Stack traces
        if (st < stack) {
            for (size_t i = 0; i < spt; i++) {
                acmltr[i] += buff_ptrs[0][i].real()/stack;
            }
            st++;

            if(st == floor(stack/2)) { 
                write(p[1], &md.time_spec, sizeof(uhd::time_spec_t));
            }
        }
        if(st == stack) {
            ntrace++;
            write(p[1], &acmltr.front(), spt*4);
            write(p[1], &ntrace, sizeof(unsigned long long int));
            //fix = saveTrace(dataFile, &acmltr.front(), nmea, md.time_spec, spt);
            //fix.ntrace = ntrace;
            //stsend++;
            //if(stsend == 4) {
            //    stsend = 0;
            //    guiSend(sockfd, &acmltr.front(), fix, spt);
            //}
            st = 0;
            memset(&acmltr.front(), 0, spt*sizeof(float));
        }
    }

    // Shut down receiver
    stream_cmd.stream_mode = uhd::stream_cmd_t::STREAM_MODE_STOP_CONTINUOUS;
    rx_stream->issue_stream_cmd(stream_cmd);
}


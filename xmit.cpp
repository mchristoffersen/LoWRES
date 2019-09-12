#include <uhd/usrp/multi_usrp.hpp>
#include <iostream>
#include "xmit.h"
#include "signal.h"
#include "util.h"



/***********************************************************************
 * transmit_worker function
 * A function to be used as a boost::thread_group thread for transmitting
 **********************************************************************/
void transmit_worker(uhd::usrp::multi_usrp::sptr usrp,
    std::vector<std::complex<float>> chirp,
    uhd::tx_streamer::sptr tx_streamer,
    uhd::tx_metadata_t md,
    double prf)
{
    // Caller must set time spec
    md.start_of_burst = true;
    md.end_of_burst = true;
    md.has_time_spec = true;

    std::vector<std::complex<float>*> buffs(1, &chirp.front());
    
    // send data until the signal handler gets called
    while (not stop_signal_called) {
        // Send chirp
        tx_streamer->send(buffs, chirp.size(), md);
        // Increment send time
        md.time_spec += uhd::time_spec_t(1/prf);
    }
}

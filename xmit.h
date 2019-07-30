#pragma once

void transmit_worker(uhd::usrp::multi_usrp::sptr usrp,
    std::vector<std::complex<float>> chirp,
    uhd::tx_streamer::sptr tx_streamer,
    uhd::tx_metadata_t md,
    double prf);

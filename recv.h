#pragma once

void recv_to_file(uhd::usrp::multi_usrp::sptr usrp,
    const std::string& cpu_format,
    const std::string& wire_format,
    const std::string& file,
    size_t spb,
    size_t spt,
    FILE *dataFile,
    int stack,
    double prf,
    uhd::time_spec_t begin);

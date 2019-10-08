//
// Copyright 2010-2012,2014-2015 Ettus Research LLC
// Copyright 2018 Ettus Research, a National Instruments Company
//
// SPDX-License-Identifier: GPL-3.0-or-later
//

#include <uhd/exception.hpp>
#include <uhd/types/tune_request.hpp>
#include <uhd/usrp/multi_usrp.hpp>
#include <uhd/utils/safe_main.hpp>
#include <uhd/utils/static.hpp>
#include <uhd/utils/thread.hpp>
#include <boost/algorithm/string.hpp>
#include <boost/filesystem.hpp>
#include <boost/format.hpp>
#include <boost/program_options.hpp>
#include <boost/thread/thread.hpp>
#include <csignal>
#include <cstdio>
#include <iostream>
#include "util.h"
#include "xmit.h"
#include "recv.h"
#include "signal.h"
#include "socket.h"

namespace po = boost::program_options;

// GPIO DEFS
#define AMP_GPIO_MASK   (1 << 3)

/***********************************************************************
 * Main function
 **********************************************************************/
int UHD_SAFE_MAIN(int argc, char* argv[])
{
    uhd::set_thread_priority_safe(1, true);

    FILE *dataFile;

    // transmit variables to be set by po
    std::string args, wave_type, tx_ant, tx_subdev, ref, otw, tx_channels;
    double tx_rate, tx_freq;
    uhd::time_spec_t begin;

    // receive variables to be set by po
    std::string file, type, rx_ant, rx_subdev, rx_channels;
    size_t spb, spt;
    double rx_rate, rx_freq;
    double settling;

    // Chirp/trace variables
    double chbw, champ, chlen, chcf, chprf, trlen;
    unsigned int stack;

    // Pipe for communicating recvd data to saver
    int fd[2];

    // String for sending display data back to
    std::string ip_display;

    // setup the program options
    po::options_description desc("Allowed options");
    // clang-format off
    desc.add_options()
        ("help", "help message")
        //("args", po::value<std::string>(&args)->default_value(""), "uhd device address args")
        ("settling", po::value<double>(&settling)->default_value(double(0.2)), "settling time (seconds) before receiving")
        ("tx-rate", po::value<double>(&tx_rate), "rate of transmit outgoing samples")
        ("rx-rate", po::value<double>(&rx_rate), "rate of receive incoming samples")
        ("tx-freq", po::value<double>(&tx_freq), "transmit RF center frequency in Hz")
        ("rx-freq", po::value<double>(&rx_freq), "receive RF center frequency in Hz")
        ("ref", po::value<std::string>(&ref)->default_value("internal"), "clock reference (internal, external, mimo)")
        ("tx-int-n", "tune USRP TX with integer-N tuning")
        ("rx-int-n", "tune USRP RX with integer-N tuning")
        ("chirp-cf", po::value<double>(&chcf)->default_value(2500000), "chirp center frequency")
        ("chirp-bw", po::value<double>(&chbw)->default_value(100), "chirp bandwidth")
        ("chirp-len", po::value<double>(&chlen)->default_value(0.000005), "chirp length")
        ("chirp-amp", po::value<double>(&champ)->default_value(.5), "chirp amplitude")
        ("chirp-prf", po::value<double>(&chprf)->default_value(2000), "chirp pulse repetition frequency")
        ("trace-len", po::value<double>(&trlen)->default_value(0.00005), "trace length")
        ("stack", po::value<unsigned int>(&stack)->default_value(100), "number of traces to stack")
	("ip-display", po::value<std::string>(&ip_display)->default_value(""), "IP address of display computer")
    ;

    // Options short-circuited from command line options
    otw = "sc16";
    ref = "gpsdo";
    args = "type=x300,addr=192.168.30.2,second_addr=192.168.40.2";
    std::vector<size_t> tx_channel_nums = {0};
    std::vector<size_t> rx_channel_nums = {0};
    tx_subdev = "A:AB";
    rx_subdev = "A:AB";

    // clang-format on
    po::variables_map vm;
    po::store(po::parse_command_line(argc, argv, desc), vm);
    po::notify(vm);

    // print the help message
    if (vm.count("help")) {
        std::cout << boost::format("UHD TXRX Loopback to File %s") % desc << std::endl;
        return ~0;
    }

    // create a usrp device
    std::cout << std::endl;
    std::cout << boost::format("Creating the usrp device with: %s...") % args
              << std::endl;
    uhd::usrp::multi_usrp::sptr usrp = uhd::usrp::multi_usrp::make(args);

    std::cout << "USRP device created\n";

    // Select the subdevice
    usrp->set_tx_subdev_spec(tx_subdev);
    usrp->set_rx_subdev_spec(rx_subdev);

    // Lock mboard clock to gpsdo
    usrp->set_clock_source(ref);
    usrp->set_time_source(ref);

    //std::cout << boost::format("Using TX Device: %s") % usrp->get_pp_string()
    //          << std::endl;

    // set the transmit sample rate// set up our masks, defining the pin numbers
    if (not vm.count("tx-rate")) {
        std::cerr << "Please specify the transmit sample rate with --tx-rate"
                  << std::endl;
        return ~0;
    }
    std::cout << boost::format("Setting TX Rate: %f Msps...") % (tx_rate / 1e6)
              << std::endl;
    usrp->set_tx_rate(tx_rate);
    std::cout << boost::format("Actual TX Rate: %f Msps...")
                     % (usrp->get_tx_rate() / 1e6)
              << std::endl
              << std::endl;

    // set the receive sample rate
    if (not vm.count("rx-rate")) {
        std::cerr << "Please specify the sample rate with --rx-rate" << std::endl;
        return ~0;
    }
    std::cout << boost::format("Setting RX Rate: %f Msps...") % (rx_rate / 1e6)
              << std::endl;
    usrp->set_rx_rate(rx_rate);
    std::cout << boost::format("Actual RX Rate: %f Msps...")
                     % (usrp->get_rx_rate() / 1e6)
              << std::endl
              << std::endl;

    // set the transmit center frequency
    if (not vm.count("tx-freq")) {
        std::cerr << "Please specify the transmit center frequency with --tx-freq"
                  << std::endl;
        return ~0;
    }

    for (size_t ch = 0; ch < tx_channel_nums.size(); ch++) {
        size_t channel = tx_channel_nums[ch];
        if (tx_channel_nums.size() > 1) {
            std::cout << "Configuring TX Channel " << channel << std::endl;
        }
        std::cout << boost::format("Setting TX Freq: %f MHz...") % (tx_freq / 1e6)
                  << std::endl;
        uhd::tune_request_t tx_tune_request(tx_freq);
        if (vm.count("tx-int-n"))
            tx_tune_request.args = uhd::device_addr_t("mode_n=integer");
        usrp->set_tx_freq(tx_tune_request, channel);
        std::cout << boost::format("Actual TX Freq: %f MHz...")
                         % (usrp->get_tx_freq(channel) / 1e6)
                  << std::endl
                  << std::endl;
    }

    for (size_t ch = 0; ch < rx_channel_nums.size(); ch++) {
        size_t channel = rx_channel_nums[ch];
        if (rx_channel_nums.size() > 1) {
            std::cout << "Configuring RX Channel " << channel << std::endl;
        }

        // set the receive center frequency
        if (not vm.count("rx-freq")) {
            std::cerr << "Please specify the center frequency with --rx-freq"
                      << std::endl;
            return ~0;
        }
        std::cout << boost::format("Setting RX Freq: %f MHz...") % (rx_freq / 1e6)
                  << std::endl;
        uhd::tune_request_t rx_tune_request(rx_freq);
        if (vm.count("rx-int-n"))
            rx_tune_request.args = uhd::device_addr_t("mode_n=integer");
        usrp->set_rx_freq(rx_tune_request, channel);
        std::cout << boost::format("Actual RX Freq: %f MHz...")
                         % (usrp->get_rx_freq(channel) / 1e6)
                  << std::endl
                  << std::endl;

    }


    // create a transmit streamer
    // linearly map channels (index0 = channel0, index1 = channel1, ...)
    uhd::stream_args_t stream_args("fc32", otw);
    stream_args.channels             = tx_channel_nums;
    uhd::tx_streamer::sptr tx_stream = usrp->get_tx_stream(stream_args);

    // Check Ref and LO Lock detect
    
    std::vector<std::string> tx_sensor_names, rx_sensor_names;
    tx_sensor_names = usrp->get_tx_sensor_names(0);
    if (std::find(tx_sensor_names.begin(), tx_sensor_names.end(), "lo_locked")
        != tx_sensor_names.end()) {
        uhd::sensor_value_t lo_locked = usrp->get_tx_sensor("lo_locked", 0);
        std::cout << boost::format("Checking TX: %s ...") % lo_locked.to_pp_string()
                  << std::endl;
        UHD_ASSERT_THROW(lo_locked.to_bool());
    }
    rx_sensor_names = usrp->get_rx_sensor_names(0);
    if (std::find(rx_sensor_names.begin(), rx_sensor_names.end(), "lo_locked")
        != rx_sensor_names.end()) {
        uhd::sensor_value_t lo_locked = usrp->get_rx_sensor("lo_locked", 0);
        std::cout << boost::format("Checking RX: %s ...") % lo_locked.to_pp_string()
                  << std::endl;
        UHD_ASSERT_THROW(lo_locked.to_bool());
    }
    

    // Some chirp-determined settings and checks
    spb = rx_rate/chprf;
    if(spb != rx_rate/chprf) {
        std::cout << boost::format("Invalid PRF: %f\nMust evenly divide into tx-rate") % chprf << std::endl;
        return 0;
    }

    spt = rx_rate*trlen;

    //std::cout << "RX RATE: " << rx_rate << std::endl;
    //std::cout << "TRLEN: " << trlen << std::endl;
    //std::cout << "SPT: " << spt << std::endl;

    // Generate a chirp to transmit
    std::vector<std::complex<float>> chirp = generateChirp(champ, chcf, chbw, chlen, tx_rate, chprf);


    // allocate a buffer which we re-use for each channel
    //int num_channels = tx_channel_nums.size();


    // GPS lock
    /*
    bool gps_locked = usrp->get_mboard_sensor("gps_locked").to_bool();
    if (gps_locked) {
        std::cout << boost::format("GPS Locked\n");
    } else {
        std::cerr
            << "WARNING:  GPS not locked - time will not be accurate until locked"
            << std::endl;
    }
    */

/*
    while(! (usrp->get_mboard_sensor("gps_locked").to_bool())) {
        std::cout << usrp->get_mboard_sensor("gps_gpgga").value << std::endl;
        boost::this_thread::sleep_for(boost::chrono::seconds(2)); // Ensure PPS sync

    }
*/

    //usrp->set_time_source(ref);

    // Amplifier triggering via GPIO[3]
    usrp->set_gpio_attr("FP0", "DDR", AMP_GPIO_MASK, AMP_GPIO_MASK); // DDR
    usrp->set_gpio_attr("FP0", "CTRL", AMP_GPIO_MASK, AMP_GPIO_MASK); // Control
    usrp->set_gpio_attr("FP0", "ATR_XX", AMP_GPIO_MASK, AMP_GPIO_MASK); // Trigger on duplex

    // Set device time to GPS time
    std::cout << boost::format("Setting device time to GPS time...") << std::endl;
    uhd::time_spec_t gps_time = uhd::time_spec_t(
        int64_t(usrp->get_mboard_sensor("gps_time").to_int()));
    usrp->set_time_next_pps(gps_time + 1.0);

    begin = uhd::time_spec_t(gps_time.get_full_secs() + 6.0);


    boost::this_thread::sleep_for(boost::chrono::seconds(2)); // Ensure PPS sync

    // setup the transmit metadata flags
    uhd::tx_metadata_t md;
    md.time_spec = begin;

    // Set up sigint to end the program
    std::signal(SIGINT, &sig_int_handler);
    std::cout << "Hit \"STOP\" on GUI to stop streaming..." << std::endl;

    //std::cout << "TRANSMIT";
    //boost::this_thread::sleep_for(boost::chrono::seconds(1));

    // Open data file and write header
    char filename[38];
    strcpy(filename, "/home/lowres/data/");
    generate_out_filename(filename+18, begin);
    std::cout << filename << std::endl;
    dataFile = fopen(filename, "wb");
    saveHdr(dataFile, chbw, chcf, chlen, champ, chprf, trlen, rx_rate, stack, begin);

    // Open socket
    int sockfd = initSocket(ip_display);
    //std::cout << "Started socket\n";

    // Set up output pipe
    if(pipe(fd)) {
        std::cout << "Failure creating pipe\n";
        return 0;
    }

    // start transmit worker thread
    boost::thread_group transmit_thread;
    transmit_thread.create_thread(boost::bind(
        &transmit_worker, usrp, chirp, tx_stream, md, chprf));
    //transmit_worker(usrp, chirp, tx_stream, md, chprf);

    // Start data handler thread
    boost::thread_group handler_thread;
    handler_thread.create_thread(boost::bind(
      &traceHandler, usrp, dataFile, sockfd, fd, spt));

    // recv to file
    recv_to_file(usrp, "fc32", otw, spb, spt, stack, chprf, begin, fd);

    // clean up transmit worker
    stop_signal_called = true;
    transmit_thread.join_all();
    handler_thread.join_all();

    // final clean up
    close(sockfd);
    fclose(dataFile);

    // finished
    std::cout << std::endl << "Done!" << std::endl << std::endl;
    return EXIT_SUCCESS;
}

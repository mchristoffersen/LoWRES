sudo sysctl -w net.core.wmem_max=24862979
sudo sysctl -w net.core.rmem_max=24862979
sudo ifconfig enp1s0f0 mtu 9000
sudo ifconfig enp1s0f1 mtu 9000
sudo ethtool -G enp1s0f0 rx 4096
sudo ethtool -G enp1s0f1 rx 4096
#python3 ./gui/ettusDaemon.py &
#python3 ./gui/gui.py

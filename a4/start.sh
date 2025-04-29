#!/bin/bash
# to filter the capture to to wireless->WLAN->options
# and right click on your AP and apply it as a filter
display_filt="(wlan.bssid==64:29:43:05:f9:ed) && (wlan.fc.type_subtype == 0x0008)"
trap '' INT
if [ "$1" == "" ]; then
	echo "Specify the channel"
else
	sudo airmon-ng check kill;
	sudo airmon-ng start wlp0s20f3 $1;
	echo -e "Starting wireshark\n"
	(trap - INT; tshark -i wlp0s20f3mon -w tmp.pcap;)
	# (trap - INT; wireshark;)
	echo -e "\nRemoving monitor mode"; 
	tshark -r tmp.pcap -Y "$display_filt" -w output.pcap;
	rm tmp.pcap;
	sudo airmon-ng stop wlp0s20f3mon;
	sudo ifconfig wlp0s20f3 up;
	sudo systemctl start wpa_supplicant;
	sudo systemctl start NetworkManager.service;
fi

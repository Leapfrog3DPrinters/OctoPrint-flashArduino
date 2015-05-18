OctoPrint-flashArduino
=============================


Plugin to flash Arduino based printer boards.

Install avrdude on your machine and point the add-on in the settings to the correct avrdude executable and avrdude.conf file. 

Select a hex file, port and board and press flash.

This project is in heavy *WIP* phase. So please be carefull. Would be nice to run octoprint in --debug mode to see whats going on. 

At the moment a limit amount of boards is supported and many are still untested. If you know your the settings for your board(programmer / baudrate / chip type) for AVR dude please make a PR with the information so I can add it to the plugin. 

##TODO 
Make board profiles wich can be edited, added and removed.

-Booli


__author__ = 'Salandora'

import re
import sarge

from flask.ext.babel import gettext
from octoprint_flasharduino.config import register_programmer
from . import Programmer

class AVRDudeProgrammer(Programmer):
    def initialize(self):
        self.register_board(gettext("ATmega2560 Leapfrog CreatrHS, Ultimaker 2, RAMPS 1.4, RAMBo"), dict(board="m2560", protocol="wiring", baudrate="115200"))
        self.register_board(gettext("ATmega1280 Arduino Mega"), dict(board="m1280", protocol="arduino", baudrate="57600"))
        self.register_board(gettext("Duemilanove /w ATmega328"), dict(board="m328p", protocol="arduino", baudrate="57600"))
        self.register_board(gettext("Duemilanove /w ATmega16"), dict(board="atmega168", protocol="arduino", baudrate="19200"))
        self.register_board(gettext("Sanguino /w ATmega1284P"), dict(board="atmega1284p", protocol="stk500", baudrate="57600"))
        self.register_board(gettext("Sanguino /w ATmega644P"), dict(board="atmega644p", protocol="stk500", baudrate="57600"))
        self.register_board(gettext("PrintrBoard"), dict(board="usb1286", protocol="avr109", baudrate="115200"))

    def get_assets(self):
        return dict(
            js=["js/programmers/avrdude.js"]
        )

    def get_settings_defaults(self):
        return dict(avrdude_path=None,
                    avrdude_conf=None)

    def get_template_configs(self):
       return [
           dict(type="plugin_flasharduino_settings", template="programmers/avrdude/avrdude_programmersettings.jinja2", custom_bindings=True),
           dict(type="plugin_flasharduino_status", template="programmers/avrdude/avrdude_status.jinja2", custom_bindings=True)
       ]

    def flash_file(self, options):
        if options is None:
            return

        ## Create list with arguments for avrdude from the POST in formData
        args = []
        if "board" in options:
            board_arg = "-p " + options['board']
            args.append(board_arg)
        if "protocol" in options:
            protocol_arg = "-c " + options['protocol']
            args.append(protocol_arg)
        if "port" in options:
            port_arg = "-P " + options['port']
            args.append(port_arg)
        if "baudrate" in options:
            baudrate_arg = "-b " + options['baudrate']
            args.append(baudrate_arg)

        avrdude_conf = self._settings.get(["avrdude_conf"])
        if avrdude_conf is not None and avrdude_conf != "":
            conf_arg = '-C"%s"' % avrdude_conf
            args.append(conf_arg)
        self._logger.debug(args)

        file_args = "-U flash:w:" + options["hex_path"] + ":i -D"
        args.append(file_args)
        self._call_avrdude(args)

    def allowed_extensions(self):
        return [ "hex" ]

    # Shameless copy + alteration from PluginManager
    def _call_avrdude(self, args):
        avrdude_command = self._settings.get(["avrdude_path"])
        if avrdude_command is None:
            # This needs the more thorough checking like the pip stuff in pluginmanager
            raise RuntimeError(
                u"No avrdude path configured and {avrdude_command} does not exist or is not executable, can't install".format(
                    **locals()))

        command = ['"%s"' % avrdude_command] + args

        self._logger.debug(u"Calling: {}".format(" ".join(command)))

        p = sarge.run(" ".join(command), shell=True, async=True, stdout=sarge.Capture(), stderr=sarge.Capture())
        p.wait_events()

        try:
            while p.returncode is None:
                line = p.stderr.readline()
                if line:
                    self._log_stderr(line)
                line = p.stdout.readline()
                if line:
                    self._log_stdout(line)

                p.commands[0].poll()

        finally:
            p.close()

        stderr = p.stderr.text
        if stderr:
            self._log_stderr(*stderr.split("\n"))

        stdout = p.stdout.text
        if stdout:
            self._log_stdout(*stdout.split("\n"))

        return p.returncode

    def _check_progress(self, line):
        initialized = re.search('initialized', line)
        if initialized:
            self._logger.debug("Device initialized")
            self._send_progress_update("busy", "flash_read")
        read = re.search('reading input', line)
        if read:
            self._logger.debug("Hex file read")
            self._send_progress_update("done", "flash_read")
            self._send_progress_update("busy", "flash_write")
        written = re.search('flash written', line)
        if written:
            self._logger.debug("Hex file written to flash")
            self._send_progress_update("done", "flash_write")
            self._send_progress_update("busy", "flash_verify")
        verified = re.search('flash verified', line)
        if verified:
            self._logger.debug("Hex file verified on flash")
            self._send_progress_update("done", "flash_verify")
            self._send_progress_update("busy", "flash_done")
            self._send_result_update("success")
        done = 'avrdude' in line and 'done' in line
        if done:
            self._logger.debug("Flashing hex file done")
            self._send_progress_update("done", "flash_done")


register_programmer(AVRDudeProgrammer("avrdude"))

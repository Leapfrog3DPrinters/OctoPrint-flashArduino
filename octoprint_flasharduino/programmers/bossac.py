__author__ = 'Salandora'

import re
import sarge

from flask.ext.babel import gettext
from octoprint_flasharduino.config import register_programmer
from . import Programmer

class BossacProgrammer(Programmer):
    def initialize(self):
        self.register_board(gettext("Arduino Due (Programming Port)"), dict(native="false", use_1200bps_touch="true", wait_for_upload_port="false"))
        self.register_board(gettext("Arduino Due (Native Port)"), dict(native="true", use_1200bps_touch="true", wait_for_upload_port="true"))

    def get_assets(self):
        return dict(
            js=["js/programmers/bossac.js"]
        )

    def get_settings_defaults(self):
        return dict(bossac_verbose=False,
                    bossac_path=None)

    def get_template_configs(self):
       return [
           dict(type="plugin_flasharduino_settings", template="programmers/bossac/bossac_programmersettings.jinja2", custom_bindings=True),
           dict(type="plugin_flasharduino_status", template="programmers/bossac/bossac_status.jinja2", custom_bindings=True)
       ]

    def flash_file(self, options):
        if options is None:
            return

        ## Create list with arguments for avrdude from the POST in formData
        args = []
        if self._settings.get(["bossac_verbose"]):
            args += ["-i", "-d"]

        if "port" in options:
            port_arg = "--port=" + options['port']
            args.append(port_arg)
            if "use_1200bps_touch" in options and options["use_1200bps_touch"]:
                self._touchPort(1200, options['port'])
                if "wait_for_upload_port" in options and options["wait_for_upload_port"] == "true":
                    self._waitForUploadPort()

        if "native" in options:
            native_arg = "-U " + options['native']
            args.append(native_arg)

        args += ["-e", "-v", "-b"]
        self._logger.debug(args)

        file_args = "-w \"" + options["hex_path"] + "\" -R"
        args.append(file_args)

        self._call_bossac(args)

    def allowed_extensions(self):
        return ["bin"]

    def _touchPort(self, baudrate, port):
        import serial
        try:
            serial_obj = serial.Serial(str(port), baudrate, parity=serial.PARITY_NONE)
            serial_obj.close()
        except Exception as e:
            self._logger.exception("Error while copying file")

    def _waitForUploadPort(self):
        pass

    # Shameless copy + alteration from PluginManager
    def _call_bossac(self, args):
        bossac_command = self._settings.get(["bossac_path"])
        if bossac_command is None:
            # This needs the more thorough checking like the pip stuff in pluginmanager
            raise RuntimeError(
                u"No avrdude path configured and {avrdude_command} does not exist or is not executable, can't install".format(
                    **locals()))

        command = ['"%s"' % bossac_command] + args

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
        erase = re.search('Erase', line)
        if erase:
            self._logger.debug("Device erased")
            self._send_progress_update("busy", "bossac_erase")
            self._send_progress_update("done", "bossac_erase")
            self._send_progress_update("busy", "bossac_write")
            return
        written = re.search('Verify', line) and not re.search('successful', line)
        if written:
            self._logger.debug("Hex file written to flash")
            self._send_progress_update("done", "bossac_write")
            self._send_progress_update("busy", "bossac_verify")
            return
        verified = re.search('Verify successful', line)
        if verified:
            self._logger.debug("Hex file verified on flash")
            self._send_progress_update("done", "bossac_verify")
            self._send_progress_update("busy", "bossac_done")
            self._send_result_update("success")
            return
        done = re.search('CPU reset', line)
        if done:
            self._logger.debug("Flashing hex file done")
            self._send_progress_update("done", "bossac_done")


register_programmer(BossacProgrammer("bossac"))

# coding=utf-8
from __future__ import absolute_import

import flask
import logging
import sarge
import logging.handlers
import octoprint.plugin
import octoprint.settings
import re
import os

##~~ Init Plugin and Metadata


class FlashArduino(octoprint.plugin.TemplatePlugin,
			  	   octoprint.plugin.AssetPlugin,
			       octoprint.plugin.SettingsPlugin,
			       octoprint.plugin.BlueprintPlugin):

		def bodysize_hook(self, current_max_body_sizes, *args, **kwargs):
			return [
				("POST", "/plugin/" + self._identifier + "/flash", 512 * 1024) # max upload size = 512KB
			]

		##~~ AssetsPlugin
		def get_assets(self):
			return dict(
				js=["js/flasharduino.js"],
				css=["css/flasharduino.css"]
			)

		##~~ Set default settings
		def get_settings_defaults(self):
			return dict(avrdude_path=None,
			            avrdude_conf=None)


		def get_template_configs(self):
			return [
				dict(type="settings", template="flasharduino_settings.jinja2", custom_bindings=True)
			]

		## Blueprint Plugin
		@octoprint.plugin.BlueprintPlugin.route("/flash", methods=["POST"])
		def flash_hex_file(self):
			import datetime
			from shutil import copy2
			import tempfile

			## Reset UI
			self._reset_progress()

			## Create list with arguments for avrdude from the POST in formData
			args = []
			if "board" in flask.request.form:
				board_arg = "-p " + flask.request.form['board']
				args.append(board_arg)
			if "programmer" in flask.request.form:
				programmer_arg = "-c " + flask.request.form['programmer']
				args.append(programmer_arg)
			if "port" in flask.request.form:
				port_arg = "-P " + flask.request.form['port']
				args.append(port_arg)
			if "baudrate" in flask.request.form:
				baudrate_arg = "-b " + flask.request.form['baudrate']
				args.append(baudrate_arg)
			avrdude_conf = self._settings.get(["avrdude_conf"])
			if avrdude_conf is not None:
				conf_arg = '-C"%s"' % avrdude_conf
				args.append(conf_arg)
			self._logger.debug(args)

			## Tornado hack
			input_name = "file"
			input_upload_name = input_name + "." + self._settings.global_get(["server", "uploads", "nameSuffix"])
			input_upload_path = input_name + "." + self._settings.global_get(["server", "uploads", "pathSuffix"])
			hex_path = flask.request.values[input_upload_path]
			ext_path = flask.request.values[input_upload_name]

			## Upload the hexfile and try to flash the file. 
			if input_upload_name in flask.request.values and input_upload_path in flask.request.values and self.allowed_file(ext_path):
				temp_file = tempfile.NamedTemporaryFile(delete=False)
				try:
					temp_file.close()
					copy2(hex_path, temp_file.name)
					self._logger.debug("File created with name %s" % temp_file.name)
					hex_path = temp_file.name
					file_args = "-U flash:w:" + hex_path + ":i -D"
					args.append(file_args)
					self._call_avrdude(args)
				except Exception as e:
					self._logger.exception("Error while copying file")
					return flask.make_response("Something went wrong while copying file with message: {message}".format(message=str(e)), 500)
				finally:
					os.remove(temp_file.name)
					self._logger.debug("File deleted with name %s" % temp_file.name)

			else:
				self._logger.warn("No .hex file included for flashing, aborting")
				self._send_result_update("failed")
				return flask.make_response("No .hex file included", 400)

			return flask.make_response("SUPER SUCCESS", 201)

		def allowed_file(self, filename):
			ext = os.path.splitext(filename)[1]
			self._logger.debug(ext)
			return (ext == ".hex")

		#Shameless copy + alteration from PLuginManager
		def _call_avrdude(self, args):
			avrdude_command = self._settings.get(["avrdude_path"])
			if avrdude_command is None:
				#This needs the more thorough checking like the pip stuff in pluginmanager
				raise RuntimeError(u"No avrdude path configured and {avrdude_command} does not exist or is not executable, can't install".format(**locals()))

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

		def _reset_progress(self):
			self._send_progress_update("reset", "all")

		def _send_progress_update(self, progress, bar_type):
			self._plugin_manager.send_plugin_message(self._identifier, dict(type="progress", progress=progress, bar_type=bar_type))

		def _send_result_update(self, result):
			self._plugin_manager.send_plugin_message(self._identifier, dict(type="result", result=result))			

		def _log_stdout(self, *lines):
			self._log(lines, prefix=">", stream="stdout")

		def _log_stderr(self, *lines):
			self._log(lines, prefix="!", stream="stderr")

		def _log(self, lines, prefix=None, stream=None, strip=True):
			if strip:
				lines = map(lambda x: x.strip(), lines)

			self._plugin_manager.send_plugin_message(self._identifier, dict(type="loglines", loglines=[dict(line=line, stream=stream) for line in lines]))
			for line in lines:
				self._check_progress(line)
				self._logger.debug(u"{prefix} {line}".format(**locals()))

__plugin_name__ = "Flash Arduino"
def __plugin_load__():
	global __plugin_implementation__
	__plugin_implementation__ = FlashArduino()

	global __plugin_hooks__
	__plugin_hooks__ = {
		"octoprint.server.http.bodysize": __plugin_implementation__.bodysize_hook
	}

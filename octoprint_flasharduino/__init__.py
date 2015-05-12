# coding=utf-8
from __future__ import absolute_import

import flask
import logging
import sarge
import logging.handlers
import octoprint.plugin
import octoprint.settings

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
			return dict(avrdude_path=None)


		def get_template_configs(self):
			return [
				dict(type="settings", template="flasharduino_settings.jinja2", custom_bindings=True)
			]

		## Blueprint Plugin
		@octoprint.plugin.BlueprintPlugin.route("/flash", methods=["POST"])
		def flash_hex_file(self):
			import datetime
			from shutil import copy2
			import os
			import tempfile


			input_name = "file"
			input_upload_name = input_name + "." + self._settings.global_get(["server", "uploads", "nameSuffix"])
			input_upload_path = input_name + "." + self._settings.global_get(["server", "uploads", "pathSuffix"])

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
			self._logger.debug(args)

			if input_upload_name in flask.request.values and input_upload_path in flask.request.values:
				temp_file = tempfile.NamedTemporaryFile(delete=False, dir="/tmp")
				hex_path = flask.request.values[input_upload_path]
				try:
					temp_file.close()
					copy2(hex_path, temp_file.name)
					self._logger.debug("file created with name %s" % temp_file.name)
					hex_path = temp_file.name
					self._call_avrdude(args)
				except Exception as e:
					self._logger.exception("Error while copying file")
					return flask.make_response("Something went wrong while copying file with message: {message}".format(message=str(e)), 500)
				finally:
					os.remove(temp_file.name)
					self._logger.debug("file deleted with name %s" % temp_file.name)

			else:
				self._logger.warn("No hex file included for flashing, aborting")
				return flask.make_response("No file included", 400)

			return flask.make_response("SUPER SUCCESS", 201)

		#Shameless copy + alteration from PLuginManager
		def _call_avrdude(self, args):
			avrdude_command = self._settings.get(["avrdude_path"])
			if avrdude_command is None:
				#This needs the more thorough checking like the pip stuff in pluginmanager
				raise RuntimeError(u"No avrdude path configured and {avrdude_command} does not exist or is not executable, can't install".format(**locals()))

			command = [avrdude_command] + args

			self._logger.debug(u"Calling: {}".format(" ".join(command)))

			p = sarge.run(" ".join(command), shell=True, async=True, stdout=sarge.Capture(), stderr=sarge.Capture())
			p.wait_events()

			try:
				while p.returncode is None:
					line = p.stderr.readline(timeout=0.5)
					if line:
						self._log_stderr(line)

					line = p.stdout.readline(timeout=0.5)
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

		def _log_stdout(self, *lines):
			self._log(lines, prefix=">", stream="stdout")

		def _log_stderr(self, *lines):
			self._log(lines, prefix="!", stream="stderr")

		def _log(self, lines, prefix=None, stream=None, strip=True):
			if strip:
				lines = map(lambda x: x.strip(), lines)

			self._plugin_manager.send_plugin_message(self._identifier, dict(type="loglines", loglines=[dict(line=line, stream=stream) for line in lines]))
			for line in lines:
				self._console_logger.debug(u"{prefix} {line}".format(**locals()))

__plugin_name__ = "Flash Arduino"
def __plugin_load__():
	global __plugin_implementation__
	__plugin_implementation__ = FlashArduino()

	global __plugin_hooks__
	__plugin_hooks__ = {
		"octoprint.server.http.bodysize": __plugin_implementation__.bodysize_hook
	}

# coding=utf-8
from __future__ import absolute_import

import flask
import logging
import logging.handlers
import octoprint.plugin
import octoprint.settings

##~~ Init Plugin and Metadata


class FlashArduino(octoprint.plugin.TemplatePlugin,
			  	   octoprint.plugin.AssetPlugin,
			       octoprint.plugin.SettingsPlugin,
			       octoprint.plugin.BlueprintPlugin):

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
				dict(type="settings", custom_bindings=True)
			]

		def on_settings_save(self, data):
			super(FlashArduino, self).on_settings_save(data)

		## Blueprint Plugin
		@octoprint.plugin.BlueprintPlugin.route("/flash", methods=["POST"])
		def flash(self):
			import datetime
			from shutil import copyfile
			import os

			destination = "/tmp/octoprint-flasharduino/"
			input_name = "file"
			input_upload_name = input_name + "." + self._settings.global_get(["server", "uploads", "nameSuffix"])
			input_upload_path = input_name + "." + self._settings.global_get(["server", "uploads", "pathSuffix"])

			if input_upload_name in flask.request.values and input_upload_path in flask.request.values:
				hex_name = flask.request.values[input_upload_name]
				hex_path = flask.request.values[input_upload_path]
				try:
					copyfile(hex_path, destination)
				except Exception as e:
					self._logger.exception("Error while copying file")
					return flask.make_response("Something went wrong while copying file with message: {message}".format(str(e)), 500)
			else:
				self._logger.warn("No hex file included for flashing, aborting")
				return flask.make_response("No file included", 400)

			return flask.make_response("SUPER SUCCESS", 400)



__plugin_implementation__ = FlashArduino()
__plugin_name__ = "Flash Arduino"

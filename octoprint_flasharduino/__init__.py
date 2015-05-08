# coding=utf-8
from __future__ import absolute_import

import flask
import logging

import octoprint.plugin


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
			return dict(avrdude_path=None,
						hex_path=None,
						arduino_board=None,
						baudrate=None,
						port=None,
						programmer=None)


		def get_template_configs(self):
			return [
				dict(type="settings", custom_bindings=True)
			]

		def on_settings_save(self, data):
			super(FlashArduino, self).on_settings_save(data)

		## Blueprint Plugin
		@octoprint.plugin.BlueprintPlugin.route("/flash", methods=["POST"])
		def flash(self):
			hex_file = request.files['file']
			if hex_file:
				pass



__plugin_implementation__ = FlashArduino()
__plugin_name__ = "Flash Arduino"

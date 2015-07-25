# coding=utf-8
from __future__ import absolute_import

import os

import flask

import octoprint.plugin
import octoprint.settings
import octoprint_flasharduino.config

from octoprint.server.util.flask import restricted_access
from octoprint.server import admin_permission

from . import programmers

##~~ Init Plugin and Metadata

class FlashArduino(octoprint.plugin.TemplatePlugin,
                   octoprint.plugin.AssetPlugin,
                   octoprint.plugin.SettingsPlugin,
                   octoprint.plugin.BlueprintPlugin):

        def bodysize_hook(self, current_max_body_sizes, *args, **kwargs):
            return [
                ("POST","/flash", 512 * 1024) # max upload size = 512KB
            ]

        def templatehook(self, *args, **kwargs):
            return [
                ('settings', dict(), dict(div=lambda x: "settings_plugin_" + x, template=lambda x: x + "_programmersettings.jinja2")),
                ('status', dict(), dict(div=lambda x: "status_plugin_" + x, template=lambda x: x + "_status.jinja2")),

            ]

        def initialize(self):
            def settings_plugin_inject_factory(programmer):
                default_settings = programmer.get_settings_defaults()
                get_preprocessors, set_preprocessors = programmer.get_settings_preprocessors()
                plugin_settings = programmers.programmer_settings(self._settings.plugin_key,
                                                                   programmer._identifier,
                                                                   defaults=default_settings,
                                                                   get_preprocessors=get_preprocessors,
                                                                   set_preprocessors=set_preprocessors)
                return dict(settings=plugin_settings)

            variables = dict(
                logger=self._logger,
                plugin_manager=self._plugin_manager,
                plugin=self
            )

            # inject the additional_injects
            for name, programmer in octoprint_flasharduino.config.programmers.items():
                try:
                    for arg, value in variables.items():
                        setattr(programmer, "_" + arg, value)

                    programmer.initialize()
                except Exception as e:
                    self._logger.exception("Exception while initializing %s" % name)

                try:
                    return_value = settings_plugin_inject_factory(programmer)
                except:
                    self._logger.exception("Exception while executing settings_plugin_inject_factory")
                else:
                    if return_value is not None:
                        if isinstance(return_value, dict):
                            for arg, value in return_value.items():
                                setattr(programmer, "_" + arg, value)

        ##~~ AssetsPlugin
        def get_assets(self):
            assets = dict(
                js=["js/flasharduino_terminal.js", "js/flasharduino.js"],
                css=["css/flasharduino.css"]
            )

            for name, programmer in octoprint_flasharduino.config.programmers.items():
                programmer_assets = programmer.get_assets()
                if programmer_assets is not None:
                    assets = dict_list_merge(assets, programmer_assets)

            return assets

        ##~~ Set default settings
        def get_settings_defaults(self):
            return dict()

        def on_settings_load(self):
            data = super(self.__class__, self).on_settings_load()
            for name, programmer in octoprint_flasharduino.config.programmers.items():
                data[name] = programmer.on_settings_load()

            return data

        def on_settings_save(self, data):
            for name, programmer in octoprint_flasharduino.config.programmers.items():
                programmer.on_settings_save(data[name])
                del data[name]

            super(self.__class__, self).on_settings_save(data)

        def get_template_configs(self):
            template_configs = [
                dict(type="settings", template="flasharduino_settings.jinja2", custom_bindings=True),
                dict(type="plugin_flasharduino_settings", suffix="_main", template="flasharduino_flash.jinja2", custom_bindings=False)
            ]

            for name, programmer in octoprint_flasharduino.config.programmers.items():
                programmer_template_configs = programmer.get_template_configs()
                if programmer_template_configs is not None:
                    for k in programmer_template_configs:
                        update = dict(suffix="_"+programmer._identifier)
                        if "name" not in k:
                            update["name"] = programmer._identifier

                        k.update(update)

                    template_configs = dict_list_merge(template_configs, programmer_template_configs)

            return template_configs

        ## Blueprint Plugin
        @octoprint.plugin.BlueprintPlugin.route("/boards", methods=["GET"])
        @restricted_access
        @admin_permission.require(403)
        def getBoardList(self):
            return flask.jsonify(boards=octoprint_flasharduino.config.boards)

        @octoprint.plugin.BlueprintPlugin.route("/flash", methods=["POST"])
        @restricted_access
        @admin_permission.require(403)
        def flash_file(self):
            from shutil import copy2
            import tempfile

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

                    options=dict(
                        hex_path=temp_file.name,
                        **flask.request.form.to_dict(True)
                    )

                    ## TODO: get Programmer and call upload
                    if "programmer" in flask.request.form:
                        programmer = octoprint_flasharduino.config.get_programmer(flask.request.form["programmer"])
                        if programmer is None:
                            self._logger.debug("Programmer not found $s" % flask.request.form["programmer"])
                            return flask.make_response("Programmer not found", 500)

                        self._reset_progress(flask.request.form["programmer"])
                        programmer.flash_file(options)

                except Exception as e:
                    self._logger.exception("Error while copying file")
                    return flask.make_response("Something went wrong while copying file with message: {message}".format(message=str(e)), 500)
                finally:
                    os.remove(temp_file.name)
                    self._logger.debug("File deleted with name %s" % temp_file.name)

            else:
                self._logger.warn("No .hex file included for flashing, aborting")
                if "programmer" in flask.request.form:
                    self._send_result_update(flask.request.form["programmer"], "failed")
                return flask.make_response("No .hex file included", 400)

            return flask.make_response("SUPER SUCCESS", 201)

        def allowed_file(self, filename):
            allowed_exts = []
            for name, programmer in octoprint_flasharduino.config.programmers.items():
                exts = programmer.allowed_extensions()
                if exts is not None:
                    allowed_exts = dict_list_merge(exts, allowed_exts)

            ext = os.path.splitext(filename)[1][1:]
            self._logger.debug(ext)
            return ext in allowed_exts

        def _reset_progress(self, programmer):
            self._send_progress_update(programmer=programmer, progress="reset", bar_type="all")

        def _send_progress_update(self, programmer, progress, bar_type):
            self._plugin_manager.send_plugin_message(self._identifier,
                                                     dict(type="progress", programmer=programmer, progress=progress, bar_type=bar_type))

        def _send_result_update(self, programmer, result):
            self._plugin_manager.send_plugin_message(self._identifier, dict(type="result", programmer=programmer, result=result))

        def _log(self, programmer, lines, prefix=None, stream=None, strip=True):
            if strip:
                lines = map(lambda x: x.strip(), lines)

            self._plugin_manager.send_plugin_message(self._identifier, dict(type="loglines", programmer=programmer,
                                                                            loglines=[dict(line=line, stream=stream) for
                                                                                      line in lines]))

def dict_merge(a, b):
    from copy import deepcopy

    result = deepcopy(a)
    for k, v in b.iteritems():
        if k in result:
            if isinstance(result[k], dict) or isinstance(result[k], list):
                result[k] = dict_list_merge(result[k], v)
            else:
                result[k] = deepcopy(v)
        else:
            result[k] = deepcopy(v)

    return result

def dict_list_merge(a, b):
    if isinstance(a, dict) and isinstance(b, dict):
        return dict_merge(a, b)

    if isinstance(a, list) and isinstance(b, list):
        return a + b

    return None

__plugin_name__ = "Flash Arduino"
def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = FlashArduino()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.server.http.bodysize": __plugin_implementation__.bodysize_hook,
        "octoprint.ui.web.templatetypes": __plugin_implementation__.templatehook
    }

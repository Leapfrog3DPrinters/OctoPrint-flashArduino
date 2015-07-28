__author__ = 'Salandora'
import os

from octoprint.settings import settings
from octoprint.util import deprecated

from octoprint_flasharduino.config import register_board

def programmer_settings(plugin_identifier, programmer_key, defaults=None, get_preprocessors=None, set_preprocessors=None):
    """
    Factory method for creating a :class:`ProgrammerSettings` instance.

    Arguments:
        plugin_identifier (string): The plugin identifier
        programmer_key (string): The programmer identifier for which to create the settings instance.
        defaults (dict): The default settings for the plugin.
        get_preprocessors (dict): The getter preprocessors for the plugin.
        set_preprocessors (dict): The setter preprocessors for the plugin.

    Returns:
        ProgrammerSettings: A fully initialized :class:`ProgrammerSettings` instance to be used to access the programmer's
            settings
    """
    return ProgrammerSettings(settings(), plugin_identifier, programmer_key, defaults=defaults, get_preprocessors=get_preprocessors, set_preprocessors=set_preprocessors)

class Programmer(object):
    def __init__(self, identifier):
        self._identifier = identifier

    def initialize(self):
        pass

    def get_settings_preprocessors(self):
        return dict(), dict()

    def on_settings_load(self):
        data = self._settings.get([], asdict=True, merged=True)
        if "_config_version" in data:
            del data["_config_version"]
        return data

    def on_settings_save(self, data):
        import octoprint.util

        if "_config_version" in data:
            del data["_config_version"]

        current = self._settings.get([], asdict=True, merged=True)
        merged = octoprint.util.dict_merge(current, data)
        self._settings.set([], merged)

    def get_settings_defaults(self):
        return None

    def get_template_configs(self):
        return None

    def get_assets(self):
        return None

    def flash_file(self, options):
        pass

    def _check_progress(self, line):
        pass

    def allowed_extensions(self):
        return []

    def register_board(self, text, options):
        options.update(programmer=self._identifier)
        board = dict(
            text=text,
            value=options
        )
        register_board(board)

    def _log_stdout(self, *lines):
        self._log(lines, prefix=">", stream="stdout")

    def _log_stderr(self, *lines):
        self._log(lines, prefix="!", stream="stderr")

    def _log(self, lines, prefix=None, stream=None, strip=True):
        self._plugin._log(self._identifier, lines, prefix=prefix, stream=stream, strip=strip)

        for line in lines:
            self._check_progress(line)
            self._logger.debug(u"{prefix} {line}".format(**locals()))

    def _reset_progress(self):
        self._plugin._reset_progress()

    def _send_progress_update(self, progress, bar_type):
        self._plugin._send_progress_update(programmer=self._identifier, progress=progress, bar_type=bar_type)

    def _send_result_update(self, result):
        self._plugin._send_result_update(programmer=self._identifier, result=result)

# copy pasted from OctoPrints PluginSettings
class ProgrammerSettings(object):
    def __init__(self, settings, plugin_identifier, programmer_key, defaults=None, get_preprocessors=None, set_preprocessors=None):
        self.settings = settings
        self.plugin_identifier = plugin_identifier
        self.programmer_key = programmer_key

        if defaults is None:
            defaults = dict()
        self.defaults = dict(plugins=dict())
        self.defaults["plugins"][plugin_identifier] = dict()
        self.defaults["plugins"][plugin_identifier][programmer_key] = defaults
        self.defaults["plugins"][plugin_identifier][programmer_key]["_config_version"] = None

        if get_preprocessors is None:
            get_preprocessors = dict()
        self.get_preprocessors = dict(plugins=dict())
        self.get_preprocessors["plugins"][plugin_identifier] = dict()
        self.get_preprocessors["plugins"][plugin_identifier][programmer_key] = get_preprocessors

        if set_preprocessors is None:
            set_preprocessors = dict()
        self.set_preprocessors = dict(plugins=dict())
        self.set_preprocessors["plugins"][plugin_identifier] = dict()
        self.set_preprocessors["plugins"][plugin_identifier][programmer_key] = set_preprocessors

        def prefix_path(path):
            return ['plugins', self.plugin_identifier, self.programmer_key] + path

        def prefix_path_in_args(args, index=0):
            result = []
            if index == 0:
                result.append(prefix_path(args[0]))
                result.extend(args[1:])
            else:
                args_before = args[:index - 1]
                args_after = args[index + 1:]
                result.extend(args_before)
                result.append(prefix_path(args[index]))
                result.extend(args_after)
            return result

        def add_getter_kwargs(kwargs):
            if not "defaults" in kwargs:
                kwargs.update(defaults=self.defaults)
            if not "preprocessors" in kwargs:
                kwargs.update(preprocessors=self.get_preprocessors)
            return kwargs

        def add_setter_kwargs(kwargs):
            if not "defaults" in kwargs:
                kwargs.update(defaults=self.defaults)
            if not "preprocessors" in kwargs:
                kwargs.update(preprocessors=self.set_preprocessors)
            return kwargs

        self.access_methods = dict(
            get=("get", prefix_path_in_args, add_getter_kwargs),
            get_int=("getInt", prefix_path_in_args, add_getter_kwargs),
            get_float=("getFloat", prefix_path_in_args, add_getter_kwargs),
            get_boolean=("getBoolean", prefix_path_in_args, add_getter_kwargs),
            set=("set", prefix_path_in_args, add_setter_kwargs),
            set_int=("setInt", prefix_path_in_args, add_setter_kwargs),
            set_float=("setFloat", prefix_path_in_args, add_setter_kwargs),
            set_boolean=("setBoolean", prefix_path_in_args, add_setter_kwargs)
        )
        self.deprecated_access_methods = dict()

    def global_get(self, path, **kwargs):
        """
        Getter for retrieving settings not managed by the plugin itself from the core settings structure. Use this
        to access global settings outside of your plugin.

        Directly forwards to :func:`octoprint.settings.Settings.get`.
        """
        return self.settings.get(path, **kwargs)

    def global_get_int(self, path, **kwargs):
        """
        Like :func:`global_get` but directly forwards to :func:`octoprint.settings.Settings.getInt`.
        """
        return self.settings.getInt(path, **kwargs)

    def global_get_float(self, path, **kwargs):
        """
        Like :func:`global_get` but directly forwards to :func:`octoprint.settings.Settings.getFloat`.
        """
        return self.settings.getFloat(path, **kwargs)

    def global_get_boolean(self, path, **kwargs):
        """
        Like :func:`global_get` but directly orwards to :func:`octoprint.settings.Settings.getBoolean`.
        """
        return self.settings.getBoolean(path, **kwargs)

    def global_set(self, path, value, **kwargs):
        """
        Setter for modifying settings not managed by the plugin itself on the core settings structure. Use this
        to modify global settings outside of your plugin.

        Directly forwards to :func:`octoprint.settings.Settings.set`.
        """
        self.settings.set(path, value, **kwargs)

    def global_set_int(self, path, value, **kwargs):
        """
        Like :func:`global_set` but directly forwards to :func:`octoprint.settings.Settings.setInt`.
        """
        self.settings.setInt(path, value, **kwargs)

    def global_set_float(self, path, value, **kwargs):
        """
        Like :func:`global_set` but directly forwards to :func:`octoprint.settings.Settings.setFloat`.
        """
        self.settings.setFloat(path, value, **kwargs)

    def global_set_boolean(self, path, value, **kwargs):
        """
        Like :func:`global_set` but directly forwards to :func:`octoprint.settings.Settings.setBoolean`.
        """
        self.settings.setBoolean(path, value, **kwargs)

    def global_get_basefolder(self, folder_type, **kwargs):
        """
        Retrieves a globally defined basefolder of the given ``folder_type``. Directly forwards to
        :func:`octoprint.settings.Settings.getBaseFolder`.
        """
        return self.settings.getBaseFolder(folder_type, **kwargs)

    def get_plugin_logfile_path(self, postfix=None):
        """
        Retrieves the path to a logfile specifically for the plugin. If ``postfix`` is not supplied, the logfile
        will be named ``plugin_<plugin identifier>_<programmer_key>.log`` and located within the configured ``logs`` folder. If a
        postfix is supplied, the name will be ``plugin_<plugin identifier>_<programmer_key>_<postfix>.log`` at the same location.

        Plugins may use this for specific logging tasks. For example, a :class:`~octoprint.plugin.SlicingPlugin` might
        want to create a log file for logging the output of the slicing engine itself if some debug flag is set.

        Arguments:
            postfix (str): Postfix of the logfile for which to create the path. If set, the file name of the log file
                will be ``plugin_<plugin identifier>_<programmer_key>_<postfix>.log``, if not it will be
                ``plugin_<plugin identifier>_<programmer_key>.log``.

        Returns:
            str: Absolute path to the log file, directly usable by the plugin.
        """
        filename = "plugin_" + self.plugin_identifier + "_" + self.programmer_key
        if postfix is not None:
            filename += "_" + postfix
        filename += ".log"
        return os.path.join(self.settings.getBaseFolder("logs"), filename)

    def __getattr__(self, item):
        all_access_methods = self.access_methods.keys() + self.deprecated_access_methods.keys()
        if item in all_access_methods:
            decorator = None
            if item in self.deprecated_access_methods:
                new = self.deprecated_access_methods[item]
                decorator = deprecated("{old} has been renamed to {new}".format(old=item, new=new),
                                       stacklevel=2)
                item = new

            settings_name, args_mapper, kwargs_mapper = self.access_methods[item]
            if hasattr(self.settings, settings_name) and callable(getattr(self.settings, settings_name)):
                orig_func = getattr(self.settings, settings_name)
                if decorator is not None:
                    orig_func = decorator(orig_func)

                def _func(*args, **kwargs):
                    return orig_func(*args_mapper(args), **kwargs_mapper(kwargs))

                _func.__name__ = item
                _func.__doc__ = orig_func.__doc__ if "__doc__" in dir(orig_func) else None

                return _func

        return getattr(self.settings, item)


from . import avrdude

$(function() {
    function FlashArduinoViewModel(parameters) {
        var self = this;

        self.settings = parameters[0];
        self.loginState = parameters[1];




        self.requestData = function() {
            $.ajax({
                url: API_BASEURL + "connection",
                method: "GET",
                dataType: "json",
                success: function(response) {
                    self.fromResponse(response);
                }
            })
        };

        self.fromResponse = function(response) {
            var ports = response.options.ports;
            var baudrates = response.options.baudrates;
            var portPreference = response.options.portPreference;
            var baudratePreference = response.options.baudratePreference;
            var printerPreference = response.options.printerProfilePreference;
            var printerProfiles = response.options.printerProfiles;

            self.portOptions(ports);
            self.baudrateOptions(baudrates);

            if (!self.selectedPort() && ports && ports.indexOf(portPreference) >= 0)
                self.selectedPort(portPreference);
            if (!self.selectedBaudrate() && baudrates && baudrates.indexOf(baudratePreference) >= 0)
                self.selectedBaudrate(baudratePreference);
            if (!self.selectedPrinter() && printerProfiles && printerProfiles.indexOf(printerPreference) >= 0)
                self.selectedPrinter(printerPreference);

            self.saveSettings(false);
        };

        self._displayNotification = function(response, titleSuccess, textSuccess) {
            if (response.result) {
                new PNotify({
                    title: "Flashing firmware succeeded",
                    text: textSuccess,
                    type: "success",
                    hide: false
                })
            } else {
                new PNotify({
                    title: gettext("Something went wrong"),
                    text: gettext("Flashing the firmware failed, please see the log for details"),
                    type: "error",
                    hide: false
                });
            }
        };

        self.onStartup = function() {
            self.requestData();
        };

     }
    // This is how our plugin registers itself with the application, by adding some configuration
    // information to the global variable ADDITIONAL_VIEWMODELS
    ADDITIONAL_VIEWMODELS.push([
        // This is the constructor to call for instantiating the plugin
        FlashArduinoViewModel,

        // This is a list of dependencies to inject into the plugin, the order which you request
        // here is the order in which the dependencies will be injected into your view model upon
        // instantiation via the parameters argument
        ["settingsViewModel", "loginStateViewModel"],

        // Finally, this is the list of all elements we want this view model to be bound to.
        [document.getElementById("#settings_plugin_flasharduino")]
    ]);
});

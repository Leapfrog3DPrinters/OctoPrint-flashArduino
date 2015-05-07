$(function() {
    function FlashArduinoViewModel(parameters) {
        var self = this;

        self.settings = parameters[0];
        self.loginState = parameters[1];
        self.connection = parameters[2];

        self.hex_path = ko.observable();

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

     }
    // This is how our plugin registers itself with the application, by adding some configuration
    // information to the global variable ADDITIONAL_VIEWMODELS
    ADDITIONAL_VIEWMODELS.push([
        // This is the constructor to call for instantiating the plugin
        FlashArduinoViewModel,

        // This is a list of dependencies to inject into the plugin, the order which you request
        // here is the order in which the dependencies will be injected into your view model upon
        // instantiation via the parameters argument
        ["settingsViewModel", "loginStateViewModel", "connectionViewModel"],

        // Finally, this is the list of all elements we want this view model to be bound to.
        [document.getElementById("#settings_plugin_flasharduino")]
    ]);
});

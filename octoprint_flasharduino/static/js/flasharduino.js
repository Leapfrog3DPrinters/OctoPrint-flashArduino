$(function() {
    function FlashArduinoViewModel(parameters) {
        var self = this;

        self.settingsViewModel = parameters[0];
        self.loginState = parameters[1];
        self.connection = parameters[2];

        // Variables that will be passed to avrdude
        self.hex_path = ko.observable(undefined);
        self.selected_port = ko.observable(undefined);
        self.selected_board = ko.observableArray();

        self.flash_button = $("#settings-flash-arduino-start");
        self.upload_hex = $("#settings-flash-arduino");


        self.boards = [
            {"value": {"board": "m2560", "programmer": "wiring", "baudrate": "115200"}, "text": gettext("ATmega2560 Leapfrog CreatrHS, Ultimaker 2, RAMPS 1.4, RAMBo")},
            {"value": {"board": "m1280", "programmer": "arduino", "baudrate": "57600"}, "text": gettext("ATmega1280 Arduino Mega")},
            {"value": {"board": "m328p", "programmer": "arduino", "baudrate": "57600"}, "text": gettext("Duemilanove /w ATmega328")},
            {"value": {"board": "atmega168", "programmer": "arduino", "baudrate": "19200"}, "text": gettext("Duemilanove /w ATmega168")},
            {"value": {"board": "atmega1284p", "programmer": "stk500", "baudrate": "57600"}, "text": gettext("Sanguino /w ATmega1284P")},
            {"value": {"board": "atmega644p", "programmer": "stk500", "baudrate": "57600"}, "text": gettext("Sanguino /w ATmega644P")}
        ];

        self.upload_hex.fileupload({
            dataType: "json",
            maxNumberOfFiles: 1,
            autoUpload: false,
            add: function(e, data) {
                if (data.files.length == 0) {
                    return false;
                }
                self.hex_path(data.files[0].name);
                self.flash_button.unbind("click");
                self.flash_button.on("click", function() {
                    var flash_data = {
                        board: self.selected_board().board,
                        programmer: self.selected_board().programmer,
                        port: self.selected_port(),
                        baudrate: self.selected_board().baudrate
                    }; 
                    data.formData = flash_data;
                    data.submit();
                });
            },
            done: function(e, data) {
                return;
            }
        });

        self._displayNotification = function(response) {
            if (response == "success") {
                new PNotify({
                    title: gettext("Flashing firmware succeeded"),
                    text: gettext("Congratulations flashing the firmware was a success!"),
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

        self.bar_progress = function(bar_type, progress) {
            if(progress == "reset"){
                var bar_types = ["flash_read", "flash_write", "flash_verify", "flash_done"];
                _.each(bar_types, function(bar_type){
                    $("#"+bar_type+"_progress").removeClass();
                    $("#"+bar_type+"_progress").addClass("progress progress-info");
                });
            }

            if(progress == "busy"){
                $("#"+bar_type+"_progress").removeClass("progress-info");
                $("#"+bar_type+"_progress").addClass("progress-striped progress-warning active");
            }
            if(progress == "done"){
                $("#"+bar_type+"_progress").removeClass("progress-striped progress-warning active");
                $("#"+bar_type+"_progress").addClass("progress-success");
            }

        };

        self.onDataUpdaterPluginMessage = function(plugin, data) {
            if (plugin != "flasharduino") {
                return;
            }

            if (!data.hasOwnProperty("type")) {
                return;
            }

            var messageType = data.type;

            if (messageType == "progress") {
                var progress = data.progress;
                var bar_type = data.bar_type;

                self.bar_progress(bar_type, progress);


            } else if (messageType == "result") {
                var result = data.result
                self._displayNotification(result);
            }

        };

        self.onBeforeBinding = function () {
            self.settings = self.settingsViewModel.settings;
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
        ["#settings_plugin_flasharduino"]
    ]);
});

$(function() {
    function FlashArduinoViewModel(parameters) {
        var self = this;

        self.settingsViewModel = parameters[0];
        self.loginState = parameters[1];
        self.connection = parameters[2];

        // Variables that will be passed to avrdude
        self.hex_path = ko.observable(undefined);
        self.selected_port = ko.observable(undefined);
        self.selected_baudrate = ko.observable(undefined);
        self.selected_board = ko.observable(undefined);
        self.selected_programmer = ko.observable(undefined);

        self.flash_button = $("#settings-flash-arduino-start");
        self.upload_hex = $("#settings-flash-arduino");

        // Arrays of options
        self.programmers = [
            {"value": "arduino", "text": gettext("Arduino programmer")},
            {"value": "avr910", "text": gettext("AVR910")},
            {"value": "butterfly", "text": gettext("Atmel Butterfly evaluation board; Atmel AppNotes AVR109, AVR911")},
            {"value": "butterfly_mk", "text": gettext("Mikrokopter.de Butterfly")},
            {"value": "par", "text": gettext("Parallel port bitbanging")},
            {"value": "stk500", "text": gettext("Atmel STK500 Version 1.x firmware")},
            {"value": "stk500generic", "text": gettext("Atmel STK500, autodetect firmware version")},
            {"value": "stk500v2", "text": gettext("Atmel STK500 Version 2.x firmware")},
            {"value": "stk500hvsp", "text": gettext("Atmel STK500 V2 in high-voltage serial programming mode")},
            {"value": "stk500pp", "text": gettext("Atmel STK500 V2 in parallel programming mode")},
            {"value": "stk600", "text": gettext("Atmel STK600")},
            {"value": "stk600hvsp", "text": gettext("Atmel STK600 in high-voltage serial programming mode")},
            {"value": "stk600pp", "text": gettext("Atmel STK600 in parallel programming mode")},
            {"value": "wiring", "text": gettext("Wiring. Basically STK500v2 protocol, with some glue to trigger the bootloader")}
        ];


        self.boards = [
            {"value": "usb1286", "text": gettext("AT90USB1286 Teensy++ ")},
            {"value": "m1280", "text": gettext("ATmega1280 Arduino Mega")},
            {"value": "m2560", "text": gettext("ATmega2560 Leapfrog CreatrHS, Ultimaker, RAMPS 1.3")},
            {"value": "m644 ", "text": gettext("ATmega644 SanguinoA")},
            {"value": "m644p", "text": gettext("ATmega644P Sanguino")},
            {"value": "m1284p", "text": gettext("ATmega1284P Sanguino")},
            {"value": "m328p", "text": gettext("ATmega328P Duemilanove")},
            {"value": "usb646", "text": gettext("AT90USB646 Brainwave")}
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
                        board: self.selected_board(),
                        programmer: self.selected_programmer(),
                        port: self.selected_port(),
                        baudrate: self.selected_baudrate()
                    }; 
                    data.formData = flash_data;
                    data.submit();
                });
            },
            done: function(e, data) {
                return;
            }
        });

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

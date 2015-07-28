$(function() {
    function FlashArduinoViewModel(parameters) {
        var self = this;

        self.settingsViewModel = parameters[0];
        self.loginState = parameters[1];
        self.connection = parameters[2];

        // Variables that will be passed to avrdude
        self.hex_path = ko.observable(undefined);
        self.selected_port = ko.observable(undefined);
        self.selected_board = ko.observable();
        self.boards = ko.observableArray([]);

        self.flash_button = $("#settings-flash-arduino-start");
        self.upload_hex = $("#settings-flash-arduino");

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
                        port: self.selected_port()
                    };
                    $.extend(true, flash_data, self.selected_board());

                    var status = $('#status_plugin_flasharduino_' + self.selected_board().programmer);
                    if (status !== undefined)
                        status.addClass('active');

                    data.formData = flash_data;
                    data.submit();
                });
            },
            done: function(e, data) {
                return;
            }
        });

        self.onSettingsShown = function () {
            self.requestData();
        };

        self.requestData = function () {
            $.ajax({
                url: "/plugin/flasharduino/boards",
                method: "GET",
                dataType: "json",
                success: function (response) {
                    self._fromResponse(response);
                }
            });
        };

        self._fromResponse = function (response) {
            self.boards(response.boards)
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

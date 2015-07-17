/**
 * Created by Salandora on 17.07.2015.
 */
$(function() {
    function FlashArduinoTerminalViewModel(parameters) {
        var self = this;

        self.log = ko.observableArray([]);
        self.buffer = ko.observable(300);

        self.autoscrollEnabled = ko.observable(true);
        self.autoscrollEnabled.subscribe(function(newValue) {
            if (newValue) {
                self.log(self.log.slice(-self.buffer()));
            }
        });

        self.displayedLines = ko.computed(function() {
            return self.log();
        });
        self.displayedLines.subscribe(function() {
            self.updateOutput();
        });

        self.updateOutput = function() {
            if (self.autoscrollEnabled()) {
                self.scrollToEnd();
            }
        };

        self.toggleAutoscroll = function() {
            self.autoscrollEnabled(!self.autoscrollEnabled());
        };

        self.appendLines = function(lines) {
            self.log(self.log().concat(lines));
            if (self.autoscrollEnabled()) {
                self.log(self.log.slice(-self.buffer()));
            }
        }

        self.scrollToEnd = function() {
            var container = $("#flasharduino-terminal-output");
            if (container.length) {
                container.scrollTop(container[0].scrollHeight - container.height())
            }
        };
     }
    // This is how our plugin registers itself with the application, by adding some configuration
    // information to the global variable ADDITIONAL_VIEWMODELS
    ADDITIONAL_VIEWMODELS.push([
        FlashArduinoTerminalViewModel,
        [],
        ["#settings_plugin_flasharduino_terminal"]
    ]);
});

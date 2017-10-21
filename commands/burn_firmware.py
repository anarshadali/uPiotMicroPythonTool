import sublime
from sublime_plugin import WindowCommand

from glob import glob
from json import loads
from os.path import join, basename

from .. import tools
from ..tools import paths
from ..tools import serial


class upiotBurnFirmwareCommand(WindowCommand):
    items = None
    firmwares = None
    url = None

    def run(self):
        self.items = []
        self.firmwares = paths.firmware_folder('esp32')
        self.firmware_list()

        tools.quick_panel(self.items, self.callback_selection)

    def callback_selection(self, selection):
        """Firmware selection

        Receive the user selection and run the burn process
        in a new thread

        Arguments:
            selection {int} -- user index selection
        """
        if(selection == -1):
            return

        self.url = self.items[selection]
        sublime.set_timeout_async(self.burn_firmware, 0)

    def firmware_list(self):
        """Firmware files list

        Lis of file in the firmwares folder
        """
        firm_path = join(self.firmwares, '*')

        for firmware in glob(firm_path):
            name = basename(firmware)
            self.items.append(name)

    def burn_firmware(self):
        """Burn firmware

        Uses esptool.py to burn the firmware
        """
        filename = self.url.split('/')[-1]
        firmware = join(self.firmwares, filename)

        options = self.get_board_options('esp32')
        options.append(firmware)

        port = serial.selected_port()
        if(not port):
            return

        caption = "Do you want to erase the flash memory?"
        answer = sublime.yes_no_cancel_dialog(caption, "Yes", "No")

        # stop
        if(answer == sublime.DIALOG_CANCEL):
            return

        # show console
        tools.show_console()

        # erase flash
        if(answer == sublime.DIALOG_YES):
            tools.erase_flash()

        options.insert(0, "--port " + port)

        if(not serial.check_port(port)):
            return

        tools.run_command(options)

    @staticmethod
    def get_board_options(board):
        """get board option

        get the options defined in the json board file

        Arguments:
            board {str} -- board selected

        Returns:
            list -- board options
        """
        board_folder = paths.boards_folder()
        filename = board + '.json'
        board_path = join(board_folder, filename)

        board_file = []
        with open(board_path) as file:
            board_file = loads(file.read())

        options = []
        for key, value in board_file['upload'].items():
            if('write_flash' not in key):
                separator = '' if key.endswith('=') else ' '
                option = "{0}{1}{2}".format(key, separator, value)
                options.append(option)

        wf = board_file['upload']['write_flash']
        options.append('write_flash ' + wf)

        return options

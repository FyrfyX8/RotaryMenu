import time
from abc import ABC
from .encoder import Encoder
from RPLCD.i2c import CharLCD
import RPi.GPIO as GPIO
import asyncio
from pathlib import Path
from collections.abc import Callable

defaultLCD = CharLCD(i2c_expander="PCF8574", address=0x27, port=1, cols=20, rows=4, dotsize=8)


class DynamicSlot:
    """
    A Class to format strings with return functions whenever used in string

    Attributes
    ----------
        slot : str
            A formatted string.
        function : dict[str, function]
            A dictionary containing functions with the key set to a value
            from the formatted string.
        function_args: dict[str, tuple]
            A dictionary containing tuples for the function calls, the key
            is the same as the function key plus an _args at the end.
    """

    def __init__(self, slot: str, **kwargs: Callable[..., ...] | tuple):
        """
        Parameters
        ----------
            slot : str
                A formatted string.
            **kwargs: Callable[..., ...] | tuple
                A function with the keyword the same as a value in the formatted string,
                or a tuple with arguments for the function using the same name
                as the function keyword plus an _args as the keyword.
        """
        self.slot = slot
        self.function = {}
        self.function_args = {}
        for key in kwargs:
            if callable(kwargs.get(key)):
                self.function[key] = kwargs.get(key)
                if isinstance(kwargs.get(f"{key}_args"), tuple):
                    self.function_args[f"{key}_args"] = kwargs.get(f"{key}_args")

    def __str__(self):
        slot = self.slot
        for key in self.function:
            slot = slot.replace(f"{{{key}}}", str(self.function[key](*self.function_args.get(f"{key}_args", ()))))
        return slot


class MenuType(ABC):
    """
    Base class with function for all MenuTypes.

    Attributes
    ----------
        slots : list[str | DynamicSlot]
            A list of strings or DynamicSlot's.
        value_callback : callable
            A function with parameters (callback_type, value).
            possible callback_type's and its values:
                "setup":
                    "none"
                "after_setup":
                    "none"
                "press":
                    int based on the slot index.
                "direction":
                    "L" or "R" based on the turned direction.
                "dir_press":
                    a pathlib.Path containing the Path to the directory.
                "file_press":
                    a pathlib.Path containing the Path to the file.
        do_setup_callback : bool
            A bool, if True a RotaryMenu class will call the value_callback
            function with callback_type "setup" before this menu is set.
        after_reset_callback : bool
            A bool, if True a RotaryMenu class will call the value_callback
            function with callback_type "after_setup" after this menu is set.
        custom_cursor : bool
            A bool, if True a RotaryMenu class will call the value_callback
            function with callback_type "direction" when the rotary encoder
            is turned.

    Methods
    -------
        change_slot(index: int, slot: str | DynamicSlot)
            Changes an entry in slots based on an index.
    """

    def __init__(self, slots: list[str | DynamicSlot] = None, value_callback: callable = None, do_setup_callback=False,
                 after_reset_callback=False, custom_cursor=False):
        """
        Parameters
        ----------
            slots : list[str | DynamicSlot]
                A list of strings or DynamicSlot's.
            value_callback : callable
                A function with parameters (callback_type, value).
                possible callback_type's and its values:
                    "setup":
                        "none"
                    "after_setup":
                        "none"
                    "press":
                        int based on the slot index.
                    "direction":
                        "L" or "R" based on the turned direction.
            do_setup_callback : bool
                A bool, if True a RotaryMenu class will call the value_callback
                function with callback_type "setup" before this menu is set.
            after_reset_callback : bool
                A bool, if True a RotaryMenu class will call the value_callback
                function with callback_type "after_setup" after this menu is set.
            custom_cursor : bool
                A bool, if True a RotaryMenu class will call the value_callback
                function with callback_type "direction" when the rotary encoder
                is turned.
        """
        self.slots = slots
        self.value_callback = value_callback
        self.do_setup_callback = do_setup_callback
        self.after_reset_callback = after_reset_callback
        self.custom_cursor = custom_cursor

    def change_slot(self, index: int, slot: str | DynamicSlot):
        self.slots[index] = slot


class MenuMain(MenuType):
    """
    A class to be used in a RotaryMenu classes main argument.
    """

    def __init__(self, slots: list[str, DynamicSlot], value_callback: callable, do_setup_callback=False,
                 after_reset_callback=False, custom_cursor=False):
        """
        Parameters
        ----------
            slots : list[str | DynamicSlot]
                A list of strings or DynamicSlot's.
            value_callback : callable
                A function with parameters (callback_type, value).
                possible callback_type's and its values:
                    "setup":
                        "none"
                    "after_setup":
                        "none"
                    "press":
                        int based on the slot index.
                    "direction":
                        "L" or "R" based on the turned direction.
            do_setup_callback : bool
                A bool, if True a RotaryMenu class will call the value_callback
                function with callback_type "setup" before this menu is set.
            after_reset_callback : bool
                A bool, if True a RotaryMenu class will call the value_callback
                function with callback_type "after_setup" after this menu is set.
            custom_cursor : bool
                A bool, if True a RotaryMenu class will call the value_callback
                function with callback_type "direction" when the rotary encoder
                is turned.
        """
        super().__init__(slots=slots, value_callback=value_callback, do_setup_callback=do_setup_callback,
                         after_reset_callback=after_reset_callback, custom_cursor=custom_cursor)


class MenuSub(MenuType):
    """
        A class to be used as a sub menu.
    """

    def __init__(self, slots: list[str, DynamicSlot], value_callback: callable, do_setup_callback=False,
                 after_reset_callback=False, custom_cursor=False):
        """
        Parameters
        ----------
            slots : list[str | DynamicSlot]
                A list of strings or DynamicSlot's.
            value_callback : callable
                A function with parameters (callback_type, value).
                possible callback_type's and its values:
                    "setup":
                        "none"
                    "after_setup":
                        "none"
                    "press":
                        int based on the slot index.
                    "direction":
                        "L" or "R" based on the turned direction.
            do_setup_callback : bool
                A bool, if True a RotaryMenu class will call the value_callback
                function with callback_type "setup" before this menu is set.
            after_reset_callback : bool
                A bool, if True a RotaryMenu class will call the value_callback
                function with callback_type "after_setup" after this menu is set.
            custom_cursor : bool
                A bool, if True a RotaryMenu class will call the value_callback
                function with callback_type "direction" when the rotary encoder
                is turned.
        """
        super().__init__(slots=slots, value_callback=value_callback, do_setup_callback=do_setup_callback,
                         after_reset_callback=after_reset_callback, custom_cursor=custom_cursor)


class MenuFile(MenuType):
    """
    A class to display a filesystem in a RotaryMenu class.

    Attributes
    ----------
        path : Path
            A pathlib.Path, containing the default path.
        current_path : Path
            A pathlib.Path, containing the current path.
        extension_filter : list[str]
            A list containing strings, if the string matches a files extension
            it will be displayed, if None the list is set to [".py"].
        file_menu_depth : int
            A int, if more than 0 the return_to_parent slot is shown.
        show_folders : bool
            A bool, if True folders are shown.
        dir_affix : str
            A string containing one "#+#", the substring before is converted to the prefix and
            the substring after as the suffix.
        file_affix : dict[str, str]
            A directory containing strings like dir_affix if the key matches
            a file extension plus _affix the file will get the substrings as pre and suffix.
        pr_slots : list[str, DynamicSlot]
            A list containing strings or DynamicSlot's that are shown on top,
            when pressed they call value_callback with callback_type "press" and
            the index.
        fmd0_slots : list[str, DynamicSlot]
            A list containing strings or DynamicSlot's that are shown after the
            pr_slots but only if file_menu_depth is 0.
        pr_slots_last_index : int
            A int showing the last index of the pr/ and fmd0_slots, changing this
            could result in errors.
        custom_folder_behaviour : bool
            A bool, if True pressing on directory's won't open them instead value_callback
            with callback_type "dir_press" will be called.
    Methods
    -------
        files_to_slots() -> list[str]
            Returns a list of slots based on the files.
        return_to_parent()
            Returns to the parent directory and decreases file_menu_depth by one.
        set_path(path: Path, file_menu_depth: int = None)
            Sets the current_path to set path and changes the file_menu_depth if wanted.
        move_to_dir(dir_name: str)
            Moves into the given directory and increases the file_menu_depth by one.
        return_to_default()
            Returns to the default path.
        update_slots()
            updates the slots list.
    """

    def __init__(self, path: Path, value_callback: callable, *, extension_filter: list[str] = None,
                 show_folders=True, pr_slots: list[str, DynamicSlot] = None, dir_affix: str = "#+#",
                 custom_folder_behaviour=False, do_setup_callback=False, after_reset_callback=False,
                 custom_cursor=False, **kwargs: str):
        """
        Parameters
        ----------
            path : Path
                A pathlib.Path.
            value_callback : callable
                A function with parameters (callback_type, value).
                possible callback_type's and its values:
                    "setup":
                        "none"
                    "after_setup":
                        "none"
                    "press":
                        int based on the slot index.
                    "direction":
                        "L" or "R" based on the turned direction.
                    "dir_press":
                        a pathlib.Path containing the Path to the directory.
                    "file_press":
                        a pathlib.Path containing the Path to the file.
            extension_filter : list[str]
                A list containing strings, if the string matches a files extension
                it will be displayed, if None the list is set to [".py"].
            show_folders : bool
                A bool, if True folders are shown.
            pr_slots : list[str, DynamicSlot]
                A list containing strings or DynamicSlot's that are shown on top,
                when pressed they call value_callback with callback_type "press" and
                the index.
            dir_affix : str
                A string containing one "#+#", the substring before is converted to the prefix and
                the substring after as the suffix.
            custom_folder_behaviour : bool
                A bool, if True pressing on directory's won't open them instead value_callback
                with callback_type "dir_press" will be called.
            do_setup_callback : bool
                A bool, if True a RotaryMenu class will call the value_callback
                function with callback_type "setup" before this menu is set.
            after_reset_callback : bool
                A bool, if True a RotaryMenu class will call the value_callback
                function with callback_type "after_setup" after this menu is set.
            custom_cursor : bool
                A bool, if True a RotaryMenu class will call the value_callback
                function with callback_type "direction" when the rotary encoder
                is turned.
            **kwargs : str
                Keywords with a file extension plus _affix are used for file_affix, the string
                has to contain "#+#" as a separator.
        """
        self.path = path
        self.current_path = path
        self.extension_filter = extension_filter if extension_filter is not None else [".py"]
        self.file_menu_depth = 0
        self.show_folders = show_folders
        self.dir_affix = (dir_affix if dir_affix.count("#+#") == 1 else "#+#").split("#+#", 1)
        self.file_affix = {k: kwargs[k] for k in kwargs if k.endswith("_affix") and kwargs[k].count("#+#") == 1}
        self.pr_slots = pr_slots
        self.fmd0_slots = []
        self.pr_slots_last_index = len(pr_slots) - 1
        self.custom_folder_behaviour = custom_folder_behaviour

        super().__init__(self.pr_slots + self.fmd0_slots + self.files_to_slots(), value_callback=value_callback,
                         do_setup_callback=do_setup_callback,
                         after_reset_callback=after_reset_callback, custom_cursor=custom_cursor)

    def files_to_slots(self) -> list[str]:
        """
        Returns a list of slots based on the files.
        """
        file_slots = []
        if self.file_menu_depth > 0:
            file_slots.append(f"{self.dir_affix[0]}#+#..#+#{self.dir_affix[1]}")
        for folder in self.current_path.iterdir():
            if folder.is_dir() and not folder.name.startswith("__"):
                file_slots.append(f"{self.dir_affix[0]}#+#{folder.name}#+#{self.dir_affix[1]}")
        for file in self.current_path.iterdir():
            if file.is_file() and file.suffix in self.extension_filter:
                affix_filter = ""
                for extension in file.suffixes:
                    affix_filter = f"{affix_filter}{extension[1:]}_"
                affix_filter = f"{affix_filter}affix"
                if self.file_affix.get(affix_filter) is not None:
                    backed_file_affix = str(self.file_affix.get(affix_filter)).split("#+#", 1)
                    file_slots.append(f"{backed_file_affix[0]}#+#{file.name}#+#{backed_file_affix[1]}")
                else:
                    file_slots.append(f"#+#{file.name}#+#")
        return file_slots

    def return_to_parent(self):
        """
        Returns to the parent directory and decreases file_menu_depth by one.
        """
        self.file_menu_depth -= 1
        self.set_path(self.current_path.parent)

    def set_path(self, path: Path, file_menu_depth: int = None):
        """
        Sets the current_path to set path and changes the file_menu_depth if wanted.
        Parameters
        ----------
            path : Path
                A pathlib.Path to set the current_path to.
            file_menu_depth : int
                A int to set the file_menu_depth to. 
        """
        if file_menu_depth is not None:
            if file_menu_depth < 0:
                raise ValueError
            else:
                self.file_menu_depth = file_menu_depth
        self.current_path = path
        self.update_slots()

    def move_to_dir(self, dir_name: str):
        """
        Moves into the given directory and increases the file_menu_depth by one.

        Parameters
        ----------
            dir_name : str
                A string containing the directory name
        """
        if (self.current_path / dir_name).is_dir():
            self.file_menu_depth += 1
            self.set_path(self.current_path / dir_name)

    def return_to_default(self):
        """
        Returns to the default path.
        """
        self.set_path(self.path, 0)

    def update_slots(self):
        """
        Updates the slots list.
        """
        if self.file_menu_depth == 0:
            self.slots = self.pr_slots + self.fmd0_slots + self.files_to_slots()
            self.pr_slots_last_index = len(self.pr_slots + self.fmd0_slots) - 1
        else:
            self.slots = self.pr_slots + self.files_to_slots()
            self.pr_slots_last_index = len(self.pr_slots) - 1


class RotaryMenu:
    """
    A class to manage a menu on a Char LCD.

    Attributes
    ----------
        lcd : CharLCD
            A RPLCD.CharLCD used to display on the Char LCD.
        loop :
            The current running asyncio loop.
        main
            The Set MenuMain menu.
        menu_timeout : int
            If not 0 and the timer reaches this number the menu is set to main.
        timeout_reset : bool
            If True gets set to False after counter was set to 0
        wait : bool
            If True actions will be disabled.
        index : int
            Is used to determine the current index of the slots.
        max_index : int
            The maximal possible index value.
        shift : int
            Is used to determine the shift of the display.
        max_shift : int
            The maximal shift value.
        cursor_pos : int
            The current position of the cursor.
        max_cursor_pos : int
            The maximal position of the cursor on the screen.
        scrolling_start : bool
            If True the timer before an entry is being scrolled is active.
        scrolling : bool
            If True the current entry is being scrolled.
        end_scrolling : bool
            If True the scrolling ends at the next loop.
        scrolling_end : bool
            If True the scrolling of an entry has ended and waits for end_scrolling.
        backed_slots : list[str]
            A list of strings, the formatted version of the slots.

    Methods
    -------
        return_max_index()
            Returns the max_index.
        return_max_shift()
            Returns the max_shift.
        return_max_cursor_pos()
            Returns the max_cursor_pos.
        if_overflow(index)
            Returns True if the current entry is longer than the amount of columns.
        set(menu)
            Sets the current menu to the given menu.
        cursor(pr_cursor_pos)
            Deletes old cursor and writes new one
        reset_cursor()
            Resets the cursor to position 0
        update_current_slot()
            Updates the current slot.
        menu(keep_scrolled)
            Write the current visible slots to the Char LCD.
        reset_menu()
            Resets the current Menu.
    """

    def __init__(self, lcd: CharLCD = defaultLCD, *, left_pin: int, right_pin: int, button_pin: int, main: MenuMain,
                 menu_timeout: int = 0):
        """
        Parameters
        ----------
            lcd : CharLCD
                A RPLCD.CharLCD to write the menu to.
            left_pin : int
                The BCM pins number for the left rotation.
            right_pin : int
                The BCM pins number for the right rotation.
            button_pin : int
                The BCM pins number for button presses.
            main : MenuMain
                The main menu of the RotaryMenu.
            menu_timeout : int
                If not 0 and the timer reaches this number the menu is set to main.
        """

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(button_pin, GPIO.RISING, callback=self.__button_press, bouncetime=300)
        encoder = Encoder(left_pin, right_pin, self.__value_changed)

        self.lcd = lcd
        self.loop = asyncio.get_event_loop()
        self.main = main
        self.menu_timeout = menu_timeout
        self.timeout_reset = False
        self.current_menu = self.main
        self.wait = False
        self.index = 0
        self.max_index = self.return_max_index()
        self.shift = 0
        self.max_shift = self.return_max_shift()
        self.cursor_pos = 0
        self.max_cursor_pos = self.return_max_cursor_pos()
        self.scrolling_start = True
        self.scrolling = False
        self.end_scrolling = False
        self.scrolling_end = False
        self.backed_slots = []
        self.get_backed_slots()
        self.__shift_slot = ""
        self.__shift_str = ""
        self.__shift_backed = ""
        asyncio.run_coroutine_threadsafe(self.__timeout_timer(), self.loop)

    def return_max_index(self):
        """
        Returns the max_index based on the amount of slots.
        """
        return len(self.current_menu.slots) - 1

    def return_max_shift(self):
        """
        Returns the max_shift based on the amount of slots and
        the amount of rows of the display.
        """
        max_shift = len(self.current_menu.slots) - self.lcd.lcd.rows

        if max_shift >= 0:
            return max_shift
        else:
            return 0

    def return_max_cursor_pos(self):
        """
        Returns the max_cursor_pos based on the amount of rows of the display.
        """
        return self.lcd.lcd.rows

    def get_backed_slots(self, save_scrolled=False, /):
        """
        Sets the backed_slots to the formatted version of the current slots

        Parameters
        ----------
            save_scrolled : bool
                If True a backed version of the shifted Slot gets saved.
        """
        backed_slots = []
        index = 0
        for i in self.current_menu.slots:
            slot = str(self.current_menu.slots[index]).split("#+#")
            space = self.lcd.lcd.cols - len(slot[0]) - len(slot[2]) - 1
            if self.if_overflow(index):
                backed_name = slot[1][0:space]
            else:
                backed_name = slot[1] + " " * (space - len(slot[1]))
            if save_scrolled and self.scrolling:
                temp = self.__shift_slot.split("#+#")
                if slot[1] == temp[1]:
                    if len(slot[0]) == len(temp[0]) and len(slot[2]) == len(temp[2]):
                        self.__shift_backed = self.__shift_str
            backed_slots.append(f"{slot[0]}{backed_name}{slot[2]}")
            index += 1
        self.backed_slots = backed_slots

    async def __timeout_timer(self):
        clock = 0
        while self.menu_timeout > 0:
            if clock == self.menu_timeout and self.current_menu != self.main:
                self.__set_wait()
                self.set(self.main)
                self.__reset_wait()
                clock = 0
            if self.timeout_reset:
                self.timeout_reset = False
                clock = 0
            else:
                await asyncio.sleep(1)
                if self.current_menu != self.main and not self.wait:
                    clock += 1

    def if_overflow(self, index: int):
        """
        Returns True if the selected slot exceeds the amount of columns.

        Parameters
        ----------
            index : int
                the index of the slot to check.
        """
        slot = str(self.current_menu.slots[index]).split("#+#")
        len_prefix = len(slot[0])
        len_name = len(slot[1])
        len_suffix = len(slot[2])
        return (len_name + len_suffix + len_prefix + 1) > self.lcd.lcd.cols

    def __reset_wait(self):
        self.wait = False

    def __set_wait(self):
        self.wait = True

    def set(self, menu: MenuType = None, /):
        """
        Sets the current_menu to given menu

        Parameters
        ----------
            menu : MenuType
                The menu to set to.
        """
        while True:
            if not self.wait:
                break
            else:
                time.sleep(0.01)

        self.wait = True
        self.current_menu = menu if menu is not None else self.main
        if self.current_menu.do_setup_callback:
            self.__callback("setup", value="none")
        self.reset_menu(reset_wait=False)
        if self.current_menu.after_reset_callback:
            self.__callback("after_setup", value="none")
        self.wait = False

    def __callback(self, callback_type: str, value=None):
        self.current_menu.value_callback(callback_type, value, self)

    async def __start_scrolling(self):

        if self.if_overflow(self.index) and not self.current_menu.custom_cursor:
            self.scrolling_start = True
            shift = 0
            for t in range(1000):
                if not self.end_scrolling:
                    await asyncio.sleep(0.001)
                else:
                    return
            self.scrolling_start = False
            self.scrolling = True
            self.__shift_slot = self.current_menu.slots[self.index]
            slot = str(self.current_menu.slots[self.index]).split("#+#")
            space = self.lcd.lcd.cols - len(slot[0]) - len(slot[2]) - 1
            for i in range(len(slot[1]) - space + 1):
                while self.wait:
                    await asyncio.sleep(0.01)
                if self.end_scrolling:
                    self.scrolling = False
                    return
                self.wait = True
                self.lcd.cursor_pos = (self.cursor_pos, 1)
                shift_name = slot[1][shift:shift + space]
                self.lcd.write_string(f"{slot[0]}{shift_name}{slot[2]}")
                self.__shift_str = shift_name
                self.wait = False
                shift += 1
                for t in range(25):
                    if not self.end_scrolling:
                        await asyncio.sleep(0.01)
                    else:
                        self.scrolling = False
                        return
            self.scrolling_end = True
            return

    def __stop_scrolling(self, row, index):
        self.end_scrolling = True
        while self.scrolling or self.scrolling_start:
            if self.scrolling_start:
                self.scrolling_start = False
            elif self.scrolling_end:
                self.scrolling_end = False
                self.scrolling = False
            time.sleep(0.01)
        self.end_scrolling = False
        self.__reset_wait()
        if not self.scrolling_start:
            self.lcd.cursor_pos = (row, 1)
            self.lcd.write_string(self.backed_slots[index])

    def cursor(self, pr_cursor_pos: int):
        """
        Deletes the old curser at the old position and writes one at
        the current position.

        Parameters
        ----------
            pr_cursor_pos : int
                The position where to delete the cursor.
        """
        if not self.current_menu.custom_cursor:
            self.lcd.cursor_pos = (pr_cursor_pos, 0)
            self.lcd.write_string(" ")
            self.lcd.cursor_pos = (self.cursor_pos, 0)
            self.lcd.write_string(">")

    def reset_cursor(self):
        """
        Resets the cursor to position 0.
        """
        pr_cursor_pos = self.cursor_pos
        self.index = self.index - self.cursor_pos
        self.cursor_pos = 0
        self.cursor(pr_cursor_pos)

    def update_current_slot(self):
        """
        Updates the slot at cursor position.
        """
        if self.scrolling or self.scrolling_start:
            self.end_scrolling = True
            while self.scrolling:
                if self.scrolling_end:
                    self.scrolling_start = False
                    self.scrolling = False
                    self.scrolling_end = False
                    self.end_scrolling = False
        self.get_backed_slots()
        self.lcd.cursor_pos = (self.cursor_pos, 1)
        self.lcd.write_string(self.backed_slots[self.index])
        if self.if_overflow(self.index):
            asyncio.run_coroutine_threadsafe(self.__start_scrolling(), self.loop)

    def menu(self, keep_scrolled=False, /):
        """
        Writes the four current visible slots to the display.

        Parameters
        ----------
            keep_scrolled : bool
                If True the middle substring of a shifted slot won't rest
                if the substring is the same as before and the slot
                doesn't change in size.
        """
        current_index = self.shift
        current_row = 0
        self.get_backed_slots(keep_scrolled)
        for t in range(self.lcd.lcd.rows):
            try:
                self.lcd.cursor_pos = (current_row, 1)
                self.lcd.write_string(self.backed_slots[current_index] if not (current_index == self.index
                                                                               and self.scrolling and keep_scrolled)
                                      else self.__shift_backed)
                current_row += 1
                current_index += 1
            except IndexError:
                pass

    def reset_menu(self, reset_wait=True):
        """
        Resets the Menu and the wait bool if wanted.

        Parameters
        ----------
            reset_wait : bool
                If True wait is set to false.
        """
        self.lcd.clear()
        time.sleep(0.01)
        if isinstance(self.current_menu, MenuFile):
            self.current_menu.update_slots()
        self.max_cursor_pos = self.return_max_cursor_pos()
        self.max_index = self.return_max_index()
        self.max_shift = self.return_max_shift()
        if self.scrolling or self.scrolling_start:
            self.end_scrolling = True
            while self.scrolling:
                if self.scrolling_end:
                    self.scrolling_end = False
                    self.scrolling = False
                time.sleep(0.01)
            self.end_scrolling = False
        self.reset_cursor()
        self.index = 0
        self.shift = 0
        self.menu()
        if reset_wait:
            self.__reset_wait()

    def __value_changed(self, value, direction):
        if not self.wait:
            self.__set_wait()
            self.timeout_reset = True
            if self.current_menu.custom_cursor:
                self.__callback("direction", value=direction)
                self.__reset_wait()
            else:
                pr_index = self.index
                pr_shift = self.shift
                pr_cursor_pos = self.cursor_pos
                if direction == "R":
                    if self.index != 0:
                        self.cursor_pos -= 1
                        self.index -= 1
                        if self.cursor_pos == -1:
                            self.cursor_pos = 0
                            if self.shift != 0:
                                self.shift -= 1
                else:
                    if self.index != self.max_index:
                        self.cursor_pos += 1
                        self.index += 1
                        if self.cursor_pos == self.max_cursor_pos:
                            self.cursor_pos = self.max_cursor_pos - 1
                            if self.shift != self.max_shift:
                                self.shift += 1
                if self.scrolling or self.scrolling_start:
                    self.__stop_scrolling(pr_cursor_pos, pr_index)
                if self.cursor_pos != pr_cursor_pos:
                    self.cursor(pr_cursor_pos)
                if self.shift != pr_shift:
                    self.menu()
                if self.if_overflow(self.index):
                    asyncio.run_coroutine_threadsafe(self.__start_scrolling(), self.loop)
                self.__reset_wait()

    def __button_press(self, arg):
        def pressed():
            if isinstance(self.current_menu, MenuFile):
                if self.index <= self.current_menu.pr_slots_last_index:
                    self.__callback("press", value=self.index)
                elif self.current_menu.file_menu_depth >= 1 and self.index == self.current_menu.pr_slots_last_index + 1:
                    self.current_menu.return_to_parent()
                    self.reset_menu()
                else:
                    slot: str = self.current_menu.slots[self.index]
                    check_path = self.current_menu.current_path / slot.split("#+#")[1]
                    if check_path.is_dir():
                        if not self.current_menu.custom_folder_behaviour:
                            self.current_menu.move_to_dir(slot.split("#+#")[1])
                            self.reset_menu()
                        else:
                            self.__callback("dir_press", value=check_path)
                    elif check_path is not None:
                        if check_path.is_file():
                            self.__callback("file_press", value=check_path)
                    else:
                        self.__callback("press", value=self.index)
            else:
                self.__callback("press", value=self.index)
            self.__reset_wait()

        async def button_check():
            if not self.wait:
                self.__set_wait()
                self.timeout_reset = True
                await self.loop.run_in_executor(None, pressed)

        asyncio.run_coroutine_threadsafe(button_check(), self.loop)

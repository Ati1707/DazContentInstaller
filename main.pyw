import customtkinter as ctk
import pywinstyles
import threading

from CTkMessagebox import CTkMessagebox
from CTkToolTip import CTkToolTip
from content_database import get_archives, delete_archive
from customtkinter import CTk, filedialog, CTkLabel
from helper import file_operations
from installer import start_installer_gui
from tkinter import BooleanVar
from tkinter.constants import DISABLED
from webbrowser import open

install_asset_list = []
remove_asset_list = []


def center_window_to_display(screen: CTk, width: int, height: int, scale_factor: float = 1.0) -> str:
    """Centers the window on the main display."""
    scaled_width = int(width / scale_factor)
    scaled_height = int(height / scale_factor)
    screen_width = screen.winfo_screenwidth()
    screen_height = screen.winfo_screenheight()

    # Calculate the x and y coordinates for centering the window
    x = int((screen_width - scaled_width) / 2)
    y = int((screen_height - scaled_height) / 2)

    return f"{scaled_width}x{scaled_height}+{x}+{y}"


def truncate_string(text: str, max_length: int = 50) -> str:
    """Truncates a string with ellipsis if it exceeds the max length."""
    return text[:max_length - 3] + '...' if len(text) > max_length else text

def start_install_thread(target_function):
    thread = threading.Thread(target=target_function)
    thread.start()


class AssetWidget(ctk.CTkFrame):
    def __init__(self, parent, tab_name: str, asset_name: str = "", file_path: str = ""):
        super().__init__(parent)
        self.asset_name = asset_name
        self.file_path = file_path
        self.file_size = file_operations.get_file_size(self.file_path)

        # Checkbox for the asset
        self.checkbox = ctk.CTkCheckBox(self, text=truncate_string(asset_name))
        self.checkbox.grid(row=0, column=0, padx=20, pady=10, sticky="w")

        # Tooltip for the checkbox
        self.tooltip = CTkToolTip(self.checkbox, message=asset_name, delay=0.2)

        # Install button
        if tab_name == "Install":
            self.label = CTkLabel(self, text=self.file_size)
            self.label.grid(row=0, column=1, padx=20, pady=10, sticky="w")

            # Install button
            self.button = ctk.CTkButton(self, text=tab_name, command=lambda: start_install_thread(self.install_asset))
            self.button.grid(row=0, column=2, padx=20, pady=10, sticky="e")
        else:

            # Uninstall button
            self.button = ctk.CTkButton(self, text=tab_name, command=self.remove_asset)
            self.button.grid(row=0, column=1, padx=20, pady=10, sticky="e")

        # Column configuration for layout
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=0)
        self.columnconfigure(2, weight=0)


    def install_asset(self):
        """Installs the asset and removes its widget from the grid."""
        self.button.configure(state=DISABLED)
        start_installer_gui(self.file_path, is_delete_archive=self.winfo_toplevel().tab_view.is_delete_archive.get())
        install_asset_list.remove(self)
        self.grid_remove()

    def remove_asset(self):
        """Removes the asset."""
        delete_archive(self.asset_name)
        remove_asset_list.remove(self)
        self.grid_remove()


class MyTabView(ctk.CTkTabview):
    def __init__(self, master,  **kwargs):
        super().__init__(master, command=self.refresh_tab, **kwargs)
        self.is_delete_archive = BooleanVar()
        self.create_tabs()
        self.create_install_widgets()
        self.create_uninstall_widgets()

    def create_tabs(self):
        """Initializes the 'Install' and 'Uninstall' tabs."""
        install_tab = self.add("Install")
        uninstall_tab = self.add("Uninstall")
        self.tab("Install")

        # Configure tabs
        install_tab.grid_columnconfigure(0, weight=1)
        install_tab.grid_rowconfigure(1, weight=1)

        uninstall_tab.grid_columnconfigure(0, weight=1)
        uninstall_tab.grid_rowconfigure(1, weight=1)

        # 'Check All' checkbox
        self.check_install = ctk.CTkCheckBox(install_tab, text="Check all", command=self.toggle_all_checkboxes)
        self.check_install.grid(row=0, column=0, sticky="we")

        self.check_uninstall = ctk.CTkCheckBox(uninstall_tab, text="Check all", command=self.toggle_all_checkboxes)
        self.check_uninstall.grid(row=0, column=0, sticky="we")

        # Scrollable frame for install tab
        self.scrollable_frame = ctk.CTkScrollableFrame(install_tab, width=600, height=500)
        self.scrollable_frame.grid(row=1, column=0, sticky="news")
        self.scrollable_frame.grid_columnconfigure(0, weight=1)

        self.uninstall_scrollable_frame = ctk.CTkScrollableFrame(uninstall_tab, width=600, height=500)
        self.uninstall_scrollable_frame.grid(row=1, column=0, sticky="news")
        self.uninstall_scrollable_frame.grid_columnconfigure(0, weight=1)

    def toggle_all_checkboxes(self):
        """Checks or unchecks all asset checkboxes based on the 'Check all' checkbox."""
        if self.check_install.get():
            for asset in install_asset_list:
                asset.checkbox.select()
        else:
            for asset in install_asset_list:
                asset.checkbox.deselect()

        if self.check_uninstall.get():
            for asset in remove_asset_list:
                asset.checkbox.select()
        else:
            for asset in remove_asset_list:
                asset.checkbox.deselect()


    def create_uninstall_widgets(self):
        """Creates widgets for the uninstall tab."""
        uninstall_tab = self.tab("Uninstall")

        # Uninstall selected button
        uninstall_button = ctk.CTkButton(uninstall_tab, text="Remove selected", command=self.remove_assets)
        uninstall_button.grid(row=2, column=0, padx=20, pady=10, sticky="se")

    def create_install_widgets(self):
        """Creates widgets for the install tab."""
        install_tab = self.tab("Install")

        # Delete Archive checkbox
        del_archive_checkbox = ctk.CTkCheckBox(install_tab, text="Delete Archive after Installation", variable=self.is_delete_archive)
        del_archive_checkbox.grid(row=2, column=0, padx=20, pady=10, sticky="sw")

        # Add Asset button
        add_asset_button = ctk.CTkButton(install_tab, text="Add Asset", command=self.select_file)
        add_asset_button.grid(row=2, column=0, padx=20, pady=10, sticky="s")

        # Install selected button
        install_button = ctk.CTkButton(install_tab, text="Install selected", command=self.install_assets)
        install_button.grid(row=2, column=0, padx=20, pady=10, sticky="se")

    def add_asset_widget(self, asset_name: str, asset_path: str):
        """Adds a new asset widget to the scrollable frame."""
        asset = AssetWidget(self.scrollable_frame, "Install", asset_name=asset_name, file_path=asset_path)
        asset.configure(border_color="#4A90E2", border_width=1)
        asset.grid(row=len(self.scrollable_frame.winfo_children()), column=0, padx=20, pady=5, sticky="news")
        install_asset_list.append(asset)

    def select_file(self):
        """Prompts user to select a file and adds an asset widget."""
        file_path = filedialog.askopenfilename()
        if file_path:
            file_name = file_operations.get_file_from_path(file_path)
            asset_name = file_operations.get_file_name_without_extension(file_name)
            self.add_asset_widget(asset_name, file_path)

    def install_assets(self):
        """Installs selected assets and removes their widgets."""
        msg = CTkMessagebox(title="Install?", message="Do you want to install the selected assets?",
                            icon="question", option_1="No", option_2="Yes")
        if msg.get() == "Yes":
            temp_install_list = install_asset_list.copy()
            for asset in temp_install_list:
                if asset.checkbox.get():
                    start_install_thread(asset.install_asset)

    def remove_assets(self):
        """Removes the selected assets and their widgets."""
        msg = CTkMessagebox(title="Remove?", message="Do you want to remove the selected assets?",
                            icon="question", option_1="No", option_2="Yes")
        if msg.get() == "Yes":
            temp_uninstall_list = remove_asset_list.copy()
            for asset in temp_uninstall_list:
                if asset.checkbox.get():
                    asset.remove_asset()

    def drop_files(self, files):
        """Handles file drop to create asset widgets."""
        for file_path in files:
            file_name = file_operations.get_file_from_path(file_path)
            asset_name = file_operations.get_file_name_without_extension(file_name)
            self.after(50, self.add_asset_widget, asset_name, file_path)


    def refresh_tab(self):
        selected_tab = self.get()
        if selected_tab == "Uninstall":
            for asset_widgets in self.uninstall_scrollable_frame.winfo_children():
                asset_widgets.destroy()
            assets = get_archives()
            remove_asset_list.clear()
            for asset in assets:
                asset_widget = AssetWidget(self.uninstall_scrollable_frame, "Uninstall", asset_name=asset[0])
                asset_widget.configure(border_color="#4A90E2", border_width=1)
                asset_widget.grid(row=len(self.uninstall_scrollable_frame.winfo_children()), column=0, padx=20, pady=5, sticky="news")
                remove_asset_list.append(asset_widget)


class App(CTk):
    def __init__(self):
        super().__init__()
        self.title("Daz Content Installer")
        self.geometry(center_window_to_display(self, 1100, 650, self._get_window_scaling()))

        # Initialize and place MyTabView
        self.tab_view = MyTabView(master=self)
        self.tab_view.grid(row=0, column=0, padx=20, pady=20, sticky="news")

        # Enable drag-and-drop for the 'Install' tab
        pywinstyles.apply_dnd(self.tab_view.tab("Install"), self.tab_view.drop_files)

        # Configure main window grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        if file_operations.create_database_folder():
            msg = CTkMessagebox(title="Info",
                                message="It seems like this is your first time opening the tool!\n\n"
                                "You can use the default library which will be in this folder but you can also use a different path.\n",
                                option_1="No",
                                option_2="Open configuration file",
                                width=500, height=250)
            if msg.get() == "Open configuration file":
                open("config.ini")


# Run the application
app = App()
app.mainloop()
#
# Copyright (c) 2023, Chris Allison
#
#     This file is part of tvhtokodi.
#
#     tvhtokodi is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     tvhtokodi is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with tvhtokodi.  If not, see <http://www.gnu.org/licenses/>.
#
"""GUI module for tvhtokodi"""

import tkinter as tk
from tkinter import ttk

from tvhtokodi import appname, version
from tvhtokodi.recordings import recordedTitles


class TitleBrowser(tk.Tk):
    """Main window for browsing recorded titles."""

    def __init__(self):
        super().__init__()
        
        # Set window title
        self.title(f"{appname} v{version}")
        
        # Set window size
        self.geometry("600x400")
        
        # Create main frame
        main_frame = ttk.Frame(self, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(0, weight=1)
        
        # Create label
        label = ttk.Label(main_frame, text="Recorded Titles:")
        label.grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        # Create listbox with scrollbar
        listbox_frame = ttk.Frame(main_frame)
        listbox_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        listbox_frame.columnconfigure(0, weight=1)
        listbox_frame.rowconfigure(0, weight=1)
        
        scrollbar = ttk.Scrollbar(listbox_frame)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        self.listbox = tk.Listbox(
            listbox_frame, 
            yscrollcommand=scrollbar.set,
            selectmode=tk.SINGLE
        )
        self.listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.config(command=self.listbox.yview)
        
        # Create quit button
        quit_button = ttk.Button(main_frame, text="Quit", command=self.quit)
        quit_button.grid(row=2, column=0, pady=(10, 0))
        
        # Load titles
        self.load_titles()
    
    def load_titles(self):
        """Load recorded titles into the listbox."""
        try:
            _, titles = recordedTitles()
            
            # Sort titles alphabetically
            sorted_titles = sorted(titles.keys())
            
            # Add titles to listbox
            for title in sorted_titles:
                self.listbox.insert(tk.END, title)
                
        except Exception as e:
            # If there's an error, show it in the listbox
            self.listbox.insert(tk.END, f"Error loading titles: {e}")


def main():
    """Run the GUI application."""
    app = TitleBrowser()
    app.mainloop()


if __name__ == "__main__":
    main()

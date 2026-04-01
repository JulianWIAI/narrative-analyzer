"""
NarrativeAnalyzerGUI.py
-----------------------
Defines the NarrativeAnalyzerGUI class, a Tkinter-based desktop application
that provides a graphical interface for managing story data, editing
characters, and running basic narrative analysis with visualised results.
The GUI is split into three tabs: Story Management, Character Management,
and Analysis.

This file can be run directly as well as imported:
    python SBS/NarrativeAnalyzerGUI.py   # Tkinter desktop GUI
    python gui.py                        # Flask web GUI (main entry point)
"""

import sys
from pathlib import Path

# Allow running this file directly from inside SBS/ or from the project root
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json

from SBS.Character import Character
from SBS.CharacterRole import CharacterRole
from SBS.Gender import Gender
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class NarrativeAnalyzerGUI:
    """
    Main Tkinter GUI application for the Narrative Pattern Analyzer.

    The application window contains three tabbed panels:
    - **Story Management**: Load, save, and configure story metadata (title,
      category, year, genres, themes, setting, power system).
    - **Character Management**: Add, update, and delete characters via a form,
      with a scrollable character list for selection.
    - **Analysis**: Generate a text summary report and display Matplotlib charts
      (character role distribution, gender distribution) embedded in the window.

    Attributes:
        root:          The root Tk window.
        notebook:      The ttk.Notebook widget containing all three tabs.
        current_story: Placeholder for the currently loaded Story (not yet
                       used directly — data is stored in instance variables).
        characters:    List of Character instances for the current story.
    """

    def __init__(self, root):
        """
        Initialise the GUI, build all tabs, and set up empty story state.

        Args:
            root: The root Tk window passed in from the entry-point script.
        """
        self.root = root
        self.root.title("Narrative Pattern Analyzer")
        self.root.geometry("1200x800")

        # Create main notebook (tabbed layout)
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

        # Build all three tabs
        self.create_story_tab()
        self.create_character_tab()
        self.create_analysis_tab()

        # Initialise in-memory story state
        self.current_story = None
        self.characters = []

    def create_story_tab(self):
        """
        Build the Story Management tab.

        Creates input fields for story title, category, and year, action
        buttons for file I/O (Load / Save / New), and multi-line text areas
        for genre, theme, setting, and power-system data.
        """
        story_frame = ttk.Frame(self.notebook)
        self.notebook.add(story_frame, text="Story Management")

        # Story metadata section
        story_info_frame = ttk.LabelFrame(story_frame, text="Story Information", padding=10)
        story_info_frame.pack(fill='x', padx=5, pady=5)

        ttk.Label(story_info_frame, text="Title:").grid(row=0, column=0, sticky='w', pady=2)
        self.title_var = tk.StringVar()
        ttk.Entry(story_info_frame, textvariable=self.title_var, width=50).grid(row=0, column=1, sticky='ew', pady=2)

        ttk.Label(story_info_frame, text="Category:").grid(row=1, column=0, sticky='w', pady=2)
        self.category_var = tk.StringVar(value="anime")
        ttk.Combobox(story_info_frame, textvariable=self.category_var,
                     values=["anime", "manga", "game", "movie", "tv_show", "book", "comic", "other"],
                     width=47).grid(row=1, column=1, sticky='ew', pady=2)

        ttk.Label(story_info_frame, text="Year:").grid(row=2, column=0, sticky='w', pady=2)
        self.year_var = tk.StringVar()
        ttk.Entry(story_info_frame, textvariable=self.year_var, width=50).grid(row=2, column=1, sticky='ew', pady=2)

        button_frame = ttk.Frame(story_info_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=10)

        ttk.Button(button_frame, text="Load Story", command=self.load_story).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Save Story", command=self.save_story).pack(side='left', padx=5)
        ttk.Button(button_frame, text="New Story", command=self.new_story).pack(side='left', padx=5)

        # Free-text detail areas
        details_frame = ttk.LabelFrame(story_frame, text="Story Details", padding=10)
        details_frame.pack(fill='both', expand=True, padx=5, pady=5)

        self.genre_text = tk.Text(details_frame, height=3)
        self.genre_text.pack(fill='x', pady=2)
        ttk.Label(details_frame, text="Genres (comma separated):").pack(anchor='w')

        self.theme_text = tk.Text(details_frame, height=3)
        self.theme_text.pack(fill='x', pady=2)
        ttk.Label(details_frame, text="Themes (comma separated):").pack(anchor='w')

        self.setting_text = tk.Text(details_frame, height=3)
        self.setting_text.pack(fill='x', pady=2)
        ttk.Label(details_frame, text="Setting:").pack(anchor='w')

        self.power_system_text = tk.Text(details_frame, height=3)
        self.power_system_text.pack(fill='x', pady=2)
        ttk.Label(details_frame, text="Power System:").pack(anchor='w')

    def create_character_tab(self):
        """
        Build the Character Management tab.

        Creates a scrollable listbox of current characters alongside a form
        for editing individual character attributes (name, gender, role,
        species, hair colour).  Buttons allow adding, updating, and deleting
        the selected character.
        """
        char_frame = ttk.Frame(self.notebook)
        self.notebook.add(char_frame, text="Character Management")

        # Scrollable character list
        list_frame = ttk.LabelFrame(char_frame, text="Characters", padding=10)
        list_frame.pack(fill='both', expand=True, padx=5, pady=5)

        self.char_listbox = tk.Listbox(list_frame)
        self.char_listbox.pack(fill='both', expand=True, side='left')
        self.char_listbox.bind('<<ListboxSelect>>', self.on_char_select)

        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.char_listbox.yview)
        scrollbar.pack(side='right', fill='y')
        self.char_listbox.config(yscrollcommand=scrollbar.set)

        # Character attribute form
        details_frame = ttk.LabelFrame(char_frame, text="Character Details", padding=10)
        details_frame.pack(fill='x', padx=5, pady=5)

        char_form_frame = ttk.Frame(details_frame)
        char_form_frame.pack(fill='x')

        ttk.Label(char_form_frame, text="Name:").grid(row=0, column=0, sticky='w', pady=2)
        self.char_name_var = tk.StringVar()
        ttk.Entry(char_form_frame, textvariable=self.char_name_var, width=30).grid(row=0, column=1, sticky='ew', pady=2)

        ttk.Label(char_form_frame, text="Gender:").grid(row=1, column=0, sticky='w', pady=2)
        self.char_gender_var = tk.StringVar(value="unknown")
        ttk.Combobox(char_form_frame, textvariable=self.char_gender_var,
                     values=["male", "female", "other", "unknown"], width=27).grid(row=1, column=1, sticky='ew', pady=2)

        ttk.Label(char_form_frame, text="Role:").grid(row=2, column=0, sticky='w', pady=2)
        self.char_role_var = tk.StringVar(value="supporting")
        ttk.Combobox(char_form_frame, textvariable=self.char_role_var,
                     values=["protagonist", "deuteragonist", "antagonist", "mentor", "sidekick",
                             "rival", "love_interest", "comic_relief", "supporting", "minor"],
                     width=27).grid(row=2, column=1, sticky='ew', pady=2)

        ttk.Label(char_form_frame, text="Species:").grid(row=3, column=0, sticky='w', pady=2)
        self.char_species_var = tk.StringVar(value="human")
        ttk.Entry(char_form_frame, textvariable=self.char_species_var, width=30).grid(row=3, column=1, sticky='ew',
                                                                                      pady=2)

        ttk.Label(char_form_frame, text="Hair Color:").grid(row=4, column=0, sticky='w', pady=2)
        self.char_hair_color_var = tk.StringVar()
        ttk.Entry(char_form_frame, textvariable=self.char_hair_color_var, width=30).grid(row=4, column=1, sticky='ew',
                                                                                         pady=2)

        button_frame = ttk.Frame(details_frame)
        button_frame.pack(fill='x', pady=10)

        ttk.Button(button_frame, text="Add Character", command=self.add_character).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Update Character", command=self.update_character).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Delete Character", command=self.delete_character).pack(side='left', padx=5)

    def create_analysis_tab(self):
        """
        Build the Analysis tab.

        Provides buttons to generate a text report and to render character-role
        and gender-distribution charts.  A canvas area below the buttons
        hosts the embedded Matplotlib figures.
        """
        analysis_frame = ttk.Frame(self.notebook)
        self.notebook.add(analysis_frame, text="Analysis")

        controls_frame = ttk.Frame(analysis_frame)
        controls_frame.pack(fill='x', padx=5, pady=5)

        ttk.Button(controls_frame, text="Generate Report", command=self.generate_report).pack(side='left', padx=5)
        ttk.Button(controls_frame, text="Show Character Distribution",
                   command=self.show_char_distribution).pack(side='left', padx=5)
        ttk.Button(controls_frame, text="Show Gender Distribution",
                   command=self.show_gender_distribution).pack(side='left', padx=5)

        plot_frame = ttk.LabelFrame(analysis_frame, text="Analysis Results", padding=10)
        plot_frame.pack(fill='both', expand=True, padx=5, pady=5)

        self.plot_canvas = tk.Canvas(plot_frame)
        self.plot_canvas.pack(fill='both', expand=True)

    # ------------------------------------------------------------------
    # Story file operations
    # ------------------------------------------------------------------

    def load_story(self):
        """
        Open a file dialog and load story data from a JSON file.

        Populates all story-tab fields and rebuilds the character list from
        the loaded data.  Shows a success or error message box when done.
        """
        file_path = filedialog.askopenfilename(
            title="Select Story File",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)

                self.title_var.set(data.get('title', ''))
                self.category_var.set(data.get('category', 'anime'))
                self.year_var.set(str(data.get('year', '')))

                self.genre_text.delete(1.0, tk.END)
                self.genre_text.insert(1.0, ', '.join(data.get('genres', [])))

                self.theme_text.delete(1.0, tk.END)
                self.theme_text.insert(1.0, ', '.join(data.get('themes', [])))

                self.setting_text.delete(1.0, tk.END)
                self.setting_text.insert(1.0, data.get('setting', ''))

                self.power_system_text.delete(1.0, tk.END)
                self.power_system_text.insert(1.0, data.get('power_system', ''))

                self.characters = []
                for char_data in data.get('characters', []):
                    char = Character(**char_data)
                    self.characters.append(char)

                self.update_char_listbox()
                messagebox.showinfo("Success", "Story loaded successfully!")

            except Exception as e:
                messagebox.showerror("Error", f"Failed to load story: {str(e)}")

    def save_story(self):
        """
        Open a save dialog and persist the current story state to a JSON file.

        Validates that a title has been entered before opening the dialog.
        Shows a success or error message box when done.
        """
        if not self.title_var.get():
            messagebox.showerror("Error", "Please enter a story title")
            return

        try:
            story_data = {
                'title': self.title_var.get(),
                'category': self.category_var.get(),
                'year': int(self.year_var.get()) if self.year_var.get() else None,
                'genres': [g.strip() for g in self.genre_text.get(1.0, tk.END).strip().split(',') if g.strip()],
                'themes': [t.strip() for t in self.theme_text.get(1.0, tk.END).strip().split(',') if t.strip()],
                'setting': self.setting_text.get(1.0, tk.END).strip(),
                'power_system': self.power_system_text.get(1.0, tk.END).strip(),
                'characters': [char.to_dict() for char in self.characters]
            }

            file_path = filedialog.asksaveasfilename(
                title="Save Story File",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )

            if file_path:
                with open(file_path, 'w') as f:
                    json.dump(story_data, f, indent=2)
                messagebox.showinfo("Success", "Story saved successfully!")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save story: {str(e)}")

    def new_story(self):
        """
        Clear all fields and reset the in-memory state to start a new story.

        Resets every input widget to its default value and empties the
        character list, then confirms to the user with a message box.
        """
        self.title_var.set('')
        self.category_var.set('anime')
        self.year_var.set('')
        self.genre_text.delete(1.0, tk.END)
        self.theme_text.delete(1.0, tk.END)
        self.setting_text.delete(1.0, tk.END)
        self.power_system_text.delete(1.0, tk.END)
        self.characters = []
        self.update_char_listbox()
        messagebox.showinfo("Success", "New story created!")

    # ------------------------------------------------------------------
    # Character CRUD operations
    # ------------------------------------------------------------------

    def add_character(self):
        """
        Create a new Character from the form fields and add it to the list.

        Validates that a name has been entered.  Shows a success or error
        message box when done.
        """
        name = self.char_name_var.get()
        if not name:
            messagebox.showerror("Error", "Please enter a character name")
            return

        try:
            char = Character(
                name=name,
                story=self.title_var.get() or "Unknown",
                gender=Gender(self.char_gender_var.get()).value,
                role=CharacterRole(self.char_role_var.get()).value,
                species=self.char_species_var.get(),
                hair_color=self.char_hair_color_var.get()
            )
            self.characters.append(char)
            self.update_char_listbox()
            self.clear_char_form()
            messagebox.showinfo("Success", "Character added successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add character: {str(e)}")

    def update_character(self):
        """
        Update the selected character's attributes from the form fields.

        Requires a character to be selected in the listbox.  Shows a success
        or error message box when done.
        """
        selection = self.char_listbox.curselection()
        if not selection:
            messagebox.showerror("Error", "Please select a character to update")
            return

        try:
            char = self.characters[selection[0]]
            char.name = self.char_name_var.get()
            char.gender = Gender(self.char_gender_var.get())
            char.role = CharacterRole(self.char_role_var.get())
            char.species = self.char_species_var.get()
            char.hair_color = self.char_hair_color_var.get()

            self.update_char_listbox()
            self.clear_char_form()
            messagebox.showinfo("Success", "Character updated successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update character: {str(e)}")

    def delete_character(self):
        """
        Delete the selected character after user confirmation.

        Requires a character to be selected in the listbox.  Prompts the user
        with a yes/no dialog before proceeding.
        """
        selection = self.char_listbox.curselection()
        if not selection:
            messagebox.showerror("Error", "Please select a character to delete")
            return

        if messagebox.askyesno("Confirm", "Are you sure you want to delete this character?"):
            del self.characters[selection[0]]
            self.update_char_listbox()
            self.clear_char_form()
            messagebox.showinfo("Success", "Character deleted successfully!")

    # ------------------------------------------------------------------
    # Character list helpers
    # ------------------------------------------------------------------

    def on_char_select(self, event):
        """
        Populate the character form when a character is selected in the listbox.

        Args:
            event: Tkinter event object (not used directly).
        """
        selection = self.char_listbox.curselection()
        if selection:
            char = self.characters[selection[0]]
            self.char_name_var.set(char.name)
            self.char_gender_var.set(char.gender.value)
            self.char_role_var.set(char.role.value)
            self.char_species_var.set(char.species)
            self.char_hair_color_var.set(char.hair_color)

    def update_char_listbox(self):
        """
        Rebuild the character listbox to reflect the current characters list.

        Clears all existing entries and re-inserts one entry per character
        using the character's name.
        """
        self.char_listbox.delete(0, tk.END)
        for char in self.characters:
            self.char_listbox.insert(tk.END, char.name)

    def clear_char_form(self):
        """Reset all character form fields to their default values."""
        self.char_name_var.set('')
        self.char_gender_var.set('unknown')
        self.char_role_var.set('supporting')
        self.char_species_var.set('human')
        self.char_hair_color_var.set('')

    # ------------------------------------------------------------------
    # Analysis and visualisation
    # ------------------------------------------------------------------

    def generate_report(self):
        """
        Build a plain-text summary report and display it in a message box.

        The report lists the story's metadata and a brief summary of each
        character's key attributes.
        """
        report = f"Narrative Analysis Report for {self.title_var.get()}\n"
        report += "=" * 50 + "\n"
        report += f"Category: {self.category_var.get()}\n"
        report += f"Year: {self.year_var.get()}\n"
        report += f"Characters: {len(self.characters)}\n\n"

        report += "Character Details:\n"
        report += "-" * 30 + "\n"
        for char in self.characters:
            report += f"Name: {char.name}\n"
            report += f"Role: {char.role.value}\n"
            report += f"Gender: {char.gender.value}\n"
            report += f"Species: {char.species}\n"
            report += f"Hair Color: {char.hair_color}\n\n"

        messagebox.showinfo("Analysis Report", report)

    def show_char_distribution(self):
        """
        Render a bar chart of character role frequencies in the plot canvas.

        Clears any previously rendered figure before drawing the new one.
        The chart is embedded directly in the Tkinter canvas using
        FigureCanvasTkAgg so no separate window is opened.
        """
        roles = [char.role.value for char in self.characters]
        role_counts = {}
        for role in roles:
            role_counts[role] = role_counts.get(role, 0) + 1

        self.plot_canvas.delete("all")

        fig, ax = plt.subplots(figsize=(8, 6))
        ax.bar(list(role_counts.keys()), list(role_counts.values()))
        ax.set_title("Character Role Distribution")
        ax.set_xlabel("Role")
        ax.set_ylabel("Count")
        plt.xticks(rotation=45)

        canvas = FigureCanvasTkAgg(fig, self.plot_canvas)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)

    def show_gender_distribution(self):
        """
        Render a pie chart of character gender frequencies in the plot canvas.

        Clears any previously rendered figure before drawing the new one.
        The chart is embedded directly in the Tkinter canvas using
        FigureCanvasTkAgg so no separate window is opened.
        """
        genders = [char.gender.value for char in self.characters]
        gender_counts = {}
        for gender in genders:
            gender_counts[gender] = gender_counts.get(gender, 0) + 1

        self.plot_canvas.delete("all")

        fig, ax = plt.subplots(figsize=(8, 6))
        ax.pie(list(gender_counts.values()), labels=list(gender_counts.keys()), autopct='%1.1f%%')
        ax.set_title("Character Gender Distribution")

        canvas = FigureCanvasTkAgg(fig, self.plot_canvas)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)


if __name__ == "__main__":
    root = tk.Tk()
    app = NarrativeAnalyzerGUI(root)
    root.mainloop()

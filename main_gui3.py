import os
import customtkinter as ctk
from tkinter import filedialog, messagebox

from preprocessing_pipeline import RAGPreprocessor
from RAG import RAGPipeline
from session_manager import SessionManager

# Default Theme
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("green")
ctk.set_widget_scaling(1.2)
ctk.set_window_scaling(1.1)

class SmartScholarApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("SmartScholar – Your Study Assistant 🧠")
        self.geometry("1234x789")

        # Fonts
        self.font_large = ("Arial", 20, "bold")
        self.font_medium = ("Arial", 16)
        self.font_small = ("Arial", 13)

        # Data
        self.session_manager = SessionManager()
        self.rag = None
        self.current_sid = None
        self.chat_history = []
        self.docset_folder = None

        # Layout
        self.sidebar = ctk.CTkFrame(self, width=230)
        self.sidebar.pack(side="left", fill="y", padx=10, pady=10)

        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(side="right", expand=True, fill="both", padx=10, pady=10)

        self.build_home()
        self.build_docset_list()
        self.build_theme_settings()

    def build_home(self):
        self.clear_main_frame()

        ctk.CTkLabel(
            self.main_frame,
            text="Welcome to SmartScholar 🎓",
            font=("Arial", 25, "bold")
        ).pack(pady=30)

        ctk.CTkButton(self.main_frame, text="📁 Select New Docset", command=self.select_new_docset, font=self.font_medium, width=280, height=40).pack(pady=12)
        ctk.CTkButton(self.main_frame, text="🧠 Start New Session", command=self.manual_start_session, font=self.font_medium, width=280, height=40).pack(pady=12)
        ctk.CTkButton(self.main_frame, text="🔁 Resume Session", command=self.resume_session, font=self.font_medium, width=280, height=40).pack(pady=12)
        ctk.CTkButton(self.main_frame, text="❌ Exit", command=self.quit, font=self.font_medium, width=280, height=40).pack(pady=12)

    def build_docset_list(self):
        ctk.CTkLabel(self.sidebar, text="📚 Docsets", font=self.font_medium).pack(pady=10)
        self.docset_listbox = ctk.CTkScrollableFrame(self.sidebar, width=220, height=500)
        self.docset_listbox.pack(fill="both", expand=True)
        self.update_docset_list()

    def update_docset_list(self):
        for widget in self.docset_listbox.winfo_children():
            widget.destroy()

        docsets = self.session_manager.get_all_docxsets()
        for doc in docsets:
            ctk.CTkButton(
            self.docset_listbox,
            text=f"📁 {os.path.basename(doc)}",
            anchor="w",
            font=("Arial", 15, "bold"),
            fg_color="transparent",
            hover_color="gray20",
            command=lambda d=doc: messagebox.showinfo("Docset Path", d)
        ).pack(fill="x", padx=5, pady=2)

            sessions = [s for s in self.session_manager.get_all_sessions() if s[1] == doc]
            for s in sessions:
                sid = s[0]
                ctk.CTkButton(
                    self.docset_listbox,
                    text=f"{s[2]}",
                    font=("Arial", 13, "bold"),
                    width=200,
                    height=32,
                    fg_color="gray20",
                    command=lambda sid=sid: self.load_session(sid)
                ).pack(pady=2)

    def build_theme_settings(self):
        ctk.CTkLabel(self.sidebar, text="🎨 Appearance", font=self.font_medium).pack(pady=(20, 5))

        # Appearance Mode
        self.appearance_mode_var = ctk.StringVar(value="System")
        mode_menu = ctk.CTkOptionMenu(
            self.sidebar,
            values=["Light", "Dark"],
            variable=self.appearance_mode_var,
            command=self.change_appearance_mode,
            font=self.font_small
        )
        mode_menu.pack(pady=5, padx=10)

    def change_appearance_mode(self, mode):
        ctk.set_appearance_mode(mode)

    def clear_main_frame(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def select_new_docset(self):
        folder_path = filedialog.askdirectory(title="Select Folder")
        if not folder_path:
            return
        try:
            processor = RAGPreprocessor(folder_path)
            processor.process_and_store()
            messagebox.showinfo("Success", "Docset processed and stored!")
            self.docset_folder = folder_path
            self.update_docset_list()
            self.auto_start_session()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def auto_start_session(self):
        session_name = ctk.CTkInputDialog(text="Enter session name:", title="New Session").get_input()
        if not session_name:
            return
        self.create_session(self.docset_folder, session_name)

    def manual_start_session(self):
        docsets = self.session_manager.get_all_docxsets()
        if not docsets:
            messagebox.showinfo("No Docsets", "Please process a docset first.")
            return

        popup = ctk.CTkToplevel(self)
        popup.title("Start New Session")
        popup.geometry("450x300")
        popup.resizable(False, False)
        popup.grab_set()

        ctk.CTkLabel(popup, text="Select a Docset:", font=self.font_medium).pack(pady=10)

        selected_docset = ctk.StringVar(value=docsets[0])
        dropdown = ctk.CTkOptionMenu(popup, values=docsets, variable=selected_docset, font=self.font_small, height=36)
        dropdown.pack(pady=5)

        ctk.CTkLabel(popup, text="Enter Session Name:", font=self.font_small).pack(pady=10)
        session_name_entry = ctk.CTkEntry(popup, placeholder_text="e.g. Revision Session", font=self.font_small, height=36)
        session_name_entry.pack(pady=5)

        def on_start():
            session_name = session_name_entry.get().strip()
            docset = selected_docset.get().strip()
            if not session_name:
                messagebox.showerror("Missing Input", "Please enter a session name.")
                return
            popup.destroy()
            self.create_session(docset, session_name)

        ctk.CTkButton(popup, text="Start Session", command=on_start, font=self.font_small, height=36).pack(pady=15)

    def resume_session(self):
        sessions = self.session_manager.get_all_sessions()
        if not sessions:
            messagebox.showinfo("No Sessions", "No sessions available.")
            return

        popup = ctk.CTkToplevel(self)
        popup.title("Resume Session")
        popup.geometry("650x250")
        popup.resizable(False, False)
        popup.grab_set()

        ctk.CTkLabel(popup, text="Select a session:", font=self.font_medium).pack(pady=10)

        session_map = {
            f"[{s[0]}]  {s[2]} ➤ {s[1]}": s[0]
            for s in sessions
        }
        options = list(session_map.keys())
        selected = ctk.StringVar(value=options[0])

        dropdown = ctk.CTkOptionMenu(popup, values=options, variable=selected, font=self.font_small, height=36)
        dropdown.pack(pady=5)

        def confirm():
            sid = session_map[selected.get()]
            popup.destroy()
            self.load_session(sid)

        ctk.CTkButton(popup, text="Resume", command=confirm, font=self.font_small, height=36).pack(pady=15)

    def create_session(self, docset_folder, session_name):
        sid = self.session_manager.create_session(docset_folder, session_name)
        self.session_manager.update_last_access_time(sid)
        self.current_sid = sid
        self.rag = RAGPipeline(docset_folder)
        self.chat_history = []
        self.start_chat_interface(session_name)

    def load_session(self, sid):
        session = self.session_manager.get_session_by_id(sid)
        if not session:
            return
        self.current_sid = sid
        self.docset_folder = session[1]
        self.rag = RAGPipeline(self.docset_folder)
        self.chat_history = self.session_manager.get_chat_history(sid)
        self.start_chat_interface(session[2])

    def start_chat_interface(self, session_name):
        self.clear_main_frame()
        ctk.CTkLabel(self.main_frame, text=f"💬 Chat Session: {session_name}", font=self.font_medium).pack(pady=10)

        self.chat_display = ctk.CTkTextbox(self.main_frame, wrap="word", font=("Consolas", 13))
        self.chat_display.pack(expand=True, fill="both", padx=10, pady=10)
        self.chat_display.configure(state="disabled")
        self.chat_display.configure(state="normal")

        for q, a, _ in self.chat_history:
            self._display_message("You", q)
            self._display_message("SmartScholar", a)

        input_frame = ctk.CTkFrame(self.main_frame)
        input_frame.pack(fill="x", pady=5, padx=10)

        self.retrieval_toggle = ctk.CTkCheckBox(input_frame, text="Use Retrieval", font=self.font_small)
        self.retrieval_toggle.select()
        self.retrieval_toggle.pack(side="left", padx=5)

        self.input_entry = ctk.CTkEntry(input_frame, placeholder_text="Type your question...", font=self.font_small, height=36)
        self.input_entry.pack(side="left", expand=True, fill="x", padx=5)
        self.input_entry.bind("<Return>", lambda e: self.send_query())

        ctk.CTkButton(input_frame, text="Send", command=self.send_query, font=self.font_small, height=36).pack(side="left", padx=5)

    def _display_message(self, sender, text):
        self.chat_display.configure(state="normal")
        self.chat_display.insert("end", f"{sender}: {text}\n\n")
        self.chat_display.configure(state="disabled")
        self.chat_display.see("end")

    def send_query(self):
        query = self.input_entry.get().strip()
        if not query:
            return
        self.input_entry.delete(0, "end")
        self._display_message("You", query)

        if query.lower() == "<exit>":
            self.end_session()
            return

        use_retrieval = self.retrieval_toggle.get()
        try:
            result = self.rag.query(query, use_retrieval=use_retrieval)
            answer = result.get("answer", "No answer generated.")
        except Exception as e:
            answer = f"[Error] {str(e)}"

        self._display_message("SmartScholar", answer)
        self.session_manager.add_chat_history(self.current_sid, query, answer)

    def end_session(self):
        self.chat_history = []
        self.current_sid = None
        self.rag = None
        self.build_home()
        self.update_docset_list()


if __name__ == "__main__":
    app = SmartScholarApp()
    app.mainloop()

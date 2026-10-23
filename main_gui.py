import os
import customtkinter as ctk
from tkinter import filedialog, messagebox, scrolledtext

from preprocessing_pipeline import RAGPreprocessor
from RAG import RAGPipeline
from session_manager import SessionManager

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class SmartScholarApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("SmartScholar – Your Study Assistant \U0001f9d0")
        self.geometry("1000x650")

        # Data
        self.session_manager = SessionManager()
        self.rag = None
        self.current_sid = None
        self.chat_history = []
        self.docset_folder = None

        # Main layout containers
        self.sidebar = ctk.CTkFrame(self, width=220)
        self.sidebar.pack(side="left", fill="y", padx=10, pady=10)

        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(side="right", expand=True, fill="both", padx=10, pady=10)

        self.build_home()
        self.build_docset_list()

    def build_home(self):
        self.clear_main_frame()
        ctk.CTkLabel(self.main_frame, text="Welcome to SmartScholar \U0001f393", font=("Arial", 22, "bold")).pack(pady=20)

        ctk.CTkButton(self.main_frame, text="\U0001f4c1 Select New Docset", command=self.select_new_docset, width=250).pack(pady=10)
        ctk.CTkButton(self.main_frame, text="\U0001f9e0 Start New Session", command=self.manual_start_session, width=250).pack(pady=10)
        ctk.CTkButton(self.main_frame, text="\U0001f501 Resume Session", command=self.resume_session, width=250).pack(pady=10)
        ctk.CTkButton(self.main_frame, text="❌ Exit", command=self.quit, width=250).pack(pady=10)

    def build_docset_list(self):
        ctk.CTkLabel(self.sidebar, text="\U0001f4da Docsets", font=("Arial", 16, "bold")).pack(pady=10)
        self.docset_listbox = ctk.CTkScrollableFrame(self.sidebar, width=200, height=500)
        self.docset_listbox.pack(fill="both", expand=True)
        self.update_docset_list()

    def update_docset_list(self):
        for widget in self.docset_listbox.winfo_children():
            widget.destroy()

        docsets = self.session_manager.get_all_docxsets()
        for doc in docsets:
            ctk.CTkLabel(self.docset_listbox, text=f"\U0001f4c1 {doc}", anchor="w").pack(fill="x", padx=5)
            sessions = [s for s in self.session_manager.get_all_sessions() if s[1] == doc]
            for s in sessions:
                sid = s[0]
                label = ctk.CTkButton(self.docset_listbox, text=f"➡ {s[2]}", width=180, height=28, fg_color="gray20",
                                       command=lambda sid=sid: self.load_session(sid))
                label.pack(pady=1)

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

        docset = ctk.CTkInputDialog(text=f"Available: {', '.join(docsets)}\nEnter docset name:", title="Docset").get_input()
        if not docset or docset not in docsets:
            return
        session_name = ctk.CTkInputDialog(text="Enter session name:", title="New Session").get_input()
        if not session_name:
            return
        self.create_session(docset, session_name)

    def create_session(self, docset_folder, session_name):
        sid = self.session_manager.create_session(docset_folder, session_name)
        self.session_manager.update_last_access_time(sid)
        self.current_sid = sid
        self.rag = RAGPipeline(docset_folder)
        self.chat_history = []
        self.start_chat_interface(session_name)

    def resume_session(self):
        sessions = self.session_manager.get_all_sessions()
        if not sessions:
            messagebox.showinfo("No Sessions", "No sessions available.")
            return
        session_id = ctk.CTkInputDialog(text="Enter session ID:", title="Resume Session").get_input()
        try:
            sid = int(session_id)
            self.load_session(sid)
        except:
            messagebox.showerror("Invalid", "Enter valid session ID.")

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
        ctk.CTkLabel(self.main_frame, text=f"\U0001f4ac Chat Session: {session_name}", font=("Arial", 18, "bold")).pack(pady=10)

        self.chat_display = scrolledtext.ScrolledText(self.main_frame, wrap="word", state="disabled", height=25)
        self.chat_display.pack(expand=True, fill="both", padx=10, pady=10)

        for q, a, _ in self.chat_history:
            self._display_message("You", q)
            self._display_message("SmartScholar", a)

        input_frame = ctk.CTkFrame(self.main_frame)
        input_frame.pack(fill="x", pady=5, padx=10)

        self.retrieval_toggle = ctk.CTkCheckBox(input_frame, text="Use Retrieval")
        self.retrieval_toggle.select()
        self.retrieval_toggle.pack(side="left", padx=5)

        self.input_entry = ctk.CTkEntry(input_frame, placeholder_text="Type your question...")
        self.input_entry.pack(side="left", expand=True, fill="x", padx=5)
        self.input_entry.bind("<Return>", lambda e: self.send_query())

        ctk.CTkButton(input_frame, text="Send", command=self.send_query).pack(side="left", padx=5)

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

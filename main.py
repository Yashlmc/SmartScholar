
from preprocessing_pipeline import RAGPreprocessor

from RAG import RAGPipeline
from session_manager import SessionManager
from folder_monitor import FolderMonitor
import threading
import os
import sys
from tkinter import Tk
from tkinter.filedialog import askdirectory


def get_valid_choice(prompt, valid_choices):
    while True:
        try:
            choice = int(input(prompt))
            if choice in valid_choices:
                return choice
            else:
                print(f"Invalid choice. Please choose from {valid_choices}.\n")
        except ValueError:
            print("Invalid input. Please enter a number.\n")


class Chat:
    def __init__(self, rag: RAGPipeline, session_manager: SessionManager, session_id: int):
        self.rag : RAGPipeline = rag
        self.session_manager : SessionManager = session_manager
        self.session_id = session_id

    def start(self):
        print("\nChat Session Started! (Type '<exit>' to end)\n")
        while True:
            user_query = input("You: ").strip()
            if user_query.lower() == "<exit>":
                print("Ending chat session.")
                break
            retrieval_input = input("Do you want to use retrieval for this query? (yes/no): ").strip().lower()
            use_retrieval = True if retrieval_input == "yes" else False

            response_data = self.rag.query(user_query, use_retrieval=use_retrieval)
            answer = response_data.get('answer', 'No answer generated.')
            print(f"SmartScholar: {answer}\n")

            # Store this exchange in the session's history
            self.session_manager.add_chat_history(
                self.session_id,
                user_query,
                answer
            )

class Home:
    def __init__(self, session_manager):
        self.session_manager : SessionManager = session_manager
        self.current_session = None
        self.current_docset = None
        self.preprocessor_pipeline : RAGPreprocessor = None
        self.folder_monitor = None

    def create_folder_monitor(self, docset_name):
        path = self.current_docset.rstrip("/")
        print(path)
        folder_name_normal = path.split("/")[-1]
        print(folder_name_normal)
        if not os.path.exists(f"fm_logs/{folder_name_normal}"):
            os.makedirs(f"fm_logs/{folder_name_normal}")
        folder_monitor : FolderMonitor = FolderMonitor(folder_path=docset_name,
                                        state_file=f"fm_logs/{folder_name_normal}/file_states.json",
                                        log_file=f"fm_logs/{folder_name_normal}/folder_actions.log",
                                        enable_console_log=False,
                                        on_created=self.on_file_created,
                                        on_deleted=Home.on_file_deleted,
                                        on_modified=Home.on_file_modified,
                                        on_moved=Home.on_file_moved)
        # print("here")
        return folder_monitor

    def on_file_created(self, file_path):
        print(f"[Monitor] New file detected: {file_path}")
        self.preprocessor_pipeline.add_new_file(file_path)

    def on_file_modified(self, file_path):
        print(f"[Monitor] File modified: {file_path}")
        self.preprocessor_pipeline.update_file(file_path)

    def on_file_deleted(self, file_path):
        print(f"[Monitor] File deleted: {file_path}")
        self.preprocessor_pipeline.delete_file(file_path)

    def on_file_moved(self, src_path, dest_path):
        print(f"[Monitor] File moved: {src_path} -> {dest_path}")
        self.preprocessor_pipeline.rename_file(src_path, dest_path)

    ###
    def select_new_docset(self):
        print("@ Select New Docset")
        root = Tk()
        root.withdraw()
        folder_path = askdirectory(title="Select Folder")
        root.destroy()

        if not folder_path:
            print("No folder selected. Returning to Home Menu.\n")
            return

        self.current_docset = folder_path
        self.preprocessor_pipeline = RAGPreprocessor(docset_folder=folder_path)
        self.preprocessor_pipeline.process_and_store()

        print("Docset Saved in Vector Database")
        self.start_new_session(folder_path)
        
    def start_new_session(self, docset_name=None):
        print("@ Start New Session")
        if docset_name is None:
            docsets = self.session_manager.get_all_docxsets()
            if not docsets:
                print("No existing docsets found. Please create one first.")
                return
            
            print("\nAvailable Docsets:")
            for index, docset in enumerate(docsets, start=1):
                print(f"{index}. {docset}")

            try:
                choice = int(input("\nSelect a docset by number: "))
                if 1 <= choice <= len(docsets):
                    docset_name = docsets[choice - 1]
                    self.current_docset = docset_name
                else:
                    print("Invalid choice. Aborting session creation.")
                    return
            except ValueError:
                print("Invalid input. Aborting session creation.")
                return
        
        self.folder_monitor = self.create_folder_monitor(docset_name)
        monitor_thread = threading.Thread(target=self.folder_monitor.start, daemon=True)
        monitor_thread.start()

        session_name = input(f"Enter new session name for docset '{docset_name}': ").strip()
        if not session_name:
            print("Session name cannot be empty. Aborting.")
            return
        sid = self.session_manager.create_session(docset_name, session_name)
        self.session_manager.update_last_access_time(sid)
        self.current_session = sid
        print(f"Session '{session_name}' created with ID: {sid}")

        rag = RAGPipeline(docset_folder=docset_name)
        chat = Chat(rag, self.session_manager, sid)
        chat.start()
        self.folder_monitor.stop()
        self.folder_monitor = None

    def restart_session(self):
        print("@ Restart Existing Session")
        sessions = self.session_manager.get_all_sessions()
        if not sessions:
            print("No sessions found. Create a new one first!")
            return
        print("\nAvailable Sessions:")
        for index, session in enumerate(sessions, start=1):
            sid, docxset, sessionname, ctime, latime = session
            print(f"{index}. [{docxset}] - '{sessionname}' | Created: {ctime} | Last Active: {latime}")
        try:
            choice = int(input("\nSelect a session to restart by number: "))
            if 1 <= choice <= len(sessions):
                selected_session = sessions[choice - 1]
                sid = selected_session[0]
                self.current_session = sid
                self.session_manager.update_last_access_time(sid)
                # After setting up current_session and updating last access time
                print(f"\nSession '{selected_session[2]}' (ID: {sid}) restarted successfully!")
                history = self.session_manager.get_chat_history(sid)
                if history:
                    print("\nPrevious Conversation History:")
                    for query, response, timestamp in history:
                        print(f"[{timestamp}]\n Q: {query} \nA: {response}\n")
                else:
                    print("No conversation history found for this session yet.")
                # These should happen regardless of history
                docset_name = selected_session[1]
                self.current_docset = docset_name
                self.folder_monitor: FolderMonitor = self.create_folder_monitor(docset_name)
                monitor_thread = threading.Thread(target=self.folder_monitor.start, daemon=True)
                monitor_thread.start()

                rag = RAGPipeline(docset_folder=docset_name)
                chat = Chat(rag, self.session_manager, sid)
                chat.start()

                self.folder_monitor.stop()
                self.folder_monitor = None

            else:
                print("Invalid choice. Restart aborted.")
        except ValueError:
            print("Invalid input. Restart aborted.")

    def start(self):
        while True:
            print("@ Home")
            prompt = "1. Select New Docset\n2. Start New Session\n3. Restart session\n4. Exit\n> "
            choice = get_valid_choice(prompt, [1, 2, 3, 4])

            if choice == 1:
                self.select_new_docset()
            elif choice == 2:
                self.start_new_session()
            elif choice == 3:
                self.restart_session()
            elif choice == 4:
                print("Exiting... Goodbye!")
                self.session_manager.close()
                sys.exit(0)

class App:
    def __init__(self):
        self.session_manager = SessionManager()

    def home(self):
        home = Home(session_manager=self.session_manager)
        home.start()

    def run(self):
        self.home()


if __name__ == "__main__":
    print("""
#############################################
___________Welcome To SmartScholar___________
 * Your Personal Study and Research Assistant
#############################################\n
""")
    app = App()
    app.run()

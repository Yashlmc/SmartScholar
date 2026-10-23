import os
import time
import json
import hashlib
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class FolderMonitor:
    def __init__(
        self,
        folder_path,
        state_file="file_states.json",
        log_file="folder_actions.log",
        enable_console_log=False,
        on_created=None,
        on_deleted=None,
        on_modified=None,
        on_moved=None
    ):
        self.folder_path = folder_path
        self.state_file = state_file

        # Configure logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        # Create a file handler for logging to a file
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        self.logger.addHandler(file_handler)

        # Add a console handler if enable_console_log is True
        if enable_console_log:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
            self.logger.addHandler(console_handler)

        # Event callbacks
        self.on_created_callback = on_created
        self.on_deleted_callback = on_deleted
        self.on_modified_callback = on_modified
        self.on_moved_callback = on_moved

        self.observer = Observer()
        self.event_handler = FolderHandler(self)
        self.observer.schedule(self.event_handler, self.folder_path, recursive=True)
        self.file_states = self.load_file_states()  # Load file states from disk
        self.running = False  # Track whether the monitor is running

    def start(self):
        """Start monitoring the folder."""
        self.running = True
        self.logger.info(f"Starting to monitor folder: {self.folder_path}")
        self.check_for_changes()  # Check for changes made while the code was not running
        self.observer.start()
        try:
            while self.running:  # Use self.running to control the loop
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
        self.logger.info("Stopped monitoring folder.")

    def stop(self):
        """Stop monitoring the folder."""
        try:
            if self.observer.is_alive():  # Check if the observer is running
                self.observer.stop()      # Stop the observer
                self.observer.join()      # Wait for the observer thread to finish
                self.logger.info("Folder monitoring stopped.")
            else:
                self.logger.info("Folder monitoring is not running.")
        except Exception as e:
            self.logger.error(f"Error stopping folder monitoring: {e}")

    def load_file_states(self):
        """Load file states from a JSON file."""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, "r") as f:
                    return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading file states: {e}")
        return {}

    def save_file_states(self):
        """Save file states to a JSON file."""
        try:
            with open(self.state_file, "w") as f:
                json.dump(self.file_states, f, indent=4)
        except Exception as e:
            self.logger.error(f"Error saving file states: {e}")

    def compute_file_hash(self, file_path):
        """Compute the SHA256 hash of a file's content."""
        try:
            hash_sha256 = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            self.logger.error(f"Error computing hash for {file_path}: {e}")
            return None

    def on_created(self, file_path):
        """Handle file creation event."""
        if not os.path.isdir(file_path):
            try:
                file_hash = self.compute_file_hash(file_path)
                if file_hash:
                    self.file_states[file_path] = {
                        "timestamp": os.path.getmtime(file_path),
                        "hash": file_hash
                    }
                    self.save_file_states()  # Save updated file states
                    self.logger.info(f"New file detected: {file_path}")
                    if self.on_created_callback:
                        self.on_created_callback(file_path)  # Trigger callback
            except Exception as e:
                self.logger.error(f"Error handling file creation for {file_path}: {e}")

    def on_deleted(self, file_path):
        """Handle file deletion event."""
        if not os.path.isdir(file_path):
            try:
                if file_path in self.file_states:
                    del self.file_states[file_path]
                    self.save_file_states()  # Save updated file states
                self.logger.info(f"File deleted: {file_path}")
                if self.on_deleted_callback:
                    self.on_deleted_callback(file_path)  # Trigger callback
            except Exception as e:
                self.logger.error(f"Error handling file deletion for {file_path}: {e}")

    def on_modified(self, file_path):
        """Handle file modification event."""
        if not os.path.isdir(file_path):
            try:
                if file_path in self.file_states:
                    current_timestamp = os.path.getmtime(file_path)
                    current_hash = self.compute_file_hash(file_path)
                    if current_hash != self.file_states[file_path]["hash"]:
                        self.file_states[file_path] = {
                            "timestamp": current_timestamp,
                            "hash": current_hash
                        }
                        self.save_file_states()  # Save updated file states
                        self.logger.info(f"File modified: {file_path}")
                        if self.on_modified_callback:
                            self.on_modified_callback(file_path)  # Trigger callback
                else:
                    # Handle the case where a file is modified before being tracked
                    self.file_states[file_path] = {
                        "timestamp": os.path.getmtime(file_path),
                        "hash": self.compute_file_hash(file_path)
                    }
                    self.save_file_states()  # Save updated file states
                    self.logger.info(f"Newly tracked file modified: {file_path}")
                    if self.on_modified_callback:
                        self.on_modified_callback(file_path)  # Trigger callback
            except Exception as e:
                self.logger.error(f"Error handling file modification for {file_path}: {e}")

    def on_moved(self, src_path, dest_path):
        """Handle file renaming/moving event."""
        if not os.path.isdir(src_path):
            try:
                if src_path in self.file_states:
                    # Preserve the file's metadata and update the path
                    self.file_states[dest_path] = self.file_states[src_path]
                    del self.file_states[src_path]
                    self.save_file_states()  # Save updated file states
                    self.logger.info(f"File renamed/moved: {src_path} -> {dest_path}")
                    if self.on_moved_callback:
                        self.on_moved_callback(src_path, dest_path)  # Trigger callback
                else:
                    # Handle the case where a file is moved before being tracked
                    self.file_states[dest_path] = {
                        "timestamp": os.path.getmtime(dest_path),
                        "hash": self.compute_file_hash(dest_path)
                    }
                    self.save_file_states()  # Save updated file states
                    self.logger.info(f"Newly tracked file moved: {src_path} -> {dest_path}")
                    if self.on_moved_callback:
                        self.on_moved_callback(src_path, dest_path)  # Trigger callback
            except Exception as e:
                self.logger.error(f"Error handling file move/rename for {src_path} -> {dest_path}: {e}")

    def check_for_changes(self):
        """Check for changes made while the code was not running."""
        self.logger.info("Checking for changes made while the code was not running...")
        current_files = {}
        try:
            for root, _, files in os.walk(self.folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    current_files[file_path] = {
                        "timestamp": os.path.getmtime(file_path),
                        "hash": self.compute_file_hash(file_path)
                    }

            # Step 1: Check for new or modified files and detect renames
            for file_path, metadata in current_files.items():
                if file_path not in self.file_states:
                    # Check if this is a rename by comparing content hashes
                    is_rename = False
                    for existing_path, existing_metadata in self.file_states.items():
                        if existing_metadata["hash"] == metadata["hash"]:
                            # Treat this as a rename
                            self.on_moved(existing_path, file_path)
                            is_rename = True
                            break
                    if not is_rename:
                        # Treat this as a new file
                        self.on_created(file_path)
                else:
                    # Check if the file has been modified
                    if metadata["hash"] != self.file_states[file_path]["hash"]:
                        self.on_modified(file_path)

            # Step 2: Check for deleted files
            for file_path in list(self.file_states.keys()):
                if file_path not in current_files:
                    self.on_deleted(file_path)
        except Exception as e:
            self.logger.error(f"Error checking for changes: {e}")

class FolderHandler(FileSystemEventHandler):
    def __init__(self, monitor):
        self.monitor = monitor

    def on_created(self, event):
        self.monitor.on_created(event.src_path)

    def on_deleted(self, event):
        self.monitor.on_deleted(event.src_path)

    def on_modified(self, event):
        self.monitor.on_modified(event.src_path)

    def on_moved(self, event):
        self.monitor.on_moved(event.src_path, event.dest_path)
import sys
import json
import subprocess
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QListWidget, QListWidgetItem, QLabel, QMessageBox, QSplitter, QGroupBox
)
from PyQt6.QtCore import Qt


class PipewireManager:
    def __init__(self):
        self.internal_links = []  # Internal list of links created by the app

    def create_link(self, output_node_id, input_node_id):
        """Create a link between an output node and an input node."""
        try:
            # Check if the link already exists
            if self.link_exists(output_node_id, input_node_id):
                print(f"Link between {output_node_id} and {input_node_id} already exists.")
                return False

            # Attempt to create the link
            cmd = ["pw-link", str(output_node_id), str(input_node_id)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"Successfully linked nodes {output_node_id} and {input_node_id}")
                self.internal_links.append((output_node_id, input_node_id))  # Add to internal list
                return True
            else:
                print(f"Failed to link nodes {output_node_id} and {input_node_id}: {result.stderr}")
                return False
        except Exception as e:
            print(f"Error creating link: {e}")
            return False
        
    def link_exists(self, output_node_id, input_node_id):
        """Check if a link already exists between the given nodes."""
        try:
            # Use pw-dump to get all PipeWire objects
            cmd = ["pw-dump"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Error running pw-dump: {result.stderr}")
                return False

            # Parse the output as JSON
            pw_objects = json.loads(result.stdout)

            # Look for existing links
            for obj in pw_objects:
                if obj.get("type") == "PipeWire:Interface:Link":
                    info = obj.get("info", {})
                    existing_output_node_id = info.get("output-node-id")
                    existing_input_node_id = info.get("input-node-id")

                    # Check if the link matches the given nodes
                    if existing_output_node_id == output_node_id and existing_input_node_id == input_node_id:
                        return True

            # No matching link found
            return False
        except Exception as e:
            print(f"Error checking if link exists: {e}")
            return False
        
    def remove_link(self, output_node_id, input_node_id):
        """Remove a specific link."""
        try:
            cmd = ["pw-link", "-d", str(output_node_id), str(input_node_id)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"Successfully removed link between {output_node_id} and {input_node_id}")
                self.internal_links.remove((output_node_id, input_node_id))  # Remove from internal list
                return True
            else:
                print(f"Failed to remove link between {output_node_id} and {input_node_id}: {result.stderr}")
                return False
        except Exception as e:
            print(f"Error removing link: {e}")
            return False

    def remove_all_links(self):
        """Remove all links created by the app."""
        for output_node_id, input_node_id in self.internal_links[:]:
            self.remove_link(output_node_id, input_node_id)
        self.internal_links.clear()  # Clear the internal list


class AudioRouterApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pipewire Audio Router")
        self.setMinimumSize(800, 600)

        # Pipewire manager
        self.pw_manager = PipewireManager()

        # Setup UI
        self.setup_ui()

        # Initial update
        self.update_node_lists()

    def setup_ui(self):
        # Main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)

        # Header
        header = QLabel("Pipewire Audio Router")
        header.setStyleSheet("font-size: 18pt; font-weight: bold; margin: 10px;")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(header)

        # Description
        description = QLabel("Route audio from applications to microphones")
        description.setStyleSheet("font-size: 10pt; margin-bottom: 20px;")
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(description)

        # Refresh button at the top
        refresh_layout = QHBoxLayout()
        self.refresh_btn = QPushButton("Refresh Devices")
        self.refresh_btn.clicked.connect(self.update_node_lists)
        refresh_layout.addStretch()
        refresh_layout.addWidget(self.refresh_btn)
        main_layout.addLayout(refresh_layout)

        # Main content splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Source applications (left panel)
        source_group = QGroupBox("Source Applications (Playing Audio)")
        source_layout = QVBoxLayout(source_group)

        self.source_list = QListWidget()
        self.source_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        source_layout.addWidget(self.source_list)

        splitter.addWidget(source_group)

        # Target microphones (right panel)
        target_group = QGroupBox("Target Microphones")
        target_layout = QVBoxLayout(target_group)

        self.target_list = QListWidget()
        self.target_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        target_layout.addWidget(self.target_list)

        splitter.addWidget(target_group)

        # Add splitter to main layout
        main_layout.addWidget(splitter, 1)

        # Controls
        controls_layout = QHBoxLayout()

        self.create_link_btn = QPushButton("Create Audio Links")
        self.create_link_btn.clicked.connect(self.create_links)
        controls_layout.addWidget(self.create_link_btn)

        main_layout.addLayout(controls_layout)

        # Active links
        links_group = QGroupBox("Audio Links Created by the App")
        links_layout = QVBoxLayout(links_group)

        self.links_list = QListWidget()
        links_layout.addWidget(self.links_list)

        remove_link_btn = QPushButton("Remove Selected Links")
        remove_link_btn.clicked.connect(self.remove_selected_links)
        links_layout.addWidget(remove_link_btn)

        main_layout.addWidget(links_group)

        # Status bar
        self.statusBar().showMessage("Ready")

        self.setCentralWidget(main_widget)

    def update_node_lists(self):
        """Update the source and target node lists."""
        # Clear lists
        self.source_list.clear()
        self.target_list.clear()

        # Get active applications
        active_apps = self.get_active_applications()

        # Populate source list with applications that are playing audio
        for app_id, app_name in active_apps:
            item = QListWidgetItem()
            item.setText(app_name)
            item.setToolTip(f"Application ID: {app_id}")
            item.setData(Qt.ItemDataRole.UserRole, app_id)
            self.source_list.addItem(item)

        # Populate target list with microphones only
        microphones = self.get_microphones()
        for mic_id, mic_name in microphones:
            item = QListWidgetItem()
            item.setText(mic_name)
            item.setToolTip(f"Microphone ID: {mic_id}")
            item.setData(Qt.ItemDataRole.UserRole, mic_id)
            self.target_list.addItem(item)

        # Update status bar
        self.statusBar().showMessage(f"Found {self.source_list.count()} application(s) and {self.target_list.count()} microphone(s)")
        
    def get_active_applications(self):
        """Get applications that are currently playing audio."""
        try:
            cmd = ["pw-dump"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                return []

            pw_objects = json.loads(result.stdout)
            apps = []

            for obj in pw_objects:
                if obj.get("type") == "PipeWire:Interface:Node":
                    props = obj.get("info", {}).get("props", {})
                    media_class = props.get("media.class", "")

                    # Check if this is an application outputting audio
                    if "Stream/Output/Audio" in media_class:
                        node_id = obj.get("id")
                        process_name = props.get("application.name", props.get("node.name", "Unknown App"))
                        title = props.get("media.name", "")

                        # Combine process name and title
                        app_name = f"{process_name} - {title}" if title else process_name
                        apps.append((node_id, app_name))

            return apps
        except Exception as e:
            print(f"Error getting active applications: {e}")
            return []

    def get_microphones(self):
        """Get available microphones."""
        try:
            cmd = ["pw-dump"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                return []

            pw_objects = json.loads(result.stdout)
            microphones = []

            for obj in pw_objects:
                if obj.get("type") == "PipeWire:Interface:Node":
                    props = obj.get("info", {}).get("props", {})
                    media_class = props.get("media.class", "")

                    # Check if this is a microphone
                    if "Audio/Source" in media_class:
                        node_id = obj.get("id")
                        mic_name = props.get("node.name", "Unknown Microphone")
                        microphones.append((node_id, mic_name))

            return microphones
        except Exception as e:
            print(f"Error getting microphones: {e}")
            return []

    def create_links(self):
        """Create links between selected sources and targets."""
        selected_sources = self.source_list.selectedItems()
        selected_targets = self.target_list.selectedItems()

        if not selected_sources:
            QMessageBox.warning(self, "Warning", "Please select at least one source application")
            return

        if not selected_targets:
            QMessageBox.warning(self, "Warning", "Please select at least one target microphone")
            return

        success_count = 0
        for source_item in selected_sources:
            source_id = source_item.data(Qt.ItemDataRole.UserRole)
            for target_item in selected_targets:
                target_id = target_item.data(Qt.ItemDataRole.UserRole)
                if self.pw_manager.create_link(source_id, target_id):
                    success_count += 1
                    self.update_links_list()  # Update the links list

        if success_count > 0:
            self.statusBar().showMessage(f"Created {success_count} audio links successfully", 5000)
        else:
            self.statusBar().showMessage("Failed to create audio links", 5000)
            
    def get_node_process_name(self, node_id):
        """Get the process name for a given node ID."""
        try:
            cmd = ["pw-dump"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                return f"Unknown Node ({node_id})"

            pw_objects = json.loads(result.stdout)
            for obj in pw_objects:
                if obj.get("id") == node_id:
                    props = obj.get("info", {}).get("props", {})
                    return props.get("application.name", props.get("node.name", f"Unknown Node ({node_id})"))
        except Exception as e:
            print(f"Error getting process name for node {node_id}: {e}")
            return f"Unknown Node ({node_id})"
            
    def update_links_list(self):
        """Update the list of links created by the app."""
        self.links_list.clear()
        for output_node_id, input_node_id in self.pw_manager.internal_links:
            # Get process names for the nodes
            output_name = self.get_node_process_name(output_node_id)
            input_name = self.get_node_process_name(input_node_id)

            # Display the connection as "Process Name → Process Name"
            item = QListWidgetItem()
            item.setText(f"{output_name} → {input_name}")
            item.setData(Qt.ItemDataRole.UserRole, (output_node_id, input_node_id))
            self.links_list.addItem(item)
        
    def remove_selected_links(self):
        """Remove selected links from the list."""
        selected_items = self.links_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Warning", "Please select at least one link to remove")
            return

        for item in selected_items:
            output_node_id, input_node_id = item.data(Qt.ItemDataRole.UserRole)
            if self.pw_manager.remove_link(output_node_id, input_node_id):
                self.links_list.takeItem(self.links_list.row(item))

    def closeEvent(self, event):
        """Handle app closure and clean up connections."""
        self.pw_manager.remove_all_links()  # Remove all links created by the app
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Check if required tools are available
    missing_tools = []
    for tool in ["pw-cli", "pw-link", "pw-dump"]:
        try:
            subprocess.run(["which", tool], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError:
            missing_tools.append(tool)

    if missing_tools:
        QMessageBox.critical(None, "Error",
                             f"Required Pipewire utilities not found: {', '.join(missing_tools)}.\n"
                             "Please install pipewire-tools package.")
        sys.exit(1)

    window = AudioRouterApp()
    window.show()
    sys.exit(app.exec())
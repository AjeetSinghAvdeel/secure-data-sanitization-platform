import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import threading
import json
import os
import sys
import time
from datetime import datetime
import webbrowser

# Check for requests library
try:
    import requests
except ImportError:
    print("ERROR: 'requests' library is required.")
    print("Please install it using: pip install requests")
    sys.exit(1)

# Backend API base URL
API_BASE_URL = "http://localhost:8000"

class SecureWipeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Secure Wipe - Desktop Application")
        self.root.geometry("1200x800")
        self.root.configure(bg="#f0f0f0")
        
        # State variables
        self.devices = []
        self.certificates = []
        self.settings = {}
        self.compliance_data = {}
        self.system_health = {}
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create tabs
        self.create_dashboard_tab()
        self.create_devices_tab()
        self.create_certificates_tab()
        self.create_settings_tab()
        self.create_compliance_tab()
        self.create_tamper_tab()
        
        # Start auto-refresh
        self.refresh_all()
        self.root.after(5000, self.auto_refresh)  # Refresh every 5 seconds
        
    def create_dashboard_tab(self):
        """Main dashboard with system health and quick actions"""
        dashboard_frame = ttk.Frame(self.notebook)
        self.notebook.add(dashboard_frame, text="Dashboard")
        
        # System Health Section
        health_frame = ttk.LabelFrame(dashboard_frame, text="System Health", padding=10)
        health_frame.pack(fill="x", padx=10, pady=10)
        
        self.health_label = ttk.Label(health_frame, text="Loading...", font=("Arial", 10))
        self.health_label.pack(anchor="w")
        
        self.cpu_label = ttk.Label(health_frame, text="CPU: --%", font=("Arial", 9))
        self.cpu_label.pack(anchor="w")
        
        self.memory_label = ttk.Label(health_frame, text="Memory: --%", font=("Arial", 9))
        self.memory_label.pack(anchor="w")
        
        self.disk_label = ttk.Label(health_frame, text="Disk: --%", font=("Arial", 9))
        self.disk_label.pack(anchor="w")
        
        # Quick Actions
        actions_frame = ttk.LabelFrame(dashboard_frame, text="Quick Actions", padding=10)
        actions_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Button(actions_frame, text="Refresh Devices", command=self.refresh_devices).pack(side="left", padx=5)
        ttk.Button(actions_frame, text="View Certificates", command=lambda: self.notebook.select(2)).pack(side="left", padx=5)
        ttk.Button(actions_frame, text="Check Compliance", command=self.refresh_compliance).pack(side="left", padx=5)
        ttk.Button(actions_frame, text="System Analysis", command=self.show_system_analysis).pack(side="left", padx=5)
        
        # Log Area
        log_frame = ttk.LabelFrame(dashboard_frame, text="Activity Log", padding=10)
        log_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, wrap="word")
        self.log_text.pack(fill="both", expand=True)
        self.log_text.config(state="disabled")
        
    def create_devices_tab(self):
        """Device scanning and wiping"""
        devices_frame = ttk.Frame(self.notebook)
        self.notebook.add(devices_frame, text="Devices")
        
        # Device List
        list_frame = ttk.LabelFrame(devices_frame, text="Detected Devices", padding=10)
        list_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Treeview for devices
        columns = ("Device", "Mountpoint", "Size", "Free", "Health", "Risk")
        self.device_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=10)
        
        for col in columns:
            self.device_tree.heading(col, text=col)
            self.device_tree.column(col, width=150)
        
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.device_tree.yview)
        self.device_tree.configure(yscrollcommand=scrollbar.set)
        
        self.device_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Device Details
        details_frame = ttk.LabelFrame(devices_frame, text="Device Details", padding=10)
        details_frame.pack(fill="x", padx=10, pady=10)
        
        self.device_details = scrolledtext.ScrolledText(details_frame, height=8, wrap="word")
        self.device_details.pack(fill="x")
        self.device_details.config(state="disabled")
        
        # Wipe Controls
        wipe_frame = ttk.LabelFrame(devices_frame, text="Secure Wipe", padding=10)
        wipe_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Label(wipe_frame, text="Passes:").grid(row=0, column=0, padx=5, sticky="w")
        self.passes_var = tk.IntVar(value=3)
        passes_spin = ttk.Spinbox(wipe_frame, from_=1, to=7, textvariable=self.passes_var, width=10)
        passes_spin.grid(row=0, column=1, padx=5, sticky="w")
        
        ttk.Button(wipe_frame, text="Scan Devices", command=self.refresh_devices).grid(row=0, column=2, padx=5)
        ttk.Button(wipe_frame, text="Wipe Selected Device", command=self.wipe_selected_device, 
                  style="Danger.TButton").grid(row=0, column=3, padx=5)
        
        # Bind selection event
        self.device_tree.bind("<<TreeviewSelect>>", self.on_device_select)
        
    def create_certificates_tab(self):
        """Certificate management"""
        certs_frame = ttk.Frame(self.notebook)
        self.notebook.add(certs_frame, text="Certificates")
        
        # Certificate List
        list_frame = ttk.LabelFrame(certs_frame, text="Certificates", padding=10)
        list_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        columns = ("ID", "Device", "Method", "Date", "Status")
        self.cert_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=12)
        
        for col in columns:
            self.cert_tree.heading(col, text=col)
            self.cert_tree.column(col, width=200)
        
        cert_scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.cert_tree.yview)
        self.cert_tree.configure(yscrollcommand=cert_scrollbar.set)
        
        self.cert_tree.pack(side="left", fill="both", expand=True)
        cert_scrollbar.pack(side="right", fill="y")
        
        # Certificate Actions
        actions_frame = ttk.Frame(certs_frame)
        actions_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Button(actions_frame, text="Refresh Certificates", command=self.refresh_certificates).pack(side="left", padx=5)
        ttk.Button(actions_frame, text="Download Selected PDF", command=self.download_certificate).pack(side="left", padx=5)
        ttk.Button(actions_frame, text="View Details", command=self.view_certificate_details).pack(side="left", padx=5)
        
        # Wipe Verification Section
        verify_frame = ttk.LabelFrame(certs_frame, text="Wipe Verification", padding=10)
        verify_frame.pack(fill="x", padx=10, pady=10)
        
        # Info label
        info_text = "Note: After secure wipe, files are deleted. Use this to verify:\n" \
                   "1. Files BEFORE wiping (to check if they contain sensitive data)\n" \
                   "2. Test files to demonstrate wipe effectiveness\n" \
                   "3. Files that were overwritten but not yet deleted"
        ttk.Label(verify_frame, text=info_text, font=("Arial", 8), foreground="gray").grid(
            row=0, column=0, columnspan=4, sticky="w", pady=(0, 10))
        
        ttk.Label(verify_frame, text="File to Verify:").grid(row=1, column=0, padx=5, sticky="w")
        self.verify_file_var = tk.StringVar()
        ttk.Entry(verify_frame, textvariable=self.verify_file_var, width=40).grid(row=1, column=1, padx=5)
        ttk.Button(verify_frame, text="Browse", command=self.browse_verify_file).grid(row=1, column=2, padx=5)
        ttk.Button(verify_frame, text="Verify", command=self.verify_file_wipe).grid(row=1, column=3, padx=5)
        
        self.verify_results = scrolledtext.ScrolledText(verify_frame, height=8, wrap="word")
        self.verify_results.grid(row=2, column=0, columnspan=4, sticky="ew", pady=5)
        self.verify_results.config(state="disabled")
        
    def create_settings_tab(self):
        """Settings management"""
        settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(settings_frame, text="Settings")
        
        # Settings Form
        form_frame = ttk.LabelFrame(settings_frame, text="Wipe Settings", padding=20)
        form_frame.pack(fill="x", padx=10, pady=10)
        
        # Wipe Method
        ttk.Label(form_frame, text="Wipe Method:").grid(row=0, column=0, sticky="w", pady=5)
        self.wipe_method_var = tk.StringVar(value="3-pass")
        method_combo = ttk.Combobox(form_frame, textvariable=self.wipe_method_var, 
                                   values=["1-pass", "3-pass", "7-pass"], state="readonly", width=20)
        method_combo.grid(row=0, column=1, sticky="w", pady=5, padx=10)
        
        # Generate Certificates
        self.generate_certs_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(form_frame, text="Generate Certificates", 
                       variable=self.generate_certs_var).grid(row=1, column=0, columnspan=2, sticky="w", pady=5)
        
        # Include QR Code
        self.include_qr_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(form_frame, text="Include QR Code in Certificates", 
                       variable=self.include_qr_var).grid(row=2, column=0, columnspan=2, sticky="w", pady=5)
        
        # Compliance Standard
        ttk.Label(form_frame, text="Compliance Standard:").grid(row=3, column=0, sticky="w", pady=5)
        self.compliance_var = tk.StringVar(value="NIST SP 800-88")
        compliance_combo = ttk.Combobox(form_frame, textvariable=self.compliance_var,
                                       values=["NIST SP 800-88", "GDPR Article 17", "DoD 5220.22-M"], 
                                       state="readonly", width=20)
        compliance_combo.grid(row=3, column=1, sticky="w", pady=5, padx=10)
        
        # Tamper Detection
        self.tamper_detection_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(form_frame, text="Enable Tamper Detection", 
                       variable=self.tamper_detection_var).grid(row=4, column=0, columnspan=2, sticky="w", pady=5)
        
        # Save Button
        ttk.Button(form_frame, text="Save Settings", command=self.save_settings).grid(row=5, column=0, columnspan=2, pady=20)
        
    def create_compliance_tab(self):
        """Compliance dashboard"""
        compliance_frame = ttk.Frame(self.notebook)
        self.notebook.add(compliance_frame, text="Compliance")
        
        # Compliance Scores
        scores_frame = ttk.LabelFrame(compliance_frame, text="Compliance Scores", padding=20)
        scores_frame.pack(fill="x", padx=10, pady=10)
        
        self.nist_label = ttk.Label(scores_frame, text="NIST SP 800-88: --", font=("Arial", 12, "bold"))
        self.nist_label.pack(anchor="w", pady=5)
        
        self.gdpr_label = ttk.Label(scores_frame, text="GDPR Article 17: --", font=("Arial", 12, "bold"))
        self.gdpr_label.pack(anchor="w", pady=5)
        
        self.dod_label = ttk.Label(scores_frame, text="DoD 5220.22-M: --", font=("Arial", 12, "bold"))
        self.dod_label.pack(anchor="w", pady=5)
        
        self.overall_label = ttk.Label(scores_frame, text="Overall Compliance: --", 
                                       font=("Arial", 14, "bold"), foreground="blue")
        self.overall_label.pack(anchor="w", pady=10)
        
        ttk.Button(scores_frame, text="Refresh Compliance", command=self.refresh_compliance).pack(anchor="w", pady=10)
        
    def create_tamper_tab(self):
        """Tamper detection and verification"""
        tamper_frame = ttk.Frame(self.notebook)
        self.notebook.add(tamper_frame, text="Tamper Detection")
        
        # Verification Section
        verify_frame = ttk.LabelFrame(tamper_frame, text="Verify Certificate", padding=10)
        verify_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Label(verify_frame, text="Certificate ID:").grid(row=0, column=0, padx=5, sticky="w")
        self.cert_id_var = tk.StringVar()
        ttk.Entry(verify_frame, textvariable=self.cert_id_var, width=30).grid(row=0, column=1, padx=5)
        ttk.Button(verify_frame, text="Verify", command=self.verify_certificate).grid(row=0, column=2, padx=5)
        
        # Results
        results_frame = ttk.LabelFrame(tamper_frame, text="Verification Results", padding=10)
        results_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.tamper_results = scrolledtext.ScrolledText(results_frame, height=15, wrap="word")
        self.tamper_results.pack(fill="both", expand=True)
        self.tamper_results.config(state="disabled")
        
    # API Methods
    def api_request(self, method, endpoint, data=None):
        """Make API request to backend"""
        try:
            url = f"{API_BASE_URL}{endpoint}"
            if method == "GET":
                response = requests.get(url, timeout=5)
            elif method == "POST":
                response = requests.post(url, json=data, timeout=5)
            else:
                return None
            
            if response.status_code == 200:
                return response.json()
            else:
                self.log(f"API Error: {response.status_code} - {response.text}")
                return None
        except requests.exceptions.ConnectionError:
            self.log("Error: Cannot connect to backend server. Is it running on localhost:8000?")
            return None
        except Exception as e:
            self.log(f"API Request Error: {str(e)}")
            return None
    
    def refresh_all(self):
        """Refresh all data"""
        self.refresh_health()
        self.refresh_devices()
        self.refresh_certificates()
        self.refresh_settings()
        self.refresh_compliance()
    
    def refresh_health(self):
        """Refresh system health"""
        def update():
            health_data = self.api_request("GET", "/api/health")
            if health_data:
                self.system_health = health_data
                self.root.after(0, lambda: self.update_health_display(health_data))
        
        threading.Thread(target=update, daemon=True).start()
    
    def update_health_display(self, data):
        """Update health display"""
        self.health_label.config(text="System Status: Connected" if data.get("connected") else "System Status: Disconnected")
        self.cpu_label.config(text=f"CPU Usage: {data.get('cpu', 0):.1f}%")
        self.memory_label.config(text=f"Memory Usage: {data.get('memory', 0):.1f}%")
        self.disk_label.config(text=f"Disk Usage: {data.get('disk', 0):.1f}%")
    
    def refresh_devices(self):
        """Refresh device list"""
        def update():
            self.log("Scanning for devices...")
            devices_data = self.api_request("GET", "/devices")
            if devices_data:
                self.devices = devices_data.get("devices", [])
                self.root.after(0, lambda: self.update_devices_display())
        
        threading.Thread(target=update, daemon=True).start()
    
    def update_devices_display(self):
        """Update devices treeview"""
        # Clear existing items
        for item in self.device_tree.get_children():
            self.device_tree.delete(item)
        
        # Add devices
        for device in self.devices:
            size_gb = device.get("total", 0) / (1024**3)
            free_gb = device.get("free", 0) / (1024**3)
            health = device.get("health", 0)
            risk = device.get("analysis", {}).get("risk_score", 0)
            
            self.device_tree.insert("", "end", values=(
                device.get("device", "Unknown"),
                device.get("mountpoint", "N/A"),
                f"{size_gb:.2f} GB",
                f"{free_gb:.2f} GB",
                f"{health}%",
                f"{risk}%"
            ))
        
        self.log(f"Found {len(self.devices)} device(s)")
    
    def on_device_select(self, event):
        """Handle device selection"""
        selection = self.device_tree.selection()
        if not selection:
            return
        
        item = self.device_tree.item(selection[0])
        mountpoint = item["values"][1]
        
        # Find device details
        device = next((d for d in self.devices if d.get("mountpoint") == mountpoint), None)
        if device:
            self.device_details.config(state="normal")
            self.device_details.delete(1.0, tk.END)
            
            details = f"Device: {device.get('device', 'N/A')}\n"
            details += f"Mountpoint: {device.get('mountpoint', 'N/A')}\n"
            details += f"Total Size: {device.get('total', 0) / (1024**3):.2f} GB\n"
            details += f"Free Space: {device.get('free', 0) / (1024**3):.2f} GB\n"
            details += f"Health: {device.get('health', 0)}%\n"
            
            analysis = device.get("analysis", {})
            details += f"\nRisk Analysis:\n"
            details += f"Risk Score: {analysis.get('risk_score', 0)}%\n"
            details += f"Files Analyzed: {len(analysis.get('files', []))}\n"
            
            self.device_details.insert(1.0, details)
            self.device_details.config(state="disabled")
    
    def wipe_selected_device(self):
        """Wipe selected device"""
        selection = self.device_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a device to wipe.")
            return
        
        item = self.device_tree.item(selection[0])
        mountpoint = item["values"][1]
        
        if not messagebox.askyesno("Confirm Wipe", 
                                   f"Are you sure you want to wipe:\n{mountpoint}\n\nThis action cannot be undone!"):
            return
        
        def wipe():
            self.log(f"Starting wipe operation on {mountpoint}...")
            passes = self.passes_var.get()
            data = {"mountpoint": mountpoint, "passes": passes}
            result = self.api_request("POST", "/wipe-usb", data)
            
            if result:
                self.root.after(0, lambda: messagebox.showinfo("Success", 
                    f"Wipe completed successfully!\nCertificate ID: {result.get('certificate', {}).get('id', 'N/A')}"))
                self.root.after(0, self.refresh_certificates)
                self.log(f"Wipe completed: {result.get('message', 'Success')}")
            else:
                self.root.after(0, lambda: messagebox.showerror("Error", "Wipe operation failed."))
        
        threading.Thread(target=wipe, daemon=True).start()
    
    def refresh_certificates(self):
        """Refresh certificate list"""
        def update():
            certs_data = self.api_request("GET", "/api/certificates")
            if certs_data:
                self.certificates = certs_data if isinstance(certs_data, list) else []
                self.root.after(0, lambda: self.update_certificates_display())
        
        threading.Thread(target=update, daemon=True).start()
    
    def update_certificates_display(self):
        """Update certificates treeview"""
        # Clear existing items
        for item in self.cert_tree.get_children():
            self.cert_tree.delete(item)
        
        # Add certificates
        for cert in self.certificates:
            self.cert_tree.insert("", "end", values=(
                cert.get("id", "N/A"),
                cert.get("device", "N/A"),
                cert.get("method", "N/A"),
                cert.get("date", "N/A"),
                cert.get("status", "N/A")
            ))
    
    def download_certificate(self):
        """Download selected certificate PDF"""
        selection = self.cert_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a certificate to download.")
            return
        
        item = self.cert_tree.item(selection[0])
        cert_id = item["values"][0]
        
        try:
            url = f"{API_BASE_URL}/api/certificates/download/{cert_id}"
            webbrowser.open(url)
            self.log(f"Downloading certificate: {cert_id}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to download certificate: {str(e)}")
    
    def view_certificate_details(self):
        """View certificate details"""
        selection = self.cert_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a certificate to view.")
            return
        
        item = self.cert_tree.item(selection[0])
        cert_id = item["values"][0]
        
        def fetch():
            cert_data = self.api_request("GET", f"/api/certificates/{cert_id}")
            if cert_data:
                details = f"Certificate ID: {cert_data.get('id', 'N/A')}\n"
                details += f"Device: {cert_data.get('device', 'N/A')}\n"
                details += f"Method: {cert_data.get('method', 'N/A')}\n"
                details += f"Date: {cert_data.get('date', 'N/A')}\n"
                details += f"Status: {cert_data.get('status', 'N/A')}\n"
                if cert_data.get('files_wiped'):
                    details += f"Files Wiped: {cert_data.get('files_wiped')}\n"
                
                self.root.after(0, lambda: messagebox.showinfo("Certificate Details", details))
        
        threading.Thread(target=fetch, daemon=True).start()
    
    def browse_verify_file(self):
        """Browse for file to verify"""
        file_path = filedialog.askopenfilename(title="Select file to verify wipe")
        if file_path:
            self.verify_file_var.set(file_path)
    
    def verify_file_wipe(self):
        """Verify that a file has been properly wiped or check if it contains sensitive data"""
        file_path = self.verify_file_var.get().strip()
        if not file_path:
            messagebox.showwarning("No File", "Please select a file to verify.")
            return
        
        if not os.path.exists(file_path):
            response = messagebox.askyesno(
                "File Not Found", 
                f"File not found: {file_path}\n\n"
                "This is normal if the file was already wiped (files are deleted after secure wipe).\n\n"
                "Would you like to:\n"
                "- Verify a different file that still exists?\n"
                "- Check the device/directory for any remaining recoverable data?\n\n"
                "Click Yes to browse for another file, or No to cancel."
            )
            if response:
                self.browse_verify_file()
            return
        
        def verify():
            self.log(f"Verifying file: {file_path}")
            data = {"file_path": file_path}
            result = self.api_request("POST", "/api/verify-wipe", data)
            
            if result:
                self.verify_results.config(state="normal")
                self.verify_results.delete(1.0, tk.END)
                
                status = result.get('status', 'unknown')
                verified = result.get('verified', False)
                entropy = result.get('entropy', 0)
                issues = result.get('issues', [])
                
                report = f"Verification Report for: {file_path}\n"
                report += "=" * 60 + "\n\n"
                report += f"Status: {status.upper()}\n"
                
                # Interpret results
                if entropy > 7.5:
                    report += f"Entropy: {entropy:.2f} (HIGH - File contains random data)\n"
                    report += f"Interpretation: File appears to be WIPED or contains encrypted/random data\n"
                    report += f"Verified as Wiped: {'YES ✓' if verified else 'PARTIALLY'}\n"
                elif entropy > 0:
                    report += f"Entropy: {entropy:.2f} (LOW - File contains structured data)\n"
                    report += f"Interpretation: File contains readable/recoverable data\n"
                    report += f"Verified as Wiped: NO ✗\n"
                    report += f"⚠ This file has NOT been wiped and may contain sensitive data!\n"
                else:
                    report += f"Entropy: {entropy:.2f} (Cannot calculate)\n"
                
                if result.get('file_size'):
                    size_mb = result['file_size'] / (1024 * 1024)
                    report += f"\nFile Size: {result['file_size']:,} bytes ({size_mb:.2f} MB)\n"
                
                if result.get('current_hash'):
                    report += f"Current Hash: {result['current_hash']}\n"
                
                if result.get('hash_changed') is not None:
                    report += f"Hash Changed: {'YES ✓' if result['hash_changed'] else 'NO ✗'}\n"
                
                if issues:
                    report += f"\nIssues/Warnings Found:\n"
                    for issue in issues:
                        report += f"  - {issue}\n"
                else:
                    report += "\nNo issues detected.\n"
                
                # Final assessment
                report += "\n" + "=" * 60 + "\n"
                if verified:
                    report += "✓ ASSESSMENT: Data appears to be permanently deleted.\n"
                    report += "  Original data cannot be recovered.\n"
                elif entropy > 7.5:
                    report += "⚠ ASSESSMENT: File contains random data.\n"
                    report += "  May be wiped, but verify with hash comparison if available.\n"
                else:
                    report += "✗ ASSESSMENT: File contains recoverable data.\n"
                    report += "  This file has NOT been securely wiped.\n"
                    report += "  Consider wiping this file to permanently delete its contents.\n"
                
                self.verify_results.insert(1.0, report)
                self.verify_results.config(state="disabled")
                
                # Show message
                if verified:
                    self.root.after(0, lambda: messagebox.showinfo("Verification Complete", 
                        "File verification PASSED.\nData appears to be permanently deleted."))
                elif entropy > 7.5:
                    self.root.after(0, lambda: messagebox.showinfo("Verification Complete", 
                        "File contains random data (high entropy).\nMay be wiped, but verify with hash if needed."))
                else:
                    self.root.after(0, lambda: messagebox.showwarning("Verification Warning", 
                        "File contains recoverable data (low entropy).\nThis file has NOT been securely wiped.\n\n"
                        "Consider wiping this file to permanently delete its contents."))
                
                self.log(f"Verification complete: Status={status}, Entropy={entropy:.2f}")
            else:
                self.root.after(0, lambda: messagebox.showerror("Error", "Failed to verify file."))
        
        threading.Thread(target=verify, daemon=True).start()
    
    def refresh_settings(self):
        """Load settings from backend"""
        def update():
            settings_data = self.api_request("GET", "/api/settings")
            if settings_data:
                self.settings = settings_data
                self.root.after(0, lambda: self.update_settings_display(settings_data))
        
        threading.Thread(target=update, daemon=True).start()
    
    def update_settings_display(self, settings):
        """Update settings UI"""
        self.wipe_method_var.set(settings.get("wipeMethod", "3-pass"))
        self.generate_certs_var.set(settings.get("generateCerts", True))
        self.include_qr_var.set(settings.get("includeQRCode", True))
        self.compliance_var.set(settings.get("compliance", "NIST SP 800-88"))
        self.tamper_detection_var.set(settings.get("tamperDetection", True))
    
    def save_settings(self):
        """Save settings to backend"""
        settings = {
            "wipeMethod": self.wipe_method_var.get(),
            "generateCerts": self.generate_certs_var.get(),
            "includeQRCode": self.include_qr_var.get(),
            "compliance": self.compliance_var.get(),
            "tamperDetection": self.tamper_detection_var.get()
        }
        
        def save():
            result = self.api_request("POST", "/api/settings", settings)
            if result:
                self.root.after(0, lambda: messagebox.showinfo("Success", "Settings saved successfully!"))
                self.log("Settings saved")
            else:
                self.root.after(0, lambda: messagebox.showerror("Error", "Failed to save settings."))
        
        threading.Thread(target=save, daemon=True).start()
    
    def refresh_compliance(self):
        """Refresh compliance data"""
        def update():
            compliance_data = self.api_request("GET", "/compliance")
            if compliance_data:
                self.compliance_data = compliance_data
                self.root.after(0, lambda: self.update_compliance_display(compliance_data))
        
        threading.Thread(target=update, daemon=True).start()
    
    def update_compliance_display(self, data):
        """Update compliance display"""
        nist = data.get("nist_sp_800_88", 0)
        gdpr = data.get("gdpr_article_17", 0)
        dod = data.get("dod_5220_22m", 0)
        overall = data.get("overall", 0)
        
        self.nist_label.config(text=f"NIST SP 800-88: {nist}%")
        self.gdpr_label.config(text=f"GDPR Article 17: {gdpr}%")
        self.dod_label.config(text=f"DoD 5220.22-M: {dod}%")
        self.overall_label.config(text=f"Overall Compliance: {overall}%")
    
    def verify_certificate(self):
        """Verify certificate for tampering"""
        cert_id = self.cert_id_var.get().strip()
        if not cert_id:
            messagebox.showwarning("No ID", "Please enter a certificate ID.")
            return
        
        def verify():
            result = self.api_request("GET", f"/tamper/verify/{cert_id}")
            if result:
                status = result.get("status", "unknown")
                message = f"Certificate ID: {cert_id}\n"
                message += f"Status: {status.upper()}\n"
                
                if status == "verified":
                    message += "\n✓ Certificate is valid and untampered."
                elif status == "tampered":
                    message += "\n✗ Certificate has been tampered with!"
                    message += f"\nExpected Hash: {result.get('expected_hash', 'N/A')}"
                    message += f"\nCurrent Hash: {result.get('current_hash', 'N/A')}"
                elif status == "invalid_signature":
                    message += "\n✗ Invalid signature detected!"
                elif status == "not_registered":
                    message += "\n⚠ Certificate not found in tamper database."
                
                self.tamper_results.config(state="normal")
                self.tamper_results.insert(tk.END, f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}\n\n")
                self.tamper_results.see(tk.END)
                self.tamper_results.config(state="disabled")
                
                self.root.after(0, lambda: messagebox.showinfo("Verification Result", message))
                self.log(f"Certificate verification: {status}")
        
        threading.Thread(target=verify, daemon=True).start()
    
    def show_system_analysis(self):
        """Show system analysis"""
        def fetch():
            analysis_data = self.api_request("GET", "/system-analysis")
            if analysis_data:
                system = analysis_data.get("system", {})
                message = f"System Analysis\n\n"
                message += f"Mountpoint: {system.get('mountpoint', 'N/A')}\n"
                message += f"Total: {system.get('total', 0) / (1024**3):.2f} GB\n"
                message += f"Free: {system.get('free', 0) / (1024**3):.2f} GB\n"
                message += f"Health: {system.get('health', 0)}%\n"
                message += f"Risk Score: {system.get('analysis', {}).get('risk_score', 0)}%"
                
                self.root.after(0, lambda: messagebox.showinfo("System Analysis", message))
        
        threading.Thread(target=fetch, daemon=True).start()
    
    def log(self, message):
        """Add message to log"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")
    
    def auto_refresh(self):
        """Auto-refresh health and devices"""
        self.refresh_health()
        self.root.after(5000, self.auto_refresh)

if __name__ == "__main__":
    root = tk.Tk()
    app = SecureWipeApp(root)
    root.mainloop()


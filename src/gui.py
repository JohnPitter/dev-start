"""Graphical User Interface for dev-start using tkinter."""
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, font
import threading
import sys
import os
import stat
import time
import shutil
from pathlib import Path
from datetime import datetime
from .proxy_manager import ProxyManager
from .repo_manager import RepositoryManager
from .detector import TechnologyDetector, Technology
from .installers.git_installer import GitInstaller
from .installers.java_installer import JavaInstaller
from .installers.python_installer import PythonInstaller
from .installers.nodejs_installer import NodeJSInstaller


# Application Theme Colors
class AppTheme:
    """Application color palette and theme constants."""
    PRIMARY = "#CC092F"      # Primary red
    PRIMARY_DARK = "#A00724"  # Darker red
    PRIMARY_LIGHT = "#E63946" # Lighter red
    WHITE = "#FFFFFF"
    BACKGROUND = "#F5F5F5"    # Light gray
    DARK_GRAY = "#333333"
    LIGHT_GRAY = "#E0E0E0"
    TEXT_DARK = "#2B2B2B"
    SUCCESS = "#28A745"
    ERROR = "#DC3545"
    WARNING = "#FFC107"


class LogRedirector:
    """Redirect stdout/stderr to GUI text widget."""

    def __init__(self, text_widget, tag="stdout"):
        self.text_widget = text_widget
        self.tag = tag

    def write(self, message):
        """Write message to text widget."""
        if message.strip():
            self.text_widget.insert(tk.END, message, self.tag)
            self.text_widget.see(tk.END)
            self.text_widget.update()

    def flush(self):
        """Flush method for compatibility."""
        pass


class InstallationReport:
    """Generate and display installation reports."""

    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.repositories = []
        self.successful = []
        self.failed = []
        self.git_installed = False
        self.technologies_detected = {}

    def start(self):
        """Mark start of installation."""
        self.start_time = datetime.now()

    def end(self):
        """Mark end of installation."""
        self.end_time = datetime.now()

    def add_repository(self, url, success, technology=None, error=None):
        """Add repository result."""
        self.repositories.append({
            'url': url,
            'success': success,
            'technology': technology,
            'error': error
        })
        if success:
            self.successful.append(url)
            if technology:
                self.technologies_detected[url] = technology
        else:
            self.failed.append(url)

    def get_duration(self):
        """Get installation duration."""
        if self.start_time and self.end_time:
            delta = self.end_time - self.start_time
            return f"{delta.total_seconds():.2f}s"
        return "N/A"

    def generate_report(self):
        """Generate formatted report."""
        lines = []
        lines.append("=" * 70)
        lines.append("INSTALLATION REPORT")
        lines.append("=" * 70)
        lines.append(f"Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S') if self.start_time else 'N/A'}")
        lines.append(f"Completed: {self.end_time.strftime('%Y-%m-%d %H:%M:%S') if self.end_time else 'N/A'}")
        lines.append(f"Duration: {self.get_duration()}")
        lines.append("")
        lines.append(f"Git Installed: {'Yes' if self.git_installed else 'No'}")
        lines.append("")
        lines.append(f"Total Repositories: {len(self.repositories)}")
        lines.append(f"Successful: {len(self.successful)}")
        lines.append(f"Failed: {len(self.failed)}")
        lines.append("")

        if self.successful:
            lines.append("SUCCESSFUL INSTALLATIONS:")
            lines.append("-" * 70)
            for url in self.successful:
                tech = self.technologies_detected.get(url, 'Unknown')
                tech_str = tech.value if hasattr(tech, 'value') else str(tech)
                lines.append(f"  ✓ {url}")
                lines.append(f"    Technology: {tech_str}")
            lines.append("")

        if self.failed:
            lines.append("FAILED INSTALLATIONS:")
            lines.append("-" * 70)
            for repo in self.repositories:
                if not repo['success']:
                    lines.append(f"  ✗ {repo['url']}")
                    if repo['error']:
                        lines.append(f"    Error: {repo['error']}")
            lines.append("")

        lines.append("=" * 70)
        return "\n".join(lines)


class DevStartGUI:
    """Main GUI application for dev-start."""

    def __init__(self, root):
        self.root = root
        self.root.title("dev-start Technology Configurator")
        self.root.geometry("1000x750")

        # Apply application theme
        self.root.configure(bg=AppTheme.BACKGROUND)

        # Configure custom styles
        self.setup_styles()

        # Initialize managers
        self.proxy_manager = ProxyManager()
        self.repo_manager = RepositoryManager(self.proxy_manager)
        self.detector = TechnologyDetector()
        self.base_dir = Path.home() / 'dev-start-projects'
        self.base_dir.mkdir(exist_ok=True)

        # Installation report
        self.report = InstallationReport()

        # Create UI
        self.create_widgets()

        # Redirect output
        self.stdout_redirector = LogRedirector(self.log_text, "stdout")
        self.stderr_redirector = LogRedirector(self.log_text, "stderr")

    def setup_styles(self):
        """Setup custom application themed styles."""
        style = ttk.Style()
        style.theme_use('clam')

        # Configure colors
        style.configure('.',
                       background=AppTheme.BACKGROUND,
                       foreground=AppTheme.TEXT_DARK,
                       fieldbackground=AppTheme.WHITE)

        # Primary Button
        style.configure('Primary.TButton',
                       background=AppTheme.PRIMARY,
                       foreground=AppTheme.WHITE,
                       borderwidth=0,
                       focuscolor='none',
                       padding=(20, 10),
                       font=('Segoe UI', 10, 'bold'))

        style.map('Primary.TButton',
                 background=[('active', AppTheme.PRIMARY_DARK),
                           ('pressed', AppTheme.PRIMARY_DARK)])

        # Secondary Button
        style.configure('Secondary.TButton',
                       background=AppTheme.LIGHT_GRAY,
                       foreground=AppTheme.TEXT_DARK,
                       borderwidth=1,
                       padding=(15, 8),
                       font=('Segoe UI', 9))

        # Frame styles
        style.configure('TFrame',
                       background=AppTheme.BACKGROUND)

        style.configure('Card.TFrame',
                       background=AppTheme.WHITE,
                       relief='flat',
                       borderwidth=1)

        # Label styles
        style.configure('TLabel',
                       background=AppTheme.BACKGROUND,
                       foreground=AppTheme.TEXT_DARK,
                       font=('Segoe UI', 9))

        style.configure('Title.TLabel',
                       background=AppTheme.PRIMARY,
                       foreground=AppTheme.WHITE,
                       font=('Segoe UI', 18, 'bold'))

        style.configure('Subtitle.TLabel',
                       background=AppTheme.WHITE,
                       foreground=AppTheme.TEXT_DARK,
                       font=('Segoe UI', 11, 'bold'))

        # LabelFrame
        style.configure('TLabelframe',
                       background=AppTheme.WHITE,
                       foreground=AppTheme.TEXT_DARK,
                       borderwidth=0,
                       relief='flat')

        style.configure('TLabelframe.Label',
                       background=AppTheme.WHITE,
                       foreground=AppTheme.PRIMARY,
                       font=('Segoe UI', 11, 'bold'))

        # Entry
        style.configure('TEntry',
                       fieldbackground=AppTheme.WHITE,
                       foreground=AppTheme.TEXT_DARK,
                       borderwidth=1)

        # Progressbar
        style.configure('Primary.Horizontal.TProgressbar',
                       background=AppTheme.PRIMARY,
                       troughcolor=AppTheme.LIGHT_GRAY,
                       bordercolor=AppTheme.LIGHT_GRAY,
                       lightcolor=AppTheme.PRIMARY,
                       darkcolor=AppTheme.PRIMARY)

    def create_widgets(self):
        """Create UI widgets with application theme."""
        # Application Header
        header_frame = tk.Frame(self.root, bg=AppTheme.PRIMARY, height=80)
        header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E))
        header_frame.grid_propagate(False)

        # Logo/Title container
        logo_container = tk.Frame(header_frame, bg=AppTheme.PRIMARY)
        logo_container.pack(expand=True, fill=tk.BOTH, padx=20)

        # Application Logo/Title
        title_label = tk.Label(
            logo_container,
            text="dev-start",
            font=('Segoe UI', 24, 'bold'),
            bg=AppTheme.PRIMARY,
            fg=AppTheme.WHITE
        )
        title_label.pack(side=tk.LEFT, pady=15)

        # Subtitle
        subtitle_label = tk.Label(
            logo_container,
            text="Technology Configurator",
            font=('Segoe UI', 12),
            bg=AppTheme.PRIMARY,
            fg=AppTheme.WHITE
        )
        subtitle_label.pack(side=tk.LEFT, padx=20, pady=15)

        # Input frame
        input_frame = ttk.LabelFrame(self.root, text="Configuração", padding="15")
        input_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N), padx=20, pady=10)

        # Repository URLs
        ttk.Label(input_frame, text="URLs de Repositórios (uma por linha):").grid(
            row=0, column=0, sticky=tk.W, pady=5
        )
        self.repo_text = scrolledtext.ScrolledText(
            input_frame, height=4, width=70
        )
        self.repo_text.grid(row=1, column=0, columnspan=2, pady=5)

        # Proxy toggle button
        self.proxy_visible = False
        self.proxy_button = ttk.Button(
            input_frame,
            text="⚙ Configurar Proxy",
            style='Secondary.TButton',
            command=self.toggle_proxy
        )
        self.proxy_button.grid(row=2, column=0, columnspan=2, pady=10, sticky=tk.W)

        # Proxy settings (initially hidden)
        self.http_proxy_label = ttk.Label(input_frame, text="HTTP Proxy:")
        self.http_proxy_entry = ttk.Entry(input_frame, width=50)
        self.http_proxy_entry.insert(0, "http://proxy.example.com:8080")

        self.https_proxy_label = ttk.Label(input_frame, text="HTTPS Proxy:")
        self.https_proxy_entry = ttk.Entry(input_frame, width=50)
        self.https_proxy_entry.insert(0, "http://proxy.example.com:8080")

        # Buttons with application styling
        button_frame = tk.Frame(self.root, bg=AppTheme.BACKGROUND, pady=15)
        button_frame.grid(row=2, column=0, sticky=tk.W, padx=20)

        self.start_button = ttk.Button(
            button_frame,
            text="Iniciar Instalação",
            style='Primary.TButton',
            command=self.start_installation
        )
        self.start_button.pack(side=tk.LEFT, padx=5)

        self.clear_button = ttk.Button(
            button_frame,
            text="Limpar Log",
            style='Secondary.TButton',
            command=self.clear_log
        )
        self.clear_button.pack(side=tk.LEFT, padx=5)

        self.report_button = ttk.Button(
            button_frame,
            text="Exibir Relatório",
            style='Secondary.TButton',
            command=self.show_report,
            state=tk.DISABLED
        )
        self.report_button.pack(side=tk.LEFT, padx=5)

        # Log area with application styling
        log_frame = ttk.LabelFrame(self.root, text="Log de Instalação", padding="10")
        log_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=20, pady=10)

        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=20,
            width=100,
            state=tk.NORMAL,
            bg=AppTheme.WHITE,
            fg=AppTheme.TEXT_DARK,
            font=('Consolas', 9),
            borderwidth=1,
            relief='solid'
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Configure tags for colored output
        self.log_text.tag_config("stdout", foreground=AppTheme.TEXT_DARK)
        self.log_text.tag_config("stderr", foreground=AppTheme.ERROR)
        self.log_text.tag_config("success", foreground=AppTheme.SUCCESS, font=('Consolas', 9, 'bold'))
        self.log_text.tag_config("error", foreground=AppTheme.ERROR, font=('Consolas', 9, 'bold'))

        # Progress bar with application styling
        self.progress = ttk.Progressbar(
            self.root,
            mode='indeterminate',
            style='Primary.Horizontal.TProgressbar'
        )
        self.progress.grid(row=4, column=0, sticky=(tk.W, tk.E), padx=20, pady=5)

        # Status bar with application styling
        status_frame = tk.Frame(self.root, bg=AppTheme.DARK_GRAY, height=30)
        status_frame.grid(row=5, column=0, sticky=(tk.W, tk.E))

        self.status_label = tk.Label(
            status_frame,
            text="Pronto",
            bg=AppTheme.DARK_GRAY,
            fg=AppTheme.WHITE,
            font=('Segoe UI', 9),
            anchor=tk.W,
            padx=20
        )
        self.status_label.pack(fill=tk.BOTH, expand=True)

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(3, weight=1)

    def log(self, message):
        """Log message to text area."""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)

    def clear_log(self):
        """Clear log text area."""
        self.log_text.delete(1.0, tk.END)

    def set_status(self, message):
        """Update status bar."""
        self.status_label.config(text=message)

    def toggle_proxy(self):
        """Toggle visibility of proxy configuration."""
        if self.proxy_visible:
            # Hide proxy fields
            self.http_proxy_label.grid_remove()
            self.http_proxy_entry.grid_remove()
            self.https_proxy_label.grid_remove()
            self.https_proxy_entry.grid_remove()
            self.proxy_button.config(text="⚙ Configurar Proxy")
            self.proxy_visible = False
        else:
            # Show proxy fields
            self.http_proxy_label.grid(row=3, column=0, sticky=tk.W, pady=5)
            self.http_proxy_entry.grid(row=3, column=1, pady=5, sticky=tk.W)
            self.https_proxy_label.grid(row=4, column=0, sticky=tk.W, pady=5)
            self.https_proxy_entry.grid(row=4, column=1, pady=5, sticky=tk.W)
            self.proxy_button.config(text="✓ Ocultar Proxy")
            self.proxy_visible = True

    def remove_readonly(self, func, path, excinfo):
        """Error handler for shutil.rmtree to handle read-only files."""
        os.chmod(path, stat.S_IWRITE)
        func(path)

    def safe_rmtree(self, path, max_retries=3):
        """Safely remove directory tree with retry logic for locked files."""
        for attempt in range(max_retries):
            try:
                if os.path.exists(path):
                    # First attempt: standard removal with error handler
                    shutil.rmtree(path, onerror=self.remove_readonly)
                    print(f"✓ Removed existing directory: {path}")
                    return True
            except PermissionError as e:
                if attempt < max_retries - 1:
                    print(f"⚠ Attempt {attempt + 1}/{max_retries}: Directory is locked, retrying in 1s...")
                    time.sleep(1)
                else:
                    print(f"✗ Failed to remove directory after {max_retries} attempts")
                    print(f"  Error: {e}")
                    print(f"  Please close any programs using files in: {path}")
                    print(f"  Then manually delete the directory and try again")
                    return False
            except Exception as e:
                print(f"✗ Error removing directory: {e}")
                return False
        return False

    def start_installation(self):
        """Start installation process in separate thread."""
        # Validate input
        repo_urls = self.repo_text.get(1.0, tk.END).strip().split('\n')
        repo_urls = [url.strip() for url in repo_urls if url.strip()]

        if not repo_urls:
            messagebox.showerror("Error", "Please enter at least one repository URL")
            return

        # Disable start button
        self.start_button.config(state=tk.DISABLED)
        self.clear_log()
        self.set_status("Installation in progress...")
        self.progress.start()

        # Reset report
        self.report = InstallationReport()
        self.report.start()

        # Run in thread
        thread = threading.Thread(
            target=self.run_installation,
            args=(repo_urls,),
            daemon=True
        )
        thread.start()

    def run_installation(self, repo_urls):
        """Run installation process."""
        # Redirect output
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = self.stdout_redirector
        sys.stderr = self.stderr_redirector

        try:
            # Setup proxy
            http_proxy = self.http_proxy_entry.get().strip()
            https_proxy = self.https_proxy_entry.get().strip()

            if http_proxy and http_proxy != "http://proxy.example.com:8080":
                self.proxy_manager.set_proxy(http_proxy=http_proxy, https_proxy=https_proxy)
                print(f"✓ Proxy configured: {http_proxy}")

            # Check Git
            print("\n" + "=" * 60)
            print("Checking Git installation...")
            print("=" * 60)

            git_installer = GitInstaller(self.base_dir, self.proxy_manager)
            if not git_installer.is_installed():
                print("⚠ Git not installed. Installing...")
                if git_installer.install():
                    print("✓ Git installed successfully")
                    self.report.git_installed = True

                    # Configure Git - prompt user for details
                    git_config = self._prompt_git_config()
                    if git_config:
                        git_installer.configure(
                            user_name=git_config['name'],
                            user_email=git_config['email'],
                            ssl_verify=git_config['ssl_verify']
                        )
                    else:
                        print("⚠ Git configuration skipped")
                else:
                    print("✗ Failed to install Git")
                    messagebox.showerror("Error", "Failed to install Git")
                    return
            else:
                version = git_installer.detect_version()
                print(f"✓ Git is installed (version {version})")

                # Check if Git needs configuration
                if not git_installer._is_git_configured():
                    print("⚠ Git is not configured")
                    git_config = self._prompt_git_config()
                    if git_config:
                        git_installer.configure(
                            user_name=git_config['name'],
                            user_email=git_config['email'],
                            ssl_verify=git_config['ssl_verify']
                        )

            # Process repositories
            for repo_url in repo_urls:
                try:
                    print(f"\n{'=' * 60}")
                    print(f"Processing: {repo_url}")
                    print("=" * 60)

                    # Clone repository
                    repo_name = self.repo_manager.get_repo_name(repo_url)
                    repo_path = self.base_dir / repo_name

                    if repo_path.exists():
                        print(f"⚠ Repository already exists: {repo_path}")
                        if not self.safe_rmtree(str(repo_path)):
                            error = "Failed to remove existing repository (directory may be locked)"
                            print(f"✗ {error}")
                            self.report.add_repository(repo_url, False, error=error)
                            continue

                    if not self.repo_manager.clone_repository(repo_url, repo_path):
                        error = "Failed to clone repository"
                        print(f"✗ {error}")
                        self.report.add_repository(repo_url, False, error=error)
                        continue

                    # Detect technology
                    print("\nDetecting technology...")
                    technology = self.detector.detect(repo_path)

                    if technology == Technology.UNKNOWN:
                        error = "Could not detect project technology"
                        print(f"✗ {error}")
                        self.report.add_repository(repo_url, False, error=error)
                        continue

                    print(f"✓ Detected: {technology.value}")

                    # Install and configure
                    installer = self._get_installer(technology, repo_path)
                    if not installer:
                        error = f"No installer available for {technology.value}"
                        print(f"✗ {error}")
                        self.report.add_repository(repo_url, False, error=error)
                        continue

                    if not installer.is_installed():
                        print(f"\nInstalling {technology.value}...")
                        if not installer.install():
                            error = "Installation failed"
                            print(f"✗ {error}")
                            self.report.add_repository(repo_url, False, technology=technology, error=error)
                            continue
                        print(f"✓ Installation completed")
                    else:
                        print(f"✓ {technology.value} is already installed")

                    print("\nConfiguring project...")
                    if not installer.configure():
                        error = "Configuration failed"
                        print(f"✗ {error}")
                        self.report.add_repository(repo_url, False, technology=technology, error=error)
                        continue

                    print("✓ Configuration completed")
                    print(f"\n✓ Project ready at: {repo_path}")
                    self.report.add_repository(repo_url, True, technology=technology)

                except Exception as e:
                    error = str(e)
                    print(f"✗ Error processing {repo_url}: {error}")
                    self.report.add_repository(repo_url, False, error=error)

            # Finish
            self.report.end()
            print("\n" + "=" * 60)
            print("INSTALLATION COMPLETE")
            print("=" * 60)
            print(f"Successful: {len(self.report.successful)}")
            print(f"Failed: {len(self.report.failed)}")
            print(f"Duration: {self.report.get_duration()}")

        finally:
            # Restore output
            sys.stdout = old_stdout
            sys.stderr = old_stderr

            # Update UI
            self.root.after(0, self.installation_complete)

    def installation_complete(self):
        """Called when installation is complete."""
        self.progress.stop()
        self.start_button.config(state=tk.NORMAL)
        self.report_button.config(state=tk.NORMAL)
        self.set_status("Installation complete")
        messagebox.showinfo(
            "Complete",
            f"Installation complete!\n\nSuccessful: {len(self.report.successful)}\nFailed: {len(self.report.failed)}"
        )

    def show_report(self):
        """Show installation report in new window."""
        report_window = tk.Toplevel(self.root)
        report_window.title("Installation Report")
        report_window.geometry("800x600")

        # Report text
        report_text = scrolledtext.ScrolledText(
            report_window,
            width=100,
            height=35,
            font=('Courier', 10)
        )
        report_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Insert report
        report_content = self.report.generate_report()
        report_text.insert(1.0, report_content)
        report_text.config(state=tk.DISABLED)

        # Save button
        save_button = ttk.Button(
            report_window,
            text="Save Report",
            command=lambda: self.save_report(report_content)
        )
        save_button.pack(pady=5)

    def save_report(self, content):
        """Save report to file."""
        from tkinter import filedialog
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            messagebox.showinfo("Saved", f"Report saved to {filename}")

    def _prompt_git_config(self):
        """Prompt user for Git configuration."""
        # Create a simple dialog using simpledialog
        from tkinter import simpledialog

        result = messagebox.askyesno(
            "Configurar Git",
            "Git precisa ser configurado com suas informações.\n\n"
            "Deseja configurar agora?\n\n"
            "(Nome e email são necessários para commits)"
        )

        if not result:
            return None

        # Get user name
        name = simpledialog.askstring(
            "Configuração Git - Nome",
            "Digite seu nome completo:",
            parent=self.root
        )

        if not name:
            return None

        # Get user email
        email = simpledialog.askstring(
            "Configuração Git - Email",
            "Digite seu email:",
            parent=self.root
        )

        if not email:
            return None

        # Ask about SSL verification
        ssl_verify = messagebox.askyesno(
            "Configuração Git - SSL",
            "Ativar verificação SSL?\n\n"
            "Selecione 'Não' se estiver em uma rede corporativa\n"
            "com certificados próprios.",
            default=messagebox.YES
        )

        return {
            'name': name,
            'email': email,
            'ssl_verify': ssl_verify
        }

    def _get_installer(self, technology: Technology, repo_path: Path):
        """Get appropriate installer for technology."""
        installers = {
            Technology.JAVA_SPRINGBOOT: JavaInstaller,
            Technology.PYTHON: PythonInstaller,
            Technology.NODEJS: NodeJSInstaller
        }

        installer_class = installers.get(technology)
        if installer_class:
            return installer_class(repo_path, self.proxy_manager)
        return None


def main():
    """Run GUI application."""
    root = tk.Tk()
    app = DevStartGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()

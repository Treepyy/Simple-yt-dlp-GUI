import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import subprocess
import threading
import shlex

class YTDLP_GUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Treepy's yt-dlp GUI")
        self.root.geometry("600x550")
        
        style = ttk.Style()
        style.theme_use('clam')
        
        # Variables
        self.url_var = tk.StringVar()
        self.mode_var = tk.StringVar(value="Basic")
        self.start_time_var = tk.StringVar(value="00:00:00")
        self.end_time_var = tk.StringVar(value="00:00:10")
        self.custom_cmd_var = tk.StringVar(value="yt-dlp -F <URL>")
        self.audio_quality_var = tk.StringVar(value="320")
        
        # 1. URL Section
        url_frame = ttk.LabelFrame(root, text="Target URL", padding=10)
        url_frame.pack(fill="x", padx=10, pady=5)
        ttk.Entry(url_frame, textvariable=self.url_var).pack(fill="x")

        # 2. Mode Selection
        mode_frame = ttk.LabelFrame(root, text="Download Mode", padding=10)
        mode_frame.pack(fill="x", padx=10, pady=5)
        
        modes = [
            ("Basic Video Download", "Basic"),
            ("Video Section Download", "Section"),
            ("MP3 Download (Audio Only)", "MP3"),
            ("Custom Command", "Custom")
        ]
        
        for text, mode in modes:
            ttk.Radiobutton(mode_frame, text=text, variable=self.mode_var, 
                            value=mode, command=self.toggle_inputs).pack(anchor="w", pady=2)

        # 3. Dynamic Options Frame
        self.options_frame = ttk.Frame(root, padding=10)
        self.options_frame.pack(fill="x", padx=10)
        
        # (Widgets for Section Download)
        self.section_widgets = ttk.Frame(self.options_frame)
        ttk.Label(self.section_widgets, text="Start Time (HH:MM:SS):").pack(side="left")
        ttk.Entry(self.section_widgets, textvariable=self.start_time_var, width=10).pack(side="left", padx=5)
        ttk.Label(self.section_widgets, text="End Time (HH:MM:SS):").pack(side="left")
        ttk.Entry(self.section_widgets, textvariable=self.end_time_var, width=10).pack(side="left", padx=5)
        
        # Restricts MP3 quality input to numbers only
        vcmd = (self.root.register(self.validate_only_numbers), '%P')
        
        # (Widgets for MP3 Download)
        self.mp3_widgets = ttk.Frame(self.options_frame)
        ttk.Label(self.mp3_widgets, text="Audio Quality in kbps (e.g. 192, 320):").pack(side="left")
        ttk.Entry(self.mp3_widgets, textvariable=self.audio_quality_var, validate="key", validatecommand=vcmd, width=10).pack(side="left", padx=5)
        ttk.Label(self.mp3_widgets, text="kbps").pack(side="left")
        
        # (Widgets for Custom Command)
        self.custom_widgets = ttk.Frame(self.options_frame)
        ttk.Label(self.custom_widgets, text="Command:").pack(side="left")
        ttk.Entry(self.custom_widgets, textvariable=self.custom_cmd_var).pack(side="left", fill="x", expand=True, padx=5)

        # 4. Action Button
        self.download_btn = ttk.Button(root, text="Execute", command=self.start_download_thread)
        self.download_btn.pack(pady=10)

        # 5. Output Log
        log_frame = ttk.LabelFrame(root, text="Output Log", padding=10)
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)
        self.log_area = scrolledtext.ScrolledText(log_frame, height=10, state='disabled', font=("Consolas", 9))
        self.log_area.pack(fill="both", expand=True)

        # Initialize input visibility
        self.toggle_inputs()

    def toggle_inputs(self):
        """Show/Hide specific input fields based on selected mode."""
        self.section_widgets.pack_forget()
        self.custom_widgets.pack_forget()
        self.mp3_widgets.pack_forget()
        
        mode = self.mode_var.get()
        if mode == "Section":
            self.section_widgets.pack(fill="x", pady=5)
        elif mode == "MP3":
            self.mp3_widgets.pack(fill="x", pady=5)
        elif mode == "Custom":
            self.custom_widgets.pack(fill="x", pady=5)

    def log(self, message):
        """Thread-safe logging to the text area."""
        self.log_area.config(state='normal')
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)
        self.log_area.config(state='disabled')
    
    def validate_only_numbers(self, char):
        return char.isdigit() or char == ""
    
    def build_command(self):
        url = self.url_var.get().strip()
        mode = self.mode_var.get()
        
        if not url and mode != "Custom":
            messagebox.showerror("Error", "Please enter a URL")
            return None

        cmd = []

        if mode == "Basic":
            cmd = ['yt-dlp', '--no-mtime', url]
            
        elif mode == "Section":
            start = self.start_time_var.get()
            end = self.end_time_var.get()
            section_arg = f"*{start}-{end}"
            cmd = ['yt-dlp', '--no-mtime', '--download-sections', section_arg, url]
            
        elif mode == "MP3":
            quality = self.audio_quality_var.get()
            mp3_arg = f"{quality}K"
            cmd = ['yt-dlp', '-x', '--no-mtime', '--audio-format', 'mp3', '--audio-quality', mp3_arg, url]
            
        elif mode == "Custom":
            raw_cmd = self.custom_cmd_var.get()
            # Replace <URL> placeholder if it exists, otherwise append URL if not present
            if "<URL>" in raw_cmd:
                raw_cmd = raw_cmd.replace("<URL>", url)
            elif url and url not in raw_cmd:
                raw_cmd += f" {url}"
                
            try:
                cmd = shlex.split(raw_cmd)
            except Exception as e:
                self.log(f"Error parsing custom command: {e}")
                return None

        return cmd

    def run_process(self, cmd):
        """Runs the subprocess and captures output."""
        self.download_btn.config(state='disabled')
        self.log("-" * 40)
        self.log(f"Executing: {' '.join(cmd)}")
        self.log("-" * 40)

        try:
            # Popen allows reading stdout line by line
            process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT, 
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if subprocess.os.name == 'nt' else 0
            )

            # Read output in real-time
            for line in process.stdout:
                self.log(line.strip())

            process.wait()
            
            if process.returncode == 0:
                self.log("\n[SUCCESS] Operation completed.")
            else:
                self.log(f"\n[ERROR] Process failed with return code {process.returncode}.")

        except FileNotFoundError:
            self.log("\n[CRITICAL ERROR] 'yt-dlp' was not found. Is it installed and in your PATH?")
        except Exception as e:
            self.log(f"\n[ERROR] An unexpected error occurred: {str(e)}")
        finally:
            self.download_btn.config(state='normal')

    def start_download_thread(self):
        cmd = self.build_command()
        if cmd:
            threading.Thread(target=self.run_process, args=(cmd,), daemon=True).start()

if __name__ == "__main__":
    root = tk.Tk()
    app = YTDLP_GUI(root)
    root.mainloop()
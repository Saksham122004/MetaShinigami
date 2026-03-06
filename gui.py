import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, scrolledtext
import json

# reuse core functionality from MetaShinigami to avoid duplication
from MetaShinigami import extract_metadata, flatten_dict


class MetadataGUI(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("🔎 Universal Metadata Extractor - Pro")
        self.geometry("1100x700")
        self.configure(bg="#0f172a")  # Dark background

        self.file_path = tk.StringVar()
        self.output_format = tk.StringVar(value="json")

        self.style = ttk.Style(self)
        self.style.theme_use("clam")

        # Dark theme styling
        self.style.configure("TFrame", background="#0f172a")
        self.style.configure("TLabel", background="#0f172a", foreground="#e2e8f0", font=("Segoe UI", 11))
        self.style.configure("TButton", font=("Segoe UI", 10, "bold"))
        self.style.configure("TCombobox", fieldbackground="#1e293b", background="#1e293b", foreground="white")

        self.create_widgets()

    def create_widgets(self):

        # ===== HEADER =====
        header = tk.Label(
            self,
            text="UNIVERSAL METADATA EXTRACTOR",
            bg="#0f172a",
            fg="#38bdf8",
            font=("Segoe UI", 20, "bold")
        )
        header.pack(pady=15)

        # ===== MAIN CARD =====
        main_frame = ttk.Frame(self)
        main_frame.pack(fill="x", padx=30, pady=10)

        ttk.Label(main_frame, text="Target File:").grid(row=0, column=0, sticky="w", pady=5)

        file_entry = ttk.Entry(main_frame, textvariable=self.file_path, width=75)
        file_entry.grid(row=0, column=1, padx=10)

        browse_btn = tk.Button(
            main_frame,
            text="Browse",
            command=self.browse_file,
            bg="#2563eb",
            fg="white",
            relief="flat",
            padx=10
        )
        browse_btn.grid(row=0, column=2)

        ttk.Label(main_frame, text="Output Format:").grid(row=1, column=0, sticky="w", pady=10)

        format_box = ttk.Combobox(
            main_frame,
            textvariable=self.output_format,
            values=["json", "csv", "txt"],
            state="readonly",
            width=15
        )
        format_box.grid(row=1, column=1, sticky="w")

        extract_btn = tk.Button(
            main_frame,
            text="Extract Metadata",
            command=self.run_extraction,
            bg="#22c55e",
            fg="white",
            font=("Segoe UI", 11, "bold"),
            relief="flat",
            padx=15,
            pady=5
        )
        extract_btn.grid(row=1, column=2, padx=10)

        # ===== PROGRESS BAR =====
        self.progress = ttk.Progressbar(self, mode="indeterminate")
        self.progress.pack(fill="x", padx=30, pady=10)

        # ===== OUTPUT AREA =====
        self.output_box = scrolledtext.ScrolledText(
            self,
            wrap=tk.WORD,
            bg="#1e293b",
            fg="#e2e8f0",
            insertbackground="white",
            font=("Consolas", 10)
        )
        self.output_box.pack(fill="both", expand=True, padx=30, pady=10)

        # ===== STATUS BAR =====
        self.status = tk.Label(
            self,
            text="Ready",
            bg="#0f172a",
            fg="#94a3b8",
            anchor="w"
        )
        self.status.pack(fill="x", side="bottom", padx=10, pady=5)

    def browse_file(self):
        path = filedialog.askopenfilename()
        if path:
            self.file_path.set(path)
            self.status.config(text=f"Selected: {os.path.basename(path)}")

    def run_extraction(self):
        path = self.file_path.get()

        if not path or not os.path.isfile(path):
            messagebox.showerror("Error", "Please select a valid file")
            return

        try:
            self.progress.start()
            self.status.config(text="Extracting metadata...")

            metadata = extract_metadata(path)
            self.output_box.delete("1.0", tk.END)

            if self.output_format.get() == "json":
                text = json.dumps(metadata, indent=2, default=str)

            elif self.output_format.get() == "csv":
                flat = flatten_dict(metadata)
                text = ",".join(flat.keys()) + "\n" + ",".join(map(str, flat.values()))

            else:
                lines = []

                def walk(d, indent=0):
                    for k, v in d.items():
                        if isinstance(v, dict):
                            lines.append("  " * indent + f"[{k}]")
                            walk(v, indent + 1)
                        else:
                            lines.append("  " * indent + f"{k}: {v}")

                walk(metadata)
                text = "\n".join(lines)

            self.output_box.insert(tk.END, text)
            self.status.config(text="Extraction Completed ✅")

        except Exception as e:
            messagebox.showerror("Extraction Error", str(e))
            self.status.config(text="Error occurred ❌")

        finally:
            self.progress.stop()

if __name__ == "__main__":
    app = MetadataGUI()
    app.mainloop()

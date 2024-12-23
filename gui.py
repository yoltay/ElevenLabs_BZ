import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import requests
import os
import csv

class TTSApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Hasan Hoca TTS")

        self.save_api_keys = tk.BooleanVar()
        self.api_key = tk.StringVar()
        self.voice_id = tk.StringVar()
        self.text_template = tk.StringVar(value="Merhaba Canım öğrencim {variable1}, nasılsın? {variable2} testlerini kontrol ettim, harika gidiyorsun. {variable3} gerçekten çok iyi bir puan.")
        self.csv_filepath = tk.StringVar()

        self.stability = tk.DoubleVar(value=1.0)
        self.similarity = tk.DoubleVar(value=1.0)
        self.style_exaggeration = tk.DoubleVar(value=0.20)

        # API Anahtarlarını Yükle
        self.load_api_keys()

        # API Key Girişi
        ttk.Label(root, text="ElevenLabs API Key:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        ttk.Entry(root, textvariable=self.api_key, width=50, show="*").grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        # Voice ID Girişi
        ttk.Label(root, text="Voice ID:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        ttk.Entry(root, textvariable=self.voice_id, width=50).grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        # API Key Kaydetme Checkbox
        ttk.Checkbutton(root, text="API Key ve Voice ID'yi Kaydet", variable=self.save_api_keys).grid(row=2, column=1, padx=5, pady=5, sticky="w")

        # Text Template Alanı
        ttk.Label(root, text="Text Şablonu:").grid(row=3, column=0, padx=5, pady=5, sticky="ne")
        self.text_area = tk.Text(root, height=5, width=60)
        self.text_area.grid(row=3, column=1, padx=5, pady=5, sticky="nsew")
        self.text_area.insert(tk.END, self.text_template.get())

        # Voice Settings Alanı
        ttk.Label(root, text="Voice Settings:").grid(row=4, column=0, padx=5, pady=5, sticky="nw")
        settings_frame = ttk.Frame(root)
        settings_frame.grid(row=4, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(settings_frame, text="Stability:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.stability_slider = tk.Scale(settings_frame, from_=0.0, to=1.0, resolution=0.01, orient=tk.HORIZONTAL, variable=self.stability)
        self.stability_slider.grid(row=0, column=1, padx=5, pady=2, sticky="ew")

        ttk.Label(settings_frame, text="Similarity:").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.similarity_slider = tk.Scale(settings_frame, from_=0.0, to=1.0, resolution=0.01, orient=tk.HORIZONTAL, variable=self.similarity)
        self.similarity_slider.grid(row=1, column=1, padx=5, pady=2, sticky="ew")

        ttk.Label(settings_frame, text="Style Exaggeration:").grid(row=2, column=0, padx=5, pady=2, sticky="w")
        self.style_slider = tk.Scale(settings_frame, from_=0.0, to=1.0, resolution=0.01, orient=tk.HORIZONTAL, variable=self.style_exaggeration)
        self.style_slider.grid(row=2, column=1, padx=5, pady=2, sticky="ew")

        settings_frame.columnconfigure(1, weight=1)

        # CSV Upload Alanı
        upload_frame = ttk.Frame(root)
        upload_frame.grid(row=5, column=1, padx=5, pady=5, sticky="ew")
        ttk.Button(upload_frame, text="CSV Yükle", command=self.upload_csv).pack(side=tk.LEFT, padx=5)
        ttk.Label(upload_frame, textvariable=self.csv_filepath).pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Değişken Tablosu
        ttk.Label(root, text="Değişkenler:").grid(row=6, column=0, padx=5, pady=5, sticky="nw")
        self.tree = ttk.Treeview(root, columns=("variable1", "variable2", "variable3", "variable4"), show="headings")
        self.tree.heading("variable1", text="variable1")
        self.tree.heading("variable2", text="variable2")
        self.tree.heading("variable3", text="variable3")
        self.tree.heading("variable4", text="variable4")
        self.tree.grid(row=6, column=1, padx=5, pady=5, sticky="nsew")

        # Düzenleme için tıklama olayı
        self.tree.bind("<Double-1>", self.on_cell_edit)

        # Kopyala-yapıştır desteği
        self.tree.bind("<Control-v>", self.paste_from_clipboard)

        # Sağ Tık Menüsü (Ekle/Sil)
        self.context_menu = tk.Menu(root, tearoff=0)
        self.context_menu.add_command(label="Satır Ekle", command=self.add_row)
        self.context_menu.add_command(label="Satır Sil", command=self.delete_selected_rows)
        self.tree.bind("<Button-3>", self.show_context_menu)

        # Butonlar
        ttk.Button(root, text="Oluştur", command=self.generate_audio).grid(row=7, column=1, padx=5, pady=10, sticky="e")

        # Log İzleme Alanı
        ttk.Label(root, text="Log:").grid(row=8, column=0, padx=5, pady=5, sticky="nw")
        self.log_area = tk.Text(root, height=5, width=60, state=tk.DISABLED)
        self.log_area.grid(row=8, column=1, padx=5, pady=5, sticky="nsew")

        self.log_scrollbar = ttk.Scrollbar(root, command=self.log_area.yview)
        self.log_scrollbar.grid(row=8, column=2, sticky='ns')
        self.log_area.config(yscrollcommand=self.log_scrollbar.set)

        # Grid yapılandırması
        root.grid_columnconfigure(1, weight=1)
        root.grid_rowconfigure(6, weight=1)
        root.grid_rowconfigure(8, weight=1)

        self.add_row("Merve", "Günlük", "95")
        self.add_row("Emrullah", "Görev listendeki", "88")
        self.add_row("Edin Džeko", "kondisyon", "47")

        self.editing_item = None
        self.editing_col = None
        self.edit_entry = None

    def load_api_keys(self):
        try:
            with open("api_keys.txt", "r") as f:
                lines = f.readlines()
                if len(lines) >= 2:
                    self.api_key.set(lines[0].strip())
                    self.voice_id.set(lines[1].strip())
        except FileNotFoundError:
            pass  # Dosya bulunamadıysa sorun değil
        except Exception as e:
            print(f"API anahtarları yüklenirken bir hata oluştu: {e}")

    def save_api_keys_to_file(self):
        try:
            with open("api_keys.txt", "w") as f:
                f.write(f"{self.api_key.get()}\n")
                f.write(f"{self.voice_id.get()}\n")
        except Exception as e:
            print(f"API anahtarları kaydedilirken bir hata oluştu: {e}")

    def log(self, message):
        self.log_area.config(state=tk.NORMAL)
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)
        self.log_area.config(state=tk.DISABLED)
        self.root.update()

    def show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def add_row(self, var1="", var2="", var3="", var4=""):
        self.tree.insert("", tk.END, values=(var1, var2, var3, var4))

    def delete_selected_rows(self):
        selected_items = self.tree.selection()
        for item in selected_items:
            self.tree.delete(item)

    def on_cell_edit(self, event):
        if self.editing_item:  # Başka bir hücre düzenleniyorsa
            return

        item = self.tree.identify_row(event.y)
        column = self.tree.identify_column(event.x)

        if not column or column == '#0':
            return

        self.editing_item = item
        self.editing_col = column

        x, y, width, height = self.tree.bbox(item, column)
        current_value = self.tree.set(item, column)

        self.edit_entry = ttk.Entry(self.tree, width=int(width/7))  # Genişliği ayarla
        self.edit_entry.place(x=x, y=y, width=width, height=height)
        self.edit_entry.insert(0, current_value)
        self.edit_entry.focus_set()
        self.edit_entry.bind("<Return>", self.finish_edit)
        self.edit_entry.bind("<FocusOut>", self.finish_edit)

    def finish_edit(self, event):
        if self.editing_item and self.editing_col and self.edit_entry:
            new_value = self.edit_entry.get()
            self.tree.set(self.editing_item, self.editing_col, new_value)
            self.edit_entry.destroy()
            self.editing_item = None
            self.editing_col = None
            self.edit_entry = None

    def paste_from_clipboard(self, event=None):
        try:
            clipboard_data = self.root.clipboard_get()
            rows = clipboard_data.strip().split('\n')
            self.tree.delete(*self.tree.get_children())  # Mevcut verileri temizle
            for row in rows:
                cols = row.split('\t')  # Excel genellikle tab ile ayırır
                if len(cols) >= 1:
                    self.tree.insert("", tk.END, values=cols)
        except tk.TclError:
            messagebox.showerror("Hata", "Panodan veri okunamadı.")

    def upload_csv(self):
        filepath = filedialog.askopenfilename(
            defaultextension=".csv",
            filetypes=[("CSV dosyaları", "*.csv"), ("Tüm dosyalar", "*.*")]
        )
        if filepath:
            self.csv_filepath.set(filepath)
            self.log(f"CSV dosyası yüklendi: {filepath}")
            self.load_csv_data(filepath)

    def load_csv_data(self, filepath):
        try:
            self.tree.delete(*self.tree.get_children())  # Mevcut verileri temizle
            with open(filepath, mode='r', encoding='utf-8-sig') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    self.tree.insert("", tk.END, values=(row.get('variable1', ''), row.get('variable2', ''), row.get('variable3', ''), row.get('variable4', '')))
        except FileNotFoundError:
            messagebox.showerror("Hata", "CSV dosyası bulunamadı.")
        except Exception as e:
            messagebox.showerror("Hata", f"CSV dosyası okunurken bir hata oluştu: {e}")

    def generate_audio(self):
        api_key = self.api_key.get()
        voice_id = self.voice_id.get()
        text_template = self.text_area.get("1.0", tk.END).strip()

        if not api_key:
            messagebox.showerror("Hata", "Lütfen ElevenLabs API Key girin.")
            return

        if not voice_id:
            messagebox.showerror("Hata", "Lütfen Voice ID girin.")
            return

        if not text_template:
            messagebox.showerror("Hata", "Lütfen Text Template girin.")
            return

        voice_settings = {
            "stability": self.stability.get(),
            "similarity_boost": self.similarity.get(),
            "style": self.style_exaggeration.get()
        }

        variables_data = []
        if self.csv_filepath.get():
            try:
                with open(self.csv_filepath.get(), mode='r', encoding='utf-8-sig') as csvfile:
                    reader = csv.DictReader(csvfile)
                    for row in reader:
                        variables_data.append((row.get('variable1', ''), row.get('variable2', ''), row.get('variable3', ''), row.get('variable4', '')))
            except Exception as e:
                messagebox.showerror("Hata", f"CSV dosyası okunurken bir hata oluştu: {e}")
                return
        else:
            for item in self.tree.get_children():
                variables_data.append(self.tree.item(item)["values"])

        if not variables_data:
            messagebox.showerror("Hata", "Lütfen değişken verilerini girin veya bir CSV dosyası yükleyin.")
            return

        output_dir = "sesler"
        os.makedirs(output_dir, exist_ok=True)

        API_URL = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream"
        headers = {
            "xi-api-key": api_key,
            "Content-Type": "application/json"
        }

        if self.save_api_keys.get():
            self.save_api_keys_to_file()

        for i, row_data in enumerate(variables_data):
            variable1, variable2, variable3, variable4 = row_data
            variables = {"variable1": variable1, "variable2": variable2, "variable3": variable3, "variable4": variable4}
            formatted_text = text_template.format(**variables)

            payload = {
                "text": formatted_text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": voice_settings
            }

            try:
                self.log(f"İşleniyor: {variable1}")
                response = requests.post(API_URL, headers=headers, json=payload, stream=True)
                response.raise_for_status()

                output_filename = os.path.join(output_dir, f"{variable1}.mp3")
                with open(output_filename, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=None):
                        if chunk:
                            f.write(chunk)
                self.log(f"Başarıyla oluşturuldu: {output_filename}")
            except requests.exceptions.RequestException as e:
                error_message = f"API Hatası (Satır {i+1}): {e}"
                self.log(error_message)
                messagebox.showerror("API Hatası", error_message)
            except Exception as e:
                error_message = f"Beklenmeyen Hata (Satır {i+1}): {e}"
                self.log(error_message)
                messagebox.showerror("Beklenmeyen Hata", error_message)

        self.log("İşlem tamamlandı.")
        messagebox.showinfo("Tamamlandı", "Ses dosyaları başarıyla oluşturuldu ve 'sesler' klasörüne kaydedildi.")

if __name__ == "__main__":
    root = tk.Tk()
    app = TTSApp(root)
    root.mainloop()

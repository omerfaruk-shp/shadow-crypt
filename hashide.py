import customtkinter as ctk
import threading
import hashlib
import itertools
import string
import time
import sys
import os
import datetime
from collections import deque

# Gemini Kontrolü
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# --- ARAYÜZ AYARLARI ---
ctk.set_appearance_mode("Dark")  # Karanlık Mod
ctk.set_default_color_theme("dark-blue")  # Tema Rengi

class ShadowCryptApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Pencere Ayarları
        self.title("ShadowCrypt v1.0 | Advanced Hash Cracker")
        self.geometry("900x700")
        self.resizable(False, False)

        # Değişkenler
        self.stop_flag = False
        self.is_running = False
        
        # --- ANA DÜZEN (GRID) ---
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=0) # Header
        self.grid_rowconfigure(1, weight=1) # Content

        # 1. HEADER (SOL TARAFTA LOGO, SAĞDA DURUM)
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar.grid_rowconfigure(4, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar, text="Shadow\nCrypt", font=ctk.CTkFont(size=30, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        self.lbl_status = ctk.CTkLabel(self.sidebar, text="DURUM: HAZIR", text_color="green", font=("Consolas", 12, "bold"))
        self.lbl_status.grid(row=1, column=0, padx=20, pady=10)

        # --- ORTA ALAN: AYARLAR ---
        self.main_frame = ctk.CTkFrame(self, corner_radius=10)
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")

        # Hash Girişi
        self.lbl_hash = ctk.CTkLabel(self.main_frame, text="Hedef Hash:", font=("Arial", 14, "bold"))
        self.lbl_hash.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.entry_hash = ctk.CTkEntry(self.main_frame, width=400, placeholder_text="Hash buraya...")
        self.entry_hash.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        
        # Algoritma Seçimi
        self.algo_var = ctk.StringVar(value="MD5")
        self.combo_algo = ctk.CTkComboBox(self.main_frame, values=["MD5", "SHA1", "SHA256"], variable=self.algo_var)
        self.combo_algo.grid(row=0, column=2, padx=10, pady=10)

        # Salt Ayarları
        self.lbl_salt = ctk.CTkLabel(self.main_frame, text="Salt (Tuz):", font=("Arial", 12))
        self.lbl_salt.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.entry_salt = ctk.CTkEntry(self.main_frame, width=200, placeholder_text="Opsiyonel")
        self.entry_salt.grid(row=1, column=1, padx=10, pady=5, sticky="w")
        
        self.salt_pos_var = ctk.StringVar(value="Suffix (Son)")
        self.switch_salt = ctk.CTkSwitch(self.main_frame, text="Salt Sonda", variable=self.salt_pos_var, onvalue="Suffix", offvalue="Prefix")
        self.switch_salt.grid(row=1, column=2, padx=10, pady=5)

        # --- SEKMELER (SALDIRI MODLARI) ---
        self.tabview = ctk.CTkTabview(self, width=650)
        self.tabview.grid(row=1, column=1, padx=20, pady=10, sticky="nsew")
        
        self.tab_dict = self.tabview.add("📚 Dictionary")
        self.tab_brute = self.tabview.add("🔨 Brute Force")
        self.tab_ai = self.tabview.add("🧠 Gemini AI")

        # TAB 1: DICTIONARY
        self.lbl_wordlist = ctk.CTkLabel(self.tab_dict, text="Wordlist Dosyası (Boş = Otomatik Oluştur):")
        self.lbl_wordlist.pack(pady=5)
        self.entry_wordlist = ctk.CTkEntry(self.tab_dict, width=400, placeholder_text="wordlist.txt")
        self.entry_wordlist.pack(pady=5)
        self.lbl_info1 = ctk.CTkLabel(self.tab_dict, text="* Kelimenin büyük/küçük harf halleri otomatik denenir.", text_color="gray")
        self.lbl_info1.pack()

        # TAB 2: BRUTE FORCE
        self.lbl_charset = ctk.CTkLabel(self.tab_brute, text="Karakter Seti:")
        self.lbl_charset.pack(pady=5)
        self.charset_var = ctk.StringVar(value="lower")
        self.radio_num = ctk.CTkRadioButton(self.tab_brute, text="Sadece Rakam", variable=self.charset_var, value="digits")
        self.radio_num.pack(pady=2)
        self.radio_lower = ctk.CTkRadioButton(self.tab_brute, text="Küçük Harf (a-z)", variable=self.charset_var, value="lower")
        self.radio_lower.pack(pady=2)
        self.radio_mix = ctk.CTkRadioButton(self.tab_brute, text="Harf + Rakam", variable=self.charset_var, value="mix")
        self.radio_mix.pack(pady=2)
        
        self.frame_len = ctk.CTkFrame(self.tab_brute, fg_color="transparent")
        self.frame_len.pack(pady=10)
        ctk.CTkLabel(self.frame_len, text="Min:").pack(side="left", padx=5)
        self.entry_min = ctk.CTkEntry(self.frame_len, width=50)
        self.entry_min.insert(0, "4")
        self.entry_min.pack(side="left")
        ctk.CTkLabel(self.frame_len, text="Max:").pack(side="left", padx=5)
        self.entry_max = ctk.CTkEntry(self.frame_len, width=50)
        self.entry_max.insert(0, "6")
        self.entry_max.pack(side="left")

        # TAB 3: GEMINI AI
        self.lbl_api = ctk.CTkLabel(self.tab_ai, text="Gemini API Key:")
        self.lbl_api.pack(pady=5)
        self.entry_api = ctk.CTkEntry(self.tab_ai, width=400, show="*")
        self.entry_api.pack(pady=5)
        
        self.lbl_hint = ctk.CTkLabel(self.tab_ai, text="İpucu / Bağlam (Örn: İsim, Takım):")
        self.lbl_hint.pack(pady=5)
        self.entry_hint = ctk.CTkEntry(self.tab_ai, width=400)
        self.entry_hint.pack(pady=5)

        # --- ALT KISIM: KONSOL VE BUTON ---
        self.btn_start = ctk.CTkButton(self.sidebar, text="BAŞLAT", fg_color="green", hover_color="darkgreen", font=("Arial", 16, "bold"), command=self.start_attack_thread)
        self.btn_start.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        
        self.btn_stop = ctk.CTkButton(self.sidebar, text="DURDUR", fg_color="red", hover_color="darkred", command=self.stop_attack, state="disabled")
        self.btn_stop.grid(row=3, column=0, padx=20, pady=10, sticky="ew")

        # Konsol Çıktısı
        self.console = ctk.CTkTextbox(self, height=200, font=("Consolas", 12))
        self.console.grid(row=2, column=1, padx=20, pady=(0, 20), sticky="nsew")
        self.log("ShadowCrypt v1.0 Sistem Hazır...")
        self.log("Lütfen bir hedef hash girin ve modu seçin.")

    def log(self, message, color="white"):
        self.console.insert("end", f">> {message}\n")
        self.console.see("end")

    def stop_attack(self):
        self.stop_flag = True
        self.is_running = False
        self.btn_start.configure(state="normal")
        self.btn_stop.configure(state="disabled")
        self.lbl_status.configure(text="DURDURULDU", text_color="red")
        self.log("İşlem kullanıcı tarafından durduruldu.")

    def start_attack_thread(self):
        if self.is_running: return
        
        target = self.entry_hash.get().strip()
        if not target:
            self.log("HATA: Hash girmediniz!")
            return

        self.stop_flag = False
        self.is_running = True
        self.btn_start.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        self.lbl_status.configure(text="ÇALIŞIYOR...", text_color="orange")
        self.console.delete("1.0", "end")
        
        # İşlemi ayrı thread'de başlat ki arayüz donmasın
        threading.Thread(target=self.run_attack, args=(target,), daemon=True).start()

    def run_attack(self, target):
        algo = self.algo_var.get().lower()
        salt = self.entry_salt.get().strip()
        salt_pos = self.salt_pos_var.get()
        
        mode = self.tabview.get() # Hangi sekme açık?
        
        self.log(f"Hedef: {target}")
        self.log(f"Algoritma: {algo.upper()}")
        if salt: self.log(f"Salt: {salt} ({salt_pos})")

        found_pass = None
        start_time = time.time()

        # --- MOD SEÇİMİ VE MANTIK ---
        
        # 1. DICTIONARY MODE
        if mode == "📚 Dictionary":
            path = self.entry_wordlist.get().strip()
            if not path:
                path = "wordlist_temp.txt"
                if not os.path.exists(path):
                    with open(path, "w") as f:
                        defaults = ["admin", "password", "123456", "faruk", "siber"]
                        for d in defaults: f.write(d+"\n")
                    self.log("Otomatik wordlist oluşturuldu.")
            
            self.log(f"Dosya taranıyor: {path}")
            found_pass = self.logic_dictionary(target, algo, salt, salt_pos, path)

        # 2. BRUTE FORCE MODE
        elif mode == "🔨 Brute Force":
            charset_key = self.charset_var.get()
            if charset_key == "digits": charset = string.digits
            elif charset_key == "lower": charset = string.ascii_lowercase
            else: charset = string.ascii_lowercase + string.digits
            
            try:
                min_l = int(self.entry_min.get())
                max_l = int(self.entry_max.get())
            except:
                self.log("HATA: Min/Max sayı olmalı.")
                self.stop_attack()
                return

            self.log(f"Karakter seti: {charset}")
            found_pass = self.logic_brute(target, algo, salt, salt_pos, min_l, max_l, charset)

        # 3. GEMINI AI MODE
        elif mode == "🧠 Gemini AI":
            api_key = self.entry_api.get().strip()
            hint = self.entry_hint.get().strip()
            
            if not GEMINI_AVAILABLE:
                self.log("HATA: Google Generative AI kütüphanesi yüklü değil!")
            elif not api_key:
                self.log("HATA: API Key girilmedi!")
            else:
                found_pass = self.logic_gemini(target, algo, salt, salt_pos, api_key, hint)

        # --- SONUÇ ---
        duration = round(time.time() - start_time, 2)
        if found_pass:
            self.log("-" * 30)
            self.log(f"BAŞARILI! ŞİFRE: {found_pass}")
            self.log(f"Süre: {duration} saniye")
            self.lbl_status.configure(text="ŞİFRE KIRILDI", text_color="#00FF00")
        else:
            if not self.stop_flag:
                self.log("Başarısız. Şifre bulunamadı.")
                self.lbl_status.configure(text="BAŞARISIZ", text_color="red")

        self.is_running = False
        self.btn_start.configure(state="normal")
        self.btn_stop.configure(state="disabled")

    # --- MANTIK FONKSİYONLARI ---
    
    def check_hash(self, text, target, algo, salt, salt_pos):
        # Salt
        attempt = text
        if salt:
            attempt = (text + salt) if salt_pos == "Suffix" else (salt + text)
        
        try:
            encoded = attempt.encode("utf-8")
            if algo == "md5": h = hashlib.md5(encoded).hexdigest()
            elif algo == "sha1": h = hashlib.sha1(encoded).hexdigest()
            elif algo == "sha256": h = hashlib.sha256(encoded).hexdigest()
            else: return False
            
            return h == target
        except: return False

    def logic_dictionary(self, target, algo, salt, salt_pos, path):
        suffixes = ["", "123", "1", "!", "2024", "2025", "1905", "1907", "1903"]
        try:
            with open(path, "r", encoding="latin-1") as f:
                lines = f.readlines()
            
            total = len(lines)
            self.log(f"{total} kelime yüklendi. Varyasyonlar deneniyor...")
            
            for i, line in enumerate(lines):
                if self.stop_flag: return None
                word = line.strip()
                if not word: continue
                
                # Varyasyonlar
                variations = {word, word.lower(), word.upper(), word.capitalize()}
                
                for base in variations:
                    for suff in suffixes:
                        attempt = base + suff
                        if self.check_hash(attempt, target, algo, salt, salt_pos):
                            return attempt
                
                if i % 500 == 0: # Arayüz donmasın diye ara ver
                    self.update_idletasks()
            return None
        except Exception as e:
            self.log(f"Dosya Hatası: {e}")
            return None

    def logic_brute(self, target, algo, salt, salt_pos, min_l, max_l, charset):
        count = 0
        for length in range(min_l, max_l + 1):
            self.log(f"{length} haneli kombinasyonlar deneniyor...")
            for guess in itertools.product(charset, repeat=length):
                if self.stop_flag: return None
                
                word = "".join(guess)
                count += 1
                
                if self.check_hash(word, target, algo, salt, salt_pos):
                    return word
                
                if count % 5000 == 0:
                    self.log(f"Deneniyor: {word}")
                    # Eski logları temizle ki bellek şişmesin
                    # self.console.delete("1.0", "end-50l") 
        return None

    def logic_gemini(self, target, algo, salt, salt_pos, api_key, hint):
        self.log("Gemini 2.5 Pro'ya bağlanılıyor...")
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.5-pro')
            
            prompt = f"Sen bir siber güvenlik uzmanısın. Bağlam: '{hint}'. Olası 150 şifreyi listele. Sadece şifreleri yaz."
            
            response = model.generate_content(prompt)
            candidates = [c.strip().replace('*', '').split(' ')[-1] for c in response.text.split('\n') if c.strip()]
            
            self.log(f"{len(candidates)} adet AI tahmini alındı.")
            
            for word in candidates:
                if self.stop_flag: return None
                self.log(f"AI Deniyor: {word}")
                
                # Varyasyonlu deneme
                variations = {word, word.lower(), word.upper(), word.capitalize()}
                for base in variations:
                    if self.check_hash(base, target, algo, salt, salt_pos):
                        return base
                time.sleep(0.02)
            
            return None
        except Exception as e:
            self.log(f"AI Hatası: {e}")
            return None

if __name__ == "__main__":
    app = ShadowCryptApp()
    app.mainloop()

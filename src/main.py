import pygame
import threading
import time
import collections
import os
import glob

# --- MAPREDUCE MOTORU VE ARKA PLAN İŞLEYİCİSİ ---
shuffle_lock = threading.Lock()

class MapReduceEngine:
    def __init__(self, num_threads=4):
        self.num_threads = num_threads
        self.words = []            
        self.chunks = [[] for _ in range(num_threads)] 
        
        self.map_results = []      
        self.shuffled_dict = collections.defaultdict(list) 
        self.final_counts = {}     
        
        self.thread_progress = [0.0] * num_threads
        self.thread_states = ["IDLE"] * num_threads
        self.current_stage = "MAPPING"
        
        self.map_index = 0
        self.shuffle_index = 0
        self.reduce_index = 0
        self.reduce_keys = []

    def reset_and_start(self):
        """Yeni dosya seçildiğinde motoru sıfırlar"""
        self.words = []
        self.chunks = [[] for _ in range(self.num_threads)]
        self.map_results = []
        self.shuffled_dict.clear()
        self.final_counts.clear()
        self.thread_progress = [0.0] * self.num_threads
        self.thread_states = ["IDLE"] * self.num_threads
        self.current_stage = "MAPPING"
        self.map_index = 0
        self.shuffle_index = 0
        self.reduce_index = 0
        self.reduce_keys = []

    def step_map(self):
        all_finished = True
        for i in range(self.num_threads):
            if self.map_index < len(self.chunks[i]):
                self.thread_states[i] = "RUNNING"
                word = self.chunks[i][self.map_index]
                with shuffle_lock:
                    self.map_results.append((word, 1))
                self.thread_progress[i] = (self.map_index + 1) / len(self.chunks[i])
                all_finished = False
            else:
                self.thread_states[i] = "FINISHED"
                self.thread_progress[i] = 1.0
                
        if not all_finished:
            self.map_index += 1
        else:
            if len(self.map_results) > 0:
                self.current_stage = "SHUFFLING"

    def step_shuffle(self):
        if self.shuffle_index < len(self.map_results):
            word, count = self.map_results[self.shuffle_index]
            self.shuffled_dict[word].append(count)
            self.shuffle_index += 1
        else:
            self.current_stage = "REDUCING"
            self.reduce_keys = list(self.shuffled_dict.keys())

    def step_reduce(self):
        if self.reduce_index < len(self.reduce_keys):
            word = self.reduce_keys[self.reduce_index]
            self.final_counts[word] = sum(self.shuffled_dict[word])
            self.reduce_index += 1
        else:
            self.current_stage = "FINISHED"


def arka_plan_dosya_okuyucu(engine, dosya_yolu):
    if not os.path.exists(dosya_yolu):
        return

    blok_boyutu = 1024 * 512  
    with open(dosya_yolu, "r", encoding="utf-8") as f:
        while True:
            kısım = f.read(blok_boyutu)
            if not kısım:
                break
            
            yeni_kelimeler = [w.lower().strip(".,!?\"'()[]") for w in kısım.split() if w]
            
            if yeni_kelimeler:
                with shuffle_lock:
                    engine.words.extend(yeni_kelimeler)
                    c_size = max(1, len(engine.words) // engine.num_threads)
                    
                    temp_chunks = [engine.words[i:i + c_size] for i in range(0, len(engine.words), c_size)]
                    engine.chunks = [[] for _ in range(engine.num_threads)]
                    for idx, chunk in enumerate(temp_chunks):
                        if idx < engine.num_threads:
                            engine.chunks[idx] = chunk
            
            time.sleep(0.01)


# --- PYGAME GÖRSEL ARAYÜZÜ ---
class MapReduceVisualizer:
    def __init__(self, engine):
        pygame.init()
        self.engine = engine
        self.width, self.height = 1200, 750
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("PROJE 25: Devasa Veriler İçin Paralel MapReduce Framework Simülasyonu")
        
        self.clock = pygame.time.Clock()
        self.is_paused = False
        
        # MENÜ DURUMLARI: 'FILE_SELECT' -> 'SPEED_SELECT' -> 'SIMULATION'
        self.menu_stage = 'FILE_SELECT'
        self.secilen_dosya = None
        
        # DİNAMİK DOSYA ALGILAMA
        self.txt_dosyalari = glob.glob("*.txt")
        # Eğer hiç .txt yoksa test amaçlı bir tane oluştur
        if not self.txt_dosyalari:
            with open("buyuk_veri.txt", "w", encoding="utf-8") as f:
                f.write("baba dert dunya yalan dert keder dunya müslüm yalnız garip ömür kul kader hasret " * 6000)
            self.txt_dosyalari = glob.glob("*.txt")

        self.vitesler = [1, 5, 25, 100, 500, 2500, 10000]
        self.vites_labels = ["1 (Karınca Hızı)", "5 (Çok Yavaş)", "25 (Yavaş)", "100 (Normal Hız)", "500 (Hızlı)", "2500 (Turbo)", "10000 (Işık Hızı)"]
        self.vites_index = 3 
        
        self.shuffle_scroll = 0
        self.reduce_scroll = 0
        self.filter_mode = "ALL" 
        
        self.font = pygame.font.SysFont("Segoe UI", 16)
        self.bold_font = pygame.font.SysFont("Segoe UI", 18, bold=True)
        self.title_font = pygame.font.SysFont("Segoe UI", 24, bold=True)
        
        self.BG_COLOR = (18, 22, 28)
        self.PANEL_COLOR = (28, 35, 46)
        self.TEXT_COLOR = (220, 225, 235)
        self.GREEN = (39, 174, 96)
        self.BLUE = (41, 128, 185)
        self.ORANGE = (211, 84, 0)
        self.RED = (192, 41, 43)

    def draw_text(self, text, font, color, x, y):
        surface = font.render(text, True, color)
        self.screen.blit(surface, (x, y))

    def run(self):
        running = True
        while running:
            self.screen.fill(self.BG_COLOR)
            mouse_pos = pygame.mouse.get_pos()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                # --- MENÜ ETKİLEŞİMLERİ ---
                if self.menu_stage == 'FILE_SELECT':
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        for i, dosya in enumerate(self.txt_dosyalari[:8]): # Ekrana maksimum 8 dosya sığdır
                            rect = pygame.Rect(400, 200 + (i * 55), 400, 45)
                            if rect.collidepoint(mouse_pos):
                                self.secilen_dosya = dosya
                                self.menu_stage = 'SPEED_SELECT'
                                
                elif self.menu_stage == 'SPEED_SELECT':
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        for i in range(len(self.vitesler)):
                            rect = pygame.Rect(450, 200 + (i * 50), 300, 40)
                            if rect.collidepoint(mouse_pos):
                                self.vites_index = i
                                self.menu_stage = 'SIMULATION'
                                # Hız ve dosya seçildi arka plan işleyicisini başlat
                                self.engine.reset_and_start()
                                okuyucu_thread = threading.Thread(target=arka_plan_dosya_okuyucu, args=(self.engine, self.secilen_dosya), daemon=True)
                                okuyucu_thread.start()
                                
                # --- SİMÜLASYON ETKİLEŞİMLERİ ---
                elif self.menu_stage == 'SIMULATION':
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_SPACE:
                            self.is_paused = not self.is_paused
                        elif event.key == pygame.K_UP:
                            if self.vites_index < len(self.vitesler) - 1:
                                self.vites_index += 1
                        elif event.key == pygame.K_DOWN:
                            if self.vites_index > 0:
                                self.vites_index -= 1
                        elif event.key == pygame.K_1:
                            self.filter_mode = "REPEATED"
                        elif event.key == pygame.K_2:
                            self.filter_mode = "UNIQUE"
                        elif event.key == pygame.K_3:
                            self.filter_mode = "ALL"
                        elif event.key == pygame.K_RIGHT and self.is_paused:
                            self._update_logic(forced=True)
                    
                    elif event.type == pygame.MOUSEBUTTONDOWN:
                        if event.button == 4: 
                            if 600 <= mouse_pos[0] <= 860:
                                self.shuffle_scroll = max(0, self.shuffle_scroll - 1)
                            elif 880 <= mouse_pos[0] <= 1170:
                                self.reduce_scroll = max(0, self.reduce_scroll - 1)
                        elif event.button == 5: 
                            if 600 <= mouse_pos[0] <= 860:
                                self.shuffle_scroll += 1
                            elif 880 <= mouse_pos[0] <= 1170:
                                self.reduce_scroll += 1

            # Çizim Mantığı
            if self.menu_stage == 'FILE_SELECT':
                self._draw_file_menu(mouse_pos)
            elif self.menu_stage == 'SPEED_SELECT':
                self._draw_speed_menu(mouse_pos)
            elif self.menu_stage == 'SIMULATION':
                if not self.is_paused:
                    self._update_logic()
                self._draw_layout()
                if self.engine.current_stage == "FINISHED":
                    self._draw_amdahl_graph()

            pygame.display.flip()
            self.clock.tick(60) 

        pygame.quit()

    def _draw_file_menu(self, mouse_pos):
        """Otomatik algılanan dosyaların listelendiği ekran"""
        self.draw_text("MAPREDUCE METİN DOSYASI SEÇİMİ", self.title_font, self.ORANGE, 410, 80)
        self.draw_text("Sistem klasördeki tüm (.txt) uzantılı dosyaları otomatik olarak algıladı:", self.font, self.TEXT_COLOR, 370, 130)
        self.draw_text("Analiz etmek istediğiniz veri kümesini seçin.", self.font, (150, 160, 180), 460, 155)
        
        for i, dosya in enumerate(self.txt_dosyalari[:8]):
            buton_y = 200 + (i * 55)
            rect = pygame.Rect(400, buton_y, 400, 45)
            renk = self.BLUE if rect.collidepoint(mouse_pos) else self.PANEL_COLOR
            
            pygame.draw.rect(self.screen, renk, rect)
            pygame.draw.rect(self.screen, self.BLUE, rect, 1)
            
            # Dosya simgesi niyetine minik bir ok işareti koyalım
            self.draw_text(f"📄  {dosya}", self.bold_font, self.TEXT_COLOR, 420, buton_y + 11)

    def _draw_speed_menu(self, mouse_pos):
        self.draw_text("MAPREDUCE BAŞLANGIÇ HIZ SEÇİMİ", self.title_font, self.ORANGE, 420, 80)
        self.draw_text(f"Seçilen Dosya: {self.secilen_dosya}", self.bold_font, self.GREEN, 500, 130)
        self.draw_text("Simülasyonun hangi hızda başlamasını istiyorsunuz?", self.font, self.TEXT_COLOR, 430, 160)
        
        for i, label in enumerate(self.vites_labels):
            buton_y = 210 + (i * 50)
            rect = pygame.Rect(450, buton_y, 300, 40)
            renk = self.GREEN if rect.collidepoint(mouse_pos) else self.PANEL_COLOR
            
            pygame.draw.rect(self.screen, renk, rect)
            pygame.draw.rect(self.screen, self.ORANGE, rect, 1)
            self.draw_text(label, self.bold_font, self.TEXT_COLOR, 470, buton_y + 8)

    def _update_logic(self, forced=False):
        BATCH_SIZE = self.vitesler[self.vites_index] if not forced else 1 

        if self.engine.current_stage == "MAPPING":
            for _ in range(BATCH_SIZE):
                if self.engine.current_stage == "MAPPING":
                    self.engine.step_map()
                else:
                    break
        elif self.engine.current_stage == "SHUFFLING":
            for _ in range(BATCH_SIZE):
                if self.engine.current_stage == "SHUFFLING":
                    self.engine.step_shuffle()
                else:
                    break
        elif self.engine.current_stage == "REDUCING":
            for _ in range(BATCH_SIZE):
                if self.engine.current_stage == "REDUCING":
                    self.engine.step_reduce()
                else:
                    break

    def _draw_layout(self):
        durum = "DURDURULDU (Adım adım gitmek için: SAĞ OK)" if self.is_paused else f"ÇALIŞIYOR (Vites: {self.vitesler[self.vites_index]} kelime/kare)"
        status_text = f"Aşama: {self.engine.current_stage} | {durum}"
        self.draw_text(status_text, self.title_font, self.ORANGE, 30, 15)
        
        filtre_durum = f"Aktif Filtre: {self.filter_mode} (Değiştirmek için -> 1: Tekrar Edenler | 2: Tekrar Etmeyenler | 3: Hepsi)"
        self.draw_text(filtre_durum, self.font, self.GREEN, 30, 48)
        self.draw_text(f"Dosya: {self.secilen_dosya} | Hız Değişimi: KLAVYE YUKARI / AŞAĞI | Kaydırma: MOUSE TEKERLEĞİ", self.font, self.TEXT_COLOR, 30, 72)
        
        PANEL_Y = 110
        PANEL_H = 420

        # 1. PANEL: DISKTEN AKAN GİRİŞ VERİSİ
        pygame.draw.rect(self.screen, self.PANEL_COLOR, (30, PANEL_Y, 250, PANEL_H))
        pygame.draw.rect(self.screen, self.ORANGE, (30, PANEL_Y, 250, PANEL_H), 1)
        self.draw_text("1. Disk Veri Akışı (Stream)", self.bold_font, self.TEXT_COLOR, 40, PANEL_Y + 10)
        self.draw_text(f"Toplam Okunan: {len(self.engine.words)} kelime", self.font, self.BLUE, 40, PANEL_Y + 35)
        
        y_offset = PANEL_Y + 70
        with shuffle_lock:
            for word in self.engine.words[-14:]: 
                self.draw_text(f"» {word}", self.font, self.TEXT_COLOR, 45, y_offset)
                y_offset += 22

        # 2. PANEL: PARALEL MAP THREADS
        pygame.draw.rect(self.screen, self.PANEL_COLOR, (300, PANEL_Y, 280, PANEL_H))
        pygame.draw.rect(self.screen, self.GREEN, (300, PANEL_Y, 280, PANEL_H), 1)
        self.draw_text("2. Map Aşaması (Paralel)", self.bold_font, self.TEXT_COLOR, 310, PANEL_Y + 10)
        
        for i in range(self.engine.num_threads):
            y = PANEL_Y + 60 + (i * 85)
            durum_rengi = self.GREEN if self.engine.thread_states[i] == "RUNNING" else self.TEXT_COLOR
            self.draw_text(f"Thread-{i+1} [{self.engine.thread_states[i]}]", self.font, durum_rengi, 310, y)
            self.draw_text(f"Yük: {len(self.engine.chunks[i])}", self.font, self.TEXT_COLOR, 470, y)
            
            pygame.draw.rect(self.screen, (40, 45, 55), (310, y + 25, 260, 15))
            if len(self.engine.chunks[i]) > 0:
                bar_width = int(260 * self.engine.thread_progress[i])
                pygame.draw.rect(self.screen, self.GREEN, (310, y + 25, bar_width, 15))

        # 3. PANEL: SHUFFLE & SORT
        pygame.draw.rect(self.screen, self.PANEL_COLOR, (600, PANEL_Y, 260, PANEL_H))
        pygame.draw.rect(self.screen, self.BLUE, (600, PANEL_Y, 260, PANEL_H), 1)
        self.draw_text("3. Shuffle & Sort (Gruplama)", self.bold_font, self.TEXT_COLOR, 610, PANEL_Y + 10)
        
        all_shuffle_items = list(self.engine.shuffled_dict.items())
        filtered_shuffle = []
        for word, counts in all_shuffle_items:
            if self.filter_mode == "REPEATED" and len(counts) <= 1: continue
            if self.filter_mode == "UNIQUE" and len(counts) > 1: continue
            filtered_shuffle.append((word, counts))
            
        self.draw_text(f"Grup: {len(filtered_shuffle)} | Satır: {self.shuffle_scroll}", self.font, self.TEXT_COLOR, 610, PANEL_Y + 35)
        
        if self.shuffle_scroll > max(0, len(filtered_shuffle) - 13):
            self.shuffle_scroll = max(0, len(filtered_shuffle) - 13)
            
        visible_shuffle = filtered_shuffle[self.shuffle_scroll : self.shuffle_scroll + 13]
        y_offset = PANEL_Y + 70
        for word, counts in visible_shuffle:
            self.draw_text(f"'{word}' -> {counts[:3]}...", self.font, self.BLUE, 610, y_offset)
            y_offset += 25

        # 4. PANEL: REDUCE SONUÇLARI
        pygame.draw.rect(self.screen, self.PANEL_COLOR, (880, PANEL_Y, 290, PANEL_H))
        pygame.draw.rect(self.screen, self.TEXT_COLOR, (880, PANEL_Y, 290, PANEL_H), 1)
        self.draw_text("4. Reduce Aşaması (Sonuçlar)", self.bold_font, self.TEXT_COLOR, 890, PANEL_Y + 10)
        
        all_reduce_items = list(self.engine.final_counts.items())
        filtered_reduce = []
        for word, count in all_reduce_items:
            if self.filter_mode == "REPEATED" and count <= 1: continue
            if self.filter_mode == "UNIQUE" and count > 1: continue
            filtered_reduce.append((word, count))
            
        self.draw_text(f"Öge: {len(filtered_reduce)} | Satır: {self.reduce_scroll}", self.font, self.TEXT_COLOR, 890, PANEL_Y + 35)
        
        if self.reduce_scroll > max(0, len(filtered_reduce) - 13):
            self.reduce_scroll = max(0, len(filtered_reduce) - 13)
            
        visible_reduce = filtered_reduce[self.reduce_scroll : self.reduce_scroll + 13]
        y_offset = PANEL_Y + 70
        for word, count in visible_reduce:
            self.draw_text(f"Grup Toplamı ['{word}']: {count}", self.font, self.GREEN, 890, y_offset)
            y_offset += 25

    def _draw_amdahl_graph(self):
        start_x, start_y = 420, 715
        pygame.draw.rect(self.screen, (24, 30, 40), (350, 555, 500, 180))
        pygame.draw.rect(self.screen, self.ORANGE, (350, 555, 500, 180), 2)
        
        self.draw_text("Mühendislik Çıktısı: Amdahl Kanunu Performans Analizi", self.bold_font, self.ORANGE, 370, 565)
        
        pygame.draw.line(self.screen, self.TEXT_COLOR, (start_x, start_y), (start_x + 400, start_y), 2) 
        pygame.draw.line(self.screen, self.TEXT_COLOR, (start_x, start_y), (start_x, start_y - 100), 2) 
        
        points = [(1, 10), (2, 40), (4, 70), (8, 92)] 
        prev_pos = None
        
        for i, (threads, speedup) in enumerate(points):
            x = start_x + (i * 100) + 40
            y = start_y - speedup
            
            pygame.draw.circle(self.screen, self.RED, (x, y), 6)
            self.draw_text(f"{threads} Core", self.font, self.TEXT_COLOR, x - 20, start_y + 8)
            self.draw_text(f"{speedup/10:.1f}x", self.font, self.GREEN, x - 10, y - 22)
            
            if prev_pos:
                pygame.draw.line(self.screen, self.GREEN, prev_pos, (x, y), 3)
            prev_pos = (x, y)
            
        self.draw_text("Hızlanma (Speedup)", self.font, self.TEXT_COLOR, 250, 605)


if __name__ == "__main__":
    mapreduce_motoru = MapReduceEngine(num_threads=4)
    arayuz = MapReduceVisualizer(mapreduce_motoru)
    arayuz.run()

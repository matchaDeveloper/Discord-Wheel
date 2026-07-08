import tkinter as tk
from tkinter import messagebox
import json
import os
import math
import random
import colorsys

DATA_FILE = os.path.join("data", "teilnehmer.json")


class WheelLogic:
    def __init__(self, data_file):
        self.data_file = data_file
        self.names = []
        self.probabilities = []
        self.load_data()


    def load_data(self):
        if not os.path.exists(self.data_file):
            return
        try:
            with open(self.data_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.names = data.get("names", [])
                self.probabilities = data.get("probability_of_name", [])

                if not self.probabilities or len(self.probabilities) != len(self.names):
                    self.reset_probabilities()
        except (json.JSONDecodeError, FileNotFoundError):
            pass


    def reset_probabilities(self):
        n = len(self.names)
        self.probabilities = [100.0 / n if n > 0 else 0.0] * n
        self.save_data()


    def save_data(self):
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        data = {
            "names": self.names,
            "probability_of_name": [round(p, 2) for p in self.probabilities]
        }
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


    def get_active_participants(self):
        active = []
        for i, (name, prob) in enumerate(zip(self.names, self.probabilities)):
            if prob > 0.0:
                active.append({"original_index": i, "name": name})
        return active


    def update_probabilities_after_win(self, winner_index):
        n = len(self.names)
        if n <= 1:
            return

        fair_max_share = 100.0 / (n - 1)

        new_probs = []
        for i, current_p in enumerate(self.probabilities):
            if i == winner_index:
                new_probs.append(0.0)
            else:
                recovered_p = current_p + (fair_max_share - current_p) * 0.5
                new_probs.append(recovered_p)

        total_sum = sum(new_probs)
        if total_sum > 0:
            self.probabilities = [(p / total_sum) * 100.0 for p in new_probs]
        else:
            self.reset_probabilities()

        self.save_data()


# =====================================================================
# GUI APPLICATION
# =====================================================================
class WheelOfNamesApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Wheel of Names")
        self.root.geometry("520x720")
        self.root.configure(bg="#f5f7fa")

        self.logic = WheelLogic(DATA_FILE)

        self.is_spinning = False
        self.current_angle = 0

        self.create_widgets()

        if not self.logic.names:
            messagebox.showwarning("Keine Daten", "JSON-Datei leer oder nicht gefunden! Es werden Testdaten erstellt.")
            self.logic.names = []
            self.logic.probabilities = []
            self.logic.save_data()

        self.draw_wheel()


    def generate_colors(self, n):
        colors = []
        for i in range(n):
            hue = i / n
            rgb = colorsys.hsv_to_rgb(hue, 0.75, 0.9)
            hex_color = f'#{int(rgb[0] * 255):02x}{int(rgb[1] * 255):02x}{int(rgb[2] * 255):02x}'
            colors.append(hex_color)
        return colors


    def create_widgets(self):
        title_label = tk.Label(self.root, text="Gamba, gamba, gamba!!", font=("Arial", 20, "bold"), bg="#f5f7fa",
                               fg="#333")
        title_label.pack(pady=10)

        self.canvas_size = 380
        self.canvas = tk.Canvas(self.root, width=self.canvas_size, height=self.canvas_size, bg="#f5f7fa",
                                highlightthickness=0)
        self.canvas.pack(pady=5)

        self.result_label = tk.Label(self.root, text="", font=("Arial", 18, "bold"), bg="#f5f7fa", fg="#2e7d32")
        self.result_label.pack(pady=5, fill=tk.X)

        self.prob_label = tk.Label(self.root, text="", font=("Courier", 9), bg="#f5f7fa", fg="#555", justify=tk.LEFT)
        self.prob_label.pack(pady=5)
        self.update_prob_display()

        btn_frame = tk.Frame(self.root, bg="#f5f7fa")
        btn_frame.pack(pady=5)

        self.spin_button = tk.Button(btn_frame, text="Drehen!", font=("Arial", 14, "bold"), bg="#6e8efb", fg="white",
                                     padx=20, pady=8, command=self.start_spin, relief=tk.FLAT)
        self.spin_button.pack(side=tk.LEFT, padx=10)

        refresh_button = tk.Button(btn_frame, text="Aktualisieren", font=("Arial", 12), bg="#a777e3", fg="white",
                                   padx=15, pady=8, command=self.refresh_data, relief=tk.FLAT)
        refresh_button.pack(side=tk.LEFT, padx=10)


    def update_prob_display(self):
        text_lines = []
        for name, prob in zip(self.logic.names, self.logic.probabilities):
            text_lines.append(f"{name:<20}: {prob:>5.1f}%")
        self.prob_label.config(text="\n".join(text_lines))


    def draw_wheel(self):
        self.canvas.delete("all")
        active_participants = self.logic.get_active_participants()
        num_segments = len(active_participants)
        if num_segments == 0: return
        extent = 360 / num_segments
        colors = self.generate_colors(num_segments)
        cx, cy = self.canvas_size / 2, self.canvas_size / 2
        r = self.canvas_size / 2 - 25
        for i, participant in enumerate(active_participants):
            start_angle = (-self.current_angle + (i * extent)) % 360

            self.canvas.create_arc(cx - r, cy - r, cx + r, cy + r,
                                   start=start_angle, extent=extent,
                                   fill=colors[i], outline="white", width=1)

            text_angle_rad = math.radians(start_angle + extent / 2)
            tx = cx + (r * 0.65) * math.cos(text_angle_rad)
            ty = cy - (r * 0.65) * math.sin(text_angle_rad)

            self.canvas.create_text(tx, ty, text=participant["name"], fill="white", font=("Arial", 10, "bold"),
                                    justify=tk.CENTER)

        px = cx
        py = cy - r - 20
        self.canvas.create_polygon(px, py + 18, px - 10, py, px + 10, py, fill="#ff4444", outline="white")


    def start_spin(self):
        if self.is_spinning or not self.logic.get_active_participants():
            return

        self.is_spinning = True
        self.spin_button.config(state=tk.DISABLED)
        self.result_label.config(text="")

        total_spin = (360 * random.randint(4, 6)) + random.uniform(0, 360)
        self.animate_spin(total_spin, initial_speed=25)


    def animate_spin(self, remaining_distance, initial_speed):
        speed = (remaining_distance / 20) + 0.1
        if speed > initial_speed:
            speed = initial_speed

        if remaining_distance > 0.2:
            self.current_angle = (self.current_angle + speed) % 360
            self.draw_wheel()
            self.root.after(12, self.animate_spin, remaining_distance - speed, initial_speed)
        else:
            self.is_spinning = False
            self.spin_button.config(state=tk.NORMAL)
            self.determine_winner()


    def determine_winner(self):
        active_participants = self.logic.get_active_participants()
        num_segments = len(active_participants)
        if num_segments == 0: return
        extent = 360 / num_segments
        target_angle = (90 + self.current_angle) % 360
        winning_active_index = int(target_angle / extent) % num_segments
        winner_data = active_participants[winning_active_index]
        winner_name = winner_data["name"]
        original_json_index = winner_data["original_index"]

        self.result_label.config(text=f"Opfer: {winner_name}!")
        self.logic.update_probabilities_after_win(original_json_index)
        self.update_prob_display()

        self.draw_wheel()


    def refresh_data(self):
        if self.is_spinning:
            return
        self.logic.load_data()
        if self.logic.names:
            self.result_label.config(text="Daten aus JSON neu geladen!", fg="#333")
            self.update_prob_display()
            self.draw_wheel()


if __name__ == "__main__":
    root = tk.Tk()
    app = WheelOfNamesApp(root)
    root.mainloop()

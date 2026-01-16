import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from collections import deque
import random
import tkinter.messagebox as mb

# --- Configuration ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

PROCESS_COLORS = [
    "#e74c3c", "#3498db", "#2ecc71", "#f1c40f", 
    "#9b59b6", "#e67e22", "#1abc9c", "#34495e"
]

class RoundRobinScheduler(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Round Robin Scheduler: Presentation Edition")
        self.geometry("1350x950")
        
        # Grid Configuration
        self.grid_columnconfigure(1, weight=1) 
        self.grid_rowconfigure(0, weight=1)

        # --- Variables ---
        self.process_entries = []
        self.is_animating = False
        self.current_tick = 0
        self.total_ticks = 0
        self.gantt_log = []
        self.event_log = {} 
        self.queue_history = {} 
        self.animation_job = None
        self.processes_data = []
        self.metrics_data = {}
        self.process_color_map = {} 

        # --- Layouts ---
        self.create_sidebar()
        self.create_main_content()

    # --- SIMULATION CONTROLS ---
    def rewind_animation(self):
        self.pause_animation()
        if self.current_tick > 0:
            self.current_tick -= 1
            self.draw_frame(self.current_tick)
            self.update_commentary(self.current_tick)

    def step_forward(self):
        self.pause_animation()
        if self.current_tick <= self.total_ticks:
            self.draw_frame(self.current_tick)
            self.update_commentary(self.current_tick)
            self.current_tick += 1

    def pause_animation(self):
        self.is_animating = False
        self.btn_play.configure(text="▶ Play", fg_color="#2ecc71")
        if self.animation_job:
            self.after_cancel(self.animation_job)
            self.animation_job = None

    # --- UI CONSTRUCTION ---
    def create_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=320, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(2, weight=1) 
        self.sidebar.grid_propagate(False)

        # Title
        title_lbl = ctk.CTkLabel(self.sidebar, text="Round Robin\nScheduler", 
                               font=ctk.CTkFont(size=24, weight="bold"))
        title_lbl.pack(padx=20, pady=(30, 20))

        # Scrollable Content Area
        self.info_scroll = ctk.CTkScrollableFrame(self.sidebar, fg_color="transparent")
        self.info_scroll.pack(fill="both", expand=True, padx=10, pady=5)

        # --- Helper for Sidebar Rows ---
        def add_definition_row(term, definition, help_key=None):
            f = ctk.CTkFrame(self.info_scroll, fg_color=("gray90", "gray20"))
            f.pack(fill="x", pady=5)
            
            # Header Row (Term + Button)
            header = ctk.CTkFrame(f, fg_color="transparent", height=25)
            header.pack(fill="x", padx=5, pady=(5,0))
            
            ctk.CTkLabel(header, text=f"• {term}", font=ctk.CTkFont(size=13, weight="bold"), 
                       text_color="#3498db").pack(side="left")
            
            if help_key:
                btn = ctk.CTkButton(header, text="?", width=20, height=20, corner_radius=10,
                                  fg_color="#e67e22", text_color="white", font=("Arial", 11, "bold"),
                                  command=lambda k=help_key: self.show_term_help(k))
                btn.pack(side="right")

            # Definition (Strict Wrapping)
            ctk.CTkLabel(f, text=definition, font=ctk.CTkFont(size=12), 
                       justify="left", anchor="w", wraplength=270).pack(fill="x", padx=8, pady=(2,8))

        # Core Concepts Section
        ctk.CTkLabel(self.info_scroll, text="CORE CONCEPTS", font=ctk.CTkFont(size=15, weight="bold"), 
                     text_color="#f1c40f", anchor="w").pack(fill="x", pady=(15,5))

        add_definition_row("Logic Rule", "New arrivals enter the queue BEFORE timeouts (processes whose time is up).")
        add_definition_row("Preemptive", "The CPU is taken away forcefully if time expires.")
        add_definition_row("Fairness", "Every process gets an equal slice of time.")

        ctk.CTkFrame(self.info_scroll, height=2, fg_color=("gray70", "gray40")).pack(fill="x", pady=15)

        # Vocabulary Section with Help Buttons
        ctk.CTkLabel(self.info_scroll, text="VOCABULARY & MATH", font=ctk.CTkFont(size=15, weight="bold"), 
                     anchor="w").pack(fill="x", pady=(0,5))

        add_definition_row("Time Quantum", "The fixed time limit per turn.", "quantum")
        add_definition_row("Context Switch", "Saving the old process and loading the new one.", "context")
        add_definition_row("Turnaround Time", "Total time spent in the system (Working + Waiting).", "tat")
        add_definition_row("Waiting Time", "Total time spent sitting in the queue doing nothing.", "wt")

        # Theme Switcher
        self.appearance_mode_optionemenu = ctk.CTkOptionMenu(self.sidebar, values=["Light", "Dark"], command=self.change_appearance_mode_event)
        self.appearance_mode_optionemenu.set("Dark")
        self.appearance_mode_optionemenu.pack(side="bottom", padx=20, pady=20)

    def change_appearance_mode_event(self, new_appearance_mode: str):
        ctk.set_appearance_mode(new_appearance_mode)
        if hasattr(self, 'queue_canvas'): self.update_canvas_colors()
        if hasattr(self, 'tabview') and self.tabview.get() == "3. Static Analysis": self.update_static_results()

    def show_term_help(self, key):
        title = ""
        msg = ""
        
        if key == "quantum":
            title = "Time Quantum (Time Slice)"
            msg = ("DEFINITION:\nThe maximum amount of time a process can run before the CPU interrupts it.\n\n"
                   "ANALOGY:\nImagine a shared arcade machine. You get 2 minutes (Quantum). If you don't beat the level in 2 minutes, "
                   "you must go to the back of the line and let the next kid play.")
        
        elif key == "context":
            title = "Context Switch"
            msg = ("DEFINITION:\nThe process of storing the state of the current process so that it can be resumed later.\n\n"
                   "ANALOGY:\nLike a bookmark in a book. Before you switch to a new book, you must place a bookmark (save state) "
                   "so you don't lose your page.")

        elif key == "tat":
            title = "Turnaround Time (TAT)"
            msg = ("FORMULA:\nTAT = Completion Time - Arrival Time\n\n"
                   "DEFINITION:\nThe total lifespan of the process in the system.\n\n"
                   "EXAMPLE:\nYou arrived at 10:00 AM. You finished your work at 10:30 AM.\n"
                   "Your Turnaround Time is 30 minutes (even if you only worked for 5 minutes of that time).")

        elif key == "wt":
            title = "Waiting Time (WT)"
            msg = ("FORMULA:\nWT = Turnaround Time - Burst Time\n\n"
                   "DEFINITION:\nThe total time the process spent in the Ready Queue waiting to get the CPU.\n\n"
                   "EXAMPLE:\nYou were in the bank for 30 minutes (Turnaround). The teller only talked to you for 5 minutes (Burst).\n"
                   "Your Waiting Time = 30 - 5 = 25 minutes.")

        mb.showinfo(title, msg)

    def create_main_content(self):
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

        self.tabview = ctk.CTkTabview(self.main_frame, command=self.on_tab_change)
        self.tabview.pack(fill="both", expand=True)

        self.tab_config = self.tabview.add("1. Configuration")
        self.tab_sim = self.tabview.add("2. Live Simulation")
        self.tab_results = self.tabview.add("3. Static Analysis")

        self.build_configuration_tab()
        self.build_simulation_tab()
        self.build_results_tab()

    def on_tab_change(self):
        if self.tabview.get() == "3. Static Analysis":
            # BUG FIX: Delay the plot drawing by 50ms. 
            # This gives the tab enough time to "finish" switching and set its size.
            self.after(50, self.update_static_results)

    # --- TAB 1: CONFIGURATION ---
    def build_configuration_tab(self):
        ctk.CTkLabel(self.tab_config, text="Setup your processes here.", text_color="gray60").pack(pady=(10,5))

        top_panel = ctk.CTkFrame(self.tab_config, fg_color=("gray90", "gray20"))
        top_panel.pack(fill="x", pady=10, padx=5)

        # Time Quantum Input with Help
        q_frame = ctk.CTkFrame(top_panel, fg_color="transparent")
        q_frame.pack(side="left", padx=15, pady=10)
        
        ctk.CTkLabel(q_frame, text="Time Slice (Quantum):", font=("Arial", 16, "bold")).pack(side="left", padx=(0,5))
        
        help_btn = ctk.CTkButton(q_frame, text="?", width=25, height=25, corner_radius=15, 
                               fg_color="#f39c12", text_color="white", 
                               font=("Arial", 14, "bold"),
                               command=lambda: self.show_term_help("quantum"))
        help_btn.pack(side="left", padx=(0, 10))

        self.tq_entry = ctk.CTkEntry(q_frame, width=60, font=("Arial", 16), justify="center")
        self.tq_entry.insert(0, "2")
        self.tq_entry.pack(side="left")

        btn_frame = ctk.CTkFrame(top_panel, fg_color="transparent")
        btn_frame.pack(side="right", padx=10)
        ctk.CTkButton(btn_frame, text="+ Add Process", command=self.add_process_row, fg_color="#27ae60", width=120).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="🎲 Randomize", command=self.randomize_data, fg_color="#e67e22", width=120).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="🗑 Clear All", command=self.clear_processes, fg_color="#c0392b", width=100).pack(side="left", padx=5)

        # Header
        header_frame = ctk.CTkFrame(self.tab_config, height=40, fg_color=("gray85", "gray25"))
        header_frame.pack(fill="x", padx=5, pady=(10, 0))
        
        headers = [
            ("Process Name", "ID"), 
            ("Arrival Time (Start)", "When it appears"), 
            ("Burst Time (Duration)", "Total work needed"), 
            ("Color", ""), 
            ("Action", "")
        ]
        
        for h, sub in headers:
            f = ctk.CTkFrame(header_frame, fg_color="transparent")
            f.pack(side="left", expand=True, fill="x")
            ctk.CTkLabel(f, text=h, font=("Arial", 12, "bold")).pack()
            if sub: ctk.CTkLabel(f, text=sub, font=("Arial", 10), text_color="gray").pack(pady=(0,2))

        self.scroll_frame = ctk.CTkScrollableFrame(self.tab_config, fg_color=("white", "gray15"))
        self.scroll_frame.pack(fill="both", expand=True, pady=5, padx=5)
        for _ in range(3): self.add_process_row()

        self.btn_calc = ctk.CTkButton(self.tab_config, text="🚀 INITIALIZE SIMULATION", height=50, 
                                    font=("Arial", 18, "bold"), command=self.run_scheduler)
        self.btn_calc.pack(fill="x", pady=15, padx=5)

    def add_process_row(self, at=None, bt=None):
        pid = len(self.process_entries) + 1
        color = PROCESS_COLORS[(pid-1) % len(PROCESS_COLORS)]
        
        row_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        row_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(row_frame, text=f"P{pid}", width=60, font=("Arial", 14, "bold")).pack(side="left", expand=True)
        
        entry_at = ctk.CTkEntry(row_frame, placeholder_text="0", justify="center")
        entry_at.insert(0, str(at) if at is not None else str(random.randint(0, 5)))
        entry_at.pack(side="left", fill="x", expand=True, padx=10)
        
        entry_bt = ctk.CTkEntry(row_frame, placeholder_text="1", justify="center")
        entry_bt.insert(0, str(bt) if bt is not None else str(random.randint(1, 10)))
        entry_bt.pack(side="left", fill="x", expand=True, padx=10)
        
        color_box = ctk.CTkLabel(row_frame, text="", width=40, height=20, fg_color=color, corner_radius=5)
        color_box.pack(side="left", expand=True)

        ctk.CTkButton(row_frame, text="✖", width=40, fg_color="transparent", text_color="#c0392b", 
                    command=lambda: self.delete_row(row_frame)).pack(side="left", expand=True)

        self.process_entries.append({"frame": row_frame, "id": f"P{pid}", "at": entry_at, "bt": entry_bt, "color": color})
        self.renumber_rows()

    def delete_row(self, frame):
        for item in self.process_entries:
            if item["frame"] == frame:
                frame.destroy()
                self.process_entries.remove(item)
                break
        self.renumber_rows()

    def renumber_rows(self):
        for idx, entry in enumerate(self.process_entries):
            new_id = f"P{idx+1}"
            entry["id"] = new_id
            entry["color"] = PROCESS_COLORS[idx % len(PROCESS_COLORS)]
            children = entry["frame"].winfo_children()
            children[0].configure(text=new_id) 
            children[3].configure(fg_color=entry["color"]) 

    def clear_processes(self):
        for entry in self.process_entries: entry["frame"].destroy()
        self.process_entries = []

    def randomize_data(self):
        self.clear_processes()
        for _ in range(4): self.add_process_row(random.randint(0, 8), random.randint(3, 8))

    # --- TAB 2: SIMULATION ---
    def build_simulation_tab(self):
        ctrl_frame = ctk.CTkFrame(self.tab_sim, fg_color=("gray90", "gray20"), height=60)
        ctrl_frame.pack(fill="x", pady=10, padx=5)

        speed_frame = ctk.CTkFrame(ctrl_frame, fg_color="transparent")
        speed_frame.pack(side="left", padx=10)
        ctk.CTkLabel(speed_frame, text="Speed:", font=("Arial", 10)).pack()
        self.speed_slider = ctk.CTkSlider(speed_frame, from_=2000, to=200, number_of_steps=10, width=100)
        self.speed_slider.set(1000) 
        self.speed_slider.pack()

        self.sim_time_lbl = ctk.CTkLabel(ctrl_frame, text="Time: 0", font=("Arial", 24, "bold"), width=120)
        self.sim_time_lbl.pack(side="left", padx=20)

        self.btn_rewind = ctk.CTkButton(ctrl_frame, text="⏮ Back", width=60, fg_color="#9b59b6", command=self.rewind_animation)
        self.btn_rewind.pack(side="left", padx=5)
        self.btn_play = ctk.CTkButton(ctrl_frame, text="▶ Play", width=80, command=self.toggle_animation)
        self.btn_play.pack(side="left", padx=5)
        self.btn_step = ctk.CTkButton(ctrl_frame, text="⏭ Step", width=60, fg_color="#e67e22", command=self.step_forward)
        self.btn_step.pack(side="left", padx=5)
        self.btn_reset = ctk.CTkButton(ctrl_frame, text="↺ Reset", width=60, fg_color="transparent", border_width=1, text_color=("black", "white"), command=self.reset_animation)
        self.btn_reset.pack(side="left", padx=5)

        ctk.CTkLabel(self.tab_sim, text="LIVE EXPLANATION LOG (What's happening now?)", font=("Arial", 12, "bold"), anchor="w").pack(fill="x", padx=20)
        
        self.commentary_box = ctk.CTkTextbox(self.tab_sim, height=160, 
                                           fg_color="#1a1a1a", 
                                           text_color="#00ff00", 
                                           font=("Consolas", 14),
                                           wrap="word") 
        self.commentary_box.pack(fill="x", padx=20, pady=(0, 10))
        self.commentary_box.insert("0.0", "System Initialized. Press 'Play' or 'Step' to see the CPU in action.")
        self.commentary_box.configure(state="disabled")

        cpu_container = ctk.CTkFrame(self.tab_sim, fg_color="transparent")
        cpu_container.pack(fill="x", pady=0, padx=20)
        
        ctk.CTkLabel(cpu_container, text="Active CPU Process:", font=("Arial", 12, "bold")).pack(side="left", padx=(0, 10))
        
        self.cpu_box = ctk.CTkLabel(cpu_container, text="IDLE", font=("Courier", 18, "bold"), 
                                  width=80, height=40, 
                                  fg_color=("#e0e0e0", "#2b2b2b"), corner_radius=10)
        self.cpu_box.pack(side="left")

        queue_container = ctk.CTkFrame(self.tab_sim, fg_color="transparent")
        queue_container.pack(fill="x", pady=5, padx=20)
        ctk.CTkLabel(queue_container, text="Ready Queue (Waiting Line)", font=("Arial", 12, "bold")).pack(anchor="w")
        self.queue_canvas = ctk.CTkCanvas(queue_container, height=60, bg="#242424", highlightthickness=0)
        self.queue_canvas.pack(fill="x", pady=5)

        gantt_container = ctk.CTkFrame(self.tab_sim, fg_color="transparent")
        gantt_container.pack(fill="both", expand=True, pady=5, padx=20)
        ctk.CTkLabel(gantt_container, text="Gantt Chart History", font=("Arial", 12, "bold")).pack(anchor="w")
        self.live_gantt_canvas = ctk.CTkCanvas(gantt_container, bg="#242424", highlightthickness=0)
        self.live_gantt_canvas.pack(fill="both", expand=True, pady=5)
        self.update_canvas_colors()

    def update_canvas_colors(self):
        mode = ctk.get_appearance_mode()
        bg_color = "#e0e0e0" if mode == "Light" else "#242424"
        self.queue_canvas.configure(bg=bg_color)
        self.live_gantt_canvas.configure(bg=bg_color)

    def build_results_tab(self):
        self.results_metrics_frame = ctk.CTkFrame(self.tab_results, height=100, fg_color="transparent")
        self.results_metrics_frame.pack(fill="x", padx=10, pady=10)
        self.results_plot_frame = ctk.CTkFrame(self.tab_results, fg_color="transparent")
        self.results_plot_frame.pack(fill="both", expand=True, padx=10, pady=10)

    # --- LOGIC ENGINE ---
    def run_scheduler(self):
        processes = []
        self.process_color_map = {}
        
        try:
            tq = int(self.tq_entry.get())
            if tq <= 0: raise ValueError
        except:
            self.show_error("Time Quantum must be a positive number.")
            return

        for entry in self.process_entries:
            try:
                pid, at, bt, color = entry["id"], int(entry["at"].get()), int(entry["bt"].get()), entry["color"]
                if at < 0 or bt <= 0: raise ValueError
                processes.append({'id': pid, 'at': at, 'bt': bt, 'rem_bt': bt, 'orig_bt': bt})
                self.process_color_map[pid] = color
            except:
                self.show_error(f"Please check inputs for {entry['id']}")
                return
        
        if not processes:
            self.show_error("Add at least one process!")
            return

        # SETUP
        processes.sort(key=lambda x: x['at'])
        current_time = 0
        ready_queue = deque()
        gantt = []
        visited_indices = set()
        self.event_log = {}
        self.queue_history = {}
        
        def get_arrivals(t):
            arrived = []
            for i, p in enumerate(processes):
                if i not in visited_indices and p['at'] <= t:
                    visited_indices.add(i)
                    arrived.append(i)
            return arrived

        initial_arrivals = get_arrivals(0)
        for idx in initial_arrivals:
            ready_queue.append(idx)
        
        metrics = {p['id']: {'ct':0, 'tat':0, 'wt':0} for p in processes}
        completed_count = 0
        n = len(processes)
        active_p_idx = None
        quantum_timer = 0
        
        while completed_count < n:
            daily_log = []
            daily_log.append(f"--- Second {current_time} to {current_time+1} ---")
            
            self.queue_history[current_time] = [processes[i]['id'] for i in ready_queue]
            
            if active_p_idx is None:
                if ready_queue:
                    active_p_idx = ready_queue.popleft()
                    quantum_timer = 0
                    p_curr = processes[active_p_idx]
                    daily_log.append(f"⚡ ACTION: {p_curr['id']} has been loaded into the CPU.")
                else:
                    gantt.append({"id": "IDLE", "start": current_time, "end": current_time + 1})
                    daily_log.append("💤 STATUS: The CPU is idle. No processes are ready yet.")
                    
                    current_time += 1
                    
                    new_guys = get_arrivals(current_time)
                    if new_guys:
                        names = [processes[i]['id'] for i in new_guys]
                        daily_log.append(f"📢 NEW ARRIVAL: {', '.join(names)} just arrived and joined the waiting line.")
                        for i in new_guys: ready_queue.append(i)

                    self.event_log[current_time-1] = daily_log
                    continue

            p = processes[active_p_idx]
            
            if gantt and gantt[-1]['id'] == p['id'] and gantt[-1]['end'] == current_time:
                gantt[-1]['end'] += 1
            else:
                gantt.append({"id": p['id'], "start": current_time, "end": current_time + 1})

            p['rem_bt'] -= 1
            quantum_timer += 1
            
            status_msg = f"⚙️ WORKING: {p['id']} is running."
            status_msg += f" It has {p['rem_bt']}s work left."
            status_msg += f" (Slice used: {quantum_timer}/{tq}s)"
            daily_log.append(status_msg)
            
            current_time += 1
            
            new_guys = get_arrivals(current_time)
            if new_guys:
                names = [processes[i]['id'] for i in new_guys]
                daily_log.append(f"📢 NEW ARRIVAL: {', '.join(names)} arrived and joined the line.")
                for i in new_guys: ready_queue.append(i)
            
            if p['rem_bt'] == 0:
                completed_count += 1
                metrics[p['id']]['ct'] = current_time
                metrics[p['id']]['tat'] = current_time - p['at']
                metrics[p['id']]['wt'] = metrics[p['id']]['tat'] - p['orig_bt']
                daily_log.append(f"✅ FINISHED: {p['id']} has completed all its work! It leaves the system.")
                active_p_idx = None
            elif quantum_timer == tq:
                ready_queue.append(active_p_idx)
                daily_log.append(f"⚖️ TIME'S UP: {p['id']} used its full time slice ({tq}s). Moving it to back of line to be fair.")
                active_p_idx = None
            
            self.event_log[current_time-1] = daily_log

        self.queue_history[current_time] = []
        self.event_log[current_time] = ["🏁 SIMULATION COMPLETE: All processes have finished execution."]
        self.total_ticks = current_time
        self.gantt_log = gantt
        self.metrics_data = metrics
        self.processes_data = processes

        self.tabview.set("2. Live Simulation")
        self.update_canvas_colors()
        self.reset_animation()
        self.update_static_results()

    def show_error(self, msg):
        mb.showerror("Error", msg)

    # --- ANIMATION ---
    def reset_animation(self):
        self.pause_animation()
        self.current_tick = 0
        self.draw_frame(0)
        self.update_commentary(0)

    def toggle_animation(self):
        if not self.gantt_log: return
        
        if self.current_tick >= self.total_ticks:
            self.current_tick = 0

        if self.is_animating:
            self.pause_animation()
        else:
            self.is_animating = True
            self.btn_play.configure(text="⏸ Pause", fg_color="#f1c40f")
            self.animate_tick()

    def animate_tick(self):
        if not self.is_animating: return
        if self.current_tick > self.total_ticks:
            self.is_animating = False
            self.btn_play.configure(text="▶ Replay", fg_color="#2ecc71")
            return
        
        self.draw_frame(self.current_tick)
        self.update_commentary(self.current_tick)
        self.current_tick += 1
        
        delay = int(self.speed_slider.get())
        self.animation_job = self.after(delay, self.animate_tick)

    def update_commentary(self, tick):
        self.commentary_box.configure(state="normal")
        self.commentary_box.delete("0.0", "end")
        
        msgs = self.event_log.get(tick, [])
        full_text = ""
        if msgs:
            full_text = "\n\n".join(msgs)
        else:
            full_text = f"⏱ Time {tick}: Ready to start."
            
        self.commentary_box.insert("0.0", full_text)
        self.commentary_box.configure(state="disabled")

    def draw_frame(self, tick):
        self.sim_time_lbl.configure(text=f"Time: {tick}")
        active_id, cpu_color = "IDLE", ("#e0e0e0", "#2b2b2b")
        
        for slice in self.gantt_log:
            if slice['start'] <= tick < slice['end']:
                active_id = slice['id']
                if active_id != "IDLE":
                    cpu_color = self.process_color_map.get(active_id, "gray")
                break
        
        if tick >= self.total_ticks and self.total_ticks > 0: 
            active_id, cpu_color = "DONE", "#8e44ad"
        
        self.cpu_box.configure(text=active_id, fg_color=cpu_color)
        current_q = self.queue_history.get(tick, [])
        self.draw_queue_visuals_strict(current_q)
        self.draw_live_gantt(tick)

    def draw_queue_visuals_strict(self, queue_list):
        self.queue_canvas.delete("all")
        x_offset = 10
        txt_color = "black" if ctk.get_appearance_mode() == "Light" else "white"
        
        for pid in queue_list:
            p_color = self.process_color_map.get(pid, "gray")
            self.queue_canvas.create_rectangle(x_offset, 10, x_offset+50, 50, fill=p_color, outline=txt_color, width=2)
            self.queue_canvas.create_text(x_offset+25, 30, text=pid, fill="white", font=("Arial", 12, "bold"))
            x_offset += 60

    def draw_live_gantt(self, current_time):
        self.live_gantt_canvas.delete("all")
        h = 60 
        scale = 35 
        txt_color = "black" if ctk.get_appearance_mode() == "Light" else "white"
        
        for slice in self.gantt_log:
            if slice['start'] < current_time:
                end_draw = min(slice['end'], current_time)
                width = (end_draw - slice['start']) * scale
                start_x = slice['start'] * scale
                
                color = "gray" if slice['id'] == "IDLE" else self.process_color_map.get(slice['id'], "gray")

                self.live_gantt_canvas.create_rectangle(start_x, 10, start_x + width, 10+h, fill=color, outline=txt_color)
                
                if width > 15:
                    self.live_gantt_canvas.create_text(start_x + width/2, 10+h/2, text=slice['id'], fill="white", font=("Arial", 11, "bold"))
                
                self.live_gantt_canvas.create_text(start_x, 10+h+12, text=str(slice['start']), fill=txt_color, font=("Arial", 9))
                if end_draw == slice['end']:
                    self.live_gantt_canvas.create_text(start_x + width, 10+h+12, text=str(end_draw), fill=txt_color, font=("Arial", 9))
        self.live_gantt_canvas.configure(scrollregion=self.live_gantt_canvas.bbox("all"))

    # --- TAB 3: RESULTS ---
    def update_static_results(self):
        self.update_idletasks()
        
        for w in self.results_metrics_frame.winfo_children(): w.destroy()
        for w in self.results_plot_frame.winfo_children(): w.destroy()
        
        if not self.metrics_data: return

        avg_tat = sum(m['tat'] for m in self.metrics_data.values()) / len(self.metrics_data)
        avg_wt = sum(m['wt'] for m in self.metrics_data.values()) / len(self.metrics_data)
        
        for label, val in [("Avg Turnaround", f"{avg_tat:.2f}s"), ("Avg Waiting", f"{avg_wt:.2f}s")]:
            card = ctk.CTkFrame(self.results_metrics_frame, fg_color=("gray85", "#34495e"))
            card.pack(side="left", padx=20, expand=True, fill="both")
            ctk.CTkLabel(card, text=val, font=("Arial", 28, "bold"), text_color="#2ecc71").pack(pady=(15,0))
            ctk.CTkLabel(card, text=label, font=("Arial", 14), text_color=("gray20", "gray80")).pack(pady=(0,15))

        is_light = ctk.get_appearance_mode() == "Light"
        bg_color, text_color = ('#f0f0f0', 'black') if is_light else ('#2b2b2b', 'white')

        fig, ax = plt.subplots(figsize=(10, 5)) 
        fig.patch.set_facecolor(bg_color)
        ax.set_facecolor(bg_color)
        
        process_ids = [p['id'] for p in self.processes_data][::-1]
        
        for slice in self.gantt_log:
            if slice['id'] == "IDLE": continue
            y_idx = process_ids.index(slice['id'])
            duration = slice['end'] - slice['start']
            p_color = self.process_color_map.get(slice['id'], "#3498db")
            
            ax.barh(y_idx, duration, left=slice['start'], height=0.6, color=p_color, edgecolor=text_color, alpha=0.9)
            if duration > 0.5:
                ax.text(slice['start'] + duration/2, y_idx, f"{duration}", ha='center', va='center', color='white', fontsize=9, fontweight='bold')

        ax.set_yticks(range(len(process_ids)))
        ax.set_yticklabels(process_ids, color=text_color, fontsize=12, fontweight='bold')
        ax.set_xlabel("Time (Seconds)", color=text_color, fontsize=12)
        ax.set_title("Final Execution Timeline", color=text_color, fontsize=14, pad=15)
        ax.tick_params(colors=text_color)
        ax.grid(True, axis='x', linestyle='--', alpha=0.3, color=text_color)
        
        for spine in ax.spines.values(): spine.set_color(text_color)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

        plt.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=self.results_plot_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

if __name__ == "__main__":
    app = RoundRobinScheduler()
    app.mainloop()
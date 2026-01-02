import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from collections import deque



ctk.set_appearance_mode("Dark")

ctk.set_default_color_theme("blue")

class SchedulerApplication(ctk.CTk):

    
    def __init__(self):
        super().__init__()

        self.title("Round Robin Scheduler")
        self.geometry("1100x700")

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=3)
        self.grid_rowconfigure(0, weight=1)

        self.navigationPanel = ctk.CTkFrame(self, width=300, corner_radius=0)
        self.navigationPanel.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        self.titleLabel = ctk.CTkLabel(self.navigationPanel, text="Configuration", font=ctk.CTkFont(size=20, weight="bold"))
        self.titleLabel.pack(pady=20)

        self.timeQuantumValue = ctk.StringVar(value="2")
        self.timeQuantumLabel = ctk.CTkLabel(self.navigationPanel, text="Time Quantum:")
        self.timeQuantumLabel.pack(pady=5)
        self.timeQuantumInput = ctk.CTkEntry(self.navigationPanel, textvariable=self.timeQuantumValue)
        self.timeQuantumInput.pack(pady=5, padx=20)

        self.processCountValue = ctk.StringVar(value="3")
        self.processCountLabel = ctk.CTkLabel(self.navigationPanel, text="Number of Processes:")
        self.processCountLabel.pack(pady=5)
        self.processCountInput = ctk.CTkEntry(self.navigationPanel, textvariable=self.processCountValue)
        self.processCountInput.pack(pady=5, padx=20)

        self.processListScroll = ctk.CTkScrollableFrame(self.navigationPanel, label_text="Process Details")
        self.processListScroll.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.processListEntries = []
        self.refreshProcessFields()
        
        self.processCountInput.bind("<FocusOut>", lambda event: self.refreshProcessFields())
        self.processCountInput.bind("<Return>", lambda event: self.refreshProcessFields())

        self.startExecutionButton = ctk.CTkButton(self.navigationPanel, text="Calculate & Visualize", command=self.initiateScheduling)
        self.startExecutionButton.pack(pady=20)

        self.resultsDisplayArea = ctk.CTkFrame(self)
        self.resultsDisplayArea.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.resultsDisplayArea.grid_rowconfigure(0, weight=1)
        self.resultsDisplayArea.grid_rowconfigure(1, weight=1)
        self.resultsDisplayArea.grid_columnconfigure(0, weight=1)

        self.metricsTableView = ctk.CTkScrollableFrame(self.resultsDisplayArea, label_text="Scheduling Metrics")
        self.metricsTableView.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        self.ganttChartContainer = ctk.CTkFrame(self.resultsDisplayArea)
        self.ganttChartContainer.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

    def refreshProcessFields(self):
        for widgets in self.processListEntries:
            for widget in widgets:
                widget.destroy()
        self.processListEntries = []

        try:
            rawInputValue = self.processCountValue.get()
            numProcesses = int(rawInputValue) if rawInputValue else 0
            if numProcesses > 10: numProcesses = 10
        except ValueError:
            numProcesses = 0

        for index in range(numProcesses):
            processLabel = ctk.CTkLabel(self.processListScroll, text=f"P{index+1} (AT, BT):")
            processLabel.grid(row=index, column=0, padx=5, pady=5)
            arrivalTimeField = ctk.CTkEntry(self.processListScroll, width=50, placeholder_text="AT")
            arrivalTimeField.insert(0, "0")
            arrivalTimeField.grid(row=index, column=1, padx=2, pady=5)
            burstTimeField = ctk.CTkEntry(self.processListScroll, width=50, placeholder_text="BT")
            burstTimeField.insert(0, str(index+2))
            burstTimeField.grid(row=index, column=2, padx=2, pady=5)
            self.processListEntries.append((processLabel, arrivalTimeField, burstTimeField))

    def runRoundRobinAlgorithm(self, processList, timeQuantum):
        totalProcesses = len(processList)
        processList = sorted(processList, key=lambda p: p['arrival'])
        readyQueue = deque()
        calculationResults = {p['id']: {'arrival': p['arrival'], 'burst': p['burst'], 'remaining': p['burst'], 
                             'comp': 0, 'tat': 0, 'wt': 0, 'rt': -1} for p in processList}
        currentClockTime = 0
        completedCount = 0
        ganttLog = []
        nextProcessIndex = 0

        while nextProcessIndex < totalProcesses and processList[nextProcessIndex]['arrival'] <= currentClockTime:
            readyQueue.append(processList[nextProcessIndex]['id'])
            nextProcessIndex += 1

        while completedCount < totalProcesses:
            if not readyQueue:
                if nextProcessIndex < totalProcesses:
                    currentClockTime = processList[nextProcessIndex]['arrival']
                    while nextProcessIndex < totalProcesses and processList[nextProcessIndex]['arrival'] <= currentClockTime:
                        readyQueue.append(processList[nextProcessIndex]['id'])
                        nextProcessIndex += 1
                else:
                    break

            activeProcessId = readyQueue.popleft()
            activeProcessData = calculationResults[activeProcessId]
            
            if activeProcessData['rt'] == -1:
                activeProcessData['rt'] = currentClockTime - activeProcessData['arrival']
            
            timeToExecute = min(activeProcessData['remaining'], timeQuantum)
            ganttLog.append({'Process': activeProcessId, 'Start': currentClockTime, 'Finish': currentClockTime + timeToExecute})
            
            currentClockTime += timeToExecute
            activeProcessData['remaining'] -= timeToExecute

            while nextProcessIndex < totalProcesses and processList[nextProcessIndex]['arrival'] <= currentClockTime:
                readyQueue.append(processList[nextProcessIndex]['id'])
                nextProcessIndex += 1

            if activeProcessData['remaining'] > 0:
                readyQueue.append(activeProcessId)
            else:
                activeProcessData['comp'] = currentClockTime
                activeProcessData['tat'] = activeProcessData['comp'] - activeProcessData['arrival']
                activeProcessData['wt'] = activeProcessData['tat'] - activeProcessData['burst']
                completedCount += 1
                
        return calculationResults, ganttLog

    def initiateScheduling(self):
        try:
            quantumValue = int(self.timeQuantumValue.get())
            rawProcesses = []
            for index, (_, arrivalField, burstField) in enumerate(self.processListEntries):
                rawProcesses.append({
                    'id': f"P{index+1}", 
                    'arrival': int(arrivalField.get() or 0), 
                    'burst': int(burstField.get() or 1)
                })
            
            finalMetrics, ganttPlotData = self.runRoundRobinAlgorithm(rawProcesses, quantumValue)
            self.renderMetricsAndTable(finalMetrics, ganttPlotData)
        except Exception as error:
            print(f"Error encountered: {error}")

    def renderMetricsAndTable(self, metricsData, ganttPlotData):
        for widget in self.metricsTableView.winfo_children():
            widget.destroy()

        summaryLayout = ctk.CTkFrame(self.metricsTableView, fg_color="transparent")
        summaryLayout.pack(fill="x", padx=10, pady=10)

        overallTAT, overallWT, overallRT = 0, 0, 0
        totalItems = len(metricsData)
        for _, stats in metricsData.items():
            overallTAT += stats['tat']
            overallWT += stats['wt']
            overallRT += stats['rt']

        if totalItems > 0:
            meanTAT = overallTAT / totalItems
            meanWT = overallWT / totalItems
            meanRT = overallRT / totalItems

            cardsInfo = [
                ("Avg Turnaround", f"{meanTAT:.2f}", "#3498db"),
                ("Avg Waiting", f"{meanWT:.2f}", "#e67e22"),
                ("Avg Response", f"{meanRT:.2f}", "#2ecc71")
            ]

            for labelText, displayVal, accentColor in cardsInfo:
                statsCard = ctk.CTkFrame(summaryLayout, fg_color=accentColor, corner_radius=10, width=150)
                statsCard.pack(side="left", padx=10, pady=5, expand=True, fill="both")
                ctk.CTkLabel(statsCard, text=labelText, font=ctk.CTkFont(size=12, weight="bold"), text_color="white").pack(pady=(10, 2))
                ctk.CTkLabel(statsCard, text=displayVal, font=ctk.CTkFont(size=20, weight="bold"), text_color="white").pack(pady=(2, 10))

        tableBody = ctk.CTkFrame(self.metricsTableView, fg_color="#2b2b2b", corner_radius=10)
        tableBody.pack(fill="both", expand=True, padx=10, pady=10)

        columnHeaders = ["Process", "Arrival", "Burst", "Complete", "TAT", "Wait", "Response"]
        headerRow = ctk.CTkFrame(tableBody, fg_color="#3d3d3d", corner_radius=5)
        headerRow.pack(fill="x", padx=5, pady=5)
        
        for headerText in columnHeaders:
            headerLabel = ctk.CTkLabel(headerRow, text=headerText, font=ctk.CTkFont(size=13, weight="bold"), width=80)
            headerLabel.pack(side="left", expand=True, padx=2)

        for processId, stats in metricsData.items():
            rowContainer = ctk.CTkFrame(tableBody, fg_color="transparent")
            rowContainer.pack(fill="x", padx=5, pady=2)
            
            rowValues = [processId, stats['arrival'], stats['burst'], stats['comp'], stats['tat'], stats['wt'], stats['rt']]
            for value in rowValues:
                dataCell = ctk.CTkLabel(rowContainer, text=str(value), width=80)
                dataCell.pack(side="left", expand=True, padx=2)

        self.buildGanttVisualization(ganttPlotData)

    def buildGanttVisualization(self, ganttPlotData):
        for widget in self.ganttChartContainer.winfo_children():
            widget.destroy()

        if not ganttPlotData:
            return

        figure, axis = plt.subplots(figsize=(8, 3))
        figure.patch.set_facecolor('#242424')
        axis.set_facecolor('#242424')
        
        import matplotlib.cm as colormaps
        colorPalette = colormaps.get_cmap('tab10', 10)
        
        distinctProcesses = sorted(list(set(entry['Process'] for entry in ganttPlotData)))
        processIdToIndex = {procId: i for i, procId in enumerate(distinctProcesses)}
        
        for entry in ganttPlotData:
            procId = entry['Process']
            vIndex = processIdToIndex[procId]
            axis.broken_barh([(entry['Start'], entry['Finish'] - entry['Start'])], 
                           (vIndex*10, 8), facecolors=colorPalette(vIndex))
            axis.text(entry['Start'] + (entry['Finish'] - entry['Start'])/2, 
                    vIndex*10 + 4, procId, color='white', ha='center', va='center', weight='bold')

        axis.set_xlabel('Time', color='white')
        axis.set_yticks([processIdToIndex[procId]*10 + 4 for procId in distinctProcesses])
        axis.set_yticklabels(distinctProcesses, color='white')
        axis.tick_params(axis='x', colors='white')
        axis.spines['bottom'].set_color('white')
        axis.spines['top'].set_visible(False)
        axis.spines['right'].set_visible(False)
        axis.spines['left'].set_color('white')
        
        plt.tight_layout()
        plotCanvas = FigureCanvasTkAgg(figure, master=self.ganttChartContainer)
        plotCanvas.draw()
        plotCanvas.get_tk_widget().pack(fill="both", expand=True)

if __name__ == "__main__":
    appInstance = SchedulerApplication()
    appInstance.mainloop()

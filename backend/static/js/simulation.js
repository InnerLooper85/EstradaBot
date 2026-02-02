/**
 * Production Simulation - Visual Factory Floor Animation
 * Animates stators moving through production stations
 */

class ProductionSimulation {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.stations = [];
        this.parts = [];
        this.partElements = {};
        this.stationElements = {};

        // Time control
        this.isPlaying = false;
        this.speed = 1;  // 1 = 1 simulated minute per real second (60X)
        this.currentTime = null;
        this.startTime = null;
        this.endTime = null;
        this.selectedDate = null;
        this.dataLoaded = false;

        // Animation
        this.animationFrame = null;
        this.lastFrameTime = 0;

        this.setupControls();
        console.log('ProductionSimulation initialized');
    }

    setupControls() {
        // Play button
        const btnPlay = document.getElementById('btnPlay');
        const btnPause = document.getElementById('btnPause');
        const btnReset = document.getElementById('btnReset');

        if (btnPlay) btnPlay.addEventListener('click', () => this.play());
        if (btnPause) btnPause.addEventListener('click', () => this.pause());
        if (btnReset) btnReset.addEventListener('click', () => this.reset());

        // Speed buttons
        document.querySelectorAll('.speed-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                document.querySelectorAll('.speed-btn').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                this.speed = parseInt(e.target.dataset.speed);
                console.log('Speed set to', this.speed);
            });
        });

        // Time scrubber
        const scrubber = document.getElementById('timeScrubber');
        if (scrubber) {
            scrubber.addEventListener('input', (e) => {
                this.scrubTo(e.target.value / 100);
            });
        }

        // Date navigation
        const datePicker = document.getElementById('datePicker');
        if (datePicker) {
            datePicker.addEventListener('change', (e) => {
                this.jumpToDate(e.target.value);
            });
        }

        const btnPrevDay = document.getElementById('btnPrevDay');
        const btnNextDay = document.getElementById('btnNextDay');
        if (btnPrevDay) btnPrevDay.addEventListener('click', () => this.navigateDay(-1));
        if (btnNextDay) btnNextDay.addEventListener('click', () => this.navigateDay(1));
    }

    async loadData() {
        console.log('Loading simulation data...');
        try {
            const response = await fetch('/api/simulation-data');

            if (!response.ok) {
                console.error('API response not OK:', response.status);
                this.showNoSchedule();
                return;
            }

            const data = await response.json();

            if (data.error) {
                console.error('Simulation data error:', data.error);
                this.showNoSchedule();
                return;
            }

            console.log('=== SIMULATION DATA LOADED ===');
            console.log('Total parts:', data.parts.length);
            console.log('Total stations:', data.stations.length);

            // Debug: check how many parts have operations
            const partsWithOps = data.parts.filter(p => p.operations && p.operations.length > 0);
            console.log('Parts WITH operations:', partsWithOps.length);
            console.log('Parts WITHOUT operations:', data.parts.length - partsWithOps.length);

            if (partsWithOps.length > 0) {
                console.log('Sample part:', partsWithOps[0].wo_number);
                console.log('Sample operations:', JSON.stringify(partsWithOps[0].operations.slice(0, 2)));
            }

            this.stations = data.stations;
            this.parts = data.parts;
            this.startTime = new Date(data.schedule_info.start_date);
            this.endTime = new Date(data.schedule_info.end_date);
            this.currentTime = new Date(this.startTime);
            this.selectedDate = this.startTime.toISOString().split('T')[0];

            console.log('Time range:', this.startTime.toISOString(), 'to', this.endTime.toISOString());
            console.log('Current time set to:', this.currentTime.toISOString());

            // Update UI
            const scheduleInfo = document.getElementById('scheduleInfo');
            if (scheduleInfo) {
                scheduleInfo.textContent = `${data.schedule_info.total_orders} orders | ${this.formatDate(this.startTime)} - ${this.formatDate(this.endTime)}`;
            }

            const statTotal = document.getElementById('statTotal');
            if (statTotal) {
                statTotal.textContent = data.schedule_info.total_orders;
            }

            // Set date picker bounds
            const datePicker = document.getElementById('datePicker');
            if (datePicker) {
                datePicker.min = this.startTime.toISOString().split('T')[0];
                datePicker.max = this.endTime.toISOString().split('T')[0];
                datePicker.value = this.selectedDate;
            }

            this.hideNoSchedule();
            this.renderFloor();
            this.renderParts();
            this.updateDisplay();

            console.log('=== INITIALIZATION COMPLETE ===');
            console.log('Parts elements created:', Object.keys(this.partElements).length);
            console.log('Station elements created:', Object.keys(this.stationElements).length);
            console.log('Data loaded flag:', this.dataLoaded);

        } catch (error) {
            console.error('Failed to load simulation data:', error);
            this.showNoSchedule();
        }
    }

    showNoSchedule() {
        const msg = document.getElementById('noScheduleMessage');
        const legend = document.getElementById('legend');
        if (msg) msg.style.display = 'block';
        if (legend) legend.style.display = 'none';
        this.dataLoaded = false;
    }

    hideNoSchedule() {
        const msg = document.getElementById('noScheduleMessage');
        const legend = document.getElementById('legend');
        if (msg) {
            msg.style.display = 'none';
            msg.remove();  // Remove from DOM entirely
        }
        if (legend) legend.style.display = 'flex';
        this.dataLoaded = true;
    }

    renderFloor() {
        console.log('Rendering floor with', this.stations.length, 'stations');

        // Clear existing elements
        const existing = this.container.querySelectorAll('.station, .flow-arrow, .part');
        existing.forEach(el => el.remove());
        this.stationElements = {};

        // Create station elements
        this.stations.forEach(station => {
            const el = document.createElement('div');
            el.className = 'station idle';
            el.id = `station-${station.id.replace(/\s+/g, '-')}`;
            el.style.left = `${station.x}px`;
            el.style.top = `${station.y}px`;
            el.style.width = `${station.width}px`;
            el.style.height = `${station.height}px`;

            // Station label
            const label = document.createElement('div');
            label.className = 'station-label';
            label.textContent = station.name;
            el.appendChild(label);

            // Capacity indicator
            if (station.capacity) {
                const cap = document.createElement('div');
                cap.className = 'station-capacity';
                cap.textContent = `Cap: ${station.capacity}`;
                el.appendChild(cap);
            }

            // Queue badge
            const queue = document.createElement('div');
            queue.className = 'station-queue empty';
            queue.id = `queue-${station.id.replace(/\s+/g, '-')}`;
            queue.textContent = '0';
            el.appendChild(queue);

            // Desma machines for injection
            if (station.machines) {
                el.classList.add('injection');
                el.innerHTML = '';
                const labelDiv = document.createElement('div');
                labelDiv.className = 'station-label';
                labelDiv.textContent = 'INJECTION';
                labelDiv.style.width = '100%';
                labelDiv.style.textAlign = 'center';
                labelDiv.style.marginBottom = '4px';
                el.appendChild(labelDiv);

                const machineContainer = document.createElement('div');
                machineContainer.style.display = 'flex';
                machineContainer.style.gap = '4px';
                machineContainer.style.flexWrap = 'wrap';
                machineContainer.style.justifyContent = 'center';

                station.machines.forEach(machine => {
                    const machineEl = document.createElement('div');
                    machineEl.className = 'desma-machine';
                    machineEl.id = `machine-${machine}`;
                    machineEl.textContent = machine;
                    machineContainer.appendChild(machineEl);
                });
                el.appendChild(machineContainer);
            }

            this.container.appendChild(el);
            this.stationElements[station.id] = el;
        });

        // Add flow arrows
        this.renderFlowArrows();
    }

    renderFlowArrows() {
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('class', 'flow-arrow');
        svg.style.position = 'absolute';
        svg.style.top = '0';
        svg.style.left = '0';
        svg.style.width = '100%';
        svg.style.height = '100%';
        svg.style.pointerEvents = 'none';

        const flows = [
            { from: 'BLAST', to: 'TUBE PREP' },
            { from: 'BLAST', to: 'CORE OVEN' },
            { from: 'TUBE PREP', to: 'ASSEMBLY' },
            { from: 'CORE OVEN', to: 'ASSEMBLY' },
            { from: 'ASSEMBLY', to: 'INJECTION' },
            { from: 'INJECTION', to: 'CURE' },
            { from: 'CURE', to: 'QUENCH' },
            { from: 'QUENCH', to: 'DISASSEMBLY' },
            { from: 'DISASSEMBLY', to: 'BLD END CUTBACK' },
            { from: 'BLD END CUTBACK', to: 'CUT THREADS' },
            { from: 'CUT THREADS', to: 'INSPECT' }
        ];

        flows.forEach(flow => {
            const fromStation = this.stations.find(s => s.id === flow.from);
            const toStation = this.stations.find(s => s.id === flow.to);
            if (!fromStation || !toStation) return;

            const x1 = fromStation.x + fromStation.width / 2;
            const y1 = fromStation.y + fromStation.height / 2;
            const x2 = toStation.x + toStation.width / 2;
            const y2 = toStation.y + toStation.height / 2;

            const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
            path.setAttribute('d', `M ${x1} ${y1} L ${x2} ${y2}`);
            svg.appendChild(path);
        });

        this.container.insertBefore(svg, this.container.firstChild);
    }

    renderParts() {
        console.log('Rendering', this.parts.length, 'parts');

        // Clear existing parts
        Object.values(this.partElements).forEach(el => el.remove());
        this.partElements = {};

        // Create part elements
        this.parts.forEach((part, index) => {
            const el = document.createElement('div');
            el.className = `part priority-${this.getPriorityClass(part.priority)}`;
            el.id = `part-${index}`;
            el.title = `WO# ${part.wo_number}`;
            el.style.display = 'none';

            el.addEventListener('click', () => this.showPartDetail(part));

            this.container.appendChild(el);
            this.partElements[index] = el;
        });

        console.log('Created', Object.keys(this.partElements).length, 'part elements');
    }

    getPriorityClass(priority) {
        if (!priority) return 'normal';
        const p = priority.toLowerCase();
        if (p.includes('asap')) return 'hot-asap';
        if (p.includes('dated') || p.includes('hot')) return 'hot-dated';
        if (p.includes('rework') || p.includes('reline')) return 'rework';
        if (p.includes('cavo')) return 'cavo';
        return 'normal';
    }

    getPartPositionAtTime(part, time) {
        if (!part.operations || part.operations.length === 0) {
            return { status: 'no_ops' };  // Changed from null to track this case
        }

        const ops = [...part.operations].sort((a, b) =>
            new Date(a.start) - new Date(b.start)
        );

        const firstOpStart = new Date(ops[0].start);
        const lastOpEnd = new Date(ops[ops.length - 1].end);

        // Before first operation - pending
        if (time < firstOpStart) {
            return { status: 'pending' };
        }

        // After last operation - completed
        if (time > lastOpEnd) {
            return { status: 'completed' };
        }

        // Find current operation
        for (let i = 0; i < ops.length; i++) {
            const op = ops[i];
            const opStart = new Date(op.start);
            const opEnd = new Date(op.end);

            if (time >= opStart && time <= opEnd) {
                const station = this.stations.find(s => s.id === op.station);
                if (station) {
                    // Add some jitter so parts don't stack exactly on top of each other
                    const jitterX = (Math.random() - 0.5) * 20;
                    const jitterY = (Math.random() - 0.5) * 20;
                    return {
                        status: 'at_station',
                        station: op.station,
                        x: station.x + station.width / 2 - 6 + jitterX,
                        y: station.y + station.height / 2 - 6 + jitterY,
                        operation: op
                    };
                }
            }

            // Between operations - transitioning
            if (i < ops.length - 1) {
                const nextOp = ops[i + 1];
                const nextStart = new Date(nextOp.start);

                if (time > opEnd && time < nextStart) {
                    const fromStation = this.stations.find(s => s.id === op.station);
                    const toStation = this.stations.find(s => s.id === nextOp.station);

                    if (fromStation && toStation) {
                        const progress = (time - opEnd) / (nextStart - opEnd);
                        return {
                            status: 'transitioning',
                            from: op.station,
                            to: nextOp.station,
                            x: fromStation.x + (toStation.x - fromStation.x) * progress + fromStation.width / 2 - 6,
                            y: fromStation.y + (toStation.y - fromStation.y) * progress + fromStation.height / 2 - 6
                        };
                    }
                }
            }
        }

        return { status: 'unknown' };
    }

    updateDisplay() {
        if (!this.currentTime) {
            console.warn('updateDisplay called but currentTime is null');
            return;
        }

        const time = this.currentTime;

        // Update time display
        const timeDisplay = document.getElementById('timeDisplay');
        if (timeDisplay) {
            timeDisplay.textContent = this.formatDateTime(time);
        }

        // Update scrubber position
        const dayStart = new Date(time);
        dayStart.setHours(0, 0, 0, 0);
        const dayEnd = new Date(dayStart);
        dayEnd.setHours(23, 59, 59, 999);

        const dayProgress = (time - dayStart) / (dayEnd - dayStart);
        const scrubber = document.getElementById('timeScrubber');
        if (scrubber) {
            scrubber.value = dayProgress * 100;
        }

        // Track stats
        let inProgress = 0;
        let completed = 0;
        let pending = 0;
        let noOps = 0;

        // Update station queues
        const stationCounts = {};

        // Update parts positions
        this.parts.forEach((part, index) => {
            const el = this.partElements[index];
            if (!el) return;  // Skip if element doesn't exist

            const pos = this.getPartPositionAtTime(part, time);

            if (pos.status === 'pending') {
                el.style.display = 'none';
                pending++;
            } else if (pos.status === 'completed') {
                el.style.display = 'none';
                completed++;
            } else if (pos.status === 'no_ops') {
                el.style.display = 'none';
                noOps++;
            } else if (pos.status === 'at_station' || pos.status === 'transitioning') {
                el.style.display = 'block';
                el.style.left = `${pos.x}px`;
                el.style.top = `${pos.y}px`;
                inProgress++;

                if (pos.status === 'at_station') {
                    stationCounts[pos.station] = (stationCounts[pos.station] || 0) + 1;
                }
            } else {
                el.style.display = 'none';
                pending++;
            }
        });

        // Update station states
        this.stations.forEach(station => {
            const el = this.stationElements[station.id];
            if (!el) return;

            const count = stationCounts[station.id] || 0;
            const queueEl = el.querySelector('.station-queue');

            if (count > 0) {
                el.classList.remove('idle');
                el.classList.add('busy');
                if (station.capacity && count >= station.capacity) {
                    el.classList.add('full');
                }
                if (queueEl) {
                    queueEl.textContent = count;
                    queueEl.classList.remove('empty');
                }
            } else {
                el.classList.remove('busy', 'full');
                el.classList.add('idle');
                if (queueEl) {
                    queueEl.classList.add('empty');
                }
            }
        });

        // Update stats display
        const statInProgress = document.getElementById('statInProgress');
        const statCompleted = document.getElementById('statCompleted');
        const statPending = document.getElementById('statPending');

        if (statInProgress) statInProgress.textContent = inProgress;
        if (statCompleted) statCompleted.textContent = completed;
        if (statPending) statPending.textContent = pending + noOps;

        // Debug output (only on first call or every 60 frames)
        if (!this._updateCount) this._updateCount = 0;
        this._updateCount++;
        if (this._updateCount === 1 || this._updateCount % 60 === 0) {
            console.log(`Update #${this._updateCount}: Time=${this.formatDateTime(time)}, InProgress=${inProgress}, Completed=${completed}, Pending=${pending}, NoOps=${noOps}`);
        }
    }

    play() {
        if (this.isPlaying) {
            console.log('Already playing');
            return;
        }
        if (!this.dataLoaded) {
            console.warn('Cannot play - no data loaded');
            alert('No schedule data loaded. Please generate a schedule first.');
            return;
        }

        console.log('=== STARTING PLAYBACK ===');
        console.log('Current time:', this.currentTime);
        console.log('Speed:', this.speed, '(1 real second =', this.speed, 'simulated minutes)');

        this.isPlaying = true;

        const btnPlay = document.getElementById('btnPlay');
        const btnPause = document.getElementById('btnPause');
        if (btnPlay) {
            btnPlay.disabled = true;
            btnPlay.classList.add('active');
        }
        if (btnPause) {
            btnPause.disabled = false;
        }

        this.lastFrameTime = performance.now();
        this.animate();
    }

    pause() {
        console.log('Pausing simulation');
        this.isPlaying = false;

        const btnPlay = document.getElementById('btnPlay');
        const btnPause = document.getElementById('btnPause');
        if (btnPlay) {
            btnPlay.disabled = false;
            btnPlay.classList.remove('active');
        }
        if (btnPause) {
            btnPause.disabled = true;
        }

        if (this.animationFrame) {
            cancelAnimationFrame(this.animationFrame);
            this.animationFrame = null;
        }
    }

    reset() {
        console.log('Resetting simulation');
        this.pause();
        if (this.startTime) {
            this.currentTime = new Date(this.startTime);
            this.selectedDate = this.startTime.toISOString().split('T')[0];
            const datePicker = document.getElementById('datePicker');
            if (datePicker) {
                datePicker.value = this.selectedDate;
            }
            this.updateDisplay();
        }
    }

    animate() {
        if (!this.isPlaying) return;

        const now = performance.now();
        const delta = now - this.lastFrameTime;
        this.lastFrameTime = now;

        // Advance simulation time
        // speed = simulated minutes per real second
        // At speed=1: 1 real second = 1 simulated minute
        // At speed=30: 1 real second = 30 simulated minutes
        const realSeconds = delta / 1000;
        const simMinutes = realSeconds * this.speed;
        const simMillis = simMinutes * 60 * 1000;

        this.currentTime = new Date(this.currentTime.getTime() + simMillis);

        // Check if we've reached end of schedule
        if (this.currentTime > this.endTime) {
            this.currentTime = new Date(this.endTime);
            this.pause();
            console.log('Simulation reached end of schedule');
            return;
        }

        this.updateDisplay();

        this.animationFrame = requestAnimationFrame(() => this.animate());
    }

    scrubTo(progress) {
        if (!this.selectedDate) return;

        const dayStart = new Date(this.selectedDate);
        dayStart.setHours(5, 0, 0, 0);
        const dayEnd = new Date(this.selectedDate);
        dayEnd.setHours(23, 59, 59, 999);

        this.currentTime = new Date(dayStart.getTime() + (dayEnd - dayStart) * progress);
        this.updateDisplay();
    }

    jumpToDate(dateStr) {
        this.selectedDate = dateStr;
        const date = new Date(dateStr);
        date.setHours(5, 0, 0, 0);
        this.currentTime = date;
        this.updateDisplay();
        console.log('Jumped to date:', dateStr, 'Time:', this.currentTime);
    }

    navigateDay(direction) {
        if (!this.selectedDate || !this.startTime || !this.endTime) return;

        const current = new Date(this.selectedDate);
        current.setDate(current.getDate() + direction);

        const minDate = new Date(this.startTime.toISOString().split('T')[0]);
        const maxDate = new Date(this.endTime.toISOString().split('T')[0]);

        if (current >= minDate && current <= maxDate) {
            this.selectedDate = current.toISOString().split('T')[0];
            const datePicker = document.getElementById('datePicker');
            if (datePicker) {
                datePicker.value = this.selectedDate;
            }
            this.jumpToDate(this.selectedDate);
        }
    }

    showPartDetail(part) {
        document.getElementById('modalWoNumber').textContent = `WO# ${part.wo_number}`;
        document.getElementById('modalPartNumber').textContent = part.part_number || '-';
        document.getElementById('modalCustomer').textContent = part.customer || '-';
        document.getElementById('modalPriority').textContent = part.priority || 'Normal';
        document.getElementById('modalRubberType').textContent = part.rubber_type || '-';
        document.getElementById('modalCore').textContent = part.assigned_core || '-';

        const opsContainer = document.getElementById('modalOperations');
        opsContainer.innerHTML = '';

        if (part.operations && part.operations.length > 0) {
            part.operations.forEach(op => {
                const opStart = new Date(op.start);
                const opEnd = new Date(op.end);
                const isCurrent = this.currentTime >= opStart && this.currentTime <= opEnd;
                const isCompleted = this.currentTime > opEnd;

                const opEl = document.createElement('div');
                opEl.className = `operation-item ${isCurrent ? 'current' : ''} ${isCompleted ? 'completed' : ''}`;
                opEl.innerHTML = `
                    <span class="operation-name">${op.station}</span>
                    <span class="operation-time">${this.formatTime(opStart)} - ${this.formatTime(opEnd)}</span>
                `;
                opsContainer.appendChild(opEl);
            });
        } else {
            opsContainer.innerHTML = '<p class="text-muted">No operation data available</p>';
        }

        const modal = new bootstrap.Modal(document.getElementById('partDetailModal'));
        modal.show();
    }

    formatDate(date) {
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    }

    formatTime(date) {
        return date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
    }

    formatDateTime(date) {
        return date.toLocaleString('en-US', {
            month: 'short',
            day: 'numeric',
            hour: 'numeric',
            minute: '2-digit'
        });
    }
}

// Make available globally
window.ProductionSimulation = ProductionSimulation;

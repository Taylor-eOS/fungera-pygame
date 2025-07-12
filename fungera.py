import numpy as np
import os
import sys
import glob
import pickle
import memory as m
import queue as q
import common as c
import organism as o
from pygame_visualizer import PygameVisualizer

class Fungera:
    def __init__(self):
        self.is_minimal = False
        self.visualizer = PygameVisualizer(m.memory, q.queue, c.config)
        self.timer = c.RepeatedTimer(c.config['autosave_rate'], self.save_state, (True,))
        np.random.seed(c.config['random_seed'])
        self.ensure_initial_genome()
        genome_size = self.load_genome_into_memory('initial.gen', c.config['memory_size'] // 2)
        o.OrganismFull(c.config['memory_size'] // 2, genome_size)
        self.cycle = 0
        self.purges = 0
        self.update_info()
        if c.config['snapshot_to_load'] != 'new':
            self.load_state()

    def ensure_initial_genome(self):
        if not os.path.exists('initial.gen'):
            genome = [
                "v$<...vdc@<>..@cd>Sb.v.",
                ">....v>Sbv^^b?bP<......",
                "..b......>...........v.",
                "va0aS<>....>..?d^>?avv.",
                ">1d::.^a-a-a-ax-..a&<..",
                ".v.<cS.dSaSbdWbaL<vc?<<",
                "..^..a+aPc0d0<>..^>..v.",
                ".>v.>..+yd?yc^^.>...v&.",
                "v<..^ay+cy-.aPdP..cP<b.",
                "@..^.bdWbaL....<^cx?<..",
                "c.>.+xa+xd-xc.......^:.",
                "d^<.vd0.....cab~b+by+<.",
                ">v.vb-b0bP<^b?b-..<.<..",
                "d..S>PbSb?b^>-b?bv^.^..",
                "c.^b.............<.....",
                "@>...................:^",
                "^..<..................."]
            with open('initial.gen', 'w') as f:
                for line in genome:
                    f.write(line + '\n')
            print("Created initial.gen with large genome")

    def run(self):
        self.visualizer.main_loop(self)

    def load_genome_into_memory(self, filename: str, address: np.array) -> np.array:
        try:
            with open(filename) as genome_file:
                lines = [line.strip() for line in genome_file if line.strip()]
                max_width = max(len(line) for line in lines) if lines else 1
                genome = np.full((len(lines), max_width), '.', dtype=str)
                for i, line in enumerate(lines):
                    for j, char in enumerate(line):
                        genome[i, j] = char
            m.memory.load_genome(genome, address, genome.shape)
            print(f"Loaded genome of size {genome.shape} at position {address}")
            return genome.shape
        except Exception as e:
            print(f"Error loading genome: {e}")
            genome = np.array([['1', 'a'], ['^', '.']], dtype=str)
            m.memory.load_genome(genome, address, genome.shape)
            return genome.shape

    def update_position(self, delta):
        m.memory.scroll(delta)
        q.queue.update_all()
        self.update_info()

    def update_info_full(self):
        try:
            self.visualizer.info_window.erase()
            info = ''
            info += '[{}]           \n'.format(c.config['simulation_name'])
            info += 'Cycle      : {}\n'.format(self.cycle)
            info += 'Position   : {}\n'.format(list(m.memory.position))
            info += 'Total      : {}\n'.format(len(q.queue.organisms))
            info += 'Purges     : {}\n'.format(self.purges)
            info += 'Organism   : {}\n'.format(q.queue.index)
            if q.queue.organisms:
                info += q.queue.get_organism().info()
            self.visualizer.info_window.print(info)
        except Exception as e:
            print(f"Error updating info: {e}")

    def update_info_minimal(self):
        try:
            self.visualizer.info_window.erase()
            info = ''
            info += 'Minimal mode '
            info += '[Running]\n' if c.config.get('is_running', False) else '[Paused]\n'
            info += 'Cycle      : {}\n'.format(self.cycle)
            info += 'Total      : {}\n'.format(len(q.queue.organisms))
            self.visualizer.info_window.print(info)
        except Exception as e:
            print(f"Error updating minimal info: {e}")

    def update_info(self):
        if not self.is_minimal:
            self.update_info_full()
        elif self.cycle % c.config['cycle_gap'] == 0:
            self.update_info_minimal()

    def toogle_minimal(self, memory=None):
        self.is_minimal = not self.is_minimal
        self.update_info_minimal()
        m.memory.clear()
        m.memory = m.memory.toogle() if memory is None else memory.toogle()
        m.memory.update(refresh=True)
        q.queue.toogle_minimal()

    def save_state(self, from_timer=False):
        try:
            return_to_full = False
            if not self.is_minimal:
                if from_timer:
                    return
                self.toogle_minimal()
                return_to_full = True
            os.makedirs('snapshots', exist_ok=True)
            filename = 'snapshots/{}_cycle_{}.snapshot'.format(
                c.config['simulation_name'].lower().replace(' ', '_'), self.cycle)
            with open(filename, 'wb') as f:
                state = {'cycle': self.cycle, 'memory': m.memory, 'queue': q.queue}
                pickle.dump(state, f)
            if not self.is_minimal or return_to_full:
                self.toogle_minimal()
        except Exception as e:
            print(f"Error saving state: {e}")

    def load_state(self):
        try:
            return_to_full = False
            if not self.is_minimal:
                self.toogle_minimal()
                return_to_full = True
            if c.config['snapshot_to_load'] in ('last', 'new'):
                snapshots = glob.glob('snapshots/*')
                if snapshots:
                    filename = max(snapshots, key=os.path.getctime)
                else:
                    return
            else:
                filename = c.config['snapshot_to_load']
            with open(filename, 'rb') as f:
                state = pickle.load(f)
                memory = state['memory']
                q.queue = state['queue']
                self.cycle = state['cycle']
            if not self.is_minimal or return_to_full:
                self.toogle_minimal(memory)
            else:
                m.memory = memory
                self.update_info_minimal()
        except Exception as e:
            print(f"Error loading state: {e}")

    def make_cycle(self):
        try:
            if self.cycle % c.config['random_rate'] == 0:
                m.memory.cycle()
            if self.cycle % c.config['cycle_gap'] == 0 and m.memory.is_time_to_kill():
                q.queue.kill_organisms()
                self.purges += 1
            if not self.is_minimal:
                q.queue.update_all()
            self.cycle += 1
            self.update_info()
        except Exception as e:
            print(f"Error in make_cycle: {e}")

if __name__ == '__main__':
    try:
        Fungera().run()
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()


import numpy as np
import argparse
from threading import Thread, Event

instructions = {
    '.': [np.array([0, 0]), 'no_operation'],
    ':': [np.array([0, 1]), 'no_operation'],
    'a': [np.array([1, 0]), 'no_operation'],
    'b': [np.array([1, 1]), 'no_operation'],
    'c': [np.array([1, 2]), 'no_operation'],
    'd': [np.array([1, 3]), 'no_operation'],
    'x': [np.array([2, 0]), 'no_operation'],
    'y': [np.array([2, 1]), 'no_operation'],
    '^': [np.array([3, 0]), 'move_up'],
    'v': [np.array([3, 1]), 'move_down'],
    '>': [np.array([3, 2]), 'move_right'],
    '<': [np.array([3, 3]), 'move_left'],
    '&': [np.array([4, 0]), 'find_template'],
    '?': [np.array([5, 0]), 'if_not_zero'],
    '1': [np.array([6, 0]), 'one'],
    '0': [np.array([6, 1]), 'zero'],
    '-': [np.array([6, 2]), 'decrement'],
    '+': [np.array([6, 3]), 'increment'],
    '~': [np.array([6, 4]), 'subtract'],
    'L': [np.array([7, 0]), 'load_inst'],
    'W': [np.array([7, 1]), 'write_inst'],
    '@': [np.array([7, 2]), 'allocate_child'],
    '$': [np.array([7, 3]), 'split_child'],
    'S': [np.array([8, 0]), 'push'],
    'P': [np.array([8, 1]), 'pop']}

deltas = {
    'left': np.array([0, -1]),
    'right': np.array([0, 1]),
    'up': np.array([-1, 0]),
    'down': np.array([1, 0])}

colors = {
    'parent_bold': 1,
    'child_bold': 2,
    'ip_bold': 3,
    'parent': 4,
    'child': 5,
    'ip': 6}

parser = argparse.ArgumentParser(description='Fungera - two-dimensional artificial life simulator')
parser.add_argument('--name', default='Simulation 1', help='Simulation name')
parser.add_argument('--state', default='new', help='State file to load (new/last/filename)')
line_args = parser.parse_args()

config = {
    'simulation_name': line_args.name,
    'snapshot_to_load': line_args.state,
    'memory_size': np.array([128, 128]),
    'random_seed': 42,
    'autosave_rate': [60, 1],
    'cycle_gap': 5,
    'random_rate': 7,
    'memory_full_ratio': 0.7,
    'kill_organisms_ratio': 0.3,
    'is_running': True,
    'memory_display_size': [200, 200],
    'info_display_size': [30, 25],
    'cell_size': 4,
    'scroll_step': 50,
    'stack_length': 8,
    'organism_death_rate': 100,
    'kill_if_no_child': 25000,
    'penalize_parasitism': 100}

class RepeatedTimer(Thread):
    def __init__(self, interval, function, args=None, kwargs=None):
        Thread.__init__(self)
        self.interval = interval
        self.function = function
        self.args = args if args is not None else []
        self.kwargs = kwargs if kwargs is not None else {}
        self.finished = Event()
        self.start()

    def cancel(self):
        self.finished.set()

    def run(self):
        while not self.finished.wait(self.interval[0]):
            if not self.finished.is_set():
                self.function(*self.args, **self.kwargs)
                self.interval[0] *= self.interval[1]
        self.finished.set()


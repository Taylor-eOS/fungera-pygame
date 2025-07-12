import numpy as np
import common as c

class WindowStub:
    def __init__(self):
        pass

    def derived(self, start, size):
        return self

    def background(self, color):
        return self

class Memory:
    def __init__(self, memory_map=None, allocation_map=None, position=None):
        memory_size = c.config['memory_size']
        if memory_map is None:
            memory_map = np.full(memory_size, '.', dtype=str)
        if allocation_map is None:
            allocation_map = np.zeros(memory_size, dtype=int)
        if position is None:
            position = memory_size // 2
        self.memory_map = memory_map
        self.allocation_map = allocation_map
        self.position = position
        self.size = np.array([200, 200])
        self.window = WindowStub()

    def is_time_to_kill(self):
        used = np.count_nonzero(self.allocation_map)
        total = self.allocation_map.size
        return (used / total) > c.config['memory_full_ratio']

    def is_allocated_region(self, address: np.array, size: np.array):
        memory_size = c.config['memory_size']
        if (address < 0).any():
            return None
        if (address + size > memory_size).any():
            return None
        y0, x0 = address
        y1, x1 = y0 + size[0], x0 + size[1]
        region = self.allocation_map[y0:y1, x0:x1]
        return bool(np.count_nonzero(region))

    def is_allocated(self, address: np.array):
        memory_size = c.config['memory_size']
        if (address < 0).any() or (address >= memory_size).any():
            return False
        y, x = address
        return bool(self.allocation_map[y, x])

    def allocate(self, address: np.array, size: np.array):
        memory_size = c.config['memory_size']
        if (address < 0).any() or (address + size > memory_size).any():
            return
        y0, x0 = address
        y1, x1 = y0 + size[0], x0 + size[1]
        self.allocation_map[y0:y1, x0:x1] = 1

    def deallocate(self, address: np.array, size: np.array):
        memory_size = c.config['memory_size']
        if (address < 0).any() or (address + size > memory_size).any():
            return
        y0, x0 = address
        y1, x1 = y0 + size[0], x0 + size[1]
        self.allocation_map[y0:y1, x0:x1] = 0

    def inst(self, address: np.array):
        memory_size = c.config['memory_size']
        if (address < 0).any() or (address >= memory_size).any():
            return '.'
        y, x = address
        return self.memory_map[y, x]

    def write_inst(self, address: np.array, value):
        memory_size = c.config['memory_size']
        if (address < 0).any() or (address >= memory_size).any():
            return
        y, x = address
        instruction_chars = list(c.instructions.keys())
        if hasattr(value, '__iter__') and len(value) > 0:
            char_index = int(value[0]) % len(instruction_chars)
            self.memory_map[y, x] = instruction_chars[char_index]
        else:
            char_index = int(value) % len(instruction_chars)
            self.memory_map[y, x] = instruction_chars[char_index]

    def cycle(self):
        memory_size = c.config['memory_size']
        max_y, max_x = memory_size
        y = np.random.randint(0, max_y)
        x = np.random.randint(0, max_x)
        self.memory_map[y, x] = np.random.choice(list(c.instructions.keys()))

    def get_grid(self):
        return self.memory_map

    def load_genome(self, genome: np.array, address: np.array, size: np.array):
        memory_size = c.config['memory_size']
        y0, x0 = address
        y1, x1 = y0 + size[0], x0 + size[1]
        if y1 <= memory_size[0] and x1 <= memory_size[1]:
            self.memory_map[y0:y1, x0:x1] = genome

    def clear(self):
        pass

    def update(self, refresh=True):
        pass

    def scroll(self, delta: np.array):
        memory_size = c.config['memory_size']
        new = self.position + delta
        max_y, max_x = memory_size
        h, w = self.size
        self.position = np.minimum(np.maximum(new, 0), [max_y - h, max_x - w])

    def toogle(self):
        return self

memory = Memory()


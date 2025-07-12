import numpy as np
import uuid
from copy import copy
import common as c
import memory as m
import queue as q

class RegsDict(dict):
    allowed_keys = ['a', 'b', 'c', 'd']

    def __setitem__(self, key, value):
        if key not in self.allowed_keys:
            raise ValueError
        super().__setitem__(key, value)

class Organism:
    def __init__(
        self,
        address: np.array,
        size: np.array,
        ip: np.array = None,
        delta: np.array = None,
        start: np.array = None,
        regs: RegsDict = None,
        stack: list = None,
        errors: int = 0,
        child_size: np.array = None,
        child_start: np.array = None,
        is_selected: bool = False,
        children: int = 0,
        reproduction_cycle: int = 0,
        parent: uuid.UUID = None,
        organism_id: uuid.UUID = None,):
        self.organism_id = uuid.uuid4() if organism_id is None else organism_id
        self.parent = parent
        if address is not None:
            address = np.array(address)
        self.ip = np.array(address) if ip is None and address is not None else (ip if ip is not None else np.array([0, 0]))
        self.delta = delta if delta is not None else np.array([0, 1])
        self.size = np.array(size)
        self.start = np.array(address) if start is None and address is not None else (start if start is not None else np.array([0, 0]))
        self.regs = regs if regs is not None else RegsDict({
            'a': np.array([0, 0]),
            'b': np.array([0, 0]),
            'c': np.array([0, 0]),
            'd': np.array([0, 0]),})
        self.stack = stack if stack is not None else []
        self.errors = errors
        self.child_size = child_size if child_size is not None else np.array([0, 0])
        self.child_start = child_start if child_start is not None else np.array([0, 0])
        self.is_selected = is_selected
        self.reproduction_cycle = reproduction_cycle
        self.children = children
        if address is not None:
            m.memory.allocate(address, self.size)
        q.queue.add_organism(self)
        if start is None and address is not None:
            q.queue.archive.append(copy(self))
        self.mods = {'x': 0, 'y': 1}

    def no_operation(self):
        pass

    def move_up(self):
        self.delta = c.deltas['up']

    def move_down(self):
        self.delta = c.deltas['down']

    def move_right(self):
        self.delta = c.deltas['right']

    def move_left(self):
        self.delta = c.deltas['left']

    def ip_offset(self, offset: int = 0) -> np.array:
        return self.ip + offset * self.delta

    def inst(self, offset: int = 0) -> str:
        return m.memory.inst(self.ip_offset(offset))

    def find_template(self):
        try:
            register = self.inst(1)
            if register not in self.regs:
                return
            template = []
            max_size = min(max(self.size), 100)  
            for i in range(2, max_size):
                inst_char = self.inst(i)
                if inst_char in ['.', ':']:
                    template.append(':' if inst_char == '.' else '.')
                else:
                    break
            if not template:
                return
            counter = 0
            for i in range(i, max_size):
                if self.inst(i) == template[counter]:
                    counter += 1
                else:
                    counter = 0
                if counter == len(template):
                    self.regs[register] = self.ip + i * self.delta
                    break
        except:
            pass

    def if_not_zero(self):
        try:
            if self.inst(1) in self.mods.keys():
                reg_name = self.inst(2)
                if reg_name in self.regs:
                    value = self.regs[reg_name][self.mods[self.inst(1)]]
                    start_from = 1
                else:
                    return
            else:
                reg_name = self.inst(1)
                if reg_name in self.regs:
                    value = self.regs[reg_name]
                    start_from = 0
                else:
                    return
            if not np.any(value):
                self.ip = self.ip_offset(start_from + 1)
            else:
                self.ip = self.ip_offset(start_from + 2)
        except:
            pass

    def increment(self):
        try:
            if self.inst(1) in self.mods.keys():
                reg_name = self.inst(2)
                if reg_name in self.regs:
                    self.regs[reg_name][self.mods[self.inst(1)]] += 1
            else:
                reg_name = self.inst(1)
                if reg_name in self.regs:
                    self.regs[reg_name] += 1
        except:
            pass

    def decrement(self):
        try:
            if self.inst(1) in self.mods.keys():
                reg_name = self.inst(2)
                if reg_name in self.regs:
                    self.regs[reg_name][self.mods[self.inst(1)]] -= 1
            else:
                reg_name = self.inst(1)
                if reg_name in self.regs:
                    self.regs[reg_name] -= 1
        except:
            pass

    def zero(self):
        try:
            reg_name = self.inst(1)
            if reg_name in self.regs:
                self.regs[reg_name] = np.array([0, 0])
        except:
            pass

    def one(self):
        try:
            reg_name = self.inst(1)
            if reg_name in self.regs:
                self.regs[reg_name] = np.array([1, 1])
        except:
            pass

    def subtract(self):
        try:
            reg1 = self.inst(1)
            reg2 = self.inst(2)
            reg3 = self.inst(3)
            if all(reg in self.regs for reg in [reg1, reg2, reg3]):
                self.regs[reg3] = self.regs[reg1] - self.regs[reg2]
        except:
            pass

    def allocate_child(self):
        try:
            reg1 = self.inst(1)
            reg2 = self.inst(2)
            if reg1 not in self.regs or reg2 not in self.regs:
                return
            size = np.copy(self.regs[reg1])
            if (size <= 0).any():
                return
            max_search = min(max(c.config['memory_size']), 100)
            is_space_found = False
            for i in range(2, max_search):
                test_pos = self.ip_offset(i)
                is_allocated_region = m.memory.is_allocated_region(test_pos, size)
                if is_allocated_region is None:
                    break
                if not is_allocated_region:
                    self.child_start = test_pos
                    self.regs[reg2] = np.copy(self.child_start)
                    is_space_found = True
                    break
            if is_space_found:
                self.child_size = np.copy(size)
                m.memory.allocate(self.child_start, self.child_size)
        except:
            pass

    def load_inst(self):
        try:
            reg1 = self.inst(1)
            reg2 = self.inst(2)
            if reg1 in self.regs and reg2 in self.regs:
                inst_char = m.memory.inst(self.regs[reg1])
                if inst_char in c.instructions:
                    self.regs[reg2] = c.instructions[inst_char][0]
        except:
            pass

    def write_inst(self):
        try:
            if not np.array_equal(self.child_size, np.array([0, 0])):
                reg1 = self.inst(1)
                reg2 = self.inst(2)
                if reg1 in self.regs and reg2 in self.regs:
                    m.memory.write_inst(self.regs[reg1], self.regs[reg2])
        except:
            pass

    def push(self):
        try:
            if len(self.stack) < c.config['stack_length']:
                reg_name = self.inst(1)
                if reg_name in self.regs:
                    self.stack.append(np.copy(self.regs[reg_name]))
        except:
            pass

    def pop(self):
        try:
            if self.stack:
                reg_name = self.inst(1)
                if reg_name in self.regs:
                    self.regs[reg_name] = np.copy(self.stack.pop())
        except:
            pass

    def split_child(self):
        try:
            if not np.array_equal(self.child_size, np.array([0, 0])):
                m.memory.deallocate(self.child_start, self.child_size)
                self.__class__(self.child_start, self.child_size, parent=self.organism_id)
                self.children += 1
                self.reproduction_cycle = 0
            self.child_size = np.array([0, 0])
            self.child_start = np.array([0, 0])
        except:
            pass

    def __lt__(self, other):
        return self.errors < other.errors

    def kill(self):
        try:
            m.memory.deallocate(self.start, self.size)
            self.size = np.array([0, 0])
            if not np.array_equal(self.child_size, np.array([0, 0])):
                m.memory.deallocate(self.child_start, self.child_size)
            self.child_size = np.array([0, 0])
        except:
            pass

    def cycle(self):
        try:
            current_inst = self.inst()
            if current_inst in c.instructions:
                method_name = c.instructions[current_inst][1]
                if hasattr(self, method_name):
                    getattr(self, method_name)()
            if (c.config['penalize_parasitism'] and 
                not m.memory.is_allocated(self.ip) and
                max(np.abs(self.ip - self.start)) > c.config['penalize_parasitism']):
                raise ValueError("Parasitism penalty")
        except Exception:
            self.errors += 1
        new_ip = self.ip + self.delta
        self.reproduction_cycle += 1
        if (self.errors > c.config['organism_death_rate'] or
            self.reproduction_cycle > c.config['kill_if_no_child']):
            if self in q.queue.organisms:
                q.queue.organisms.remove(self)
            self.kill()
            return
        if (new_ip < 0).any() or (new_ip >= c.config['memory_size']).any():
            return
        self.ip = np.copy(new_ip)

    def update(self):
        pass

    def toggle(self):
        OrganismFull(
            address=None,
            size=self.size,
            ip=self.ip,
            delta=self.delta,
            start=self.start,
            regs=self.regs,
            stack=self.stack,
            errors=self.errors,
            child_size=self.child_size,
            child_start=self.child_start,
            is_selected=self.is_selected,
            children=self.children,
            reproduction_cycle=self.reproduction_cycle,
            parent=self.parent,
            organism_id=self.organism_id,)

class OrganismFull(Organism):
    def __init__(
        self,
        address: np.array,
        size: np.array,
        ip: np.array = None,
        delta: np.array = None,
        start: np.array = None,
        regs: RegsDict = None,
        stack: list = None,
        errors: int = 0,
        child_size: np.array = None,
        child_start: np.array = None,
        is_selected: bool = False,
        children: int = 0,
        reproduction_cycle: int = 0,
        parent: uuid.UUID = None,
        organism_id: uuid.UUID = None,):

        super(OrganismFull, self).__init__(
            address=address,
            size=size,
            ip=ip,
            delta=delta,
            start=start,
            regs=regs,
            stack=stack,
            errors=errors,
            child_size=child_size,
            child_start=child_start,
            is_selected=is_selected,
            children=children,
            reproduction_cycle=reproduction_cycle,
            parent=parent,
            organism_id=organism_id,)
        self.update()

    def update_window(self, size, start, color):
        try:
            new_start = start - m.memory.position
            new_size = size + new_start.clip(max=0)
            if (new_size > 0).all() and (m.memory.size - new_start > 0).all():
                m.memory.window.derived(
                    new_start.clip(min=0),
                    np.amin([new_size, m.memory.size - new_start, m.memory.size], axis=0),
                ).background(color)
        except:
            pass

    def update_ip(self):
        try:
            new_position = self.ip - m.memory.position
            color = c.colors['ip_bold'] if self.is_selected else c.colors['ip']
            if ((new_position >= 0).all() and 
                (m.memory.size - new_position > 0).all() and
                m.memory.is_allocated(self.ip)):
                m.memory.window.derived(new_position, (1, 1)).background(color)
        except:
            pass

    def update(self):
        try:
            parent_color = c.colors['parent_bold'] if self.is_selected else c.colors['parent']
            self.update_window(self.size, self.start, parent_color)
            child_color = c.colors['child_bold'] if self.is_selected else c.colors['child']
            self.update_window(self.child_size, self.child_start, child_color)
            self.update_ip()
        except:
            pass

    def info(self):
        try:
            info = ''
            info += '  errors   : {}\n'.format(self.errors)
            info += '  ip       : {}\n'.format(list(self.ip))
            info += '  delta    : {}\n'.format(list(self.delta))
            for reg in self.regs:
                info += '  r{}       : {}\n'.format(reg, list(self.regs[reg]))
            for i in range(len(self.stack)):
                info += '  stack[{}] : {}\n'.format(i, list(self.stack[i]))
            for i in range(len(self.stack), c.config['stack_length']):
                info += '  stack[{}] : \n'.format(i)
            return info
        except:
            return "Error displaying info\n"

    def kill(self):
        super(OrganismFull, self).kill()
        self.update()
        m.memory.update(refresh=True)

    def toggle(self):
        Organism(
            address=None,
            size=self.size,
            ip=self.ip,
            delta=self.delta,
            start=self.start,
            regs=self.regs,
            stack=self.stack,
            errors=self.errors,
            child_size=self.child_size,
            child_start=self.child_start,
            is_selected=self.is_selected,
            children=self.children,
            reproduction_cycle=self.reproduction_cycle,
            parent=self.parent,
            organism_id=self.organism_id,)


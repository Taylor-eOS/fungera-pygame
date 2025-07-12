import numpy as np
from copy import copy
import common as c

class Queue:
    def __init__(self):
        self.organisms = []
        self.archive = []
        self.index = None

    def add_organism(self, organism):
        self.organisms.append(organism)
        if self.index is None:
            self.index = 0
            self.organisms[self.index].is_selected = True

    def get_organism(self):
        try:
            return self.organisms[self.index]
        except (IndexError, TypeError):
            if not self.organisms:
                raise Exception('No more organisms alive!')
            return self.organisms[0]

    def select_next(self):
        if self.index is not None and self.index + 1 < len(self.organisms):
            self.organisms[self.index].is_selected = False
            self.organisms[self.index].update()
            self.index += 1
            self.organisms[self.index].is_selected = True
            self.organisms[self.index].update()

    def select_previous(self):
        if self.index is not None and self.index - 1 >= 0:
            self.organisms[self.index].is_selected = False
            self.organisms[self.index].update()
            self.index -= 1
            self.organisms[self.index].is_selected = True
            self.organisms[self.index].update()

    def cycle_all(self):
        for organism in copy(self.organisms):
            organism.cycle()

    def kill_organisms(self):
        if not self.organisms:
            return
        sorted_organisms = sorted(self.organisms, reverse=True)
        ratio = max(1, int(len(self.organisms) * c.config['kill_organisms_ratio']))
        for organism in sorted_organisms[:ratio]:
            organism.kill()
        self.organisms = sorted_organisms[ratio:]
        if self.index is not None and self.index >= len(self.organisms):
            self.index = max(0, len(self.organisms) - 1) if self.organisms else None

    def update_all(self):
        for organism in copy(self.organisms):
            organism.update()

    def toogle_minimal(self):
        organisms = self.organisms
        self.organisms = []
        for organism in organisms:
            organism.toogle()

    def info_text(self, cycle, purges):
        import memory as m
        lines = []
        lines.append(f"[{c.config['simulation_name']}]")
        lines.append(f"Cycle      : {cycle}")
        lines.append(f"Position   : {list(m.memory.position)}")
        lines.append(f"Total      : {len(self.organisms)}")
        lines.append(f"Purges     : {purges}")
        lines.append(f"Organism   : {self.index}")
        if self.organisms:
            lines.append(self.get_organism().info())
        return "\n".join(lines)

queue = Queue()


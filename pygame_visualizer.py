import pygame
import sys

class InfoWindow:
    def __init__(self):
        self.text = ""
    
    def erase(self):
        self.text = ""
    
    def print(self, text):
        self.text = text
    
    def get_text(self):
        return self.text

class PygameVisualizer:
    def __init__(self, memory, queue, config):
        pygame.init()
        self.memory = memory
        self.queue = queue
        self.config = config
        self.cell_size = config.get('cell_size', 4)
        mem_display_h, mem_display_w = config.get('memory_display_size', [200, 200])
        info_w, info_h = config.get('info_display_size', [30, 25])
        width = mem_display_w * self.cell_size + info_w * self.cell_size
        height = max(mem_display_h * self.cell_size, info_h * self.cell_size)
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption(config.get('simulation_name', 'Fungera'))
        self.font = pygame.font.SysFont('Consolas', self.cell_size * 2)
        self.colors = {
            27: (0, 95, 255),
            33: (0, 135, 255),
            117: (95, 135, 215),
            126: (95, 175, 215),
            128: (0, 135, 0),
            160: (215, 0, 0),
            'bg': (0, 0, 0),
            'text': (200, 200, 200),}
        self.clock = pygame.time.Clock()
        self.is_running = False
        self.offset_x = 0
        self.offset_y = 0
        self.info_window = InfoWindow()

    def draw_memory(self):
        grid = self.memory.get_grid()
        h, w = grid.shape
        mem_display_h, mem_display_w = self.config.get('memory_display_size', [200, 200])
        for y in range(mem_display_h):
            for x in range(mem_display_w):
                grid_y = y + self.offset_y
                grid_x = x + self.offset_x
                if 0 <= grid_y < h and 0 <= grid_x < w:
                    val = ord(grid[grid_y, grid_x]) if isinstance(grid[grid_y, grid_x], str) else grid[grid_y, grid_x]
                    col = self.colors.get(val, self.colors['bg'])
                    rect = pygame.Rect(x * self.cell_size, y * self.cell_size, self.cell_size, self.cell_size)
                    pygame.draw.rect(self.screen, col, rect)

    def draw_info(self):
        info_text = self.info_window.get_text()
        if info_text:
            start_x = self.config.get('memory_display_size', [200, 200])[1] * self.cell_size + 5
            y = 5
            for line in info_text.splitlines():
                surf = self.font.render(line, False, self.colors['text'])
                self.screen.blit(surf, (start_x, y))
                y += self.cell_size * 2 + 2

    def handle_events(self):
        grid_h, grid_w = self.memory.get_grid().shape
        mem_display_h, mem_display_w = self.config.get('memory_display_size', [200, 200])
        scroll_step = self.config.get('scroll_step', 50)
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if ev.type == pygame.KEYDOWN:
                key = ev.key
                if key == pygame.K_SPACE:
                    self.is_running = not self.is_running
                if key == pygame.K_m:
                    self.caller.toogle_minimal()
                if key == pygame.K_p:
                    self.caller.save_state()
                if key == pygame.K_l:
                    self.caller.load_state()
                if not getattr(self.caller, 'is_minimal', False):
                    if key == pygame.K_LEFT:
                        self.offset_x = max(0, self.offset_x - scroll_step)
                    if key == pygame.K_RIGHT:
                        self.offset_x = min(max(0, grid_w - mem_display_w), self.offset_x + scroll_step)
                    if key == pygame.K_UP:
                        self.offset_y = max(0, self.offset_y - scroll_step)
                    if key == pygame.K_DOWN:
                        self.offset_y = min(max(0, grid_h - mem_display_h), self.offset_y + scroll_step)
                    if key == pygame.K_d:
                        self.queue.select_next()
                        if hasattr(self.caller, 'update_info'):
                            self.caller.update_info()
                    if key == pygame.K_a:
                        self.queue.select_previous()
                        if hasattr(self.caller, 'update_info'):
                            self.caller.update_info()
                if not self.is_running and key == pygame.K_c:
                    self.queue.cycle_all()
                    if hasattr(self.caller, 'make_cycle'):
                        self.caller.make_cycle()

    def main_loop(self, caller):
        self.caller = caller
        while True:
            self.handle_events()
            if self.is_running:
                self.queue.cycle_all()
                if hasattr(self.caller, 'make_cycle'):
                    self.caller.make_cycle()
            self.screen.fill(self.colors['bg'])
            self.draw_memory()
            self.draw_info()
            pygame.display.flip()
            self.clock.tick(50)


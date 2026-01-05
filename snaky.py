import curses
import random
import time
import heapq
import sys
import traceback
import argparse
import os
from collections import deque

FOOD_CHAR = '● '
HEAD_CHARS = {'U': '▲ ', 'D': '▼ ', 'L': '◀ ', 'R': '▶ '}
TAIL_CHAR = '▪ '
VISION_CHAR = '· '

SPEEDS = {
    "Normal": 0.05, "Fast": 0.03, "Insane": 0.01, "WTF": 0.0001
}
SPEED_LIST = ["Normal", "Fast", "Insane", "WTF"]

WIDE_RENDER = {'│': '│ ', '─': '──', '┌': '┌─', '┐': '┐ ', '└': '└─', '┘': '┘ '}
PIPE_MAP = {
    frozenset(['U', 'D']): '│', frozenset(['L', 'R']): '─',
    frozenset(['D', 'R']): '┌', frozenset(['D', 'L']): '┐',
    frozenset(['U', 'R']): '└', frozenset(['U', 'L']): '┘',
}

BANNER = [
    "███████╗███╗   ██╗ █████╗ ██╗  ██╗██╗   ██╗",
    "██╔════╝████╗  ██║██╔══██╗██║ ██╔╝╚██╗ ██╔╝",
    "███████╗██╔██╗ ██║███████║█████╔╝  ╚████╔╝ ",
    "╚════██║██║╚██╗██║██╔══██║██╔═██╗   ╚██╔╝  ",
    "███████║██║ ╚████║██║  ██║██║  ██╗   ██║   ",
    "╚══════╝╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   "
]

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

class PriorityQueue:
    def __init__(self):
        self.elements = []
    def empty(self):
        return len(self.elements) == 0
    def put(self, item, priority):
        heapq.heappush(self.elements, (priority, item))
    def get(self):
        return heapq.heappop(self.elements)[1]

class SnakeAI:
    def __init__(self, stdscr, args):
        self.stdscr = stdscr

        self.resolve_speed(args.speed)
        self.show_vision = args.vision
        self.hide_ui = args.hide_ui

        y, x = stdscr.getmaxyx()
        self.max_y = y
        self.max_x = x // 2

        if self.max_y < 10 or self.max_x < 10:
            raise Exception(f"Terminal too small! ({self.max_y}x{self.max_x})")

        self.play_top = 1
        self.play_bottom = self.max_y - 2
        self.grid_area = self.max_y * self.max_x

        playable_height = (self.play_bottom - self.play_top) + 1
        playable_width = (self.max_x - 2)
        self.playable_area = playable_height * playable_width
        self.start_length = 10

        self.dynamic_limit = max(4000, self.grid_area * 8)

        self.score = 0
        self.high_score = 0
        self.paused = False
        self.vision_path = []
        self.prev_vision_path = []

        self.stall_start_time = None

        self.head_history = deque(maxlen=200)

        self.game_over = False
        self.killer_pos = None
        self.reset(first_launch=True)

    def resolve_speed(self, arg_speed):
        lookup = {
            'n': 'Normal', 'normal': 'Normal',
            'f': 'Fast', 'fast': 'Fast',
            'i': 'Insane', 'insane': 'Insane',
            'w': 'WTF', 'wtf': 'WTF'
        }
        target = lookup.get(str(arg_speed).lower(), 'Normal')
        try:
            self.speed_idx = SPEED_LIST.index(target)
        except ValueError:
            self.speed_idx = 0
        self.update_speed()

    def update_speed(self):
        self.speed_name = SPEED_LIST[self.speed_idx]
        self.speed_delay = SPEEDS[self.speed_name]

    def change_speed(self, delta):
        new_idx = self.speed_idx + delta
        if 0 <= new_idx < len(SPEED_LIST):
            self.speed_idx = new_idx
            self.update_speed()

    def reset(self, first_launch=False):
        y, x = self.stdscr.getmaxyx()
        self.max_y = y
        self.max_x = x // 2

        self.play_top = 1
        self.play_bottom = self.max_y - 2

        playable_height = (self.play_bottom - self.play_top) + 1
        playable_width = (self.max_x - 2)
        self.playable_area = playable_height * playable_width

        self.grid_area = self.max_y * self.max_x
        self.dynamic_limit = max(4000, self.grid_area * 8)

        cy, cx = self.max_y // 2, self.max_x // 2
        self.body = [(cy, cx - i) for i in range(self.start_length)]
        self.food = self.spawn_food()
        self.alive = True
        self.status_msg = "Ready"
        self.score = 0
        self.head_history.clear()
        self.game_over = False
        self.killer_pos = None
        self.vision_path = []

        self.stall_start_time = None

        self.stdscr.clear()
        if not first_launch:
            pass

        self.draw_ui()
        self.draw_food()
        self.draw_full_snake()

    def print_centered(self, y, text, attr=0):
        try:
            screen_width = self.max_x * 2
            x = max(0, (screen_width // 2) - (len(text) // 2))
            if 0 <= y < self.max_y:
                self.stdscr.addstr(y, x, text, attr)
        except: pass

    def spawn_food(self):
        fill_ratio = len(self.body) / max(1, self.grid_area)
        pad = 2 if fill_ratio < 0.50 else 0

        attempts = 0
        while attempts < 500:
            attempts += 1
            min_y = self.play_top + pad
            max_y = self.play_bottom - pad
            min_x = 1 + pad
            max_x = self.max_x - 2 - pad

            if max_y <= min_y or max_x <= min_x:
                min_y, max_y = self.play_top, self.play_bottom
                min_x, max_x = 1, self.max_x - 2

            fy = random.randint(min_y, max_y)
            fx = random.randint(min_x, max_x)

            if (fy, fx) not in self.body:
                neighbors = self.get_neighbors((fy, fx), self.body)
                if len(neighbors) > 0:
                    return (fy, fx)
        return (self.play_top, 1)

    def heuristic_simple(self, a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def heuristic_hunt(self, a, b, obstacles_set=None):
        cost = abs(a[0] - b[0]) + abs(a[1] - b[1])
        if obstacles_set:
            y, x = a
            empty_neighbors = 0
            for dy, dx in [(-1,0), (1,0), (0,-1), (0,1)]:
                ny, nx = y + dy, x + dx
                if not (self.play_top <= ny <= self.play_bottom and 0 < nx < self.max_x - 1):
                    continue
                if (ny, nx) in obstacles_set:
                    continue
                empty_neighbors += 1
            cost += empty_neighbors * 1.5
        return cost

    def get_neighbors(self, node, body_obstacles):
        y, x = node
        neighbors = []
        obstacles_set = set(body_obstacles)
        for dy, dx in [(-1,0), (1,0), (0,-1), (0,1)]:
            ny, nx = y + dy, x + dx
            if self.play_top <= ny <= self.play_bottom and 0 < nx < self.max_x - 1:
                if (ny, nx) not in obstacles_set:
                    neighbors.append((ny, nx))
        return neighbors

    def a_star(self, start, goal, body_obstacles, max_steps=None, use_complex_heuristic=False):
        if max_steps is None: max_steps = self.dynamic_limit
        frontier = PriorityQueue()
        frontier.put(start, 0)
        came_from = {start: None}
        cost_so_far = {start: 0}

        obstacles_set = set(body_obstacles)
        steps = 0

        while not frontier.empty():
            steps += 1
            if steps > max_steps: break
            current = frontier.get()
            if current == goal: break

            y, x = current
            for dy, dx in [(-1,0), (1,0), (0,-1), (0,1)]:
                ny, nx = y + dy, x + dx
                if self.play_top <= ny <= self.play_bottom and 0 < nx < self.max_x - 1:
                    if (ny, nx) not in obstacles_set:
                        new_cost = cost_so_far[current] + 1
                        if (ny, nx) not in cost_so_far or new_cost < cost_so_far[(ny, nx)]:
                            cost_so_far[(ny, nx)] = new_cost
                            if use_complex_heuristic:
                                priority = new_cost + self.heuristic_hunt(goal, (ny, nx), obstacles_set)
                            else:
                                priority = new_cost + self.heuristic_simple(goal, (ny, nx))
                            frontier.put((ny, nx), priority)
                            came_from[(ny, nx)] = current

        if goal not in came_from: return None
        path = []
        current = goal
        while current != start:
            path.append(current)
            current = came_from[current]
        path.reverse()
        return path

    def flood_fill(self, start, body_obstacles, max_depth=None):
        if max_depth is None: max_depth = self.grid_area
        queue = deque([start])
        visited = {start}
        count = 0
        obstacles_set = set(body_obstacles)
        while queue:
            curr = queue.popleft()
            count += 1
            if count >= max_depth: return count
            for n in self.get_neighbors(curr, []):
                if n not in obstacles_set and n not in visited:
                    visited.add(n)
                    queue.append(n)
        return count

    def is_move_safe(self, move):
        virtual_body = list(self.body)
        virtual_body.insert(0, move)
        if move == self.food: pass
        else: virtual_body.pop()
        future_head = virtual_body[0]
        future_tail = virtual_body[-1]
        future_obstacles = virtual_body[:-1]
        if self.a_star(future_head, future_tail, future_obstacles, max_steps=self.dynamic_limit, use_complex_heuristic=False):
            return True
        return False

    def is_path_fully_safe(self, path):
        if not path: return False
        virtual_body = list(self.body)
        for step in path:
            virtual_body.insert(0, step)
            if step != self.food: virtual_body.pop()
        virtual_head = virtual_body[0]
        virtual_tail = virtual_body[-1]
        virtual_obstacles = virtual_body[:-1]
        check_path = self.a_star(virtual_head, virtual_tail, virtual_obstacles, max_steps=self.dynamic_limit, use_complex_heuristic=False)
        return True if check_path else False

    def get_ai_move(self):
        head = self.body[0]
        self.head_history.append(head)
        self.vision_path = []

        path_to_food = self.a_star(head, self.food, self.body[:-1], max_steps=self.dynamic_limit, use_complex_heuristic=True)
        if path_to_food:
            if self.is_path_fully_safe(path_to_food):
                self.status_msg = "Hunting (Aggressive)"
                self.vision_path = path_to_food
                return path_to_food[0]

        neighbors = self.get_neighbors(head, self.body[:-1])
        neighbors.sort(key=lambda n: self.heuristic_simple(n, self.food))

        for n in neighbors:
            detour_path = self.a_star(n, self.food, self.body[:-1], max_steps=self.dynamic_limit, use_complex_heuristic=True)
            if detour_path:
                full_detour = [n] + detour_path
                if self.is_path_fully_safe(full_detour):
                    self.status_msg = "Hunting (Detour)"
                    return n

        safe_moves = [n for n in neighbors if self.is_move_safe(n)]
        if safe_moves:
            best_move = None
            max_space = -1
            for move in safe_moves:
                space_available = self.flood_fill(move, self.body[:-1])
                if space_available > max_space:
                    max_space = space_available
                    best_move = move
                elif space_available == max_space:
                    d_tail_current = self.heuristic_simple(best_move, self.body[-1])
                    d_tail_new = self.heuristic_simple(move, self.body[-1])
                    if d_tail_new > d_tail_current:
                        best_move = move
            self.status_msg = f"Stalling (Space: {max_space})"
            return best_move

        if neighbors:
            self.status_msg = "Panic!"
            return max(neighbors, key=lambda n: self.flood_fill(n, self.body[:-1]))
        self.status_msg = "Accepting Fate"
        return None

    def get_render_char(self, curr, prev, nxt):
        y, x = curr
        if prev is None:
            if not nxt: return "O "
            ny, nx = nxt
            if ny < y: return HEAD_CHARS['D']
            if ny > y: return HEAD_CHARS['U']
            if nx < x: return HEAD_CHARS['R']
            if nx > x: return HEAD_CHARS['L']
        if nxt is None: return TAIL_CHAR
        neighbors = []
        for node in [prev, nxt]:
            ny, nx = node
            if ny < y: neighbors.append('U')
            elif ny > y: neighbors.append('D')
            elif nx < x: neighbors.append('L')
            elif nx > x: neighbors.append('R')
        base = PIPE_MAP.get(frozenset(neighbors), ' ')
        return WIDE_RENDER.get(base, '  ')

    def erase_at(self, y, x):
        try: self.stdscr.addstr(y, x * 2, "  ")
        except: pass

    def draw_segment(self, i):
        y, x = self.body[i]
        attr = curses.color_pair(1)
        if i == 0: attr |= curses.A_BOLD
        if self.game_over and (y, x) == self.killer_pos: attr = curses.color_pair(2) | curses.A_BOLD
        prev = self.body[i-1] if i > 0 else None
        nxt = self.body[i+1] if i < len(self.body) - 1 else None
        char = self.get_render_char((y, x), prev, nxt)
        try: self.stdscr.addstr(y, x * 2, char, attr)
        except: pass

    def draw_full_snake(self):
        for i in range(len(self.body)): self.draw_segment(i)

    def draw_food(self):
        try: self.stdscr.addstr(self.food[0], self.food[1] * 2, FOOD_CHAR, curses.color_pair(1) | curses.A_BOLD)
        except: pass

    def draw_ui(self):
        if self.hide_ui: return
        white = curses.color_pair(1)
        bold = white | curses.A_BOLD
        vision_state = "ON" if self.show_vision else "OFF"

        theoretical_max = self.playable_area - self.start_length
        stats = f" Speed: {self.speed_name} | Vision: {vision_state} | Score: {self.score} / Max: {theoretical_max} Best: {self.high_score}"

        self.print_centered(0, stats, bold)

        controls = " [▲/▼] Speed  [R] Reset  [SPACE] Pause  [V] Vision  [Q] Quit  [H] Hide UI "
        self.print_centered(self.max_y - 1, controls, white)

    def run(self):
        self.stdscr.clear()
        self.draw_ui()
        self.draw_food()
        self.draw_full_snake()
        last_score = -1
        while True:
            t0 = time.time()
            key = self.stdscr.getch()
            if key == ord('q') or key == ord('Q'): break
            elif key == ord('r') or key == ord('R'):
                if self.score > self.high_score:
                    self.high_score = self.score
                self.reset()
                continue

            if key == ord('h') or key == ord('H'):
                self.hide_ui = not self.hide_ui
                if self.hide_ui:
                    self.stdscr.move(0, 0)
                    self.stdscr.clrtoeol()
                    self.stdscr.move(self.max_y - 1, 0)
                    self.stdscr.clrtoeol()
                else:
                    self.draw_ui()

            if not self.game_over:
                if key == ord(' '):
                    self.paused = not self.paused
                    if self.paused: self.draw_ui()
                elif key == ord('v') or key == ord('V'):
                    self.show_vision = not self.show_vision
                    if not self.show_vision:
                          for vy, vx in self.vision_path:
                            if (vy, vx) != self.food and (vy, vx) not in self.body:
                                self.erase_at(vy, vx)
                    self.draw_ui()
                elif key == curses.KEY_UP: self.change_speed(1); self.draw_ui()
                elif key == curses.KEY_DOWN: self.change_speed(-1); self.draw_ui()

            sy, sx = self.stdscr.getmaxyx()
            if (sy, sx // 2) != (self.max_y, self.max_x): self.reset(); continue

            if not self.paused and not self.game_over:
                old_tail = self.body[-1]
                next_move = self.get_ai_move()

                if "Stalling" in self.status_msg or "Panic" in self.status_msg:
                    if self.stall_start_time is None:
                        self.stall_start_time = time.time()
                    elif time.time() - self.stall_start_time > 15:
                        if self.score > self.high_score:
                            self.high_score = self.score
                        self.reset()
                        continue
                else:
                    self.stall_start_time = None

                if next_move:
                    self.body.insert(0, next_move)
                    if next_move == self.food:
                        self.score += 1
                        self.food = self.spawn_food()
                    else:
                        self.body.pop()
                        if old_tail != next_move: self.erase_at(old_tail[0], old_tail[1])

                    if self.prev_vision_path:
                        for vy, vx in self.prev_vision_path:
                            if (vy, vx) != self.food and (vy, vx) not in self.body: self.erase_at(vy, vx)
                    if self.show_vision and self.vision_path:
                        for vy, vx in self.vision_path:
                             if (vy, vx) == self.food: continue
                             try: self.stdscr.addstr(vy, vx * 2, VISION_CHAR, curses.color_pair(3) | curses.A_BOLD)
                             except: pass
                        self.prev_vision_path = list(self.vision_path)
                    else: self.prev_vision_path = []

                    self.draw_segment(0)
                    if len(self.body) > 1: self.draw_segment(1)
                    if len(self.body) > 2: self.draw_segment(len(self.body) - 1)
                    self.draw_food()

                    if self.score != last_score:
                        self.draw_ui()
                        last_score = self.score
                else:
                    if self.score > self.high_score:
                        self.high_score = self.score
                    self.reset()
                    continue

            self.stdscr.refresh()
            dt = time.time() - t0
            if dt < self.speed_delay: time.sleep(self.speed_delay - dt)

def show_intro(stdscr):
    banner_width = max(len(line) for line in BANNER)
    while True:
        stdscr.clear()
        max_y, max_x = stdscr.getmaxyx()
        start_y = max(0, (max_y - (len(BANNER) + 4)) // 2)
        start_x = max(0, (max_x - banner_width) // 2)
        for i, line in enumerate(BANNER):
            try: stdscr.addstr(start_y + i, start_x, line, curses.color_pair(1) | curses.A_BOLD)
            except: pass
        prompt = "Press [ENTER] to Start"
        px = max(0, (max_x - len(prompt)) // 2)
        try: stdscr.addstr(start_y + len(BANNER) + 1, px, prompt, curses.color_pair(1) | curses.A_BOLD)
        except: pass
        stdscr.refresh()
        key = stdscr.getch()
        if key in [10, 13]: return
        elif key == ord('q'): sys.exit(0)
        elif key == curses.KEY_RESIZE: continue

def print_help_and_exit():
    clear_screen()
    help_text = """Usage:
  snaky [-s SPEED] [-v] [-u]
  snaky -h | --help

Flags:
  -s,  --speed SPEED    Set initial speed (default: Normal)
  -v,  --vision         Enable AI pathfinding vision
  -u,  --hide-ui        Start with UI hidden
  -h,  --help           Show this help and exit

Controls:
  [UP] / [DOWN]         Adjust speed dynamically
  [SPACE]               Pause or Resume
  [R]                   Reset game
  [V]                   Toggle AI vision
  [H]                   Toggle UI visibility
  [Q]                   Quit

Speed Options:
  n, normal             Standard pacing
  f, fast               Accelerated gameplay
  i, insane             High speed challenge
  w, wtf                Maximum velocity

Examples:
  snaky
  snaky -s fast -v
  snaky -s w -v -u
"""
    print(help_text)
    sys.exit(0)

def parse_arguments():
    if '-h' in sys.argv or '--help' in sys.argv:
        print_help_and_exit()

    parser = argparse.ArgumentParser(add_help=False)

    parser.add_argument('-s', '--speed', type=str, default='Normal')
    parser.add_argument('-u', '--hide-ui', action='store_true')
    parser.add_argument('-v', '--vision', action='store_true')

    return parser.parse_args()

def main(stdscr, args, skip_intro):
    try:
        curses.start_color()
        try:
            curses.use_default_colors()
            curses.init_pair(1, curses.COLOR_WHITE, -1)
            curses.init_pair(2, curses.COLOR_RED, -1)
            curses.init_pair(3, curses.COLOR_WHITE, -1)
        except:
            curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
            curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
            curses.init_pair(3, curses.COLOR_CYAN, curses.COLOR_BLACK)
    except: pass
    curses.curs_set(0)

    if not skip_intro:
        show_intro(stdscr)

    stdscr.nodelay(True)
    try:
        game = SnakeAI(stdscr, args)
        game.run()
    except Exception as e:
        stdscr.addstr(0, 0, f"Error: {e}")
        stdscr.refresh()
        time.sleep(3)

if __name__ == "__main__":
    clear_screen()

    known_flags = {'-s', '--speed', '-v', '--vision', '-u', '--hide-ui'}
    has_args = any(arg in sys.argv for arg in known_flags)

    args = parse_arguments()

    try:
        curses.wrapper(main, args, has_args)
    except KeyboardInterrupt: pass
    except Exception:
        print(traceback.format_exc())

# Snaky

Snake that plays itself in the terminal. Uses A* pathfinding, a tail-reachability check, and flood-fill fallback moves. It can get stuck or lose; it does not follow a Hamiltonian cycle.

## Demo

<p align="center">
  <img src="./assets/demo.gif" alt="Snaky Demo">
</p>

## What it does

* Plays Snake completely on its own
* Uses A* pathfinding to reach food
* Simulates future states to avoid self-trapping
* Falls back to space-based movement when food is unsafe
* Renders using wide box-drawing characters
* Optional path “vision” overlay
* Speed can be changed while it’s running
* Zero external dependencies (on Linux)

## Pathfinding

Each move starts with an A* path to the food. Before taking it, the snake simulates the move and checks whether its head can still reach its tail.

If that path is unsafe, it uses flood fill to choose a neighboring tile with more open space. A game that stops making progress resets after 15 seconds.

## Installation

Snaky uses only the Python standard library.

```bash
# Clone the repository
git clone https://github.com/oNxZero/snaky.git

# Enter the directory
cd snaky

# Make executable (optional, Linux/macOS)
chmod +x snaky.py
```

### Windows note

Python on Windows doesn’t ship with `curses`.

```bash
pip install windows-curses
```

## Usage

```bash
python3 snaky.py
```

### Fast start (CLI flags)

```bash
# Normal speed with AI vision enabled
python3 snaky.py -s n -v

# Fast speed with AI vision and hidden UI
python3 snaky.py -s f -v -u
```

## Command line help

```bash
python3 snaky.py -h
```

```
Usage:
  snaky [-s SPEED] [-v] [-u]
  snaky -h | --help

Flags:
  -s,  --speed SPEED    Set initial speed (default: Normal)
  -v,  --vision         Enable AI pathfinding vision
  -u,  --hide-ui        Start with UI hidden

Speed options:
  n, normal             Normal speed
  f, fast               Fast speed
  i, insane             Higher speed
  w, wtf                Maximum speed

Examples:
  snaky
  snaky -s fast -v
  snaky -s w -v -u
```

## Controls

Make sure the terminal window is focused, then use these keys:

| Key | Action | Description |
| :--- | :--- | :--- |
| **[UP]** | **Increase Speed** | Speeds up the simulation. |
| **[DOWN]** | **Decrease Speed** | Slows the simulation. |
| **[SPACE]** | **Pause / Resume** | Pauses or resumes the simulation. |
| **[V]** | **Toggle Vision** | Shows or hides the AI path overlay. |
| **[H]** | **Toggle UI** | Hides or shows the status bar and controls. |
| **[R]** | **Reset** | Restarts the game from the beginning. |
| **[Q]** | **Quit** | Closes the script. |

## Configuration

Edit constants at the top of `snaky.py` to tweak visuals or speed.

```python
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
```

## License

Distributed under the MIT License. See `LICENSE` for more information.

# 🐍 Snaky: Terminal AI Snake

> **A zero-dependency Snake AI that plays itself in your terminal.**

![Python](https://img.shields.io/badge/Python-3.6%2B-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Dependencies](https://img.shields.io/badge/Dependencies-None-brightgreen)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)

I wanted something running in my terminal that wasn’t just static eye candy.

**Snaky** is an autonomous Snake implementation that uses real pathfinding to survive and grow.  
You don’t control the snake, you watch it make decisions, recover from bad situations, and occasionally fill most of the board.  
Not 100%, since it’s heuristic and intentionally **not Hamiltonian**.

It’s half terminal rice, half AI experiment.

---

## 📸 Demo

<p align="center">
  <img src="./assets/demo.gif" alt="Snaky Demo">
</p>

---

## 🎯 What it does

* Plays Snake completely on its own
* Uses A* pathfinding to reach food
* Simulates future states to avoid self-trapping
* Falls back to space-based movement when food is unsafe
* Renders using wide box-drawing characters
* Optional path “vision” overlay
* Speed can be changed while it’s running
* Zero external dependencies (on Linux)

---

## ✨ Why use this?

* No pip installs
* Runs in a normal terminal
* Not scripted or hardcoded
* Looks good while running in the background
* Surprisingly fun to watch for such a **simple** idea

---
## 🧠 How the AI behaves

The AI does not follow a fixed route and it does not rely on precomputed cycles.  
Every single move is decided in real time.

At a high level, each step works like this:

1. **Path to food**  
   The snake first tries to find the shortest path to the food using **A*** pathfinding.  
   This is the aggressive phase where the goal is simply to reach the food efficiently.

2. **Future safety check**  
   Before committing to that path, the AI simulates the move.  
   It checks whether, after taking the step (and possibly growing), the snake’s head can still reach its own tail.

   If the tail becomes unreachable, the path is rejected even if it leads directly to the food.

3. **Fallback: survive first**  
   If no safe path to food exists, the AI changes its goal.  
   Instead of chasing food, it evaluates the neighboring tiles and moves into the largest open area.

   This uses a flood-fill style space check and helps the snake avoid trapping itself while waiting for a better opportunity.

4. **Stall detection**  
   In rare cases, the snake can end up circling without making progress.  
   If that happens for too long, the game resets automatically after 15 seconds and starts fresh.

This approach does not guarantee a perfect clear. It is heuristic, not Hamiltonian and my logic probably isnt perfect either.  
The goal is clarity, adaptability to any board size, and behavior that is interesting to watch.

No hardcoded routes.  
No precomputed cycles.  
Just pathfinding and space awareness.

---

## 🚀 Installation

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

---

## 📖 Usage

```bash
python3 snaky.py
```

---

### ⚡ Fast start (CLI flags)

```bash
# Normal speed with AI vision enabled
python3 snaky.py -s n -v

# Fast speed with AI vision and hidden UI
python3 snaky.py -s f -v -u
```

---

## ⌨️ Command line help

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
  n, normal             Standard pacing
  f, fast               Accelerated gameplay
  i, insane             High speed challenge
  w, wtf                Maximum velocity

Examples:
  snaky
  snaky -s fast -v
  snaky -s w -v -u
```

---

## 🎮 Controls

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

---

## ⚙️ Configuration

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

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.

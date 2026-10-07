# Yurei

A 2D platformer written in C++ with SDL3.

## Controls

| Key | Action |
| --- | ------ |
| A / D | Move left / right |
| W | Jump |
| Space | Attack |

Jump and attack both require the player to be grounded. Attacking locks out
movement until the attack animation has played through once.

## Run

Requirements:

- CMake 3.16+
- A C++23 compiler
- Git

```bash
cmake -S . -B build
cmake --build build --config Debug
```

Run the game from the build output. For example on Windows:

```bash
./build/Debug/ledge.exe
```

If using Make, the executable is at `./build/ledge`.

## Assets

Sprites and tilesheets live in `assets/`. They are copied next to the
executable as a post-build step, and are loaded relative to the executable
rather than the working directory.

Player animation sheets are horizontal strips of 128x128 frames. The tileset
is an 8x8 grid of 32x32 tiles, and `Tile` in `src/tile.h` declares the
variants in the same row-major order the sheet is laid out in, so the enum
value of a tile doubles as its index into the sheet.

### Regenerating the tileset

`assets/tileset/Tiles.png` is generated rather than hand-drawn. Every tile is
drawn procedurally from a fixed palette and fixed seeds, so the output is
deterministic and a change to any tile function can be reviewed as a diff.

Requires Python 3 and Pillow:

```bash
pip install Pillow
python tools/gen_haunted_tileset.py
```

## Layout

| Path | Contents |
| ---- | -------- |
| `src/main.cpp` | Window setup, game loop, grid construction, player update and draw |
| `src/gameobject.h` | `GameObject` and the variant data it can hold |
| `src/animation.h` | Frame stepping on top of `Timer` |
| `src/timer.h` | Looping timer that carries leftover time into the next cycle |
| `src/tile.h` | Tile variants and their mapping into the tileset |
| `tools/` | Asset generation scripts |

The level is currently compiled into `createGrid()` in `src/main.cpp` as an
array of `Tile` values. There is no camera yet, so only the leftmost part of
the grid is reachable on screen.

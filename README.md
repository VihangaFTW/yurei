# Yurei

A 2D platformer written in C++ with SDL3.

## Controls

These are the movement currently available.

| Key | Action |
| --- | ------ |
| A / D | Move left / right |
| W | Jump |

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


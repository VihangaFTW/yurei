#pragma once
#include <array>
#include <cmath>
#include "tile.h"

constexpr size_t GRID_ROWS = 12;
constexpr size_t GRID_COLS = 50;

// How a tile reacts to things that touch it.
enum class TileCollision
{
    none,
    solid,
    // can be jumped through from below and stood on from above
    oneWay
};

constexpr TileCollision tileCollision(Tile tile)
{
    switch (tile)
    {
    case Tile::platformLeft:
    case Tile::platformMiddle:
    case Tile::platformRight:
        return TileCollision::oneWay;
    default:
        // rows 0-2 of the tileset are terrain
        return static_cast<size_t>(tile) < 3 * TILESET_COLS ? TileCollision::solid : TileCollision::none;
    }
}

// The foreground tile grid, kept around after loading so objects can collide with it.
struct Level
{
    std::array<std::array<Tile, GRID_COLS>, GRID_ROWS> tiles{};
    // world y of row 0
    float top = 0.0f;

    int colAt(float x) const
    {
        return static_cast<int>(std::floor(x / GRID_TILE_PIXELS));
    }

    int rowAt(float y) const
    {
        return static_cast<int>(std::floor((y - top) / GRID_TILE_PIXELS));
    }

    // world x of a column's left edge
    float colX(int col) const
    {
        return static_cast<float>(col * static_cast<int>(GRID_TILE_PIXELS));
    }

    // world y of a row's top edge
    float rowY(int row) const
    {
        return top + static_cast<float>(row * static_cast<int>(GRID_TILE_PIXELS));
    }

    TileCollision collisionAt(int row, int col) const
    {
        // the left and right edges of the level act as walls
        if (col < 0 || col >= static_cast<int>(GRID_COLS))
        {
            return TileCollision::solid;
        }
        // open sky above, a pit below
        if (row < 0 || row >= static_cast<int>(GRID_ROWS))
        {
            return TileCollision::none;
        }
        return tileCollision(tiles[row][col]);
    }
};

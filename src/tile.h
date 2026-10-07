#pragma once
#include <optional>
#include <SDL3/SDL.h>

constexpr size_t GRID_TILE_PIXELS = 32;
constexpr size_t TILESET_COLS = 8;

enum class Tile
{
    woodTopLeft = 0,
    woodTop,
    woodTopRight,
    stoneTopLeft,
    stoneTop,
    stoneTopRight,
    platformLeft,
    platformMiddle,

    woodLeft,
    woodCenter,
    woodRight,
    stoneLeft,
    stoneCenter,
    stoneRight,
    platformRight,
    woodTopBroken,

    woodBottomLeft,
    woodBottom,
    woodBottomRight,
    stoneBottomLeft,
    stoneBottom,
    stoneBottomRight,
    woodCenterKnotted,
    stoneCenterMossy,

    plaster,
    plasterBeam,
    pillar,
    shoji,
    shojiTorn,
    shojiHand,
    fusuma,
    baseboard,

    roofLeft,
    roofMiddle,
    roofRight,
    roofFill,
    roofEave,
    windowRound,
    windowBarred,
    wallHole,

    chochin,
    chochinObake,
    kasaObake,
    stoneLantern,
    candle,
    ofuda,
    scroll,
    cobwebLeft,

    shimenawa,
    grave,
    sotoba,
    bambooSpikes,
    hitodama1,
    hitodama2,
    hitodama3,
    hitodama4,

    jizo,
    well,
    susuki,
    mokumokuren,
    cobwebRight,
    brokenPlates,
    roots,
    debris,

    empty,
    enemy,
    player
};


/// @brief Maps a tile variant to its index in `tileset/Tiles.png`.
/// Variants that spawn characters have no tile and return std::nullopt.
constexpr std::optional<size_t> tileIndex(Tile tile)
{
    if (tile >= Tile::empty)
    {
        return std::nullopt;
    }
    return static_cast<size_t>(tile);
}

constexpr SDL_FRect tileSrcRect(size_t idx)
{
    return SDL_FRect{
        .x = static_cast<float>((idx % TILESET_COLS) * GRID_TILE_PIXELS),
        .y = static_cast<float>((idx / TILESET_COLS) * GRID_TILE_PIXELS),
        .w = static_cast<float>(GRID_TILE_PIXELS),
        .h = static_cast<float>(GRID_TILE_PIXELS)};
}

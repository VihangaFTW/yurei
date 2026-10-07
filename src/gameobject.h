#pragma once
#include <glm/glm.hpp>
#include <vector>
#include <variant>
#include <optional>
#include <SDL3/SDL.h>
#include "animation.h"

enum class PlayerState
{
    idle,
    running,
    jumping,
    attacking
};

struct PlayerData
{
    PlayerState state;

    PlayerData()
    {
        state = PlayerState::idle;
    }
};

struct LevelData
{
    SDL_FRect src;  

};

struct EnemyData
{
};

using ObjectData = std::variant<PlayerData, LevelData, EnemyData>;

// Encapsulates an object's position, movement and
// animation data.
struct GameObject
{
    ObjectData data;
    float dir, maxSpeedX;
    glm::vec2 pos, velocity, accel;
    std::vector<Animation> animations;
    std::optional<size_t> currentAnimationIdx;
    SDL_Texture *texture;

    bool isGrounded;

    GameObject()
        : data(LevelData{}),
          maxSpeedX(0.0f),
          dir(1.0f),
          pos(0.0f),
          velocity(0.0f),
          accel(0.0f),
          currentAnimationIdx(std::nullopt),
          texture(nullptr),
          isGrounded(true)

    {
    }
};

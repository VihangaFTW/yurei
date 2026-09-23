#pragma once
#include <glm/glm.hpp>
#include <vector>
#include <variant>
#include <SDL3/SDL.h>
#include "animation.h"

enum class PlayerState
{
    idle,
    running,
    jumping
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
    // index of currently playing frame of animation
    // -1 means no animation
    int currentAnimationIdx;
    SDL_Texture *texture;

    bool isGrounded;

    GameObject()
        : data(LevelData{}),
          maxSpeedX(0.0f),
          dir(1.0f),
          pos(0.0f),
          velocity(0.0f),
          accel(0.0f),
          currentAnimationIdx(-1),
          texture(nullptr),
          isGrounded(true)

    {
    }
};

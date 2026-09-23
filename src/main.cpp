#include <SDL3/SDL.h>
#include <SDL3/SDL_main.h>
#include <SDL3_image/SDL_image.h>
#include <string>
#include <stdint.h>
#include <vector>
#include <array>
#include "gameobject.h"

struct SDLState
{
    SDL_Window *window = nullptr;
    SDL_Renderer *renderer = nullptr;
    int width = 0, height = 0, logW = 0, logH = 0;
    const bool *keys = nullptr;

    SDLState() : keys(SDL_GetKeyboardState(NULL)) {};
};

const size_t LAYER_IDX_LEVEL = 0;
const size_t LAYER_IDX_CHARACTERS = 1;

const size_t SPRITE_SIZE = 128;

struct GameState
{

    // The game consists of layers and
    // each layer is made up of game objects.
    // Initially, the game starts with two layers,
    // one for the level design and another for the characters.
    std::array<std::vector<GameObject>, 2> layers;
    float gravity = 200.0f;
    float groundY = 0.0f;

    GameState()
    {
    }
};

// Handles the lifecycle of program's textures and Animations.
struct Resources
{
    const int ANIM_PLAYER_IDLE = 0;
    const int ANIM_PLAYER_RUN = 1;
    const int ANIM_PLAYER_JUMP = 2;
    // Stores all loaded animations.
    std::vector<Animation> playerAnimations;
    // Stores all loaded textures.
    std::vector<SDL_Texture *> textures;

    // Player's idle texture is displayed on game startup
    SDL_Texture *texIdle = nullptr, *texRun = nullptr, *texJump = nullptr;

    // This method loads textures from an `assets/` directory from
    // program root and it does not traverse subdirectories.
    //
    // Ensure that `filepath` includes subdirectories.
    // For example: "player/Idle.png" maps to `<exe-dir>/assets/player/Idle.png`
    SDL_Texture *loadTexture(SDL_Renderer *renderer, const std::string &filepath)
    {

        // get directory where app is run from
        const char *basePath = SDL_GetBasePath();
        // basePath already includes a trailing /
        const std::string assetDir = std::string(basePath ? basePath : "") + "assets/";

        SDL_Texture *tex = IMG_LoadTexture(renderer, (assetDir + filepath).c_str());

        SDL_SetTextureScaleMode(tex, SDL_SCALEMODE_NEAREST);

        textures.push_back(tex);

        return tex;
    };

    // Creates a Animation object for player idle animation
    // and loads its associated png as a texture.
    void load(const SDLState &state)
    {
        playerAnimations.resize(5);
        playerAnimations[ANIM_PLAYER_IDLE] = Animation(1.6f, 6);
        playerAnimations[ANIM_PLAYER_RUN] = Animation(0.5f, 8);
        playerAnimations[ANIM_PLAYER_JUMP] = Animation(1.5f, 12);

        // setup player idle texture
        texIdle = loadTexture(state.renderer, "player/Idle.png");
        texRun = loadTexture(state.renderer, "player/Run.png");
        texJump = loadTexture(state.renderer, "player/Jump.png");
    };

    // Destroys all loaded textures.
    void unload(const SDLState &)
    {
        for (SDL_Texture *tex : textures)
        {
            SDL_DestroyTexture(tex);
        }
    };
};

void cleanup(SDLState &state);
bool initialize(SDLState &state);
void drawObject(const SDLState &state, GameObject &obj);
void updateObject(const SDLState &state, GameState &gs, Resources &res, GameObject &obj, float delta);

int main(int, char *[])
{

    SDLState state{};
    state.width = 1600;
    state.height = 900;
    state.logW = 640;
    state.logH = 360;

    //*setup widow and renderer

    if (!initialize(state))
    {
        return 1;
    };

    //* load game assets
    Resources res;
    res.load(state);

    //* setup game data

    GameState gs;

    //* create player
    GameObject player;
    gs.groundY = static_cast<float>(state.logH) - static_cast<float>(SPRITE_SIZE);

    player.data = PlayerData{};

    player.texture = res.texIdle;
    player.animations = res.playerAnimations;
    player.currentAnimationIdx = res.ANIM_PLAYER_IDLE;

    player.maxSpeedX = 100;
    player.pos = glm::vec2(150.0f, gs.groundY);
    player.accel = glm::vec2(900.0f, 0.0f);
    player.velocity = glm::vec2(0.0f);

    gs.layers[LAYER_IDX_CHARACTERS].push_back(player);

    // move the player that actually lives in the layer;
    // the push_back above copied it, so `player` is now a stale duplicate
    GameObject &playerObj = gs.layers[LAYER_IDX_CHARACTERS].back();

    bool onGround = true;

    //* game loop

    // milliseconds elapsed since last frame
    uint64_t prevTicks = SDL_GetTicks();

    bool running = true;
    // one iteration  =  1 frame
    // on my laptop =  1 second has 165 frames due to vsync
    while (running)
    {
        SDL_Event event{0};
        //*  1. handle all events
        while (SDL_PollEvent(&event))
        {
            switch (event.type)
            {
            case SDL_EVENT_QUIT:
            {
                running = false;
                break;
            };

            case SDL_EVENT_WINDOW_RESIZED:
            {
                state.width = event.window.data1;
                state.height = event.window.data2;
                break;
            };
            }
        }

        //* 2. handle player movement

        uint64_t nowTicks = SDL_GetTicks();
        float elapsed = (nowTicks - prevTicks) / 1000.0f;
        prevTicks = nowTicks;

        //* update visible animation frames and positions for all game objects
        for (auto &layer : gs.layers)
        {
            for (auto &obj : layer)
            {
                updateObject(state, gs, res, obj, elapsed);

                if (obj.currentAnimationIdx != -1)
                {
                    obj.animations[obj.currentAnimationIdx].step(elapsed);
                }
            }
        }

        //* 3. draw to back buffer
        // ? LORE: framebuffer
        // A buffer is a block of memory holding the color of every pixel in window. N pixels x 4 bytes (1 byte for each R,G,B,A value per pixel).
        // There are two buffers:
        // - front buffer: Monitor checks this periodically per its refresh rate. So, we dont draw to this.
        // - back buffer: A private buffer where we can define the next frame's drawing.

        // sets the color for the back buffer (doesnt draw yet)
        SDL_SetRenderDrawColor(state.renderer, 0, 0, 0, SDL_ALPHA_OPAQUE);
        // fills the back buffer entirely with that color
        // paints the WHOLE window (including the render canvas)
        SDL_RenderClear(state.renderer);

        // separate the render canvas from the window background
        SDL_SetRenderDrawColor(state.renderer, 20, 30, 10, SDL_ALPHA_OPAQUE);

        SDL_FRect canvas{
            .x = 0.0f,
            .y = 0.0f,
            .w = static_cast<float>(state.logW),
            .h = static_cast<float>(state.logH),
        };

        SDL_RenderFillRect(state.renderer, &canvas);

        //* draw all updated game objects to screen
        for (auto &layer : gs.layers)
        {
            for (auto &obj : layer)
            {
                drawObject(state, obj);
            }
        }

        // update front buffer with our back buffer so the monitor picks it up
        //! IMP: the old front buffer typically becomes the new back buffer, but
        //! this is not guranteed so treat the new back buffer's contents
        //! as undefined after present and always RenderClear before drawing in next frame.
        SDL_RenderPresent(state.renderer);
    }

    //* freeup vram used for textures
    res.unload(state);
    cleanup(state);
    return 0;
}

// Shows the current SDL error, frees whatever was created so far
// and returns false so callers can `return initFailed(state);`
static bool initFailed(SDLState &state)
{
    SDL_ShowSimpleMessageBox(SDL_MESSAGEBOX_ERROR, "Error", SDL_GetError(), NULL);
    cleanup(state);
    return false;
}

// Sets up SDL, the window and the renderer.
// On failure, everything created so far is cleaned up before returning false.
bool initialize(SDLState &state)
{
    if (!SDL_Init(SDL_INIT_VIDEO))
    {
        return initFailed(state);
    }

    //* create window

    state.window = SDL_CreateWindow("Ledge", state.width, state.height, SDL_WINDOW_RESIZABLE);

    if (!state.window)
    {
        return initFailed(state);
    }

    //* create renderer

    state.renderer = SDL_CreateRenderer(state.window, NULL);

    if (!state.renderer)
    {
        return initFailed(state);
    }

    // w/o vsync: thousand of frames/ sec
    // with vsync: frames/sec = monitor's refresh rate
    if (!SDL_SetRenderVSync(state.renderer, 1))
    {
        return initFailed(state);
    }

    //* configure renderer dimensions
    // ignores window size and sets a fixed size for the rendered content

    if (!SDL_SetRenderLogicalPresentation(state.renderer, state.logW, state.logH, SDL_LOGICAL_PRESENTATION_LETTERBOX))
    {
        return initFailed(state);
    }

    return true;
}

void cleanup(SDLState &state)
{
    SDL_DestroyRenderer(state.renderer);
    SDL_DestroyWindow(state.window);
    SDL_Quit();
}

/// @brief Draws a game texture to the screen.
/// @param state
/// @param obj
void drawObject(const SDLState &state, GameObject &obj)

{
    float srcX = obj.currentAnimationIdx != -1 ? obj.animations[obj.currentAnimationIdx].currentFrame() * SPRITE_SIZE : 0.0f;

    // extract section from the texture
    // all dims depend on the logical renderer dims and not window dims
    // x, y are the offsets from the orgin (top left corner of image)
    SDL_FRect src{
        .x = srcX,
        .y = 0.0f,
        .w = static_cast<float>(SPRITE_SIZE),
        .h = static_cast<float>(SPRITE_SIZE),
    };

    SDL_FRect dst{
        .x = static_cast<float>(obj.pos.x),
        .y = static_cast<float>(obj.pos.y),
        .w = static_cast<float>(SPRITE_SIZE),
        .h = static_cast<float>(SPRITE_SIZE),

    };

    SDL_FlipMode flipMode = obj.dir == -1 ? SDL_FLIP_HORIZONTAL : SDL_FLIP_NONE;

    // draw player idle state to back buffer
    SDL_RenderTextureRotated(state.renderer, obj.texture, &src, &dst, 0, NULL, flipMode);
};

void updateObject(const SDLState &state, GameState &gs, Resources &res, GameObject &obj, float delta)
{
    // note: std::get_if() returns a pointer to the PlayerData
    // if that is what the variant holds, otherwise nullptr
    if (PlayerData *pd = std::get_if<PlayerData>(&obj.data))
    {
        float dirVec = 0;

        if (state.keys[SDL_SCANCODE_A])
        {
            dirVec += -1;
        }

        if (state.keys[SDL_SCANCODE_D])
        {
            dirVec += 1;
        }

        // horizontal movement registered
        if (dirVec)
        {
            obj.dir = dirVec;
        }

        if (state.keys[SDL_SCANCODE_W] && obj.isGrounded)
        {
            obj.isGrounded = false;
            pd->state = PlayerState::jumping;
            // current y speed is 0 so add jump impulse upwards
            obj.velocity.y = -150.00f;
            obj.texture = res.texJump;
            obj.currentAnimationIdx = res.ANIM_PLAYER_JUMP;
            // start every jump from the first frame
            obj.animations[res.ANIM_PLAYER_JUMP].reset();
        }

        switch (pd->state)
        {
        case PlayerState::idle:
            // update state to running if movement is registered
            if (dirVec)
            {
                pd->state = PlayerState::running;
                obj.texture = res.texRun;
                obj.currentAnimationIdx = res.ANIM_PLAYER_RUN;
            }
            else
            { //? apply deceleration on character slide after movement
                if (obj.velocity.x)
                { // deceleration strength opposite to movement direction
                    const float decelFactor = obj.velocity.x > 0 ? -1.5f : 1.5f;

                    // decel for the current time interval
                    float decel = decelFactor * obj.accel.x * delta;

                    // when |decel| is bigger than current velocity at the end of slide,
                    // character slides in opposite direction because
                    // the velocity crosses 0 and drop to negative
                    // clamp the velocity to 0
                    if (std::abs(decel) > std::abs(obj.velocity.x))
                    {
                        obj.velocity.x = 0;
                    }
                    else
                    {
                        obj.velocity.x += decel;
                    }
                }
            }

            break;

        case PlayerState::running:
            // stop running if movement key is let go
            if (!dirVec)
            {
                pd->state = PlayerState::idle;
                obj.texture = res.texIdle;
                obj.currentAnimationIdx = res.ANIM_PLAYER_IDLE;
            }
            break;

        case PlayerState::jumping:

            // check if landed
            if (obj.isGrounded)
            {
                pd->state = dirVec ? PlayerState::running : PlayerState::idle;
                obj.texture = dirVec ? res.texRun : res.texIdle;
                obj.currentAnimationIdx = dirVec ? res.ANIM_PLAYER_RUN : res.ANIM_PLAYER_IDLE;
            }
            break;
        }

        // calculate new horizontal velocity from effect of acceleration
        obj.velocity.x += dirVec * obj.accel.x * delta;

        if (std::abs(obj.velocity.x) > obj.maxSpeedX)
        {
            obj.velocity.x = dirVec * obj.maxSpeedX;
        }

        // gravity pulls down player
        obj.velocity.y += gs.gravity * delta;

        // calculate resulting player pos
        obj.pos += obj.velocity * delta;

        if (obj.pos.y >= gs.groundY)
        {
            obj.pos.y = gs.groundY;
            obj.velocity.y = 0.0f;
            obj.isGrounded = true;
        }
    }
};

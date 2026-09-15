#include <SDL3/SDL.h>
#include <SDL3/SDL_main.h>
#include <SDL3_image/SDL_image.h>
#include <string>
#include <stdint.h>

struct SDLState
{
    SDL_Window *window;
    SDL_Renderer *renderer;
    int width, height, logW, logH;
};

void cleanup(SDLState &state);
bool initialize(SDLState &state);

int main(int argc, char *argv[])
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

    const char *basePath = SDL_GetBasePath();
    // basePath includes a trailing /
    const std::string assetDir = std::string(basePath ? basePath : "") + "assets/";

    SDL_Texture *idleTex = IMG_LoadTexture(state.renderer, (assetDir + "player/Idle.png").c_str());
    SDL_SetTextureScaleMode(idleTex, SDL_SCALEMODE_NEAREST);

    if (!idleTex)
    {
        SDL_ShowSimpleMessageBox(SDL_MESSAGEBOX_ERROR, "Error", SDL_GetError(), NULL);
        cleanup(state);
        return 1;
    }

    //* setup game data

    const int spriteSize = 128;
    const bool *const keys = SDL_GetKeyboardState(NULL);

    const float groundY = state.logH - spriteSize;
    bool onGround = true;

    float playerX = 150.0f;
    float playerY = groundY;

    // updates on jump; later on manipulated by gravity
    float velocityY = 0.0f;

    // all speeds below are in pixels/sec
    const float moveSpeed = 200.0f;
    const float jumpSpeed = -320.0f;

    // gravity defined in pixels/s^2
    const float gravity = 900.0f;

    //* game loop

    // milliseconds elapsed since last frame
    uint64_t prevTicks = SDL_GetTicks();

    // flips player model horizontally when moving left/right
    bool flipPlayerHorizontal = false;

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

            // player jump fires once per press
            // the onGround flag makes sure this branch is not fired mid jump
            case SDL_EVENT_KEY_DOWN:
            {
                if (event.key.scancode == SDL_SCANCODE_W && !event.key.repeat && onGround)
                {
                    velocityY = jumpSpeed;
                    onGround = false;
                }
                break;
            }
            }
        }

        //* 2. handle player movement

        uint64_t nowTicks = SDL_GetTicks();
        float elapsed = (nowTicks - prevTicks) / 1000.0f;
        prevTicks = nowTicks;

        // player horizontal movement
        // -1.0f (moving left), +1.0f (moving right), or 0.0f (standing still)
        float vectorX = 0.0f;

        if (keys[SDL_SCANCODE_A])
        {
            vectorX -= 1.0f;
            flipPlayerHorizontal = true;
        }

        if (keys[SDL_SCANCODE_D])
        {
            flipPlayerHorizontal = false;
            vectorX += 1.0f;
        }

        // distance =  direction x speed x time
        playerX += vectorX * moveSpeed * elapsed;

        // if mid jump; add effect from gravity
        velocityY += gravity * elapsed;
        // distance =  speed * time
        playerY += velocityY * elapsed;

        // reset speed  and flags on touching ground
        if (playerY >= groundY)
        { // ensure player lands on top of ground
            playerY = groundY;
            velocityY = 0.0f;
            onGround = true;
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

        // extract section from the texture
        // all dims depend on the logical renderer dims and not window dims
        // x, y are the offsets from the orgin (top left corner of image)
        SDL_FRect src{
            .x = 0.0f,
            .y = 0.0f,
            .w = static_cast<float>(spriteSize),
            .h = static_cast<float>(spriteSize),
        };

        SDL_FRect dst{
            .x = playerX,
            .y = static_cast<float>(playerY),
            .w = static_cast<float>(spriteSize),
            .h = static_cast<float>(spriteSize),

        };

        // draw player idle state to back buffer
        SDL_RenderTextureRotated(state.renderer, idleTex, &src, &dst, 0, NULL, flipPlayerHorizontal ? SDL_FLIP_HORIZONTAL : SDL_FLIP_NONE);

        // update front buffer with our back buffer so the monitor picks it up
        //! IMP: the old front buffer typically becomes the new back buffer, but
        //! this is not guranteed so treat the new back buffer's contents
        //! as undefined after present and always RenderClear before drawing in next frame.
        SDL_RenderPresent(state.renderer);
    }

    //* freeup vram used for textures
    SDL_DestroyTexture(idleTex);
    cleanup(state);
    return 0;
}

bool initialize(SDLState &state)
{
    bool initSuccess = true;

    if (!SDL_Init(SDL_INIT_VIDEO))
    {
        SDL_ShowSimpleMessageBox(SDL_MESSAGEBOX_ERROR, "Error", SDL_GetError(), NULL);
        initSuccess = false;
    }

    //* create window

    state.window = SDL_CreateWindow("Ledge", state.width, state.height, SDL_WINDOW_RESIZABLE);

    if (!state.window)
    {
        SDL_ShowSimpleMessageBox(SDL_MESSAGEBOX_ERROR, "Error", SDL_GetError(), NULL);
        cleanup(state);
        initSuccess = false;
    }

    //* create renderer

    state.renderer = SDL_CreateRenderer(state.window, NULL);

    if (!state.renderer)
    {
        SDL_ShowSimpleMessageBox(SDL_MESSAGEBOX_ERROR, "Error", SDL_GetError(), NULL);
        cleanup(state);
        initSuccess = false;
    }

    // w/o vsync: thousand of frames/ sec
    // with vsync: frames/sec = monitor's refresh rate
    if (!SDL_SetRenderVSync(state.renderer, 1))
    {
        initSuccess = false;
    }

    //* configure renderer dimensions
    // ignores window size and sets a fixed size for the rendered content

    if (!SDL_SetRenderLogicalPresentation(state.renderer, state.logW, state.logH, SDL_LOGICAL_PRESENTATION_LETTERBOX))
    {
        initSuccess = false;
    }

    return initSuccess;
}

void cleanup(SDLState &state)
{
    SDL_DestroyRenderer(state.renderer);
    SDL_DestroyWindow(state.window);
    SDL_Quit();
}

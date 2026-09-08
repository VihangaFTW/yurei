#include <SDL3/SDL.h>
#include <SDL3/SDL_main.h>

struct SDLState
{
    SDL_Window *window;
    SDL_Renderer *renderer;
};

void cleanup(SDLState &state);

int main(int argc, char *argv[])
{

    SDLState state{};

    if (!SDL_Init(SDL_INIT_VIDEO))
    {
        SDL_ShowSimpleMessageBox(SDL_MESSAGEBOX_ERROR, "Error", SDL_GetError(), NULL);
        return 1;
    }

    // create window
    int width = 800;
    int height = 600;

    state.window = SDL_CreateWindow("Ledge", width, height, SDL_WINDOW_RESIZABLE);

    if (!state.window)
    {
        SDL_ShowSimpleMessageBox(SDL_MESSAGEBOX_ERROR, "Error", SDL_GetError(), NULL);
        cleanup(state);
        return 1;
    }

    // create renderer
    state.renderer = SDL_CreateRenderer(state.window, NULL);

    if (!state.renderer)
    {
        SDL_ShowSimpleMessageBox(SDL_MESSAGEBOX_ERROR, "Error", SDL_GetError(), NULL);
        cleanup(state);
        return 1;
    }

    // game loop
    bool running = true;
    // one iteration  =  1 frame
    while (running)
    {
        SDL_Event event{0};
        // 1. handle all events
        while (SDL_PollEvent(&event))
        {
            switch (event.type)
            {
            case SDL_EVENT_QUIT:
            {
                running = false;
                break;
            };
            }
        }

        // 2. draw to back buffer
        // ? LORE: framebuffer
        // A buffer is a block of memory holding the color of every pixel in window. N pixels x 4 bytes (1 byte for each R,G,B,A value per pixel).
        // There are two buffers:
        // - front buffer: Monitor checks this periodically per its refresh rate. So, we dont draw to this.
        // - back buffer: A private buffer where we can define the next frame's drawing.

        // sets the color for the back buffer (doesnt draw yet)
        SDL_SetRenderDrawColor(state.renderer, 255, 255, 255, SDL_ALPHA_OPAQUE);
        // fills the back buffer entirely with that color
        SDL_RenderClear(state.renderer);

        // update front buffer with our back buffer so the monitor picks it up
        //! IMP: the old front buffer typically becomes the new back buffer, but
        //! this is not guranteed so treat the new back buffer's contents
        //! as undefined after present and always RenderClear before drawing in next frame.
        SDL_RenderPresent(state.renderer);
        // w/o vsync: thousand of frames/ sec
        // with vsync: frames/sec = monitor's refresh rate
        SDL_SetRenderVSync(state.renderer, 1);
    }

    cleanup(state);
    return 0;
}

void cleanup(SDLState &state)
{
    SDL_DestroyRenderer(state.renderer);
    SDL_DestroyWindow(state.window);
    SDL_Quit();
}

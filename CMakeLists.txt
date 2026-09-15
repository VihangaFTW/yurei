cmake_minimum_required(VERSION 3.16)
project(ledge CXX)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

include(FetchContent)

# SDL3_image reads BUILD_SHARED_LIBS to decide static vs shared,
# so set it globally
set(BUILD_SHARED_LIBS OFF CACHE BOOL "" FORCE)

# ---------------------------------------------------------------- SDL3
FetchContent_Declare(
    SDL3
    GIT_REPOSITORY https://github.com/libsdl-org/SDL.git
    GIT_TAG release-3.4.16
    GIT_SHALLOW TRUE
)

# build SDL as a static lib
set(SDL_SHARED OFF CACHE BOOL "" FORCE)
set(SDL_STATIC ON  CACHE BOOL "" FORCE)
set(SDL_TEST   OFF CACHE BOOL "" FORCE)

FetchContent_MakeAvailable(SDL3)

# ---------------------------------------------------------- SDL3_image
# GIT_SUBMODULES "" skips the external/ deps
FetchContent_Declare(
    SDL3_image
    GIT_REPOSITORY https://github.com/libsdl-org/SDL_image.git
    GIT_TAG release-3.4.6
    GIT_SHALLOW TRUE
    GIT_SUBMODULES ""
)

# don't build third-party image libs from source
set(SDLIMAGE_VENDORED OFF CACHE BOOL "" FORCE)

set(SDLIMAGE_SAMPLES OFF CACHE BOOL "" FORCE)
set(SDLIMAGE_TESTS   OFF CACHE BOOL "" FORCE)
set(SDLIMAGE_INSTALL OFF CACHE BOOL "" FORCE)

# formats we don't need
set(SDLIMAGE_AVIF OFF CACHE BOOL "" FORCE)
set(SDLIMAGE_JXL  OFF CACHE BOOL "" FORCE)
set(SDLIMAGE_TIF  OFF CACHE BOOL "" FORCE)
set(SDLIMAGE_WEBP OFF CACHE BOOL "" FORCE)

# PNG and JPEG go through the built-in stb backend instead of libpng/libjpeg.
# Trade-off: no animated-PNG support
set(SDLIMAGE_PNG_LIBPNG OFF CACHE BOOL "" FORCE)

FetchContent_MakeAvailable(SDL3_image)

# ------------------------------------------------------------ our target
add_executable(ledge
    src/main.cpp
)

target_link_libraries(ledge PRIVATE
    SDL3::SDL3
    SDL3_image::SDL3_image
)

# ---------------------------------------------------------------- assets
# copy assets next to the build exe.
add_custom_command(TARGET ledge POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy_directory
        "${CMAKE_CURRENT_SOURCE_DIR}/assets"
        "$<TARGET_FILE_DIR:ledge>/assets"
    COMMENT "Copying assets to $<TARGET_FILE_DIR:ledge>"
)

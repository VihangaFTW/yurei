#pragma once
#include "timer.h"

// Wrapper around a timer that syncs an object's animation frames.
class Animation
{
    Timer timer_;
    int frames_;

public:
    // default constructor
    Animation() : timer_(0), frames_(0) {};
    Animation(float length, int frames) : timer_(length), frames_(frames) {};

    int currentFrame() const
    {
        return static_cast<int>((timer_.getTime() / timer_.getLength()) * frames_);
    }

    float getLength() const
    {
        return timer_.getLength();
    }

    void step(float delta)
    {
        timer_.step(delta);
    }

    // restarts the animation from its first frame
    void reset()
    {
        timer_.reset();
    }
};
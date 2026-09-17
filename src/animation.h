#pragma once
#include "timer.h"

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
};
#pragma once

class Timer
{
    float length_, time_;
    bool timeout_;

public:
    Timer(float length) : length_(length), time_(0), timeout_(false) {};

    void step(float delta)
    {
        time_ += delta;

        // sync internal clock to real world time as closely as possible
        // extra time is added to the next timer cycle
        if (time_ >= length_)
        {
            time_ -= length_;
            timeout_ = true;
        }
    }

    float getTime() const
    {
        return time_;
    }

    float getLength() const
    {
        return length_;
    }

    bool isTimeout() const
    {
        return timeout_;
    }

    void reset()
    {
        time_ = 0;
        timeout_ = false;
    }
};

/***
 * Testé sur la carte. Les quatre ports sont adressés correctement.
 */

#include <cstdio>
#include <cstring>
#include <cmath>
#include <thread>
#include <chrono>

#include <fmod.hpp>
#include <fmod_errors.h>

#define FMOD_CHECK(x) \
    if ((x) != FMOD_OK) \
        printf("FMOD error %d : %s\n", x, FMOD_ErrorString(x));

FMOD::System* fmodSystem = nullptr;
FMOD::Sound* sound = nullptr;
FMOD::Channel* channel = nullptr;

// ASIO mapping UR44C - VÉRIFIÉ
// Canal ASIO 0 = 1R (Line Out 1 Right)
// Canal ASIO 1 = 1L (Line Out 1 Left)
// Canal ASIO 2 = 2R (Line Out 2 Right)
// Canal ASIO 3 = 2L (Line Out 2 Left)
// Ordre de rotation: 1R, 1L, 2R, 2L
const int OUTPUTS[4] = { 0, 1, 2, 3 }; // 1R, 1L, 2R, 2L
const int ASIO_CHANNELS = 6;

// vitesse de rotation - durée par sortie
const float DURATION_PER_OUTPUT = 5.0f; // secondes par output

void InitFMOD()
{
    FMOD_CHECK(FMOD::System_Create(&fmodSystem));
    FMOD_CHECK(fmodSystem->setOutput(FMOD_OUTPUTTYPE_ASIO));

    int driverCount = 0;
    FMOD_CHECK(fmodSystem->getNumDrivers(&driverCount));
    printf("Available ASIO drivers: %d\n", driverCount);

    int selectedDriver = -1;
    for (int i = 0; i < driverCount; i++)
    {
        char name[256];
        FMOD_CHECK(fmodSystem->getDriverInfo(i, name, 256, nullptr, nullptr, nullptr, nullptr));
        printf("  Driver %d: %s\n", i, name);

        // Try to find Yamaha Steinberg USB ASIO
        if (strstr(name, "Steinberg") != nullptr || strstr(name, "Yamaha") != nullptr)
        {
            selectedDriver = i;
            printf("Found Steinberg/Yamaha driver at index %d\n", i);
        }
    }

    // If Steinberg not found, use first driver
    if (selectedDriver == -1 && driverCount > 0)
    {
        selectedDriver = 0;
        printf("WARNING: Steinberg/Yamaha driver not found, using default driver 0\n");
    }

    if (selectedDriver >= 0)
    {
        FMOD_CHECK(fmodSystem->setDriver(selectedDriver));
        printf("Selected ASIO driver: %d\n", selectedDriver);
    }

    // Configure for 6 channels (0-5, using 2-5)
    FMOD_CHECK(fmodSystem->setSoftwareFormat(
        48000,
        FMOD_SPEAKERMODE_RAW,
        6  // Request 6 channels for ASIO
    ));

    FMOD_CHECK(fmodSystem->init(512, FMOD_INIT_NORMAL, nullptr));

    int outChannels;
    FMOD_CHECK(fmodSystem->getSoftwareFormat(nullptr, nullptr, &outChannels));
    printf("FMOD output channels configured: %d\n", outChannels);
}

void LoadAndPlay()
{
    FMOD_CHECK(fmodSystem->createSound(
        "sound.wav",
        FMOD_DEFAULT | FMOD_LOOP_NORMAL,
        nullptr,
        &sound
    ));

    FMOD_CHECK(fmodSystem->playSound(sound, nullptr, false, &channel));
}

void UpdateRotation(float time)
{
    // calculate current output index (changes every DURATION_PER_OUTPUT seconds)
    int currentIndex = ((int)(time / DURATION_PER_OUTPUT)) % 4;

    // force every gain to 0
    float gains[6] = { 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f };
    
    // only activate current output
    gains[OUTPUTS[currentIndex]] = 1.0f;

    // "matrice de mixage": one input, 6 output channels
    FMOD_RESULT result = channel->setMixMatrix(
        gains,
        6,   // asio out channels
        1    // mono input
    );
    
    if (result != FMOD_OK)
    {
        printf("setMixMatrix error %d: %s\n", result, FMOD_ErrorString(result));
    }
    
    // only one active channel
    for (int i = 0; i < 6; i++)
    {
        if (i != OUTPUTS[currentIndex])
        {
            gains[i] = 0.0f;
        }
    }
    
    channel->setMixMatrix(gains, 6, 1);

    // pitch different for every output
    float pitchFactors[] = { 0.95f, 1.00f, 1.05f, 1.10f }; 
    float frequency = 48000.0f * pitchFactors[currentIndex];  
    
    result = channel->setFrequency(frequency);
    if (result != FMOD_OK)
    {
        printf("setFrequency error %d: %s\n", result, FMOD_ErrorString(result));
    }
    
    static int lastIndex = -1;
    if (currentIndex != lastIndex)
    {
        const char* outputNames[] = { "1R", "1L", "2R", "2L" };
        printf("\n========================================\n");
        printf("Playing on: %s (ASIO channel %d, pitch: %.0f%%)\n", 
            outputNames[currentIndex], OUTPUTS[currentIndex], pitchFactors[currentIndex] * 100);
        printf("========================================\n");
        lastIndex = currentIndex;
    }
}

int main()
{
    printf("=== Starting FMOD 4 Outputs ===\n");
    
    printf("Initializing FMOD...\n");
    InitFMOD();
    printf("FMOD initialized successfully\n");
    
    printf("Loading sound file...\n");
    LoadAndPlay();
    printf("Sound loaded and playing\n");

    float time = 0.0f;
    const float dt = 0.01f;

    printf("Starting rotation loop (%.1f seconds per output)...\n", DURATION_PER_OUTPUT);
    printf("=========================================\n");
    printf("Output order: 1R -> 1L -> 2R -> 2L\n");
    printf("ASIO channels: %d -> %d -> %d -> %d\n", OUTPUTS[0], OUTPUTS[1], OUTPUTS[2], OUTPUTS[3]);
    printf("Only ONE speaker should play at a time!\n");
    printf("=========================================\n\n");
    while (true)
    {
        UpdateRotation(time);
        FMOD_CHECK(fmodSystem->update());

        time += dt;
        std::this_thread::sleep_for(std::chrono::milliseconds(10));
    }

    return 0;
}

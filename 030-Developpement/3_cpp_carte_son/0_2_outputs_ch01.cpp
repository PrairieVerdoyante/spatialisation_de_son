/***
 * Son stéréo sur outputs 1 et 2 (ASIO channels 0 et 1)
 * Joue sur les deux sorties en même temps.
 * Sorties LINE OUTPUT 1R eet 1L de la carte son Steinberg UR44c.
 */

#include <cstdio>
#include <cstring>
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

// ASIO mapping UR44C
// 0 = Output 1 L
// 1 = Output 1 R
const int OUTPUT_LEFT = 0;
const int OUTPUT_RIGHT = 1;
const int TOTAL_ASIO_CHANNELS = 6;

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

        if (strstr(name, "Steinberg") != nullptr || strstr(name, "Yamaha") != nullptr)
        {
            selectedDriver = i;
            printf("Found Steinberg/Yamaha driver at index %d\n", i);
        }
    }

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

    // Configure for 6 channels ASIO
    FMOD_CHECK(fmodSystem->setSoftwareFormat(
        48000,
        FMOD_SPEAKERMODE_RAW,
        6
    ));

    FMOD_CHECK(fmodSystem->init(512, FMOD_INIT_NORMAL, nullptr));

    int outChannels;
    FMOD_CHECK(fmodSystem->getSoftwareFormat(nullptr, nullptr, &outChannels));
    printf("FMOD output channels configured: %d\n", outChannels);
}

void LoadAndPlayStereo()
{
    // Charger un fichier stéréo
    FMOD_CHECK(fmodSystem->createSound(
        "sound.wav",
        FMOD_DEFAULT | FMOD_LOOP_NORMAL,
        nullptr,
        &sound
    ));

    // Jouer le son
    FMOD_CHECK(fmodSystem->playSound(sound, nullptr, false, &channel));

    // Configuration de la matrice de mixage pour stéréo sur outputs 0 et 1
    FMOD_SOUND_FORMAT format;
    int channels;
    sound->getFormat(nullptr, &format, &channels, nullptr);
    printf("Sound format: %d channels\n", channels);

    if (channels == 1)
    {
        // Mono vers stéréo sur outputs 0-1
        float gains[6] = { 0.0f };
        gains[OUTPUT_LEFT] = 1.0f;   // Gauche (output 1)
        gains[OUTPUT_RIGHT] = 1.0f;  // Droite (output 2)
        
        FMOD_CHECK(channel->setMixMatrix(gains, 6, 1));
        printf("Mono sound routed to stereo outputs 0-1\n");
    }
    else if (channels == 2)
    {
        // Stéréo vers outputs 0-1
        // Matrice 2 inputs (L, R du fichier) x 6 outputs (ASIO)
        float gains[12] = { 0.0f };  // 2 * 6 = 12 éléments
        
        // Input 0 (Left) -> Output 0
        gains[0 * 6 + OUTPUT_LEFT] = 1.0f;
        
        // Input 1 (Right) -> Output 1
        gains[1 * 6 + OUTPUT_RIGHT] = 1.0f;
        
        FMOD_CHECK(channel->setMixMatrix(gains, 6, 2));
        printf("Stereo sound routed to outputs 0-1\n");
    }
}

int main()
{
    printf("=== FMOD Stereo on Outputs 1-2 (ASIO 0-1) ===\n");
    
    printf("Initializing FMOD...\n");
    InitFMOD();
    printf("FMOD initialized successfully\n");
    
    printf("Loading and playing sound...\n");
    LoadAndPlayStereo();
    printf("Sound is playing on outputs 1-2 (ASIO channels 0-1)\n");

    printf("Press Ctrl+C to stop...\n");
    while (true)
    {
        FMOD_CHECK(fmodSystem->update());
        std::this_thread::sleep_for(std::chrono::milliseconds(10));
    }

    return 0;
}

# 3_cpp_carte_son / FMOD 4 outputs

This sample plays a mono WAV file through a selected output speaker using FMOD with ASIO output.

## Prerequisites
- Windows x64
- Visual Studio 2022 Build Tools (MSVC) or full VS 2022
- CMake 3.20+
- FMOD Studio API (Core) for Windows. Install and set environment variable `FMOD_SDK_DIR` to the SDK root, for example:
  - `C:\\Program Files\\FMOD SoundSystem\\FMOD Studio API Windows`
- ASIO driver and device (the code looks for a driver containing `UR44C` by name)

## Build
From VS Code (recommended):
- Run task: "Build 0_4_outputs (Release)". The first run also configures CMake.

From terminal:
```
cmake -S 030-Developpement/3_cpp_carte_son -B 030-Developpement/3_cpp_carte_son/build -G "Visual Studio 17 2022" -A x64
cmake --build 030-Developpement/3_cpp_carte_son/build --config Release --target 0_4_outputs
```

## Run
cd C:\dev\0_P3\25isc_il-p3_251_spatialisation-de-son_aubrysarah\030-Developpement\3_cpp_carte_son

Reconfigurer CMake (pour détecter le nouveau fichier)
cmake -S . -B build -G "Visual Studio 17 2022" -A x64

Compiler les deux executables
cmake --build build --config Release

Lancer la version stéréo Mix 1 uniquement
.\build\Release\0_2_outputs.exe

Ou la version 4 sorties
.\build\Release\0_4_outputs.exe

## Notes
- If you don't have an ASIO device named with `UR44C`, either change the substring in the device selection loop, or remove the `setOutput(FMOD_OUTPUTTYPE_ASIO)` call to use the default output (e.g., WASAPI).
- Ensure `fmod.dll` from the FMOD SDK `api/core/lib/x64` folder is available next to the built executable. The CMake script copies it automatically when present.

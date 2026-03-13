cmake_minimum_required(VERSION 3.20)
project(0_4_outputs LANGUAGES CXX)

# Force Visual Studio generator if not already set
if(NOT CMAKE_GENERATOR)
    message(STATUS "No generator specified, using Visual Studio 16 2019")
    # Can be changed to Visual Studio 17 2022 if using newer MSVC
endif()

# -------------------------------
# C++ standard
# -------------------------------
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# -------------------------------
# Locate FMOD SDK
# -------------------------------
set(FMOD_SDK_DIR "$ENV{FMOD_SDK_DIR}")

if(NOT FMOD_SDK_DIR OR FMOD_SDK_DIR STREQUAL "")
    set(FMOD_SDK_DIR "$ENV{FMOD_DIR}")
endif()

# Fallback: hardcoded path if in 030-Developpement folder
if(NOT FMOD_SDK_DIR OR FMOD_SDK_DIR STREQUAL "")
    set(FMOD_SDK_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../FMOD Studio API Windows")
endif()

# Also try absolute path
if(NOT EXISTS "${FMOD_SDK_DIR}")
    set(FMOD_SDK_DIR "C:/Program Files (x86)/FMOD SoundSystem/FMOD Studio API Windows")
endif()

if(NOT EXISTS "${FMOD_SDK_DIR}")
    message(FATAL_ERROR
        "FMOD SDK not found.\n"
        "Tried:\n"
        "  1. Env FMOD_SDK_DIR\n"
        "  2. Env FMOD_DIR\n"
        "  3. Relative: ../FMOD Studio API Windows\n"
        "  4. Absolute: C:/Program Files (x86)/FMOD SoundSystem/FMOD Studio API Windows\n"
        "Please set FMOD_SDK_DIR environment variable or place SDK in 030-Developpement folder"
    )
endif()

message(STATUS "Using FMOD SDK at: ${FMOD_SDK_DIR}")

# -------------------------------
# FMOD include & lib paths
# -------------------------------
set(FMOD_INC_DIR
    "${FMOD_SDK_DIR}/api/core/inc"
)

set(FMOD_LIB_DIR
    "${FMOD_SDK_DIR}/api/core/lib/x64"
)

if(NOT EXISTS "${FMOD_INC_DIR}/fmod.hpp")
    message(FATAL_ERROR "fmod.hpp not found in ${FMOD_INC_DIR}")
endif()

# -------------------------------
# Find FMOD libraries
# -------------------------------
find_library(FMOD_LIBRARY_RELEASE
    NAMES fmod_vc fmod
    PATHS "${FMOD_LIB_DIR}"
    NO_DEFAULT_PATH
)

find_library(FMOD_LIBRARY_DEBUG
    NAMES fmodL_vc fmodL
    PATHS "${FMOD_LIB_DIR}"
    NO_DEFAULT_PATH
)

if(NOT FMOD_LIBRARY_RELEASE)
    message(FATAL_ERROR "FMOD release library not found in ${FMOD_LIB_DIR}")
endif()

# -------------------------------
# Executables
# -------------------------------
# 0_2_outputs_ch01: Stereo on outputs 1-2 (ASIO 0-1)
add_executable(0_2_outputs_ch01
    0_2_outputs_ch01.cpp
)

# 0_2_outputs_2r2l: Stereo on Mix 2 (ASIO 4-5)
add_executable(0_2_outputs_2r2l
    0_2_outputs_2r2l.cpp
)

# 0_4_outputs: 4 outputs rotation
add_executable(0_4_outputs
    0_4_outputs.cpp
)

# -------------------------------
# Common function to configure a target
# -------------------------------
function(configure_fmod_target target_name)
    target_include_directories(${target_name} PRIVATE
        "${FMOD_INC_DIR}"
    )

    if(MSVC)
        target_compile_options(${target_name} PRIVATE
            /utf-8
            /W3
            /permissive-
        )
    endif()

    if(FMOD_LIBRARY_DEBUG)
        target_link_libraries(${target_name} PRIVATE
            optimized ${FMOD_LIBRARY_RELEASE}
            debug     ${FMOD_LIBRARY_DEBUG}
        )
    else()
        target_link_libraries(${target_name} PRIVATE
            ${FMOD_LIBRARY_RELEASE}
        )
    endif()

    # Copy FMOD DLL next to exe
    set(FMOD_DLL_RELEASE "${FMOD_SDK_DIR}/api/core/bin/x64/fmod.dll")
    set(FMOD_DLL_DEBUG   "${FMOD_SDK_DIR}/api/core/bin/x64/fmodL.dll")
    
    if(EXISTS "${FMOD_DLL_RELEASE}")
        add_custom_command(TARGET ${target_name} POST_BUILD
            COMMAND ${CMAKE_COMMAND} -E copy_if_different
                "$<$<CONFIG:Debug>:${FMOD_DLL_DEBUG}>$<$<NOT:$<CONFIG:Debug>>:${FMOD_DLL_RELEASE}>"
                "$<TARGET_FILE_DIR:${target_name}>"
        )
    endif()
endfunction()

# Configure all targets
configure_fmod_target(0_2_outputs_ch01)
configure_fmod_target(0_2_outputs_2r2l)
configure_fmod_target(0_4_outputs)

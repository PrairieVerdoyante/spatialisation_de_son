cmake_minimum_required(VERSION 3.16)

project(demo_interface_audio VERSION 0.1 LANGUAGES CXX)

set(CMAKE_AUTOUIC ON)
set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTORCC ON)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# ---------------------------------
# FMOD SDK discovery (Windows / MSVC)
# ---------------------------------
# Usage precedence:
#   1. Env FMOD_SDK_DIR
#   2. Env FMOD_DIR
#   3. Relative to this demo: ../../../FMOD Studio API Windows
set(FMOD_SDK_DIR "$ENV{FMOD_SDK_DIR}")
if(NOT FMOD_SDK_DIR OR FMOD_SDK_DIR STREQUAL "")
    set(FMOD_SDK_DIR "$ENV{FMOD_DIR}")
endif()
if(NOT FMOD_SDK_DIR OR FMOD_SDK_DIR STREQUAL "")
    set(FMOD_SDK_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../../../FMOD Studio API Windows")
endif()

set(FMOD_INC_DIR "${FMOD_SDK_DIR}/api/core/inc")
set(FMOD_LIB_DIR "${FMOD_SDK_DIR}/api/core/lib/x64")
set(FMOD_DLL_RELEASE "${FMOD_SDK_DIR}/api/core/bin/x64/fmod.dll")
set(FMOD_DLL_DEBUG   "${FMOD_SDK_DIR}/api/core/bin/x64/fmodL.dll")

if(NOT EXISTS "${FMOD_INC_DIR}/fmod.hpp")
    message(FATAL_ERROR "FMOD header not found in ${FMOD_INC_DIR}. Set FMOD_SDK_DIR or place the SDK at ../../../FMOD Studio API Windows")
endif()

find_library(FMOD_LIBRARY_RELEASE
    NAMES fmod_vc fmod
    PATHS "${FMOD_LIB_DIR}"
)
find_library(FMOD_LIBRARY_DEBUG
    NAMES fmodL_vc fmodL
    PATHS "${FMOD_LIB_DIR}"
)

# Copy sound.wav to build directory
configure_file(${CMAKE_CURRENT_SOURCE_DIR}/sound.wav
               ${CMAKE_CURRENT_BINARY_DIR}/sound.wav
               COPYONLY)

if(NOT FMOD_LIBRARY_RELEASE)
    message(FATAL_ERROR "FMOD release library not found in ${FMOD_LIB_DIR}")
endif()

find_package(QT NAMES Qt6 Qt5 REQUIRED COMPONENTS Widgets)
find_package(Qt${QT_VERSION_MAJOR} REQUIRED COMPONENTS Widgets)

set(PROJECT_SOURCES
        main.cpp
        mainwindow.cpp
        mainwindow.h
)



if(${QT_VERSION_MAJOR} GREATER_EQUAL 6)
    qt_add_executable(demo_interface_audio
        MANUAL_FINALIZATION
        ${PROJECT_SOURCES}
    )
# Define target properties for Android with Qt 6 as:
#    set_property(TARGET demo_interface_audio APPEND PROPERTY QT_ANDROID_PACKAGE_SOURCE_DIR
#                 ${CMAKE_CURRENT_SOURCE_DIR}/android)
# For more information, see https://doc.qt.io/qt-6/qt-add-executable.html#target-creation
else()
    if(ANDROID)
        add_library(demo_interface_audio SHARED
            ${PROJECT_SOURCES}
        )
# Define properties for Android with Qt 5 after find_package() calls as:
#    set(ANDROID_PACKAGE_SOURCE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/android")
    else()
        add_executable(demo_interface_audio
            ${PROJECT_SOURCES}
        )
    endif()
endif()

target_link_libraries(demo_interface_audio PRIVATE Qt${QT_VERSION_MAJOR}::Widgets)

# MSVC: enable proper C++ version reporting for Qt6
if(MSVC)
    target_compile_options(demo_interface_audio PRIVATE /Zc:__cplusplus)
endif()


# FMOD include + link
target_include_directories(demo_interface_audio PRIVATE "${FMOD_INC_DIR}")
if(FMOD_LIBRARY_DEBUG)
    target_link_libraries(demo_interface_audio PRIVATE
        optimized ${FMOD_LIBRARY_RELEASE}
        debug     ${FMOD_LIBRARY_DEBUG}
    )
else()
    target_link_libraries(demo_interface_audio PRIVATE ${FMOD_LIBRARY_RELEASE})
endif()

# Copy FMOD runtime DLL next to the built exe (Debug -> fmodL, others -> fmod)
if(EXISTS "${FMOD_DLL_RELEASE}")
    add_custom_command(TARGET demo_interface_audio POST_BUILD
        COMMAND ${CMAKE_COMMAND} -E copy_if_different
            "$<$<CONFIG:Debug>:${FMOD_DLL_DEBUG}>$<$<NOT:$<CONFIG:Debug>>:${FMOD_DLL_RELEASE}>"
            "$<TARGET_FILE_DIR:demo_interface_audio>"
    )
endif()

# Copy Qt runtime DLLs next to the executable (Windows only)
if(WIN32 AND Qt6_DIR)
    get_target_property(QT_TARGET_TYPE demo_interface_audio TYPE)
    if(NOT QT_TARGET_TYPE STREQUAL "STATIC_LIBRARY")
        # Get Qt bin directory
        get_filename_component(QT_BIN_DIR "${Qt6Core_DIR}/../../bin" ABSOLUTE)
        
        # List of Qt DLLs to copy
        set(QT_DLLS
            Qt6Core.dll
            Qt6Gui.dll
            Qt6Widgets.dll
        )
        
        foreach(QT_DLL ${QT_DLLS})
            if(EXISTS "${QT_BIN_DIR}/${QT_DLL}")
                add_custom_command(TARGET demo_interface_audio POST_BUILD
                    COMMAND ${CMAKE_COMMAND} -E copy_if_different
                        "${QT_BIN_DIR}/${QT_DLL}"
                        "$<TARGET_FILE_DIR:demo_interface_audio>"
                )
            endif()
        endforeach()
        
        # Copy platform plugins (ANGLE, etc.)
        if(EXISTS "${QT_BIN_DIR}/../plugins/platforms")
            add_custom_command(TARGET demo_interface_audio POST_BUILD
                COMMAND ${CMAKE_COMMAND} -E copy_directory
                    "${QT_BIN_DIR}/../plugins/platforms"
                    "$<TARGET_FILE_DIR:demo_interface_audio>/platforms"
            )
        endif()
    endif()
endif()

# Qt for iOS sets MACOSX_BUNDLE_GUI_IDENTIFIER automatically since Qt 6.1.
# If you are developing for iOS or macOS you should consider setting an
# explicit, fixed bundle identifier manually though.
if(${QT_VERSION} VERSION_LESS 6.1.0)
  set(BUNDLE_ID_OPTION MACOSX_BUNDLE_GUI_IDENTIFIER com.example.demo_interface_audio)
endif()
set_target_properties(demo_interface_audio PROPERTIES
    ${BUNDLE_ID_OPTION}
    MACOSX_BUNDLE_BUNDLE_VERSION ${PROJECT_VERSION}
    MACOSX_BUNDLE_SHORT_VERSION_STRING ${PROJECT_VERSION_MAJOR}.${PROJECT_VERSION_MINOR}
    MACOSX_BUNDLE TRUE
    WIN32_EXECUTABLE TRUE
)

include(GNUInstallDirs)
install(TARGETS demo_interface_audio
    BUNDLE DESTINATION .
    LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
    RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
)

if(QT_VERSION_MAJOR EQUAL 6)
    qt_finalize_executable(demo_interface_audio)
endif()

#include "mainwindow.h"

#include <QPainter>
#include <QMouseEvent>
#include <QTimer>
#include <QPushButton>
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QLabel>
#include <QtMath>
#include <cstdio>
#include <cstring>

#include <fmod_errors.h>
#include <fmod.h>

#define FMOD_CHECK(x)                                                        \
do {                                                                     \
        FMOD_RESULT _r = (x);                                                \
        if (_r != FMOD_OK) {                                                 \
            printf("FMOD error %d : %s\n", _r, FMOD_ErrorString(_r));         \
    }                                                                    \
} while (0)

    // ASIO mapping (UR44C) reused from 0_4_outputs.cpp
    // 0 = 1R (top-right), 1 = 1L (top-left), 2 = 2R (bottom-right), 3 = 2L (bottom-left)
    static const int OUTPUTS[4] = { 0, 1, 2, 3 };

MainWindow::MainWindow(QWidget *parent)
    : QMainWindow(parent), radius(20), dragging(false), isPlaying(false),
    fmodSystem(nullptr), sound(nullptr), channel(nullptr), fmodTimer(nullptr)
{
    setWindowTitle("Spatialisation du Son");

    // Create central widget and layout
    QWidget *centralWidget = new QWidget(this);
    QVBoxLayout *mainLayout = new QVBoxLayout(centralWidget);
    mainLayout->setContentsMargins(20, 20, 20, 20);
    mainLayout->setSpacing(10);

    // Header: Logo and school info
    QWidget *headerWidget = new QWidget();
    QHBoxLayout *headerLayout = new QHBoxLayout(headerWidget);

    QLabel *logoLabel = new QLabel("He-Arc");
    QPixmap pixmap("C:/dev/0_P3/demo_interface_audio/logo_hearc.png");
    pixmap.setDevicePixelRatio(6);
    logoLabel->setStyleSheet("font-size: 14px; font-weight: bold; color: #1a1a1a;");
    logoLabel->setPixmap(pixmap);

    QLabel *schoolLabel = new QLabel("Haute École Arc\nInformatique - Ingénierie");
    schoolLabel->setStyleSheet("font-size: 15px; color: #555;");
    schoolLabel->setAlignment(Qt::AlignRight);

    headerLayout->addWidget(logoLabel);
    headerLayout->addStretch();
    headerLayout->addWidget(schoolLabel);

    // Student info
    QLabel *studentLabel = new QLabel("Étudiante: Sarah Aubry");
    studentLabel->setStyleSheet("font-size: 15px; color: #666;");
    studentLabel->setAlignment(Qt::AlignRight);

    // Create play/stop button
    playButton = new QPushButton("Play", this);
    playButton->setFixedHeight(40);
    playButton->setFixedWidth(100);
    connect(playButton, &QPushButton::clicked, this, &MainWindow::toggleAudio);

    initFMOD();
    loadSound();

    // Periodic FMOD update to keep audio responsive
    fmodTimer = new QTimer(this);
    connect(fmodTimer, &QTimer::timeout, this, [this]() {
        if (fmodSystem) {
            fmodSystem->update();
        }
    });
    fmodTimer->start(10);

    // Add widgets to main layout
    mainLayout->addWidget(headerWidget);
    mainLayout->addWidget(studentLabel);

    mainLayout->addStretch();

    // Footer: Copyright
    QLabel *copyrightLabel = new QLabel("Tous droits réservés © 2026 Haute École Arc");
    copyrightLabel->setStyleSheet("font-size: 15px; color: #999;");
    copyrightLabel->setAlignment(Qt::AlignCenter);
    mainLayout->addWidget(copyrightLabel);

    centralWidget->setLayout(mainLayout);
    setCentralWidget(centralWidget);

    // Go fullscreen
    showFullScreen();

    // Calculate geometry after fullscreen
    recalculateGeometry();

    updateMixFromCircle();
}

MainWindow::~MainWindow()
{
    if (sound) {
        sound->release();
        sound = nullptr;
    }
    if (fmodSystem) {
        fmodSystem->close();
        fmodSystem->release();
        fmodSystem = nullptr;
    }
}

void MainWindow::initFMOD()
{
    FMOD_CHECK(FMOD::System_Create(&fmodSystem));
    if (!fmodSystem) return;

    FMOD_CHECK(fmodSystem->setOutput(FMOD_OUTPUTTYPE_ASIO));

    // Driver selection: try to pick Steinberg/Yamaha, fallback to first
    int driverCount = 0;
    FMOD_CHECK(fmodSystem->getNumDrivers(&driverCount));
    int selectedDriver = -1;
    for (int i = 0; i < driverCount; ++i) {
        char name[256] = {0};
        FMOD_CHECK(fmodSystem->getDriverInfo(i, name, 256, nullptr, nullptr, nullptr, nullptr));
        if (strstr(name, "Steinberg") || strstr(name, "Yamaha")) {
            selectedDriver = i;
            break;
        }
    }
    if (selectedDriver == -1 && driverCount > 0) selectedDriver = 0;
    if (selectedDriver >= 0) {
        FMOD_CHECK(fmodSystem->setDriver(selectedDriver));
    }

    // Raw 6-channel format (we use 4 of them)
    FMOD_CHECK(fmodSystem->setSoftwareFormat(48000, FMOD_SPEAKERMODE_RAW, 6));
    FMOD_CHECK(fmodSystem->init(512, FMOD_INIT_NORMAL, nullptr));
}

void MainWindow::loadSound()
{
    if (!fmodSystem) return;

    FMOD_RESULT result = fmodSystem->createSound("C:/dev/0_P3/demo_interface_audio/sound.wav", FMOD_DEFAULT | FMOD_LOOP_NORMAL, nullptr, &sound);
    FMOD_CHECK(result);
    if (!sound) {
        printf("ERROR: Could not load sound.wav. Make sure the file exists.\n");
        return;
    }
    printf("Sound loaded successfully\n");
}

void MainWindow::recalculateGeometry()
{
    // Calculate available space for drawing
    int headerHeight = 70;
    int footerHeight = 40;
    int buttonHeight = 80;
    int margins = 60;

    int availableHeight = height() - headerHeight - footerHeight - buttonHeight - margins;
    int availableWidth = width() - margins;

    // Create a centered square that fits in the available space
    int squareSize = qMin(availableHeight, availableWidth);
    int x = (width() - squareSize) / 2;
    int y = headerHeight + 10 + (availableHeight - squareSize) / 2;

    square = QRect(x, y, squareSize, squareSize);
    circlePos = square.center();

    // Position the button below the title text
    int buttonX = (width() - playButton->width()) / 2;
    int buttonY = square.bottom() + 70;  // 20px for title + 50px spacing
    playButton->move(buttonX, buttonY);
}

void MainWindow::toggleAudio()
{
    if (!fmodSystem || !sound) return;

    if (!isPlaying) {
        // Start playback
        FMOD_RESULT result = fmodSystem->playSound(sound, nullptr, false, &channel);
        FMOD_CHECK(result);
        if (channel) {
            channel->setVolume(1.0f);
            updateMixFromCircle();  // Apply spatial mix based on current circle position
            isPlaying = true;
            playButton->setText("Stop");
            printf("Audio playback started\n");
        }
    } else {
        // Stop playback
        if (channel) {
            FMOD_RESULT result = channel->stop();
            FMOD_CHECK(result);
            channel = nullptr;
            isPlaying = false;
            playButton->setText("Play");
            printf("Audio playback stopped\n");
        }
    }
}

void MainWindow::updateMixFromCircle()
{
    if (!channel) return;

    // Normalize circle position inside the square to [0,1]
    float nx = float(circlePos.x() - square.left()) / float(square.width());
    float ny = float(circlePos.y() - square.top()) / float(square.height());
    nx = qBound(0.0f, nx, 1.0f);
    ny = qBound(0.0f, ny, 1.0f);

    // Bilinear weights for 4 speakers
    float w_tl = (1.0f - nx) * (1.0f - ny); // top-left -> 1L
    float w_tr = nx * (1.0f - ny);          // top-right -> 1R
    float w_bl = (1.0f - nx) * ny;          // bottom-left -> 2L
    float w_br = nx * ny;                   // bottom-right -> 2R

    float gains[6] = {0.f, 0.f, 0.f, 0.f, 0.f, 0.f};
    gains[OUTPUTS[1]] = w_tl; // 1L
    gains[OUTPUTS[0]] = w_tr; // 1R
    gains[OUTPUTS[3]] = w_bl; // 2L
    gains[OUTPUTS[2]] = w_br; // 2R

    FMOD_RESULT result = channel->setMixMatrix(gains, 6, 1);
    if (result != FMOD_OK) {
        printf("setMixMatrix error %d: %s\n", result, FMOD_ErrorString(result));
    }
}

void MainWindow::paintEvent(QPaintEvent *)
{
    QPainter p(this);
    p.setRenderHint(QPainter::Antialiasing, true);

    p.drawRect(square);

    // Draw speakers at corners
    const int spkR = 10;
    p.setBrush(Qt::darkGray);
    p.drawEllipse(QPoint(square.left(), square.top()), spkR, spkR);           // TL (1L)
    p.drawEllipse(QPoint(square.right(), square.top()), spkR, spkR);          // TR (1R)
    p.drawEllipse(QPoint(square.left(), square.bottom()), spkR, spkR);        // BL (2L)
    p.drawEllipse(QPoint(square.right(), square.bottom()), spkR, spkR);       // BR (2R)

    // Moving source
    p.setBrush(Qt::blue);
    p.drawEllipse(circlePos, radius, radius);


    // Draw title below the square
    QFont titleFont("Arial", 18, QFont::Bold);
    p.setFont(titleFont);
    p.setPen(Qt::black);
    QRect titleRect(square.left(), square.bottom() + 20, square.width(), 40);
    p.drawText(titleRect, Qt::AlignCenter, "Spatialisation du Son");
}

void MainWindow::mousePressEvent(QMouseEvent *event)
{
    if ((event->pos() - circlePos).manhattanLength() <= radius * 2) {
        dragging = true;
    }
}

void MainWindow::mouseMoveEvent(QMouseEvent *event)
{
    if (!dragging) return;

    QPoint pos = event->pos();
    int x = qBound(square.left() + radius, pos.x(), square.right() - radius);
    int y = qBound(square.top() + radius, pos.y(), square.bottom() - radius);
    circlePos = QPoint(x, y);

    updateMixFromCircle();
    update();
}

void MainWindow::mouseReleaseEvent(QMouseEvent *)
{
    dragging = false;
}

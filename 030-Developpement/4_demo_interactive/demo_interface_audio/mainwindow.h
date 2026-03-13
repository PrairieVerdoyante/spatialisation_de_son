#ifndef MAINWINDOW_H
#define MAINWINDOW_H

#include <QMainWindow>
#include <QRect>
#include <QPoint>
#include <QPushButton>

#include <fmod.hpp>

class QTimer;
class QMouseEvent;
class QPaintEvent;

class MainWindow : public QMainWindow
{
    Q_OBJECT

public:
    MainWindow(QWidget *parent = nullptr);
    ~MainWindow();

protected:
    void paintEvent(QPaintEvent *) override;
    void mousePressEvent(QMouseEvent *event) override;
    void mouseMoveEvent(QMouseEvent *event) override;
    void mouseReleaseEvent(QMouseEvent *event) override;

private slots:
    void toggleAudio();

private:
    // UI state
    QRect square;
    QPoint circlePos;
    int radius;
    bool dragging;
    QPushButton* playButton;
    bool isPlaying;

    // FMOD
    FMOD::System* fmodSystem;
    FMOD::Sound* sound;
    FMOD::Channel* channel;
    QTimer* fmodTimer;

    void initFMOD();
    void loadSound();
    void recalculateGeometry();
    void updateMixFromCircle();
};
#endif // MAINWINDOW_H

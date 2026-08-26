// Circuit Lens native desktop client — Qt 6 live camera + C++ TorchScript/OCR inference.
#include "inference_engine.hpp"

#include <QApplication>
#include <QButtonGroup>
#include <QCamera>
#include <QCoreApplication>
#include <QDateTime>
#include <QFrame>
#include <QHBoxLayout>
#include <QImage>
#include <QLabel>
#include <QMediaCaptureSession>
#include <QMediaDevices>
#include <QMainWindow>
#include <QPushButton>
#include <QElapsedTimer>
#include <QStyle>
#include <QScrollArea>
#include <QTextEdit>
#include <QTimer>
#include <QVBoxLayout>
#include <QVideoFrame>
#include <QVideoSink>
#include <QVideoWidget>

#include <opencv2/imgproc.hpp>

#include <cstdlib>
#include <cmath>
#include <filesystem>
#include <memory>
#include <sstream>

namespace {
std::string env_or(const char* key, const std::string& fallback = "") {
  const char* value = std::getenv(key);
  return value && *value ? value : fallback;
}

QString html_escape(const QString& value) { return value.toHtmlEscaped(); }

QString status_pill(const QString& label, const QString& color = "#A4FF3F") {
  return QString("<span style='color:%1; font-weight:700; letter-spacing:1px;'>%2</span>").arg(color, html_escape(label));
}
}

class InspectionWindow final : public QMainWindow {
 public:
  explicit InspectionWindow(InferenceEngine& engine) : engine_(engine) {
    setWindowTitle("Circuit Lens — Native C++ Live Inspection");
    setMinimumSize(1120, 720);
    resize(1440, 900);

    auto* root = new QWidget(this);
    auto* shell = new QHBoxLayout(root);
    shell->setContentsMargins(0, 0, 0, 0);
    shell->setSpacing(0);

    auto* rail = new QFrame(root);
    rail->setObjectName("rail");
    rail->setFixedWidth(212);
    auto* rail_layout = new QVBoxLayout(rail);
    rail_layout->setContentsMargins(20, 22, 16, 18);
    auto* mark = new QLabel("◉  CIRCUIT<span style='color:#A4FF3F'>LENS</span><br><small>NATIVE C++ WORKSPACE</small>");
    mark->setObjectName("brand");
    rail_layout->addWidget(mark);
    rail_layout->addSpacing(28);
    for (const auto& label : {"INSPECT", "SESSIONS", "MODELS", "SETTINGS"}) {
      auto* item = new QPushButton(label, rail);
      item->setObjectName(QString(label) == "INSPECT" ? "railActive" : "railItem");
      item->setEnabled(QString(label) == "INSPECT");
      rail_layout->addWidget(item);
    }
    rail_layout->addStretch();
    auto* runtime = new QLabel(QString("MODEL  %1\nBOARD  %2\nOCR    %3")
      .arg(engine_.component_ready() ? "TORCHSCRIPT" : "DEMO")
      .arg(engine_.board_ready() ? "TORCHSCRIPT" : "UNAVAILABLE")
      .arg("TESSERACT"));
    runtime->setObjectName("runtime");
    rail_layout->addWidget(runtime);
    shell->addWidget(rail);

    auto* work = new QWidget(root);
    auto* work_layout = new QVBoxLayout(work);
    work_layout->setContentsMargins(34, 27, 34, 28);
    work_layout->setSpacing(16);

    auto* header_row = new QHBoxLayout;
    auto* heading_box = new QVBoxLayout;
    auto* eyebrow = new QLabel("CHOOSE ANALYSIS / NATIVE EXECUTION");
    eyebrow->setObjectName("eyebrow");
    heading_box->addWidget(eyebrow);
    heading_ = new QLabel("Component analysis / Board 07");
    heading_->setObjectName("heading");
    heading_box->addWidget(heading_);
    intro_ = new QLabel("Mark and classify visual component candidates. Use even light and keep the board stable.");
    intro_->setObjectName("intro");
    intro_->setWordWrap(true);
    heading_box->addWidget(intro_);
    header_row->addLayout(heading_box, 1);

    auto* controls = new QVBoxLayout;
    arm_button_ = new QPushButton("ARM REAR CAMERA");
    arm_button_->setObjectName("primary");
    pause_button_ = new QPushButton("PAUSE SCAN");
    pause_button_->setObjectName("secondary");
    controls->addWidget(arm_button_);
    controls->addWidget(pause_button_);
    header_row->addLayout(controls);
    work_layout->addLayout(header_row);

    auto* modes = new QHBoxLayout;
    component_mode_ = new QPushButton("ANALYZE COMPONENTS\nMark & classify parts");
    board_mode_ = new QPushButton("IDENTIFY CIRCUIT BOARD\nName board or module");
    component_mode_->setCheckable(true); board_mode_->setCheckable(true); component_mode_->setChecked(true);
    component_mode_->setObjectName("mode"); board_mode_->setObjectName("mode");
    mode_group_ = new QButtonGroup(this); mode_group_->setExclusive(true); mode_group_->addButton(component_mode_, 0); mode_group_->addButton(board_mode_, 1);
    modes->addWidget(component_mode_); modes->addWidget(board_mode_); modes->addStretch();
    work_layout->addLayout(modes);

    auto* scan_row = new QHBoxLayout;
    auto* viewport_frame = new QFrame(work);
    viewport_frame->setObjectName("viewport");
    auto* viewport_layout = new QVBoxLayout(viewport_frame);
    auto* feed_meta = new QHBoxLayout;
    feed_status_ = new QLabel("● DEMO FEED / CAMERA DISARMED");
    feed_status_->setObjectName("feed");
    auto* calibration = new QLabel("0 ── 25 ── 50 mm"); calibration->setObjectName("calibration");
    feed_meta->addWidget(feed_status_); feed_meta->addStretch(); feed_meta->addWidget(calibration);
    viewport_layout->addLayout(feed_meta);
    video_ = new QVideoWidget(viewport_frame);
    video_->setMinimumSize(650, 390);
    video_->setAspectRatioMode(Qt::KeepAspectRatio);
    viewport_layout->addWidget(video_, 1);
    inference_label_ = new QLabel("INFERENCE PASS / READY");
    inference_label_->setObjectName("inference");
    viewport_layout->addWidget(inference_label_);
    scan_row->addWidget(viewport_frame, 4);

    auto* evidence_frame = new QFrame(work);
    evidence_frame->setObjectName("evidence");
    evidence_frame->setMinimumWidth(330);
    auto* evidence_layout = new QVBoxLayout(evidence_frame);
    auto* focus_title = new QLabel("LIVE EVIDENCE"); focus_title->setObjectName("eyebrow"); evidence_layout->addWidget(focus_title);
    conclusion_ = new QLabel("Awaiting a frame"); conclusion_->setObjectName("conclusion"); conclusion_->setWordWrap(true); evidence_layout->addWidget(conclusion_);
    confidence_ = new QLabel("Confidence gate active"); confidence_->setObjectName("confidence"); confidence_->setWordWrap(true); evidence_layout->addWidget(confidence_);
    markings_ = new QLabel("Marking read: —"); markings_->setObjectName("markings"); markings_->setWordWrap(true); evidence_layout->addWidget(markings_);
    evidence_layout->addSpacing(8);
    auto* instruction = new QLabel("Capture the full front side. Keep USB, RF, headers, camera socket, and silkscreen in focus.");
    instruction->setObjectName("instruction"); instruction->setWordWrap(true); evidence_layout->addWidget(instruction);
    evidence_layout->addStretch();
    scan_row->addWidget(evidence_frame, 1);
    work_layout->addLayout(scan_row, 1);

    auto* record_frame = new QFrame(work);
    record_frame->setObjectName("record");
    auto* record_layout = new QVBoxLayout(record_frame);
    auto* record_title = new QLabel("INSPECTION RECORD / PASS 01"); record_title->setObjectName("eyebrow"); record_layout->addWidget(record_title);
    candidates_ = new QTextEdit(record_frame); candidates_->setReadOnly(true); candidates_->setObjectName("candidates"); candidates_->setMinimumHeight(170); record_layout->addWidget(candidates_);
    work_layout->addWidget(record_frame);
    shell->addWidget(work, 1);
    setCentralWidget(root);

    connect(mode_group_, &QButtonGroup::idClicked, this, [this](int id) { set_mode(id == 1); });
    connect(arm_button_, &QPushButton::clicked, this, [this]() { arm_camera(); });
    connect(pause_button_, &QPushButton::clicked, this, [this]() { scanning_ = !scanning_; pause_button_->setText(scanning_ ? "PAUSE SCAN" : "RESUME SCAN"); inference_label_->setText(scanning_ ? "INFERENCE PASS / LIVE" : "INFERENCE PASS / PAUSED"); });
    initialize_camera();
  }

 private:
  void initialize_camera() {
    const auto input = QMediaDevices::defaultVideoInput();
    if (input.isNull()) { feed_status_->setText("● NO CAMERA DETECTED / DEMO STATE"); return; }
    camera_ = std::make_unique<QCamera>(input);
    capture_session_.setCamera(camera_.get());
    capture_session_.setVideoOutput(video_);
    connect(video_->videoSink(), &QVideoSink::videoFrameChanged, this, [this](const QVideoFrame& frame) { inspect_frame(frame); });
  }

  void arm_camera() {
    if (!camera_) { feed_status_->setText("● CAMERA UNAVAILABLE / CHECK DEVICE ACCESS"); return; }
    camera_->start();
    scanning_ = true;
    arm_button_->setText("CAMERA ARMED");
    arm_button_->setEnabled(false);
    feed_status_->setText("● LIVE REAR CAMERA / NORMAL ORIENTATION");
    inference_label_->setText("INFERENCE PASS / SAMPLING");
  }

  void set_mode(bool board) {
    board_mode_active_ = board;
    heading_->setText(board ? "Circuit-board identification / Board 07" : "Component analysis / Board 07");
    intro_->setText(board ? "Use the full board and legible silkscreen to form a gated module conclusion." : "Mark and classify visual component candidates. Use even light and keep the board stable.");
    component_mode_->setProperty("selected", !board); board_mode_->setProperty("selected", board);
    component_mode_->style()->unpolish(component_mode_); component_mode_->style()->polish(component_mode_);
    board_mode_->style()->unpolish(board_mode_); board_mode_->style()->polish(board_mode_);
    inference_label_->setText(board ? "INFERENCE PASS / BOARD MODE READY" : "INFERENCE PASS / COMPONENT MODE READY");
  }

  void inspect_frame(const QVideoFrame& frame) {
    if (!scanning_ || processing_ || !frame.isValid()) return;
    const qint64 cadence = board_mode_active_ ? 3000 : 1250;
    if (last_sample_.isValid() && last_sample_.elapsed() < cadence) return;
    const auto source = frame.toImage().convertToFormat(QImage::Format_RGBA8888);
    if (source.isNull()) return;
    processing_ = true;
    last_sample_.restart();
    cv::Mat rgba(source.height(), source.width(), CV_8UC4, const_cast<uchar*>(source.constBits()), source.bytesPerLine());
    cv::Mat bgr;
    cv::cvtColor(rgba, bgr, cv::COLOR_RGBA2BGR);
    try { if (board_mode_active_) update_hardware(engine_.hardware_response(bgr)); else update_components(engine_.detect(bgr)); } catch (...) { inference_label_->setText("INFERENCE PASS / RETRYING"); }
    processing_ = false;
  }

  void update_components(const std::vector<Detection>& detections) {
    inference_label_->setText("INFERENCE PASS / COMPONENT CANDIDATES — REVIEW REQUIRED");
    conclusion_->setText("Component candidates mapped");
    confidence_->setText("Broad-vocabulary outputs remain review-only. Confirm package, markings, and terminals.");
    markings_->setText("Marking read: board mode required");
    QStringList lines;
    for (const auto& d : detections) lines << QString("<b>%1 · %2</b> &nbsp; %3% &nbsp; <span style='color:#D99A70'>REVIEW</span><br><small>%4</small>")
      .arg(html_escape(QString::fromStdString(d.ref)), html_escape(QString::fromStdString(d.kind))).arg(std::round(d.confidence * 100)).arg(html_escape(QString::fromStdString(d.value)));
    candidates_->setHtml(lines.isEmpty() ? "No component candidate met the configured threshold." : lines.join("<hr>"));
  }

  void update_hardware(const nlohmann::json& result) {
    const auto accepted = result.value("conclusion_status", "needs_more_evidence") == "candidate_conclusion";
    const auto conclusion = QString::fromStdString(result.value("conclusion", "No reliable board conclusion from this frame"));
    inference_label_->setText(accepted ? "INFERENCE PASS / BOARD CANDIDATE READY" : "INFERENCE PASS / NEEDS MORE EVIDENCE");
    conclusion_->setText(conclusion);
    if (!result["evidence"].empty()) confidence_->setText(QString::fromStdString(result["evidence"][0].get<std::string>()));
    QStringList marks; for (const auto& mark : result["recognized_markings"]) marks << QString::fromStdString(mark.get<std::string>());
    markings_->setText("Marking read: " + (marks.isEmpty() ? QString("—") : marks.join(" · ")));
    QStringList lines;
    for (const auto& component : result["components"]) lines << QString("<b>%1</b> · %2% · REVIEW").arg(html_escape(QString::fromStdString(component.value("kind", "candidate")))).arg(std::round(component.value("confidence",0.F)*100));
    if (!result["board_matches"].empty()) {
      const auto& top = result["board_matches"][0];
      lines.prepend(QString("<b>BOARD RANK</b> &nbsp; %1 &nbsp; %2% %3")
        .arg(html_escape(QString::fromStdString(top.value("name", "unknown")))).arg(std::round(top.value("confidence",0.F)*100)).arg(accepted ? status_pill("CANDIDATE") : status_pill("REVIEW", "#E68A5B")));
    }
    candidates_->setHtml(lines.isEmpty() ? "No board candidate available." : lines.join("<hr>"));
  }

  InferenceEngine& engine_;
  std::unique_ptr<QCamera> camera_;
  QMediaCaptureSession capture_session_;
  QVideoWidget* video_{};
  QButtonGroup* mode_group_{};
  QPushButton *component_mode_{}, *board_mode_{}, *arm_button_{}, *pause_button_{};
  QLabel *heading_{}, *intro_{}, *feed_status_{}, *inference_label_{}, *conclusion_{}, *confidence_{}, *markings_{};
  QTextEdit* candidates_{};
  QElapsedTimer last_sample_;
  bool board_mode_active_{false}, scanning_{false}, processing_{false};
};

int main(int argc, char* argv[]) {
  QApplication app(argc, argv);
  const std::filesystem::path data = env_or("CIRCUIT_LENS_DATA_DIR", "../backend-cpp/data");
  const float threshold = std::stof(env_or("CONFIDENCE_THRESHOLD", "0.60"));
  InferenceEngine engine(data, threshold);
  app.setStyleSheet(R"(
    * { font-family: "DejaVu Sans"; } QMainWindow, QWidget { background:#10120f; color:#f1f0ea; } #rail { background:#12140f; border-right:1px solid #31372d; } #brand { color:#f1f0ea; font-size:15px; font-weight:800; letter-spacing:2px; } #brand small, #runtime { color:#81887b; font-size:10px; letter-spacing:1px; } #railItem, #railActive { text-align:left; padding:12px; border:0; font-size:12px; letter-spacing:1px; } #railItem { color:#989f91; background:#12140f; } #railActive { color:#a4ff3f; background:#1a2116; border-left:2px solid #a4ff3f; } #eyebrow { color:#92998b; font-size:10px; font-weight:800; letter-spacing:2px; } #heading { font-size:28px; font-weight:700; } #intro { color:#abb1a4; max-width:650px; font-size:12px; } #primary { color:#10120f; background:#a4ff3f; border:0; font-weight:800; padding:12px 16px; } #secondary { color:#e5e8e0; background:#20251f; border:1px solid #4a5146; font-weight:700; padding:10px 14px; } #mode { color:#a6aea0; background:#171a16; border:1px solid #424a3d; padding:10px 15px; font-size:11px; text-align:left; } #mode:checked { color:#a4ff3f; border-color:#a4ff3f; background:#1b2417; } #viewport, #evidence { background:#171a16; border:1px solid #333a30; padding:15px; } #feed, #inference { color:#a4ff3f; font-size:10px; font-weight:700; letter-spacing:1px; } #calibration { color:#858c80; font-size:9px; } QVideoWidget { background:#050605; border:1px solid #4a5442; } #conclusion { color:#f1f0ea; font-size:23px; font-weight:700; padding:10px 0; } #confidence { color:#b2b9aa; font-size:12px; line-height:1.4; } #markings { color:#a4ff3f; background:#11130f; border-left:2px solid #a4ff3f; padding:10px; font-size:11px; } #instruction { color:#858c80; font-size:11px; line-height:1.5; } #record { background:#eae6d7; border:1px solid #c9c5b5; padding:17px; } #record #eyebrow { color:#50584c; } #candidates { background:#eae6d7; color:#20251d; border:1px solid #b8b4a4; font-size:12px; } )");
  InspectionWindow window(engine);
  window.show();
  return app.exec();
}

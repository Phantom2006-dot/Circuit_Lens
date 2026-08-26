// Circuit Lens native desktop client — Qt 6 live camera + C++ TorchScript/OCR inference.
#include "inference_engine.hpp"

#include <QApplication>
#include <QButtonGroup>
#include <QCamera>
#include <QCoreApplication>
#include <QDateTime>
#include <QDesktopServices>
#include <QDir>
#include <QFile>
#include <QFileDialog>
#include <QFrame>
#include <QHBoxLayout>
#include <QImage>
#include <QInputDialog>
#include <QLabel>
#include <QLineEdit>
#include <QMediaCaptureSession>
#include <QMediaDevices>
#include <QMainWindow>
#include <QMessageBox>
#include <QPushButton>
#include <QElapsedTimer>
#include <QStandardPaths>
#include <QStyle>
#include <QScrollArea>
#include <QTextEdit>
#include <QTextStream>
#include <QTimer>
#include <QUrl>
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

QString display_label(const std::string& label) {
  auto value = QString::fromStdString(label);
  value.replace("-", " ");
  return value;
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
    auto* runtime = new QLabel(QString("MODEL  %1\nBOARD  %2\nSNAP   %3\nOCR    %4")
      .arg(engine_.component_ready() ? "TORCHSCRIPT" : "DEMO")
      .arg(engine_.board_ready() ? "TORCHSCRIPT" : "UNAVAILABLE")
      .arg(engine_.snapshot_component_ready() ? "TORCHSCRIPT" : "UNAVAILABLE")
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
    snapshot_button_ = new QPushButton("SNAPSHOT & INSPECT");
    snapshot_button_->setObjectName("secondary");
    open_image_button_ = new QPushButton("OPEN IMAGE & INSPECT");
    open_image_button_->setObjectName("secondary");
    controls->addWidget(arm_button_);
    controls->addWidget(pause_button_);
    controls->addWidget(snapshot_button_);
    controls->addWidget(open_image_button_);
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
    auto* instruction = new QLabel("For a component snapshot, centre one object in the target area. For a board, capture the full front side with USB, RF, headers, camera socket, and silkscreen in focus.");
    instruction->setObjectName("instruction"); instruction->setWordWrap(true); evidence_layout->addWidget(instruction);
    evidence_layout->addStretch();
    scan_row->addWidget(evidence_frame, 1);
    work_layout->addLayout(scan_row, 1);

    auto* record_frame = new QFrame(work);
    record_frame->setObjectName("record");
    auto* record_layout = new QVBoxLayout(record_frame);
    auto* record_header = new QHBoxLayout;
    auto* record_title = new QLabel("INSPECTION RECORD / PASS 01"); record_title->setObjectName("eyebrow"); record_header->addWidget(record_title);
    record_header->addStretch();
    correct_button_ = new QPushButton("TELL US WHAT IT IS"); correct_button_->setObjectName("recordAction");
    reference_button_ = new QPushButton("OPEN REFERENCE"); reference_button_->setObjectName("recordAction"); reference_button_->setEnabled(false);
    record_header->addWidget(correct_button_); record_header->addWidget(reference_button_);
    record_layout->addLayout(record_header);
    candidates_ = new QTextEdit(record_frame); candidates_->setReadOnly(true); candidates_->setObjectName("candidates"); candidates_->setMinimumHeight(170); record_layout->addWidget(candidates_);
    work_layout->addWidget(record_frame);
    shell->addWidget(work, 1);
    setCentralWidget(root);

    connect(mode_group_, &QButtonGroup::idClicked, this, [this](int id) { set_mode(id == 1); });
    connect(arm_button_, &QPushButton::clicked, this, [this]() { arm_camera(); });
    connect(pause_button_, &QPushButton::clicked, this, [this]() { scanning_ = !scanning_; pause_button_->setText(scanning_ ? "PAUSE SCAN" : "RESUME SCAN"); inference_label_->setText(scanning_ ? "INFERENCE PASS / LIVE" : "INFERENCE PASS / PAUSED"); });
    connect(snapshot_button_, &QPushButton::clicked, this, [this]() { capture_snapshot(); });
    connect(open_image_button_, &QPushButton::clicked, this, [this]() { open_image(); });
    connect(correct_button_, &QPushButton::clicked, this, [this]() { record_user_correction(); });
    connect(reference_button_, &QPushButton::clicked, this, [this]() { if (!last_reference_url_.isEmpty()) QDesktopServices::openUrl(QUrl(last_reference_url_)); });
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
    last_frame_ = source.copy();
    analyze_image(last_frame_, "Live camera sample", false);
    processing_ = false;
  }

  QString capture_quality(const cv::Mat& bgr) const {
    if (bgr.empty()) return "Capture quality: image unavailable.";
    cv::Mat gray, laplacian;
    cv::cvtColor(bgr, gray, cv::COLOR_BGR2GRAY);
    cv::Scalar brightness, spread, laplace_mean, laplace_spread;
    cv::meanStdDev(gray, brightness, spread);
    cv::Laplacian(gray, laplacian, CV_64F);
    cv::meanStdDev(laplacian, laplace_mean, laplace_spread);
    const double sharpness = laplace_spread[0] * laplace_spread[0];
    QStringList notes;
    if (std::min(bgr.cols, bgr.rows) < 480) notes << "small frame";
    if (brightness[0] < 62) notes << "too dark";
    if (brightness[0] > 205) notes << "washed out";
    if (sharpness < 85) notes << "soft focus";
    if (notes.isEmpty()) notes << "usable for visual review";
    return QString("Capture quality: %1 × %2 · brightness %3 · sharpness %4 · %5.")
      .arg(bgr.cols).arg(bgr.rows).arg(std::round(brightness[0])).arg(std::round(sharpness)).arg(notes.join(", "));
  }

  void analyze_image(const QImage& source, const QString& origin, bool saved_snapshot) {
    if (source.isNull()) return;
    if (!saved_snapshot) last_snapshot_path_.clear();
    cv::Mat rgba(source.height(), source.width(), CV_8UC4, const_cast<uchar*>(source.constBits()), source.bytesPerLine());
    cv::Mat bgr;
    cv::cvtColor(rgba, bgr, cv::COLOR_RGBA2BGR);
    current_quality_ = capture_quality(bgr);
    last_analysis_origin_ = origin;
    last_reference_url_.clear();
    reference_button_->setEnabled(false);
    try {
      if (board_mode_active_) update_hardware(engine_.hardware_response(bgr), saved_snapshot);
      else { const auto markings = engine_.extract_markings(bgr); update_components(engine_.detect(bgr), markings, engine_.microcontroller_evidence(markings), engine_.classify_snapshot_component(bgr), saved_snapshot); }
    } catch (...) {
      inference_label_->setText("INFERENCE PASS / RETRYING");
      conclusion_->setText("The image could not be analyzed.");
      confidence_->setText("Capture another sharp, evenly lit image, then retry.");
    }
  }

  void capture_snapshot() {
    if (last_frame_.isNull()) {
      QMessageBox::information(this, "Circuit Lens", "Arm the camera and wait for a frame before taking a snapshot.");
      return;
    }
    const auto directory = QStandardPaths::writableLocation(QStandardPaths::AppDataLocation) + "/snapshots";
    QDir().mkpath(directory);
    const auto path = directory + "/circuit-lens-" + QDateTime::currentDateTimeUtc().toString("yyyyMMdd-hhmmsszzz") + ".png";
    if (!last_frame_.save(path, "PNG")) {
      QMessageBox::warning(this, "Circuit Lens", "The snapshot could not be saved. The current frame will still be inspected.");
      analyze_image(last_frame_, "Unsaved camera snapshot", false);
      return;
    }
    last_snapshot_path_ = path;
    analyze_image(last_frame_, "Snapshot: " + path, true);
  }

  void open_image() {
    const auto path = QFileDialog::getOpenFileName(this, "Open circuit image", QString(), "Circuit images (*.jpg *.jpeg *.png *.webp)");
    if (path.isEmpty()) return;
    const QImage image(path);
    if (image.isNull()) {
      QMessageBox::warning(this, "Circuit Lens", "This file could not be opened as a supported image.");
      return;
    }
    last_frame_ = image.convertToFormat(QImage::Format_RGBA8888);
    last_snapshot_path_ = path;
    analyze_image(last_frame_, "Opened image: " + path, true);
  }

  void record_user_correction() {
    const auto text = QInputDialog::getText(this, "Tell Circuit Lens what it is", "Object or board identity:", QLineEdit::Normal);
    const auto label = text.trimmed();
    if (label.isEmpty()) return;
    const auto directory = QStandardPaths::writableLocation(QStandardPaths::AppDataLocation) + "/corrections";
    QDir().mkpath(directory);
    QFile output(directory + "/user-corrections.jsonl");
    if (!output.open(QIODevice::WriteOnly | QIODevice::Append | QIODevice::Text)) {
      QMessageBox::warning(this, "Circuit Lens", "The correction could not be saved locally.");
      return;
    }
    nlohmann::json correction = {{"timestamp_utc", QDateTime::currentDateTimeUtc().toString(Qt::ISODateWithMs).toStdString()}, {"analysis_mode", board_mode_active_ ? "board" : "component"}, {"user_supplied_identity", label.toStdString()}, {"snapshot_or_image", last_snapshot_path_.toStdString()}, {"analysis_origin", last_analysis_origin_.toStdString()}, {"model_outcome", last_outcome_}};
    QTextStream(&output) << QString::fromStdString(correction.dump()) << "\n";
    output.close();
    conclusion_->setText(label + " (user-supplied identity)");
    confidence_->setText("Saved as a local correction. It is not model-verified and will not retrain the model automatically.");
    inference_label_->setText("USER CORRECTION / SAVED FOR REVIEW");
  }

  void update_components(const std::vector<Detection>& detections, const std::vector<std::string>& markings, const nlohmann::json& microcontrollers, const std::vector<SnapshotPrediction>& snapshot_predictions, bool saved_snapshot) {
    inference_label_->setText(saved_snapshot ? "SNAPSHOT OUTCOME / COMPONENT REVIEW" : "INFERENCE PASS / COMPONENT REVIEW");
    const bool closeup_candidate = saved_snapshot && !snapshot_predictions.empty() && snapshot_predictions.front().confidence >= .55F;
    const bool microcontroller_candidate = !microcontrollers.empty();
    conclusion_->setText(microcontroller_candidate ? QString::fromStdString(microcontrollers[0].value("name", "Microcontroller")) + " (marking-assisted candidate)" : (closeup_candidate ? display_label(snapshot_predictions.front().label) + " (close-up candidate)" : (detections.empty() ? "No reliable component candidate from this image" : "Component candidates require confirmation")));
    confidence_->setText(current_quality_ + (microcontroller_candidate ? " Exact package marking was read; verify package, full marking, and board context. This is not a development-board conclusion." : (closeup_candidate ? " Close-up candidate is review-only; confirm markings and package." : " Broad-vocabulary component candidates are review-only; confirm package, markings, and terminals or use ‘Tell us what it is’.")));
    QStringList mark_list; for (const auto& marking : markings) mark_list << QString::fromStdString(marking);
    markings_->setText("Marking read: " + (mark_list.isEmpty() ? QString("—") : mark_list.join(" · ")));
    nlohmann::json closeup = nlohmann::json::array(); for (const auto& item : snapshot_predictions) closeup.push_back({{"label", item.label}, {"confidence", item.confidence}});
    last_outcome_ = {{"mode", "component"}, {"origin", last_analysis_origin_.toStdString()}, {"quality", current_quality_.toStdString()}, {"candidates", engine_.detections_json(detections)}, {"microcontroller_evidence", microcontrollers}, {"snapshot_closeup_candidates", closeup}, {"recognized_markings", markings}};
    QStringList lines;
    lines << QString("<b>%1</b><br><small>%2</small>").arg(html_escape(last_analysis_origin_), html_escape(current_quality_));
    for (const auto& microcontroller : microcontrollers) lines << QString("<b>MICROCONTROLLER MARKING CANDIDATE</b><br>%1 · %2<br><small>Package: %3 · review required<br>Reference: %4</small>").arg(html_escape(QString::fromStdString(microcontroller.value("name", "unknown"))), html_escape(QString::fromStdString(microcontroller.value("family", "microcontroller"))), html_escape(QString::fromStdString(microcontroller.value("package", "verify package"))), html_escape(QString::fromStdString(microcontroller.value("source_url", ""))));
    if (saved_snapshot && !snapshot_predictions.empty()) {
      QStringList closeup_lines;
      for (const auto& item : snapshot_predictions) closeup_lines << QString("%1 · %2% review").arg(html_escape(display_label(item.label))).arg(std::round(item.confidence * 100));
      lines << "<b>CENTRED CLOSE-UP SNAPSHOT CANDIDATES</b><br><small>Align the object in the middle of the capture area before relying on this review-only ranking.<br>" + closeup_lines.join("<br>") + "</small>";
    }
    if (!saved_snapshot) for (const auto& d : detections) lines << QString("<b>%1 · %2</b> &nbsp; %3% &nbsp; <span style='color:#D99A70'>REVIEW</span><br><small>%4</small>")
      .arg(html_escape(QString::fromStdString(d.ref)), html_escape(QString::fromStdString(d.kind))).arg(std::round(d.confidence * 100)).arg(html_escape(QString::fromStdString(d.value)));
    if (saved_snapshot) lines << "<small>Full-frame detector candidates are intentionally withheld from this still-image outcome because the close-up classifier is the more appropriate review signal for a centred target.</small>";
    const bool has_snapshot_evidence = !microcontrollers.empty() || !snapshot_predictions.empty();
    candidates_->setHtml(!saved_snapshot && detections.empty() && !has_snapshot_evidence ? lines.join("<hr>") + "<hr>No component candidate met the configured threshold. Add a correction only if you can verify the object from markings, package, BOM, or a datasheet." : lines.join("<hr>"));
  }

  void update_hardware(const nlohmann::json& result, bool saved_snapshot) {
    const auto accepted = result.value("conclusion_status", "needs_more_evidence") == "candidate_conclusion";
    auto conclusion = QString::fromStdString(result.value("conclusion", "No reliable board conclusion from this frame"));
    if (!accepted && result.contains("microcontroller_evidence") && !result["microcontroller_evidence"].empty()) conclusion = QString::fromStdString(result["microcontroller_evidence"][0].value("name", "Microcontroller")) + " is a bare microcontroller candidate; no board conclusion.";
    inference_label_->setText(accepted ? (saved_snapshot ? "SNAPSHOT OUTCOME / BOARD CANDIDATE" : "INFERENCE PASS / BOARD CANDIDATE READY") : "INFERENCE PASS / NEEDS MORE EVIDENCE");
    conclusion_->setText(conclusion);
    if (!result["evidence"].empty()) confidence_->setText(current_quality_ + " " + QString::fromStdString(result["evidence"][0].get<std::string>()));
    QStringList marks; for (const auto& mark : result["recognized_markings"]) marks << QString::fromStdString(mark.get<std::string>());
    markings_->setText("Marking read: " + (marks.isEmpty() ? QString("—") : marks.join(" · ")));
    last_outcome_ = result;
    last_outcome_["origin"] = last_analysis_origin_.toStdString();
    last_outcome_["quality"] = current_quality_.toStdString();
    QStringList lines;
    lines << QString("<b>%1</b><br><small>%2</small>").arg(html_escape(last_analysis_origin_), html_escape(current_quality_));
    if (result.contains("microcontroller_evidence")) for (const auto& microcontroller : result["microcontroller_evidence"]) lines << QString("<b>BARE MICROCONTROLLER CANDIDATE</b><br>%1 · %2 · REVIEW").arg(html_escape(QString::fromStdString(microcontroller.value("name", "unknown"))), html_escape(QString::fromStdString(microcontroller.value("package", "verify package"))));
    for (const auto& component : result["components"]) lines << QString("<b>%1</b> · %2% · REVIEW").arg(html_escape(QString::fromStdString(component.value("kind", "candidate")))).arg(std::round(component.value("confidence",0.F)*100));
    if (!result["board_matches"].empty()) {
      const auto& top = result["board_matches"][0];
      lines.prepend(QString("<b>BOARD RANK</b> &nbsp; %1 &nbsp; %2% %3")
        .arg(html_escape(QString::fromStdString(top.value("name", "unknown")))).arg(std::round(top.value("confidence",0.F)*100)).arg(accepted ? status_pill("CANDIDATE") : status_pill("REVIEW", "#E68A5B")));
      last_reference_url_ = QString::fromStdString(top.value("source_url", ""));
      reference_button_->setEnabled(!last_reference_url_.isEmpty());
      if (!last_reference_url_.isEmpty()) lines << QString("<small>Reference: %1</small>").arg(html_escape(last_reference_url_));
    }
    candidates_->setHtml(lines.isEmpty() ? "No board candidate available." : lines.join("<hr>"));
  }

  InferenceEngine& engine_;
  std::unique_ptr<QCamera> camera_;
  QMediaCaptureSession capture_session_;
  QVideoWidget* video_{};
  QButtonGroup* mode_group_{};
  QPushButton *component_mode_{}, *board_mode_{}, *arm_button_{}, *pause_button_{}, *snapshot_button_{}, *open_image_button_{}, *correct_button_{}, *reference_button_{};
  QLabel *heading_{}, *intro_{}, *feed_status_{}, *inference_label_{}, *conclusion_{}, *confidence_{}, *markings_{};
  QTextEdit* candidates_{};
  QElapsedTimer last_sample_;
  bool board_mode_active_{false}, scanning_{false}, processing_{false};
  QImage last_frame_;
  QString current_quality_, last_snapshot_path_, last_analysis_origin_, last_reference_url_;
  nlohmann::json last_outcome_ = nlohmann::json::object();
};

int main(int argc, char* argv[]) {
  QApplication app(argc, argv);
  const std::filesystem::path data = env_or("CIRCUIT_LENS_DATA_DIR", "../backend-cpp/data");
  const float threshold = std::stof(env_or("CONFIDENCE_THRESHOLD", "0.60"));
  InferenceEngine engine(data, threshold);
  app.setStyleSheet(R"(
    * { font-family: "DejaVu Sans"; } QMainWindow, QWidget { background:#10120f; color:#f1f0ea; } #rail { background:#12140f; border-right:1px solid #31372d; } #brand { color:#f1f0ea; font-size:15px; font-weight:800; letter-spacing:2px; } #brand small, #runtime { color:#81887b; font-size:10px; letter-spacing:1px; } #railItem, #railActive { text-align:left; padding:12px; border:0; font-size:12px; letter-spacing:1px; } #railItem { color:#989f91; background:#12140f; } #railActive { color:#a4ff3f; background:#1a2116; border-left:2px solid #a4ff3f; } #eyebrow { color:#92998b; font-size:10px; font-weight:800; letter-spacing:2px; } #heading { font-size:28px; font-weight:700; } #intro { color:#abb1a4; max-width:650px; font-size:12px; } #primary { color:#10120f; background:#a4ff3f; border:0; font-weight:800; padding:12px 16px; } #secondary, #recordAction { color:#e5e8e0; background:#20251f; border:1px solid #4a5146; font-weight:700; padding:10px 14px; } #recordAction { color:#25301d; background:#d6e7a8; border-color:#91a568; font-size:10px; padding:7px 9px; } #recordAction:disabled { color:#777b70; background:#d6d2c4; border-color:#b5b09f; } #mode { color:#a6aea0; background:#171a16; border:1px solid #424a3d; padding:10px 15px; font-size:11px; text-align:left; } #mode:checked { color:#a4ff3f; border-color:#a4ff3f; background:#1b2417; } #viewport, #evidence { background:#171a16; border:1px solid #333a30; padding:15px; } #feed, #inference { color:#a4ff3f; font-size:10px; font-weight:700; letter-spacing:1px; } #calibration { color:#858c80; font-size:9px; } QVideoWidget { background:#050605; border:1px solid #4a5442; } #conclusion { color:#f1f0ea; font-size:23px; font-weight:700; padding:10px 0; } #confidence { color:#b2b9aa; font-size:12px; line-height:1.4; } #markings { color:#a4ff3f; background:#11130f; border-left:2px solid #a4ff3f; padding:10px; font-size:11px; } #instruction { color:#858c80; font-size:11px; line-height:1.5; } #record { background:#eae6d7; border:1px solid #c9c5b5; padding:17px; } #record #eyebrow { color:#50584c; } #candidates { background:#eae6d7; color:#20251d; border:1px solid #b8b4a4; font-size:12px; } )");
  InspectionWindow window(engine);
  window.show();
  return app.exec();
}

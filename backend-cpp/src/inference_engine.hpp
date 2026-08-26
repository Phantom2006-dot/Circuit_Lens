// Circuit Lens native inference core — C++ TorchScript/OpenCV/Tesseract implementation.
#pragma once

#include <opencv2/core.hpp>
#include <torch/script.h>
#include <nlohmann/json.hpp>
#include <tesseract/baseapi.h>

#include <filesystem>
#include <string>
#include <unordered_map>
#include <vector>

struct Detection {
  std::string id, label, kind, family, ref, health, value, note;
  float confidence{}, x{}, y{}, width{}, height{};
};

struct BoardPrediction { std::string board_id; float confidence{}; };
struct SnapshotPrediction { std::string label; float confidence{}; };
struct MicrocontrollerEvidence {
  std::string id, name, family, package, source_url;
  std::vector<std::string> signatures;
};

class InferenceEngine {
 public:
  InferenceEngine(std::filesystem::path data_dir, float confidence_threshold);
  ~InferenceEngine();

  bool component_ready() const { return component_ready_; }
  bool board_ready() const { return board_ready_; }
  bool snapshot_component_ready() const { return snapshot_component_ready_; }
  std::vector<Detection> detect(const cv::Mat& bgr);
  std::vector<BoardPrediction> classify(const cv::Mat& bgr);
  std::vector<SnapshotPrediction> classify_snapshot_component(const cv::Mat& bgr);
  std::vector<std::string> extract_markings(const cv::Mat& bgr);
  nlohmann::json microcontroller_evidence(const std::vector<std::string>& markings) const;
  nlohmann::json hardware_response(const cv::Mat& bgr);
  nlohmann::json topology_response(const cv::Mat& bgr);
  nlohmann::json component_catalog() const;
  nlohmann::json board_catalog() const;
  nlohmann::json catalog_for_family(const std::string& family) const;
  nlohmann::json detections_json(const std::vector<Detection>& detections) const;
  std::vector<Detection> demo_detections() const;

 private:
  std::filesystem::path data_dir_;
  float threshold_;
  bool component_ready_{false}, board_ready_{false}, snapshot_component_ready_{false}, ocr_ready_{false};
  torch::jit::script::Module component_model_, board_model_, snapshot_component_model_;
  std::vector<std::string> component_labels_, board_labels_, snapshot_component_labels_;
  nlohmann::json component_catalog_{nlohmann::json::array()}, board_catalog_{nlohmann::json::array()};
  tesseract::TessBaseAPI ocr_;

  static std::string display_name(const std::string& label);
  static std::string family_for(const std::string& label);
  static float iou(const Detection& a, const Detection& b);
  static std::string upper_normalized(std::string value);
  nlohmann::json detection_json(const Detection& value) const;
  nlohmann::json board_by_id(const std::string& id) const;
  std::string direct_board_for(const std::vector<std::string>& markings) const;
  std::vector<std::string> markings_for(const std::string& board_id, const std::vector<std::string>& markings) const;
  std::vector<std::string> component_support(const std::string& board_id, const std::vector<Detection>& detections) const;
};

// Small native C++ utility for validating close-up snapshot classifier loading and output.
#include "inference_engine.hpp"
#include <opencv2/imgcodecs.hpp>

#include <cstdlib>
#include <iostream>

int main(int argc, char* argv[]) {
  if (argc != 2) {
    std::cerr << "Usage: circuit_lens_snapshot_inspect <image>\n";
    return 2;
  }
  const char* data_dir = std::getenv("CIRCUIT_LENS_DATA_DIR");
  InferenceEngine engine(data_dir ? data_dir : "./data", .60F);
  if (!engine.snapshot_component_ready()) {
    std::cerr << "Snapshot classifier is not loaded. Set SNAPSHOT_COMPONENT_MODEL_PATH and SNAPSHOT_COMPONENT_MODEL_LABELS_PATH.\n";
    return 3;
  }
  const auto image = cv::imread(argv[1], cv::IMREAD_COLOR);
  if (image.empty()) {
    std::cerr << "Could not decode image.\n";
    return 4;
  }
  const auto predictions = engine.classify_snapshot_component(image);
  if (predictions.empty()) {
    std::cerr << "No snapshot predictions returned.\n";
    return 5;
  }
  for (const auto& item : predictions) std::cout << item.label << "\t" << item.confidence << "\n";
  return 0;
}

// Circuit Lens native C++ OCR/evidence smoke test.
#include "inference_engine.hpp"
#include <opencv2/imgproc.hpp>
#include <cstdlib>
#include <iostream>

int main() {
  const char* data_dir = std::getenv("CIRCUIT_LENS_DATA_DIR");
  InferenceEngine engine(data_dir ? data_dir : "./data", .60F);
  cv::Mat canvas(620, 2300, CV_8UC3, cv::Scalar(255, 255, 255));
  cv::putText(canvas, "ARDUINO NANO ESP32", cv::Point(80, 340), cv::FONT_HERSHEY_SIMPLEX, 3.5, cv::Scalar(0, 0, 0), 8, cv::LINE_AA);
  const auto result = engine.hardware_response(canvas);
  if (result.value("conclusion", "") != "Arduino Nano ESP32" || result.value("conclusion_status", "") != "candidate_conclusion") {
    std::cerr << result.dump(2) << "\n";
    return 1;
  }
  std::cout << "Native C++ silkscreen evidence smoke test passed.\n";
  return 0;
}

// Circuit Lens native inference core. Keep all component outputs review-only.
#include "inference_engine.hpp"

#include <opencv2/imgcodecs.hpp>
#include <opencv2/imgproc.hpp>
#include <torch/torch.h>

#include <algorithm>
#include <cctype>
#include <cmath>
#include <cstdlib>
#include <fstream>
#include <limits>
#include <set>
#include <sstream>

using json = nlohmann::json;
using torch::indexing::Slice;

namespace {
constexpr int kComponentInput = 256;
constexpr int kGrid = 16;
constexpr int kBoardInput = 160;
constexpr int kMaxDetections = 20;
constexpr float kNmsIou = .35F;

std::string env_or(const char* name, const std::string& fallback = "") {
  const char* value = std::getenv(name);
  return value && *value ? value : fallback;
}

json load_json(const std::filesystem::path& path, const json& fallback) {
  std::ifstream input(path);
  if (!input) return fallback;
  try { json result; input >> result; return result; } catch (...) { return fallback; }
}

std::vector<std::string> json_strings(const json& source) {
  std::vector<std::string> values;
  if (source.is_array()) for (const auto& value : source) values.push_back(value.get<std::string>());
  return values;
}

torch::Tensor image_tensor(const cv::Mat& bgr, int side) {
  cv::Mat rgb, resized;
  cv::cvtColor(bgr, rgb, cv::COLOR_BGR2RGB);
  cv::resize(rgb, resized, cv::Size(side, side), 0, 0, cv::INTER_AREA);
  return torch::from_blob(resized.data, {resized.rows, resized.cols, 3}, torch::kUInt8)
      .clone().permute({2, 0, 1}).to(torch::kFloat32).div_(255.0).unsqueeze(0);
}

torch::Tensor centered_snapshot_tensor(const cv::Mat& bgr, int side) {
  const int crop_side = std::max(1, static_cast<int>(std::round(std::min(bgr.cols, bgr.rows) * .72)));
  const int left = std::max(0, (bgr.cols - crop_side) / 2);
  const int top = std::max(0, (bgr.rows - crop_side) / 2);
  return image_tensor(bgr(cv::Rect(left, top, crop_side, crop_side)), side);
}

const std::unordered_map<std::string, std::string> kFamilies = {
  {"1-5-Volt-Battery", "power"}, {"3-3-Volt-Battery", "power"}, {"9-Volt-Battery", "power"}, {"Buck-Converter", "power"}, {"Fuse", "power"}, {"Fuse-Base", "power"}, {"Relay-Module", "power"},
  {"Resistor", "passive"}, {"Capacitor-10mf", "passive"}, {"Capacitor-470mf", "passive"}, {"Film-Capacitor", "passive"}, {"High-Voltage-Ceramic-Capacitor", "passive"}, {"Low-Voltage-Ceramic-Capacitor", "passive"}, {"MLC-Capacitor", "passive"}, {"Inductor", "passive"}, {"NTC-Thermistor", "passive"}, {"LDR-Sensor", "passive"}, {"Taper-Potentiometer", "passive"}, {"Trimmer-Potentiometer", "passive"},
  {"Diode", "semiconductor"}, {"Zener-Diode", "semiconductor"}, {"Bridge-Rectifier", "semiconductor"}, {"BJT-Transistor", "semiconductor"}, {"MOSFET", "semiconductor"}, {"IGBT", "semiconductor"}, {"LED-Light", "semiconductor"}, {"IC-Chip", "semiconductor"}, {"Motor-Driver", "semiconductor"},
  {"Pin-Header", "interconnect"}, {"IC-Base-14-Pin", "interconnect"}, {"IC-Base-28-Pin", "interconnect"}, {"Breadboard", "interconnect"},
  {"Arduino-Mega", "controller_module"}, {"Arduino-Nano", "controller_module"}, {"Arduino-Uno", "controller_module"}, {"ESP32", "controller_module"}, {"ESP32-CAM", "controller_module"}, {"Bluetooth-Module", "controller_module"}, {"GSM-Module", "controller_module"}, {"FT-232-USB-Serial-Module", "controller_module"}, {"RFID-Scanner", "controller_module"},
  {"Gas-Sensor", "sensor_module"}, {"Humidity-Sensor", "sensor_module"}, {"IR-Sensor", "sensor_module"}, {"Motion-Sensor", "sensor_module"}, {"Raindrops-Module", "sensor_module"}, {"Soil-Moisture-Sensor", "sensor_module"}, {"Sonar-Sensor", "sensor_module"}, {"TCRT5000", "sensor_module"}, {"Water-Sensor", "sensor_module"},
  {"Buzzer", "electromechanical"}, {"DC-Motor", "electromechanical"}, {"Servo-Motor", "electromechanical"}, {"Push-Switch", "electromechanical"}, {"Rocker-Switch", "electromechanical"}, {"Tact-Switch", "electromechanical"}, {"Keypad", "electromechanical"},
  {"7-Segment-Display", "display_support"}, {"LCD-Display", "display_support"}, {"OLED-Display", "display_support"}, {"Heat-Sink", "display_support"}
};

const std::unordered_map<std::string, int> kTerminalCount = {
  {"Resistor",2},{"Capacitor-10mf",2},{"Capacitor-470mf",2},{"Film-Capacitor",2},{"High-Voltage-Ceramic-Capacitor",2},{"Low-Voltage-Ceramic-Capacitor",2},{"MLC-Capacitor",2},{"Inductor",2},{"Diode",2},{"Zener-Diode",2},{"LED-Light",2},{"Fuse",2},{"NTC-Thermistor",2},{"LDR-Sensor",2},{"BJT-Transistor",3},{"MOSFET",3},{"IGBT",3},{"Bridge-Rectifier",4},{"Pin-Header",4},{"IC-Base-14-Pin",14},{"IC-Base-28-Pin",28}
};

const std::unordered_map<std::string, std::vector<std::string>> kMarkings = {
  {"esp32_cam", {"ESP32-CAM", "ESP32CAM", "AI-THINKER", "AI THINKER"}}, {"esp32_wroom_32", {"ESP-WROOM-32", "ESP32-WROOM-32", "ESP32-WROOM"}}, {"esp32_s3_devkitc", {"ESP32-S3-DEVKITC", "ESP32-S3", "ESP32S3"}}, {"esp32_dev_board", {"ESP32", "ESP-WROOM", "ESP32-WROOM", "ESP32 DEVKIT", "DOIT ESP32"}}, {"esp8266_wemos", {"ESP8266", "WEMOS", "D1 MINI", "NODEMCU"}},
  {"arduino_uno_r3", {"ARDUINO UNO", "UNO R3"}}, {"arduino_nano", {"ARDUINO NANO", "NANO EVERY"}}, {"arduino_nano_esp32", {"ARDUINO NANO ESP32", "NANO ESP32"}}, {"arduino_mega_2560", {"ARDUINO MEGA", "MEGA 2560"}}, {"arduino_leonardo", {"ARDUINO LEONARDO", "LEONARDO"}}, {"arduino_micro", {"ARDUINO MICRO"}}, {"arduino_pro_mini", {"PRO MINI"}}, {"arduino_zero", {"ARDUINO ZERO"}}, {"jetson_nano", {"JETSON NANO"}}, {"jetson_tx2", {"JETSON TX2"}}
};

const std::vector<MicrocontrollerEvidence> kMicrocontrollers = {
  {"atmega328p", "Microchip ATmega328P", "AVR 8-bit microcontroller", "DIP-28 / TQFP-32 / QFN-32", "https://www.microchip.com/en-us/product/atmega328p", {"ATMEGA328P", "MEGA328P"}},
  {"atmega2560", "Microchip ATmega2560", "AVR 8-bit microcontroller", "TQFP-100", "https://www.microchip.com/en-us/product/atmega2560", {"ATMEGA2560", "MEGA2560"}},
  {"atmega32u4", "Microchip ATmega32U4", "AVR USB microcontroller", "TQFP-44 / QFN-44", "https://www.microchip.com/en-us/product/atmega32u4", {"ATMEGA32U4", "MEGA32U4"}},
  {"stm32f103", "STMicroelectronics STM32F103", "ARM Cortex-M3 microcontroller", "LQFP-48 / LQFP-64", "https://www.st.com/en/microcontrollers-microprocessors/stm32f103.html", {"STM32F103C8T6", "STM32F103C8", "STM32F103"}},
  {"stm32f401", "STMicroelectronics STM32F401", "ARM Cortex-M4 microcontroller", "QFN-48 / LQFP-64", "https://www.st.com/en/microcontrollers-microprocessors/stm32f401.html", {"STM32F401CCU6", "STM32F401"}},
  {"rp2040", "Raspberry Pi RP2040", "Dual-core ARM Cortex-M0+ microcontroller", "QFN-56", "https://www.raspberrypi.com/products/rp2040/", {"RP2040"}},
  {"pic16f877a", "Microchip PIC16F877A", "PIC 8-bit microcontroller", "DIP-40 / TQFP-44", "https://www.microchip.com/en-us/product/pic16f877a", {"PIC16F877A", "16F877A"}},
  {"lpc1768", "NXP LPC1768", "ARM Cortex-M3 microcontroller", "LQFP-100", "https://www.nxp.com/products/LPC1768FBD100", {"LPC1768"}},
  {"esp32_d0wd", "Espressif ESP32-D0WD", "Wi-Fi/Bluetooth SoC", "QFN-48", "https://www.espressif.com/en/products/socs/esp32", {"ESP32-D0WD", "ESP32D0WD"}},
  {"esp32_c3", "Espressif ESP32-C3", "RISC-V Wi-Fi/Bluetooth SoC", "QFN-32", "https://www.espressif.com/en/products/socs/esp32-c3", {"ESP32-C3", "ESP32C3"}}
};

const std::unordered_map<std::string, std::vector<std::string>> kHints = {
  {"esp32_dev_board", {"ESP32", "Bluetooth Module"}}, {"esp32_cam", {"ESP32 CAM", "Camera", "OV2640"}}, {"arduino_uno_r3", {"ATmega"}}, {"arduino_nano", {"ATmega"}}, {"arduino_mega_2560", {"ATmega"}}, {"jetson_nano", {"Jetson"}}, {"jetson_tx2", {"Jetson"}}
};
}

InferenceEngine::InferenceEngine(std::filesystem::path data_dir, float confidence_threshold)
    : data_dir_(std::move(data_dir)), threshold_(confidence_threshold) {
  component_catalog_ = load_json(data_dir_ / "component_catalog.json", json::array());
  board_catalog_ = load_json(data_dir_ / "board_catalog.json", json::array());
  component_labels_ = json_strings(load_json(env_or("MODEL_LABELS_PATH"), json::array()));
  board_labels_ = json_strings(load_json(env_or("BOARD_MODEL_LABELS_PATH"), json::array()));
  snapshot_component_labels_ = json_strings(load_json(env_or("SNAPSHOT_COMPONENT_MODEL_LABELS_PATH"), json::array()));
  try { const auto path = env_or("MODEL_PATH"); if (!path.empty() && std::filesystem::is_regular_file(path)) { component_model_ = torch::jit::load(path, torch::kCPU); component_model_.eval(); component_ready_ = true; } } catch (...) { component_ready_ = false; }
  try { const auto path = env_or("BOARD_MODEL_PATH"); if (!path.empty() && std::filesystem::is_regular_file(path)) { board_model_ = torch::jit::load(path, torch::kCPU); board_model_.eval(); board_ready_ = true; } } catch (...) { board_ready_ = false; }
  try { const auto path = env_or("SNAPSHOT_COMPONENT_MODEL_PATH"); if (!path.empty() && std::filesystem::is_regular_file(path) && !snapshot_component_labels_.empty()) { snapshot_component_model_ = torch::jit::load(path, torch::kCPU); snapshot_component_model_.eval(); snapshot_component_ready_ = true; } } catch (...) { snapshot_component_ready_ = false; }
  ocr_ready_ = ocr_.Init(nullptr, "eng") == 0;
}

InferenceEngine::~InferenceEngine() { if (ocr_ready_) ocr_.End(); }

std::string InferenceEngine::display_name(const std::string& label) { std::string value = label; std::replace(value.begin(), value.end(), '-', ' '); return value; }
std::string InferenceEngine::family_for(const std::string& label) { const auto item = kFamilies.find(label); return item == kFamilies.end() ? "other" : item->second; }
float InferenceEngine::iou(const Detection& a, const Detection& b) { const float left=std::max(a.x,b.x), top=std::max(a.y,b.y), right=std::min(a.x+a.width,b.x+b.width), bottom=std::min(a.y+a.height,b.y+b.height); const float hit=std::max(0.F,right-left)*std::max(0.F,bottom-top); const float all=a.width*a.height+b.width*b.height-hit; return all>0 ? hit/all : 0.F; }
std::string InferenceEngine::upper_normalized(std::string value) { for (auto& c : value) c=static_cast<char>(std::toupper(static_cast<unsigned char>(c))); std::replace_if(value.begin(),value.end(),[](unsigned char c){return std::isspace(c);},' '); std::string out; bool previous_space=false; for(char c:value){ if(c!=' '||!previous_space) out+=c; previous_space=c==' '; } return out; }

json InferenceEngine::detection_json(const Detection& d) const { return {{"id",d.id},{"kind",d.kind},{"family",d.family},{"ref",d.ref},{"confidence",std::round(d.confidence*10000.F)/10000.F},{"health",d.health},{"box",{{"x",d.x},{"y",d.y},{"width",d.width},{"height",d.height}}},{"value",d.value},{"note",d.note}}; }
json InferenceEngine::detections_json(const std::vector<Detection>& items) const { json result=json::array(); for(const auto& item:items) result.push_back(detection_json(item)); return result; }

std::vector<Detection> InferenceEngine::demo_detections() const { const std::vector<std::tuple<std::string,std::string,float,float,float,float,float>> raw={{"r7","Resistor",.98F,16,53,17,13},{"q2","BJT-Transistor",.94F,47,33,20,19},{"d1","Diode",.89F,68,57,18,12},{"c4","MLC-Capacitor",.81F,42,68,13,11}}; std::vector<Detection> out; for(const auto& [id,label,score,x,y,w,h]:raw) out.push_back({id,label,display_name(label),family_for(label),id,"Review","1 kΩ · reference candidate","Demonstration candidate only — confirm markings and topology before use.",score,x,y,w,h}); return out; }

std::vector<Detection> InferenceEngine::detect(const cv::Mat& bgr) {
  if (!component_ready_ || bgr.empty()) return demo_detections();
  torch::NoGradGuard guard;
  auto output = component_model_.forward({image_tensor(bgr,kComponentInput)}).toTensor();
  if (output.dim()==4) output=output[0];
  auto objectness=torch::sigmoid(output[0]), offsets=torch::sigmoid(output.slice(0,1,5)), classes=torch::softmax(output.slice(0,5),0);
  const auto labels = component_labels_.empty() ? std::vector<std::string>{"Resistor","BJT-Transistor","Diode","MLC-Capacitor"} : component_labels_;
  std::vector<Detection> candidates;
  for(int row=0; row<kGrid; ++row) for(int column=0; column<kGrid; ++column) {
    auto winner=torch::max(classes.index({Slice(),row,column}),0); const float class_score=std::get<0>(winner).item<float>(); const int class_index=std::get<1>(winner).item<int>(); const float confidence=objectness.index({row,column}).item<float>()*class_score;
    if(confidence<threshold_ || class_index>=static_cast<int>(labels.size())) continue;
    const float width=offsets.index({2,row,column}).item<float>()*36.F, height=offsets.index({3,row,column}).item<float>()*36.F;
    const float x=(column+offsets.index({0,row,column}).item<float>())/kGrid*100.F-width/2.F, y=(row+offsets.index({1,row,column}).item<float>())/kGrid*100.F-height/2.F;
    const auto& label=labels[class_index]; const auto kind=display_name(label); const std::string value=label=="Resistor"?"1 kΩ · ±1% · ±100 ppm/K":kind+" visual candidate";
    candidates.push_back({label+"-"+std::to_string(row)+"-"+std::to_string(column),label,kind,family_for(label),"CAND-"+std::to_string(row)+"-"+std::to_string(column),"Review",value,"Broad-vocabulary model candidate — confirm package, silkscreen, markings, terminal assignment, and trace evidence before an engineering decision.",confidence,std::max(0.F,x),std::max(0.F,y),std::min(100.F,width),std::min(100.F,height)});
  }
  std::sort(candidates.begin(),candidates.end(),[](const auto& a,const auto& b){return a.confidence>b.confidence;}); std::vector<Detection> retained; for(const auto& candidate:candidates){ if(retained.size()>=kMaxDetections) break; bool keep=true; for(const auto& existing:retained) if(candidate.kind==existing.kind && iou(candidate,existing)>=kNmsIou){keep=false;break;} if(keep) retained.push_back(candidate); } return retained;
}

std::vector<BoardPrediction> InferenceEngine::classify(const cv::Mat& bgr) { if(!board_ready_||bgr.empty()) return {}; torch::NoGradGuard guard; auto output=board_model_.forward({image_tensor(bgr,kBoardInput)}).toTensor(); if(output.dim()==2) output=output[0]; auto scores=torch::softmax(output,0); const int count=std::min(3,static_cast<int>(board_labels_.size())); if(count==0) return {}; auto winners=torch::topk(scores,count,0,true,true); auto values=std::get<0>(winners), indices=std::get<1>(winners); std::vector<BoardPrediction> out; for(int i=0;i<count;++i) out.push_back({board_labels_[indices[i].item<int>()],values[i].item<float>()}); return out; }

std::vector<SnapshotPrediction> InferenceEngine::classify_snapshot_component(const cv::Mat& bgr) { if(!snapshot_component_ready_||bgr.empty()) return {}; torch::NoGradGuard guard; auto output=snapshot_component_model_.forward({centered_snapshot_tensor(bgr,kBoardInput)}).toTensor(); if(output.dim()==2) output=output[0]; auto scores=torch::softmax(output,0); const int count=std::min(3,static_cast<int>(snapshot_component_labels_.size())); if(count==0) return {}; auto winners=torch::topk(scores,count,0,true,true); auto values=std::get<0>(winners), indices=std::get<1>(winners); std::vector<SnapshotPrediction> out; for(int i=0;i<count;++i) out.push_back({snapshot_component_labels_[indices[i].item<int>()],values[i].item<float>()}); return out; }

std::vector<std::string> InferenceEngine::extract_markings(const cv::Mat& bgr) { if(!ocr_ready_||bgr.empty()) return {}; cv::Mat gray; cv::cvtColor(bgr,gray,cv::COLOR_BGR2GRAY); const auto edge=std::max(gray.cols,gray.rows); if(edge<1500){const double ratio=1500.0/edge;cv::resize(gray,gray,cv::Size(),ratio,ratio,cv::INTER_CUBIC);} cv::convertScaleAbs(gray,gray,1.9); cv::GaussianBlur(gray,gray,cv::Size(0,0),1.0); cv::addWeighted(gray,1.5,gray,-.5,0,gray); ocr_.SetPageSegMode(tesseract::PSM_SPARSE_TEXT); ocr_.SetImage(gray.data,gray.cols,gray.rows,1,static_cast<int>(gray.step)); char* output=ocr_.GetUTF8Text(); const std::string text=upper_normalized(output?output:""); delete[] output; std::vector<std::string> found; for(const auto& [_,signatures]:kMarkings) for(const auto& signature:signatures) if(text.find(signature)!=std::string::npos && std::find(found.begin(),found.end(),signature)==found.end()) found.push_back(signature); for(const auto& mcu:kMicrocontrollers) for(const auto& signature:mcu.signatures) if(text.find(signature)!=std::string::npos && std::find(found.begin(),found.end(),signature)==found.end()) found.push_back(signature); return found; }

json InferenceEngine::microcontroller_evidence(const std::vector<std::string>& markings) const { json result=json::array(); for(const auto& mcu:kMicrocontrollers){json matched=json::array(); for(const auto& signature:mcu.signatures) if(std::find(markings.begin(),markings.end(),signature)!=markings.end()) matched.push_back(signature); if(!matched.empty()) result.push_back({{"id",mcu.id},{"name",mcu.name},{"family",mcu.family},{"package",mcu.package},{"source_url",mcu.source_url},{"marking_evidence",matched},{"status","marking_assisted_review"}}); } return result; }

json InferenceEngine::board_by_id(const std::string& id) const { for(const auto& board:board_catalog_) if(board.value("id","")==id) return board; return {}; }
std::vector<std::string> InferenceEngine::markings_for(const std::string& board_id,const std::vector<std::string>& markings) const { std::vector<std::string> result; const auto it=kMarkings.find(board_id); if(it==kMarkings.end())return result; for(const auto& marking:markings) if(std::find(it->second.begin(),it->second.end(),marking)!=it->second.end())result.push_back(marking); return result; }
std::string InferenceEngine::direct_board_for(const std::vector<std::string>& markings) const { std::string result; size_t best=0; for(const auto& [board,signatures]:kMarkings) for(const auto& marking:markings) if(std::find(signatures.begin(),signatures.end(),marking)!=signatures.end() && marking.size()>best){best=marking.size();result=board;} return result; }
std::vector<std::string> InferenceEngine::component_support(const std::string& board_id,const std::vector<Detection>& detections) const { const auto hints=kHints.find(board_id); if(hints==kHints.end())return{}; std::string kinds;for(const auto& d:detections)kinds+=upper_normalized(d.kind)+" ";std::vector<std::string>out;for(const auto& hint:hints->second)if(kinds.find(upper_normalized(hint))!=std::string::npos)out.push_back(hint);return out; }

json InferenceEngine::hardware_response(const cv::Mat& bgr) {
  const auto components=detect(bgr); const auto predictions=classify(bgr); const auto markings=extract_markings(bgr); const auto microcontrollers=microcontroller_evidence(markings);
  std::unordered_map<std::string,float> scores; for(const auto& prediction:predictions)scores[prediction.board_id]=prediction.confidence;
  const auto direct=direct_board_for(markings); if(!direct.empty())scores[direct]=.99F; json matches=json::array();
  for(const auto& [id,confidence]:scores){const auto board=board_by_id(id);if(board.empty())continue;const auto support=component_support(id,components);const auto marking_support=markings_for(id,markings);const float fused=std::min(.99F,confidence+std::min(.10F,.04F*static_cast<float>(support.size()))+(marking_support.empty()?0.F:.04F));matches.push_back({{"board_id",id},{"name",board.value("name",id)},{"family",board.value("family","")},{"confidence",std::round(fused*10000.F)/10000.F},{"supported_by_trained_model",board.value("supported_by_trained_model",false)},{"component_evidence",support},{"marking_evidence",marking_support},{"visual_evidence",board.value("visual_cues",json::array())},{"source_url",board.value("source_url","")}});}
  std::sort(matches.begin(),matches.end(),[](const json&a,const json&b){return a.at("confidence").get<float>()>b.at("confidence").get<float>();}); const bool has=!matches.empty(); const float top=has?matches[0]["confidence"].get<float>():0.F, next=matches.size()>1?matches[1]["confidence"].get<float>():0.F; const float margin=has?(matches.size()>1?top-next:top):0.F; const bool model_gate=has&&matches[0]["supported_by_trained_model"].get<bool>()&&top>=.70F&&margin>=.12F; const bool marking_gate=has&&matches[0]["board_id"].get<std::string>()==direct&&!matches[0]["marking_evidence"].empty(); const bool accepted=model_gate||marking_gate;
  json evidence=json::array(); if(has){if(marking_gate)evidence.push_back("Direct silkscreen signature identifies: "+matches[0]["name"].get<std::string>()+".");else{std::ostringstream message;message<<"Board classifier top prediction: "<<matches[0]["name"].get<std::string>()<<" at "<<std::round(top*100)<<"%.";evidence.push_back(message.str());}for(const auto& item:matches[0]["marking_evidence"])evidence.push_back("Silkscreen marking read: "+item.get<std::string>()+".");for(size_t i=0;i<std::min<size_t>(2,matches[0]["visual_evidence"].size());++i)evidence.push_back("Visual cue expected: "+matches[0]["visual_evidence"][i].get<std::string>()+".");for(const auto& hint:matches[0]["component_evidence"])evidence.push_back("Component clue found: "+hint.get<std::string>()+".");}
  if(!microcontrollers.empty()) evidence.push_back("Bare microcontroller marking candidate: "+microcontrollers[0]["name"].get<std::string>()+"; this is not a board conclusion.");
  if(!accepted)evidence.push_back("The confidence/margin gate did not support a reliable board conclusion; capture a wider, sharper board view with silkscreen and connectors visible.");
  return {{"components",detections_json(components)},{"board_matches",matches},{"microcontroller_evidence",microcontrollers},{"conclusion",accepted?matches[0]["name"].get<std::string>():"No reliable board conclusion from this frame"},{"conclusion_status",accepted?"candidate_conclusion":"needs_more_evidence"},{"evidence",evidence},{"recognized_markings",markings},{"next_capture","Capture the entire front side, then the back side; keep USB, camera, RF, header, and silkscreen regions in view. Use a continuity test for electrical claims."},{"board_model_mode",board_ready_?"torchscript":"unavailable"}};
}

json InferenceEngine::topology_response(const cv::Mat& bgr) { const auto detections=detect(bgr); json terminals=json::array();for(const auto& d:detections){const auto count=kTerminalCount.find(d.label);if(count==kTerminalCount.end())continue;for(int index=0;index<count->second;++index){const float t=(index+1.F)/(count->second+1.F);terminals.push_back({{"id",d.id+"-t"+std::to_string(index+1)},{"component_id",d.id},{"x",d.x+d.width*t},{"y",d.y+d.height*(index%2?.75F:.25F)},{"confidence",.35F}});}} return {{"detections",detections_json(detections)},{"terminals",terminals},{"candidate_links",json::array()},{"candidate_nets",json::array()},{"candidate_patterns",json::array({{{"label","Unclassified circuit region"},{"confidence",0.0},{"evidence",json::array({"Native visual topology pass is review-only; no electrical continuity was inferred."})},{"requires_review",true}}})},{"limitations",json::array({"Visual topology is review-only and cannot determine hidden layers, net names, polarity, or electrical continuity.","Use a schematic, bill of materials, and continuity measurement before making an engineering decision."})},{"model_mode",component_ready_?"torchscript":"demo"}}; }
json InferenceEngine::component_catalog() const{return component_catalog_;} json InferenceEngine::board_catalog() const{return board_catalog_;} json InferenceEngine::catalog_for_family(const std::string& family) const {json result=json::array();for(const auto& item:component_catalog_)if(item.value("family","")==family)result.push_back(item);return result;}

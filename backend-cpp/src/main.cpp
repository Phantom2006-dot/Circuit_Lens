// Circuit Lens native C++ HTTP service — preserves the existing JSON API for local and browser clients.
#include "inference_engine.hpp"
#include <httplib.h>
#include <opencv2/imgcodecs.hpp>

#include <cstdlib>
#include <filesystem>
#include <iostream>
#include <set>
#include <sstream>

using json = nlohmann::json;

namespace {
std::string env_or(const char* key, const std::string& fallback="") { const char* value=std::getenv(key); return value&&*value?value:fallback; }
std::set<std::string> origins() { std::set<std::string> allowed; std::stringstream values(env_or("ALLOWED_ORIGINS","http://localhost:5173")); for(std::string value;std::getline(values,value,',');)if(!value.empty())allowed.insert(value);return allowed; }
void cors(const httplib::Request& req, httplib::Response& res, const std::set<std::string>& allowed) { const auto origin=req.get_header_value("Origin"); if(allowed.count(origin)){res.set_header("Access-Control-Allow-Origin",origin);res.set_header("Vary","Origin");} res.set_header("Access-Control-Allow-Methods","GET, POST, OPTIONS");res.set_header("Access-Control-Allow-Headers","Content-Type"); }
void reply(httplib::Response& res,const json& body,int status=200){res.status=status;res.set_content(body.dump(),"application/json");}
bool image_from_request(const httplib::Request& req, cv::Mat& image, httplib::Response& res){if(!req.has_file("image")){reply(res,{{"detail","An image multipart field is required."}},400);return false;}const auto file=req.get_file_value("image");if(file.content.size()>12*1024*1024){reply(res,{{"detail","Image must be 12 MB or smaller."}},413);return false;}if(file.content_type!="image/jpeg"&&file.content_type!="image/png"&&file.content_type!="image/webp"){reply(res,{{"detail","Upload a JPEG, PNG, or WebP image."}},415);return false;}std::vector<unsigned char> bytes(file.content.begin(),file.content.end());image=cv::imdecode(bytes,cv::IMREAD_COLOR);if(image.empty()){reply(res,{{"detail","The upload could not be decoded as an image."}},400);return false;}return true;}
}

int main(){
  const std::filesystem::path data=env_or("CIRCUIT_LENS_DATA_DIR","./data");
  const float threshold=std::stof(env_or("CONFIDENCE_THRESHOLD","0.60"));
  InferenceEngine engine(data,threshold); const auto allowed=origins(); httplib::Server server;
  server.set_pre_routing_handler([&](const httplib::Request& req,httplib::Response& res){cors(req,res,allowed);if(req.method=="OPTIONS"){res.status=204;return httplib::Server::HandlerResponse::Handled;}return httplib::Server::HandlerResponse::Unhandled;});
  server.set_post_routing_handler([&](const httplib::Request& req,httplib::Response& res){cors(req,res,allowed);});
  server.Get("/health",[&](const auto&,auto& res){reply(res,{{"status","ok"},{"model_mode",engine.component_ready()?"torchscript":"demo"},{"board_model_mode",engine.board_ready()?"torchscript":"unavailable"}});});
  server.Get("/v1/catalog",[&](const auto&,auto& res){reply(res,{{"references",engine.component_catalog()}});});
  server.Get(R"(/v1/catalog/(.+))",[&](const auto& req,auto& res){const auto records=engine.catalog_for_family(req.matches[1]);if(records.empty())reply(res,{{"detail","No component references found for this family."}},404);else reply(res,{{"references",records}});});
  server.Get("/v1/boards",[&](const auto&,auto& res){reply(res,{{"boards",engine.board_catalog()}});});
  server.Get("/v1/detections/demo",[&](const auto&,auto& res){reply(res,{{"detections",engine.detections_json(engine.demo_detections())},{"model_mode","demo"}});});
  server.Post("/v1/detections/infer",[&](const auto& req,auto& res){cv::Mat image;if(!image_from_request(req,image,res))return;const auto detections=engine.detect(image);reply(res,{{"detections",engine.detections_json(detections)},{"model_mode",engine.component_ready()?"torchscript":"demo"}});});
  server.Post("/v1/hardware/identify",[&](const auto& req,auto& res){cv::Mat image;if(!image_from_request(req,image,res))return;reply(res,engine.hardware_response(image));});
  server.Post("/v1/topology/analyze",[&](const auto& req,auto& res){cv::Mat image;if(!image_from_request(req,image,res))return;reply(res,engine.topology_response(image));});
  const int port=std::stoi(env_or("PORT","8080"));std::cout<<"Circuit Lens C++ API on 0.0.0.0:"<<port<<"\n";return server.listen("0.0.0.0",port)?0:1;
}

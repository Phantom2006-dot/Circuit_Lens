cmake_minimum_required(VERSION 3.20)
project(circuit_lens_desktop LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

if(NOT DEFINED ENV{TORCH_PREFIX})
  set(ENV{TORCH_PREFIX} "/usr/local/lib/python3.12/dist-packages/torch")
endif()
list(APPEND CMAKE_PREFIX_PATH "$ENV{TORCH_PREFIX}")

find_package(Qt6 REQUIRED COMPONENTS Core Gui Widgets Multimedia MultimediaWidgets)
find_package(Torch REQUIRED)
find_package(OpenCV REQUIRED COMPONENTS core imgproc imgcodecs)
find_package(PkgConfig REQUIRED)
pkg_check_modules(TESSERACT REQUIRED IMPORTED_TARGET tesseract)
find_package(nlohmann_json REQUIRED)

add_executable(circuit_lens_desktop
  src/main.cpp
  ../backend-cpp/src/inference_engine.cpp
)
target_include_directories(circuit_lens_desktop PRIVATE
  ${OpenCV_INCLUDE_DIRS}
  ${CMAKE_CURRENT_SOURCE_DIR}/../backend-cpp/src
)
target_link_libraries(circuit_lens_desktop PRIVATE
  Qt6::Core Qt6::Gui Qt6::Widgets Qt6::Multimedia Qt6::MultimediaWidgets
  ${TORCH_LIBRARIES}
  ${OpenCV_LIBS}
  PkgConfig::TESSERACT
  nlohmann_json::nlohmann_json
)
target_compile_options(circuit_lens_desktop PRIVATE -Wall -Wextra -Wpedantic)
set_property(TARGET circuit_lens_desktop PROPERTY BUILD_RPATH "$ENV{TORCH_PREFIX}/lib")
set_property(TARGET circuit_lens_desktop PROPERTY INSTALL_RPATH "$ORIGIN/../lib")

install(TARGETS circuit_lens_desktop RUNTIME DESTINATION bin)

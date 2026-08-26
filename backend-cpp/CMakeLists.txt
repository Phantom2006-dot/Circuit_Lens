cmake_minimum_required(VERSION 3.20)
project(circuit_lens_native LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

if(NOT DEFINED ENV{TORCH_PREFIX})
  set(ENV{TORCH_PREFIX} "/usr/local/lib/python3.12/dist-packages/torch")
endif()
list(APPEND CMAKE_PREFIX_PATH "$ENV{TORCH_PREFIX}")

find_package(Torch REQUIRED)
find_package(OpenCV REQUIRED COMPONENTS core imgproc imgcodecs)
find_package(PkgConfig REQUIRED)
pkg_check_modules(TESSERACT REQUIRED IMPORTED_TARGET tesseract)
find_package(nlohmann_json REQUIRED)
find_library(HTTPLIB_LIBRARY NAMES cpp-httplib httplib REQUIRED)

add_executable(circuit_lens_native
  src/main.cpp
  src/inference_engine.cpp
)
add_executable(circuit_lens_native_smoke
  tests/native_smoke.cpp
  src/inference_engine.cpp
)
add_executable(circuit_lens_snapshot_inspect
  tests/snapshot_inspect.cpp
  src/inference_engine.cpp
)
foreach(target circuit_lens_native circuit_lens_native_smoke circuit_lens_snapshot_inspect)
target_include_directories(${target} PRIVATE ${OpenCV_INCLUDE_DIRS} ${CMAKE_CURRENT_SOURCE_DIR}/src)
target_link_libraries(${target} PRIVATE
  ${TORCH_LIBRARIES}
  ${OpenCV_LIBS}
  PkgConfig::TESSERACT
  nlohmann_json::nlohmann_json
  ${HTTPLIB_LIBRARY}
)
target_compile_options(${target} PRIVATE -Wall -Wextra -Wpedantic)
set_property(TARGET ${target} PROPERTY CXX_STANDARD 17)
set_property(TARGET ${target} PROPERTY BUILD_RPATH "$ENV{TORCH_PREFIX}/lib")
set_property(TARGET ${target} PROPERTY INSTALL_RPATH "$ORIGIN/../lib")
endforeach()

install(TARGETS circuit_lens_native RUNTIME DESTINATION bin)
install(DIRECTORY data/ DESTINATION share/circuit-lens/data)

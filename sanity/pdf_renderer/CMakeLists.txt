cmake_minimum_required (VERSION 3.0)
project (pdf_renderer)

set(CMAKE_CXX_STANDARD 17)

list(APPEND CMAKE_MODULE_PATH "${PROJECT_SOURCE_DIR}/cmake")

find_package(Boost COMPONENTS system program_options filesystem)
find_package(Poppler-glib)

include_directories(${CMAKE_SOURCE_DIR})
include_directories(${POPPLER_INCLUDE_DIRS})


set(SRC create_thumbnails.cpp pdf_wrapper.cpp)
add_executable(create_thumbnails  ${SRC})
target_link_libraries(create_thumbnails ${POPPLER_LIBRARIES} ${Boost_LIBRARIES})


set(SRC extract_info.cpp pdf_wrapper.cpp)
add_executable(extract_info  ${SRC})
target_link_libraries(extract_info ${POPPLER_LIBRARIES} ${Boost_LIBRARIES})



find_package(PythonLibs 3 REQUIRED)
find_package(Boost COMPONENTS system program_options filesystem python3 numpy3)
SET(Boost_USE_STATIC_LIBS OFF)
SET(Boost_USE_MULTITHREADED OFF)
SET(Boost_USE_STATIC_RUNTIME OFF)

include_directories(${PYTHON_INCLUDE_DIRS})

set(SRC pdf_python.cpp pdf_wrapper.cpp)
add_library(pdf_python  SHARED ${SRC})
target_link_libraries(pdf_python ${POPPLER_LIBRARIES} ${Boost_LIBRARIES} ${PYTHON_LIBRARY})


set(SRC pdf_python_test.cpp )
add_executable(pdf_python_test  ${SRC})
target_link_libraries(pdf_python_test pdf_python)

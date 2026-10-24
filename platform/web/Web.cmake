# Browser build adapted from rozenmad/love-web (see readme.md).
set_target_properties(love PROPERTIES SUFFIX ".js")
option(LOVE_WEB_PROFILING "Preserve Wasm function names for browser profilers" OFF)
if(LOVE_WEB_PROFILING)
  target_link_options(love PRIVATE --profiling-funcs)
endif()
target_link_options(love PRIVATE
  -fexceptions
  "SHELL:--pre-js ${CMAKE_CURRENT_LIST_DIR}/persistence.js"
  "SHELL:--js-library ${CMAKE_CURRENT_LIST_DIR}/audio.js"
  "-sMIN_WEBGL_VERSION=2" "-sMAX_WEBGL_VERSION=2"
  "-sMODULARIZE=1" "-sEXPORT_NAME=Love" "-sALLOW_MEMORY_GROWTH=1"
  "-sFORCE_FILESYSTEM=1" "-sEXIT_RUNTIME=0"
  "-sEXPORTED_RUNTIME_METHODS=['FS','callMain']" "-sINVOKE_RUN=0"
  "-lidbfs.js")
set_property(TARGET love APPEND PROPERTY LINK_DEPENDS "${CMAKE_CURRENT_LIST_DIR}/persistence.js")
set_property(TARGET love APPEND PROPERTY LINK_DEPENDS "${CMAKE_CURRENT_LIST_DIR}/audio.js")

add_custom_command(TARGET love POST_BUILD
  COMMAND ${CMAKE_COMMAND} -E copy_directory
    "${LOVE_DEPENDENCY_DIRECTORY}/package-assets/licenses" "${CMAKE_CURRENT_BINARY_DIR}/licenses"
  COMMAND ${CMAKE_COMMAND} -E copy "${love_SOURCE_DIR}/license.txt"
    "${CMAKE_CURRENT_BINARY_DIR}/licenses/LOVE.txt"
  COMMAND ${CMAKE_COMMAND} -E copy "${EMSCRIPTEN_ROOT_PATH}/LICENSE"
    "${CMAKE_CURRENT_BINARY_DIR}/licenses/Emscripten.txt")

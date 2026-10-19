# Small, portable source builds adapted from the codecs' source lists and
# love2d/megasource 5118c13ca1dea1890e298c0ce5e410846913a5a8.
# Original library licenses are included with the downloaded sources.
add_library(love_dep_ogg STATIC "${dep}/ogg/src/bitwise.c" "${dep}/ogg/src/framing.c")
file(MAKE_DIRECTORY "${CMAKE_BINARY_DIR}/dependencies/include/ogg")
file(WRITE "${CMAKE_BINARY_DIR}/dependencies/include/ogg/config_types.h"
  "#include <stdint.h>\ntypedef int16_t ogg_int16_t;\ntypedef uint16_t ogg_uint16_t;\ntypedef int32_t ogg_int32_t;\ntypedef uint32_t ogg_uint32_t;\ntypedef int64_t ogg_int64_t;\ntypedef uint64_t ogg_uint64_t;\n")
target_include_directories(love_dep_ogg PUBLIC "${dep}/ogg/include" "${CMAKE_BINARY_DIR}/dependencies/include")
target_link_libraries(lovedep::Ogg INTERFACE love_dep_ogg)

set(vorbis_files analysis bitrate block codebook envelope floor0 floor1 info lookup lpc lsp
  mapping0 mdct psy registry res0 sharedbook smallft synthesis vorbisenc window)
set(vorbis_sources)
foreach(file ${vorbis_files})
  list(APPEND vorbis_sources "${dep}/vorbis/lib/${file}.c")
endforeach()
add_library(love_dep_vorbis STATIC ${vorbis_sources})
target_include_directories(love_dep_vorbis PUBLIC "${dep}/vorbis/include" PRIVATE "${dep}/vorbis/lib")
target_link_libraries(love_dep_vorbis PUBLIC love_dep_ogg)
add_library(love_dep_vorbisfile STATIC "${dep}/vorbis/lib/vorbisfile.c")
target_include_directories(love_dep_vorbisfile PUBLIC "${dep}/vorbis/include")
target_link_libraries(love_dep_vorbisfile PUBLIC love_dep_vorbis)
target_link_libraries(lovedep::Vorbis INTERFACE love_dep_vorbisfile)

# Only decoding is used by LÖVE. Generic C implementations work for every ABI.
set(theora_files apiwrapper bitpack decapiwrapper decinfo decode dequant fragment huffdec idct info internal quant state)
set(theora_sources)
foreach(file ${theora_files})
  list(APPEND theora_sources "${dep}/theora/lib/${file}.c")
endforeach()
add_library(love_dep_theora STATIC ${theora_sources})
# Keep the AppImage recipe's x86-64 SIMD decoder acceleration.
if(CMAKE_SYSTEM_NAME STREQUAL "Linux" AND NOT ANDROID
   AND CMAKE_SYSTEM_PROCESSOR MATCHES "^(x86_64|AMD64)$"
   AND CMAKE_C_COMPILER_ID MATCHES "GNU|Clang")
  foreach(file x86cpu mmxidct mmxfrag mmxstate sse2idct x86state)
    target_sources(love_dep_theora PRIVATE "${dep}/theora/lib/x86/${file}.c")
  endforeach()
  target_compile_definitions(love_dep_theora PRIVATE OC_X86_ASM OC_X86_64_ASM)
endif()
target_include_directories(love_dep_theora PUBLIC "${dep}/theora/include" PRIVATE "${dep}/theora/lib")
target_link_libraries(love_dep_theora PUBLIC love_dep_ogg)
target_link_libraries(lovedep::Theora INTERFACE love_dep_theora)

file(GLOB modplug_sources "${dep}/modplug/src/*.cpp")
add_library(love_dep_modplug STATIC ${modplug_sources})
set_target_properties(love_dep_modplug PROPERTIES CXX_STANDARD 11)
file(MAKE_DIRECTORY "${CMAKE_BINARY_DIR}/dependencies/include/libmodplug")
configure_file("${dep}/modplug/src/modplug.h" "${CMAKE_BINARY_DIR}/dependencies/include/libmodplug/modplug.h" COPYONLY)
target_include_directories(love_dep_modplug PUBLIC "${CMAKE_BINARY_DIR}/dependencies/include" "${dep}/modplug/src"
  PRIVATE "${dep}/modplug/src" "${dep}/modplug/src/libmodplug")
target_compile_definitions(love_dep_modplug PUBLIC MODPLUG_STATIC PRIVATE HAVE_STDINT_H HAVE_INTTYPES_H)
if(NOT WIN32)
  target_compile_definitions(love_dep_modplug PRIVATE HAVE_SINF HAVE_SETENV)
endif()
target_link_libraries(lovedep::Modplug INTERFACE love_dep_modplug)

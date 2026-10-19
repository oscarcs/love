# Apple applications are generated from the same targets as desktop/Linux builds.
file(GLOB_RECURSE love_objcxx_sources "${love_SOURCE_DIR}/src/*.mm")
set_source_files_properties(${love_objcxx_sources} PROPERTIES COMPILE_OPTIONS "-fobjc-arc")
set_target_properties(love PROPERTIES MACOSX_BUNDLE TRUE)
if(CMAKE_SYSTEM_NAME STREQUAL "iOS")
  set(plist "${love_SOURCE_DIR}/platform/apple/ios.plist.in")
  target_link_libraries(love PRIVATE
    "-framework UIKit" "-framework Foundation" "-framework AVFoundation"
    "-framework AudioToolbox" "-framework CoreMotion" "-framework GameController"
    "-framework CoreGraphics" "-framework CoreHaptics" "-framework OpenGLES")
  target_link_options(love PRIVATE -ObjC)
  set_target_properties(love PROPERTIES XCODE_ATTRIBUTE_TARGETED_DEVICE_FAMILY "1,2"
    XCODE_ATTRIBUTE_CODE_SIGNING_ALLOWED NO)
  set_target_properties(love PROPERTIES XCODE_ATTRIBUTE_ASSETCATALOG_COMPILER_APPICON_NAME "iOS AppIcon")
  target_sources(love PRIVATE "${love_SOURCE_DIR}/platform/apple/Images.xcassets" "${love_SOURCE_DIR}/platform/apple/lovedocument.icns")
  set_source_files_properties("${love_SOURCE_DIR}/platform/apple/Images.xcassets" "${love_SOURCE_DIR}/platform/apple/lovedocument.icns" PROPERTIES MACOSX_PACKAGE_LOCATION Resources)
  target_sources(love PRIVATE "${love_SOURCE_DIR}/platform/apple/Launch Screen.xib")
  set_source_files_properties("${love_SOURCE_DIR}/platform/apple/Launch Screen.xib"
    PROPERTIES MACOSX_PACKAGE_LOCATION Resources)
else()
  set(plist "${love_SOURCE_DIR}/platform/apple/macos.plist.in")
  target_sources(love PRIVATE "${love_SOURCE_DIR}/platform/apple/love.icns")
  set_source_files_properties("${love_SOURCE_DIR}/platform/apple/love.icns" PROPERTIES MACOSX_PACKAGE_LOCATION Resources)
  add_custom_command(TARGET love POST_BUILD
    COMMAND iconutil -c icns "${love_SOURCE_DIR}/platform/apple/GameIcon.iconset"
      -o "$<TARGET_BUNDLE_DIR:love>/Contents/Resources/GameIcon.icns" VERBATIM)
  set_target_properties(liblove PROPERTIES INSTALL_RPATH "@loader_path")
  set_target_properties(love PROPERTIES INSTALL_RPATH "@executable_path/../Frameworks")
  install(TARGETS liblove LIBRARY DESTINATION love.app/Contents/Frameworks)
  install(PROGRAMS "$<TARGET_FILE:${LOVE_SDL_TARGET}>" "$<TARGET_FILE:OpenAL>" "${LOVE_LUAJIT_LIBRARY}"
    DESTINATION love.app/Contents/Frameworks)
  install(TARGETS love BUNDLE DESTINATION .)
  install(CODE "
    include(BundleUtilities)
    fixup_bundle(\"\${CMAKE_INSTALL_PREFIX}/love.app\" \"\" \"${CMAKE_BINARY_DIR}/dependencies/sdl;${CMAKE_BINARY_DIR}/dependencies/openal;${CMAKE_BINARY_DIR}/dependencies/luajit;${CMAKE_BINARY_DIR}\")
  ")
endif()
set_target_properties(love PROPERTIES MACOSX_BUNDLE_INFO_PLIST "${plist}"
  MACOSX_BUNDLE_GUI_IDENTIFIER "org.love2d.love"
  MACOSX_BUNDLE_BUNDLE_NAME "LÖVE"
  MACOSX_BUNDLE_SHORT_VERSION_STRING "${LOVE_VERSION_STR}"
  MACOSX_BUNDLE_BUNDLE_VERSION "${LOVE_VERSION_STR}.${LOVE_VERSION_REV}")

if(CMAKE_SYSTEM_NAME STREQUAL "iOS")
  install(TARGETS love BUNDLE DESTINATION .)
endif()

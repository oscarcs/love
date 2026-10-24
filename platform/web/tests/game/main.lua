local frame, canvas, shader, source = 0
local bufferReadback, textureReadback
function love.load()
  assert(love.system.getOS() == 'Web')
  assert(love.window.getVSync() == 1)
  love.window.setVSync(0)
  assert(love.window.getVSync() == 1)
  assert(assert(load('return value', 'save', 't', {value = 42}))() == 42)
  assert(load('return 1', 'text', 'b') == nil)
  local bytecode = string.dump(function() return 7 end)
  assert(load(bytecode, 'binary', 't') == nil)
  assert(assert(load(bytecode, 'binary', 'b'))() == 7)
  assert(load('this is invalid Lua', 'invalid', 't') == nil)
  local supplied = false
  local reader = function()
    if supplied then return nil end
    supplied = true
    return 'return value'
  end
  assert(assert(load(reader, 'reader', 't', {value = 43}))() == 43)
  if love.restart then assert(love.restart == 'web-restart') end
  canvas = love.graphics.newCanvas(16, 16)
  love.graphics.setCanvas(canvas)
  love.graphics.clear(1, 0, 0, 1)
  love.graphics.setCanvas()
  local pixels = love.graphics.readbackTexture(canvas)
  local r, g, b = pixels:getPixel(2, 2)
  assert(r > .99 and g < .01 and b < .01, 'Canvas readback failed')
  local buffer = love.graphics.newBuffer({{format = 'float', location = 0}}, {11, 22, 33, 44}, {vertex = true})
  local data = love.graphics.readbackBuffer(buffer, 4, 8)
  assert(love.data.unpack('f', data) == 22, 'Partial buffer readback failed')
  bufferReadback = love.graphics.readbackBufferAsync(buffer, 8, 4)
  bufferReadback:wait() -- Must return without spinning on the browser thread.
  textureReadback = love.graphics.readbackTextureAsync(canvas)
  shader = love.graphics.newShader([[
    vec4 effect(vec4 color, Image tex, vec2 uv, vec2 pixel) {
      return Texel(tex, uv) * color;
    }
  ]])
  local sound = love.sound.newSoundData(800, 8000, 16, 1)
  source = love.audio.newSource(sound, 'static')
  source:play()
  if love.restart then
    local previous = tonumber((love.filesystem.read('counter.txt'))) or 0
    assert(love.filesystem.write('counter.txt', tostring(previous + 1)))
    print('LOVE_WEB_SAVE_COUNT=' .. (previous + 1))
  end
end
function love.update()
  frame = frame + 1
  if frame == 5 and not love.restart then love.event.quit('restart', 'web-restart') end
  if frame == 10 and love.restart then
    bufferReadback:update()
    textureReadback:update()
    assert(bufferReadback:isComplete() and not bufferReadback:hasError())
    assert(textureReadback:isComplete() and not textureReadback:hasError())
    assert(love.data.unpack('f', bufferReadback:getBufferData()) == 33)
    local r, g, b = textureReadback:getImageData():getPixel(2, 2)
    assert(r > .99 and g < .01 and b < .01, 'Async texture readback failed')
    print('LOVE_WEB_SMOKE_OK')
  end
end
function love.draw()
  love.graphics.clear(.1, .15, .2)
  love.graphics.setShader(shader)
  love.graphics.draw(canvas, 20, 20, 0, 4, 4)
  love.graphics.setShader()
  love.graphics.print('WebGL 2: fonts, shader, canvas, audio', 10, 130)
end
function love.keypressed(key)
  if key == 'q' then love.event.quit(0) end
end

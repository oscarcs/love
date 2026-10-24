function love.conf(t)
  t.identity = 'love-web-smoke'
  t.window.width, t.window.height = 320, 200
  t.window.vsync = 0 -- Native games often request this; web must still use RAF.
  t.modules.physics, t.modules.video = false, false
end

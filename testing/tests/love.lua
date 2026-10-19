-- love
-- tests for the main love hooks + methods, mainly just that they exist

--------------------------------------------------------------------------------
--------------------------------------------------------------------------------
------------------------------------METHODS-------------------------------------
--------------------------------------------------------------------------------
--------------------------------------------------------------------------------


-- love.getVersion
love.test.love.getVersion = function(test)
  local major, minor, revision, codename = love.getVersion()
  test:assertGreaterEqual(0, major, 'check major is number')
  test:assertGreaterEqual(0, minor, 'check minor is number')
  test:assertGreaterEqual(0, revision, 'check revision is number')
  test:assertTrue(codename ~= nil, 'check has codename')
end


-- love.hasDeprecationOutput
love.test.love.hasDeprecationOutput = function(test)
  local enabled = love.hasDeprecationOutput()
  test:assertEquals(true, enabled, 'check enabled by default')
end


-- love.isVersionCompatible
love.test.love.isVersionCompatible = function(test)
  local major, minor, revision, _ = love.getVersion()
  test:assertTrue(love.isVersionCompatible(major, minor, revision), 'check own version')
end


-- love.setDeprecationOutput
love.test.love.setDeprecationOutput = function(test)
  local enabled = love.hasDeprecationOutput()
  test:assertEquals(true, enabled, 'check enabled by default')
  love.setDeprecationOutput(false)
  test:assertEquals(false, love.hasDeprecationOutput(), 'check disable')
  love.setDeprecationOutput(true)
end


-- love.errhand
love.test.love.errhand = function(test)
  test:assertTrue(type(love.errhand) == 'function', 'check defined')
end


-- love.run
love.test.love.run = function(test)
  test:assertTrue(type(love.run) == 'function', 'check defined')
end

-- Bundled ENet: exercise reliable fragmented packets through the Lua binding.
love.test.love.enet = function(test)
  local enet = require('enet')
  local server = assert(enet.host_create('127.0.0.1:0', 1, 2))
  local client = assert(enet.host_create(nil, 1, 2))
  server:compress_with_range_coder()
  client:compress_with_range_coder()
  local peer = client:connect(server:get_socket_address(), 2)
  local payload = string.rep('reliable fragmented packet\0', 4096)
  local sent, received, channel = false, nil, nil
  local deadline = love.timer.getTime() + 5
  while not received and love.timer.getTime() < deadline do
    local event = client:service(1)
    if event then
      if event.type == 'connect' and not sent then
        test:assertEquals(0, peer:send(payload, 1), 'queue reliable packet')
        sent = true
      elseif event.type == 'receive' then
        received, channel = event.data, event.channel
      end
    end
    event = server:service(1)
    if event and event.type == 'receive' then
      test:assertEquals(payload, event.data, 'server receives complete packet')
      event.peer:send(event.data, event.channel)
    end
    if not received then test:waitFrames(1) end
  end
  client:destroy()
  server:destroy()
  test:assertTrue(sent, 'loopback connection established')
  test:assertEquals(payload, received, 'client receives complete reply')
  test:assertEquals(1, channel, 'packet channel preserved')
end

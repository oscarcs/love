R"luastring"--(
-- Browser compatibility for LuaJIT's extended load signature on plain Lua 5.1.
-- Uses the same zlib license as LÖVE (see license.txt).
local load51, loadstring51, setfenv51 = load, loadstring, setfenv
local function modeError(chunk, mode)
  local binary = chunk:byte(1) == 27
  if not mode:find(binary and 'b' or 't', 1, true) then
    return 'attempt to load a ' .. (binary and 'binary' or 'text') .. ' chunk (mode is ' .. mode .. ')'
  end
end

function load(chunk, name, mode, environment)
  mode = mode or 'bt'
  if type(mode) ~= 'string' then error('load mode must be a string', 2) end
  if environment ~= nil and type(environment) ~= 'table' then
    error('load environment must be a table', 2)
  end
  local fn, err
  if type(chunk) == 'string' then
    err = modeError(chunk, mode)
    if err then return nil, err end
    fn, err = loadstring51(chunk, name)
  elseif type(chunk) == 'function' then
    local first = true
    fn, err = load51(function()
      local part = chunk()
      if first and part ~= nil and part ~= '' then
        first = false
        if type(part) ~= 'string' then error('reader function must return a string') end
        local message = modeError(part, mode)
        if message then error(message) end
      end
      return part
    end, name)
  else
    error('load expects a string or reader function', 2)
  end
  if fn and environment ~= nil then setfenv51(fn, environment) end
  return fn, err
end
--)luastring"--"

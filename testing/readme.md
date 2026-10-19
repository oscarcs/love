# API tests

The suite exercises the APIs provided by this checkout. Use the matching engine
build; older LÖVE versions may lack APIs used by the tests.

## Run tests

From the repository root, substitute the path to your executable:

```sh
love testing --all
love testing --modules filesystem,audio
love testing --method filesystem write
```

On Windows, use `lovec.exe` to see console output. All tests run by default.
The exit status is `0` when no tests fail and `1` when any test fails; skipped
tests do not count as failures. Hardware input tests provide limited coverage
without physical devices.

Results are printed as PASS, FAIL, or SKIP. Reports are written to
`testing/output/` in JUnit XML, HTML, and Markdown formats. Graphics test images
are written to `testing/output/actual/`.

## Write tests

Add tests under `testing/tests/` in the matching module file. Each function
receives a test object:

```lua
love.test.filesystem.read = function(test)
  local content, size = love.filesystem.read('resources/test.txt')
  test:assertNotNil(content)
  test:assertEquals('helloworld', content, 'content')
  test:assertEquals(10, size, 'size')
end
```

Available assertions are defined in [TestMethod.lua](classes/TestMethod.lua):

- **assertNotNil**(value)
- **assertEquals**(expected, actual, label)
- **assertTrue**(value, label)
- **assertFalse**(value, label)
- **assertNotEquals**(expected, actual, label)
- **assertRange**(actual, min, max, label)
- **assertMatch**({option1, option2, option3 ...}, actual, label)
- **assertGreaterEqual**(expected, actual, label)
- **assertLessEqual**(expected, actual, label)
- **assertObject**(table)
- **assertCoords**(expected, actual, label)

Tests run in coroutines. Use `test:waitFrames(frames)` or
`test:waitSeconds(seconds)` to wait for asynchronous effects. Use
`test:skipTest(reason)` when a test cannot run in the current environment.
See [todo.md](todo.md) for missing coverage.

## Graphics tolerance

Graphics tests compare pixels exactly unless a test specifies a tolerance:

| Test                        |    OS     |      Exception      | Reason |
| --------------------------  | --------- | ------------------- | ------ |
| love.graphics.drawInstanced |  Windows  |   1rgba tolerance   | Small differences in rendered mesh pixels |
| love.graphics.setBlendMode  |  Win/Lin  |   1rgba tolerance   | Small differences in blend results |

## Runner exceptions

Pass `--isRunner` in CI to enable the following allowances for virtual runners
and software rendering:

| Test                       |    OS     |      Exception      | Reason |
| -------------------------- | --------- | ------------------- | ------ |
| love.graphics.setWireframe |   MacOS   |    1px tolerance    | Wireframes are offset by 1,1 when drawn |
| love.graphics.arc          |   MacOS   |       Skipped       | Arc curves are drawn slightly off at really low scale  |
| love.graphics.setLineStyle | Linux / Windows GLES llvmpipe | 1rgba tolerance | Smooth-line edge blending can differ by one 8-bit color level on software-rendered CI |
| love.audio.RecordingDevice |    All    |       Skipped       | Recording devices can't be emulated on runners |

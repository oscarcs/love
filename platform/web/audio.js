// Replace Emscripten 4.0.10's one-shot gesture handlers: they retain contexts
// across restarts and leave rejected resume promises unhandled.
addToLibrary({
  $autoResumeAudioContext: (ctx, elements) => {
    elements = (elements || [document, document.getElementById('canvas')]).filter(Boolean);
    const events = ['keydown', 'mousedown', 'touchstart'];
    let disposed = false;
    const dispose = () => {
      disposed = true;
      for (const element of elements)
        for (const event of events) element.removeEventListener(event, resume);
      ctx.removeEventListener('statechange', stateChanged);
      delete ctx['loveDisposeAutoResume'];
    };
    const stateChanged = () => {
      if (ctx.state === 'running' || ctx.state === 'closed') dispose();
    };
    const resume = () => {
      if (disposed || ctx.state !== 'suspended') return;
      ctx.resume().then(() => {
        if (!disposed) stateChanged();
      }, () => {
        if (!disposed && ctx.state !== 'closed') Module['onAudioResumeError']?.();
      });
    };
    ctx['loveDisposeAutoResume'] = dispose;
    ctx.addEventListener('statechange', stateChanged);
    for (const element of elements)
      for (const event of events) element.addEventListener(event, resume);
    stateChanged();
  },
});

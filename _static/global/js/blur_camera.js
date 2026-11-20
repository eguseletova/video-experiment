// Shared background-blur camera (Google Chrome).
//
// raw camera stream -> hidden <video> -> 640px processing frame
//   -> MediaPipe Tasks ImageSegmenter, "selfie_multiclass_256x256" model
//      (classes: background, hair, body skin, face skin, clothes, accessories)
//   -> person mask = 1 - P(background), smoothed over time, generous threshold
//   -> canvas: [blurred frame] + [sharp person cut out with the mask]
//
// The participant only sees the canvas, and recordings are taken from
// canvas.captureStream(), so recordings are blurred too.
//
// Tuning knobs (see constants below):
//   KEEP_LOW / KEEP_HIGH: person-probability range mapped to 0..1 opacity.
//     Low values = more of the body/hair is kept sharp at uncertain edges.
//   TEMPORAL: how much of the previous mask is kept (reduces flicker).
//   BLUR_PX: background blur strength.
window.BlurCamera = (function () {
  const TV_VERSION = "0.10.35";
  const TV_BASE = "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@" + TV_VERSION;
  const MODEL_URL =
    "https://storage.googleapis.com/mediapipe-models/image_segmenter/selfie_multiclass_256x256/float32/latest/selfie_multiclass_256x256.tflite";

  const PROC_WIDTH = 640;  // processing / output resolution
  const BLUR_PX = 12;      // background blur radius at PROC_WIDTH
  const KEEP_LOW = 0.12;   // person prob. below this -> fully background
  const KEEP_HIGH = 0.40;  // person prob. above this -> fully sharp
  const TEMPORAL = 0.35;   // share of previous frame's mask (0 = none)
  const EDGE_FEATHER_PX = 1.5;

  function isChrome() {
    const brands = (navigator.userAgentData && navigator.userAgentData.brands) || [];
    if (brands.some((b) => /Google Chrome|Chromium|Microsoft Edge/.test(b.brand))) return true;
    return /Chrome\//.test(navigator.userAgent) && !/Firefox|FxiOS/.test(navigator.userAgent);
  }

  let segmenterPromise = null; // shared across instances on a page
  function loadSegmenter() {
    if (!segmenterPromise) {
      segmenterPromise = (async () => {
        const vision = await import(TV_BASE + "/vision_bundle.mjs");
        const fileset = await vision.FilesetResolver.forVisionTasks(TV_BASE + "/wasm");
        return vision.ImageSegmenter.createFromOptions(fileset, {
          baseOptions: { modelAssetPath: MODEL_URL, delegate: "GPU" },
          runningMode: "VIDEO",
          outputCategoryMask: false,
          outputConfidenceMasks: true,
        });
      })();
    }
    return segmenterPromise;
  }

  function create(opts) {
    const canvas = opts.canvas;
    const badge = opts.badge || null;
    const ctx = canvas.getContext("2d");

    const cam = document.createElement("video");
    cam.muted = true; cam.playsInline = true; cam.autoplay = true;
    cam.setAttribute("playsinline", "");

    const frame = document.createElement("canvas");      // downscaled camera frame
    const fctx = frame.getContext("2d", { willReadFrequently: false });
    const maskCanvas = document.createElement("canvas"); // person alpha mask
    const mctx = maskCanvas.getContext("2d");
    const person = document.createElement("canvas");     // sharp person layer
    const pctx = person.getContext("2d");

    let segmenter = null, blurOn = false, running = false, lastTs = -1;
    let prevMask = null, maskImage = null;

    function setBadge(text, ok) {
      if (!badge) return;
      badge.textContent = text;
      badge.style.background = ok === true ? "rgba(22,163,74,0.85)"
        : ok === false ? "rgba(185,28,28,0.85)" : "rgba(0,0,0,0.55)";
    }

    function updateMask(bg, w, h) {
      // bg: Float32Array P(background) per pixel
      const n = w * h;
      if (!prevMask || prevMask.length !== n) { prevMask = new Float32Array(n); prevMask.fill(-1); }
      if (!maskImage || maskImage.width !== w || maskImage.height !== h) {
        maskImage = mctx.createImageData(w, h);
        const d = maskImage.data;
        for (let i = 0; i < n; i++) { d[i * 4] = 255; d[i * 4 + 1] = 255; d[i * 4 + 2] = 255; }
      }
      const d = maskImage.data;
      const span = KEEP_HIGH - KEEP_LOW;
      for (let i = 0; i < n; i++) {
        let p = 1 - bg[i];
        if (prevMask[i] >= 0) p = TEMPORAL * prevMask[i] + (1 - TEMPORAL) * p;
        prevMask[i] = p;
        let a = (p - KEEP_LOW) / span;
        a = a <= 0 ? 0 : a >= 1 ? 1 : a * a * (3 - 2 * a); // smoothstep
        d[i * 4 + 3] = a * 255;
      }
      mctx.putImageData(maskImage, 0, 0);
    }

    function composite() {
      const w = canvas.width, h = canvas.height;
      // 1. blurred background (drawn oversized so edges don't fade)
      ctx.save();
      ctx.filter = "blur(" + BLUR_PX + "px)";
      const m = BLUR_PX * 2;
      ctx.drawImage(frame, -m, -m, w + 2 * m, h + 2 * m);
      ctx.restore();
      // 2. sharp person layer cut out with the (slightly feathered) mask
      pctx.save();
      pctx.clearRect(0, 0, w, h);
      pctx.filter = "blur(" + EDGE_FEATHER_PX + "px)";
      pctx.drawImage(maskCanvas, 0, 0, w, h);
      pctx.filter = "none";
      pctx.globalCompositeOperation = "source-in";
      pctx.drawImage(frame, 0, 0, w, h);
      pctx.restore();
      ctx.drawImage(person, 0, 0);
    }

    function tick() {
      if (!running) return;
      if (cam.readyState >= 2) {
        fctx.drawImage(cam, 0, 0, frame.width, frame.height);
        if (segmenter && blurOn) {
          let ts = performance.now();
          if (ts <= lastTs) ts = lastTs + 1;
          lastTs = ts;
          try {
            segmenter.segmentForVideo(frame, ts, (result) => {
              const masks = result.confidenceMasks;
              if (masks && masks.length) {
                const bg = masks[0];
                updateMask(bg.getAsFloat32Array(), bg.width, bg.height);
              }
              composite();
            });
          } catch (e) {
            console.error(e);
            blurOn = false;
            setBadge("Background blur unavailable", false);
          }
        } else {
          ctx.drawImage(frame, 0, 0);
        }
      }
      requestAnimationFrame(tick);
    }

    async function start(stream) {
      cam.srcObject = stream;
      await cam.play().catch(() => {});
      if (cam.readyState < 1) {
        await new Promise((r) => cam.addEventListener("loadedmetadata", r, { once: true }));
      }
      const vw = cam.videoWidth || 1280, vh = cam.videoHeight || 720;
      const w = PROC_WIDTH, h = Math.round(PROC_WIDTH * vh / vw);
      for (const c of [canvas, frame, maskCanvas, person]) { c.width = w; c.height = h; }
      running = true;
      tick();
      if (!isChrome()) {
        setBadge("Background blur requires Google Chrome", false);
        return false;
      }
      setBadge("Loading background blur…");
      try {
        segmenter = await loadSegmenter();
        blurOn = true;
        setBadge("Background blur: ON", true);
      } catch (e) {
        console.error(e);
        blurOn = false;
        setBadge("Background blur unavailable", false);
      }
      return blurOn;
    }

    function captureStream(fps) {
      return canvas.captureStream(fps || 30);
    }

    function stop() {
      running = false;
    }

    return { start, captureStream, stop, isBlurOn: () => blurOn };
  }

  return { create, isChrome };
})();

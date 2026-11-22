// Video page recorder (Video A/B/C) with automatic background blur
// (see blur_camera.js). Max length per take from data-max-seconds;
// at most data-max-takes takes (1 original + re-recordings).
// Each take is kept in the browser (IndexedDB via VideoStore) for replay on the
// ChooseVideo page. When the participant clicks Next, the final take is sent to
// the oTree server in chunks over oTree's live channel (data-upload="1"); the
// server forwards it to Box (see video_upload.py).
(function () {
  const root = document.getElementById("recorderRoot");
  const STORE_KEY = root.dataset.storeKey;
  const MAX_SECONDS = parseInt(root.dataset.maxSeconds, 10);
  const DURATION_MS = MAX_SECONDS * 1000;
  const MAX_TAKES = parseInt(root.dataset.maxTakes, 10);

  const canvas = document.getElementById("previewCanvas");
  const startBtn = document.getElementById("startBtn");
  const stopBtn = document.getElementById("stopBtn");
  const statusEl = document.getElementById("status");
  const takesEl = document.getElementById("takesInfo");
  const prepEl = document.getElementById("prepCountdownMain");
  const timeEl = document.getElementById("timeRemaining");
  const progWrap = document.getElementById("progressWrap");
  const progBar = document.getElementById("progressBar");
  const playbackWrap = document.getElementById("playbackWrap");
  const playbackVideo = document.getElementById("playbackVideo");
  const recordedInput = document.getElementById("recordedInput");
  const secondsInput = document.getElementById("secondsInput");
  const takesInput = document.getElementById("takesInput");
  const nextBtn = document.getElementById("NextButton");

  const blurCam = BlurCamera.create({ canvas, badge: document.getElementById("blurBadge") });

  let stream = null, recorder = null, chunks = [];
  let prepTimerId = null, rafId = null, blobUrl = null, recStart = 0;
  let takes = 0;
  let finalBlob = null, uploaded = false, uploading = false, uploadFailures = 0;
  let submitAfterStop = false;  // Next clicked while recording (walk-through mode)

  function setStatus(m) { statusEl.textContent = m; }
  function fmt(s) { const m = Math.floor(s / 60), r = s % 60; return m + ":" + (r < 10 ? "0" : "") + r; }
  function updateTakes() {
    const left = MAX_TAKES - takes;
    if (takes === 0) takesEl.textContent = "You may re-record this video up to " + (MAX_TAKES - 1) + " times.";
    else if (left > 0) takesEl.textContent = "Re-recordings left: " + left + ".";
    else takesEl.textContent = "You have used all re-recording attempts for this video.";
    takesInput.value = takes;
  }

  // ---------- camera ----------
  async function initCamera() {
    try {
      setStatus("Requesting camera and microphone permission...");
      stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 1280 }, height: { ideal: 720 } },
        audio: true,
      });
      setStatus("Loading background blur…");
      await blurCam.start(stream);
      setStatus("Camera ready. Click Start recording.");
      startBtn.disabled = false;
    } catch (e) {
      console.error(e);
      setStatus("Could not access camera/microphone. Please allow permission and reload the page.");
    }
  }

  // ---------- recording ----------
  function bestMimeType() {
    const c = ["video/webm;codecs=vp9,opus", "video/webm;codecs=vp8,opus", "video/webm", "video/mp4"];
    return c.find((t) => window.MediaRecorder && MediaRecorder.isTypeSupported(t)) || "";
  }

  function resetProgressUI() {
    prepEl.style.display = "none"; prepEl.textContent = "";
    timeEl.style.display = "none"; timeEl.textContent = "";
    progWrap.style.display = "none"; progBar.style.width = "100%";
    if (rafId) { cancelAnimationFrame(rafId); rafId = null; }
    if (prepTimerId) { clearInterval(prepTimerId); prepTimerId = null; }
  }

  function startProgress() {
    const start = Date.now();
    timeEl.style.display = "block";
    progWrap.style.display = "block";
    const tick = () => {
      const remainingMs = Math.max(0, DURATION_MS - (Date.now() - start));
      timeEl.textContent = fmt(Math.ceil(remainingMs / 1000)) + " remaining";
      progBar.style.width = (remainingMs / DURATION_MS) * 100 + "%";
      if (remainingMs > 0 && recorder && recorder.state === "recording") rafId = requestAnimationFrame(tick);
      else if (recorder && recorder.state === "recording") recorder.stop();
    };
    rafId = requestAnimationFrame(tick);
  }

  function startRecordingNow() {
    if (!window.MediaRecorder) { setStatus("Recording is not supported in this browser. Please use Chrome or Firefox."); return; }
    chunks = [];
    const out = new MediaStream([
      ...blurCam.captureStream(30).getVideoTracks(),
      ...stream.getAudioTracks(),
    ]);
    const mimeType = bestMimeType();
    recorder = new MediaRecorder(out, mimeType ? { mimeType } : undefined);
    recorder.ondataavailable = (e) => { if (e.data && e.data.size > 0) chunks.push(e.data); };
    recorder.onstart = () => {
      recStart = Date.now();
      takes += 1;
      updateTakes();
      setStatus("Recording…");
      startBtn.disabled = true;
      stopBtn.disabled = false;
      startProgress();
    };
    recorder.onstop = async () => {
      resetProgressUI();
      const seconds = (Date.now() - recStart) / 1000;
      const blob = new Blob(chunks, { type: recorder.mimeType || "video/webm" });
      if (blobUrl) URL.revokeObjectURL(blobUrl);
      blobUrl = URL.createObjectURL(blob);
      playbackVideo.src = blobUrl;
      playbackWrap.style.display = "block";
      try { await VideoStore.put(STORE_KEY, blob); } catch (e) { console.error(e); }
      finalBlob = blob; uploaded = false;
      recordedInput.value = "1";
      secondsInput.value = seconds.toFixed(1);
      stopBtn.disabled = true;
      if (takes < MAX_TAKES) {
        startBtn.disabled = false;
        startBtn.textContent = "Re-record";
        setStatus("Recording complete. Review it below. You can re-record, or click Next to continue.");
      } else {
        startBtn.disabled = true;
        setStatus("Recording complete. This is your final recording for this video. Click Next to continue.");
      }
      nextBtn.disabled = false;
      if (submitAfterStop) { submitAfterStop = false; uploadThenSubmit(); }
    };
    recorder.start();
  }

  function startWithPrepCountdown() {
    if (!stream || takes >= MAX_TAKES) return;
    resetProgressUI();
    playbackWrap.style.display = "none";
    nextBtn.disabled = true;
    startBtn.disabled = true;
    stopBtn.disabled = false;
    let prep = 3;
    prepEl.style.display = "block";
    prepEl.textContent = "Recording in " + prep + "...";
    prepTimerId = setInterval(() => {
      prep -= 1;
      if (prep > 0) { prepEl.textContent = "Recording in " + prep + "..."; return; }
      clearInterval(prepTimerId); prepTimerId = null;
      prepEl.style.display = "none";
      startRecordingNow();
    }, 1000);
  }

  function stopRecording() {
    if (prepTimerId) {
      // cancelled during the countdown: does not use up a take
      resetProgressUI();
      setStatus("Recording cancelled.");
      startBtn.disabled = false;
      stopBtn.disabled = true;
      if (recordedInput.value === "1") { nextBtn.disabled = false; playbackWrap.style.display = "block"; }
      return;
    }
    if (recorder && recorder.state === "recording") recorder.stop();
  }

  // ---------- upload to server (on Next) ----------
  const UPLOAD = root.dataset.upload === "1";
  const LETTER = root.dataset.letter;
  const CHUNK = 256 * 1024;
  const form = document.getElementById("form");
  const upBox = document.getElementById("uploadBox");
  const upMsg = document.getElementById("uploadMsg");
  const upBar = document.getElementById("uploadBar");
  const upRetry = document.getElementById("uploadRetry");
  let pending = null;

  // oTree calls the global liveRecv with the live_method's reply
  // (one request at a time, so the reply always belongs to the pending request)
  window.liveRecv = function (msg) {
    if (!pending || !msg) return;
    const p = pending; pending = null;
    clearTimeout(p.timer); p.resolve(msg);
  };
  function ask(msg, timeoutMs) {
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => { pending = null; reject(new Error("timeout")); }, timeoutMs || 30000);
      pending = { resolve, timer };
      try { liveSend(msg); } catch (e) { clearTimeout(timer); pending = null; reject(e); }
    }).then((r) => { if (r.type === "error") throw new Error(r.message); return r; });
  }
  function b64(buf) {
    let s = ""; const bytes = new Uint8Array(buf);
    for (let i = 0; i < bytes.length; i += 0x8000) s += String.fromCharCode.apply(null, bytes.subarray(i, i + 0x8000));
    return btoa(s);
  }
  async function uploadFinal() {
    const blob = finalBlob;
    await ask({ type: "start", letter: LETTER, size: blob.size, mime: blob.type });
    let offset = 0;
    while (offset < blob.size) {
      const buf = await blob.slice(offset, offset + CHUNK).arrayBuffer();
      const r = await ask({ type: "chunk", letter: LETTER, offset, data: b64(buf) });
      offset = r.offset;
      upBar.style.width = Math.round((offset / blob.size) * 100) + "%";
    }
    await ask({ type: "done", letter: LETTER }, 60000);
  }
  async function uploadThenSubmit() {
    if (uploading) return;
    uploading = true;
    nextBtn.disabled = true; startBtn.disabled = true;
    upBox.style.display = "block"; upRetry.style.display = "none";
    upMsg.textContent = "Saving your video… please keep this page open.";
    upBar.style.width = "0%";
    try {
      await uploadFinal();
      uploaded = true;
      upMsg.textContent = "Saved.";
      form.requestSubmit ? form.requestSubmit(nextBtn) : form.submit();
    } catch (e) {
      console.error(e);
      uploadFailures += 1;
      uploading = false;
      upRetry.style.display = "inline-block";
      if (uploadFailures >= 3) {
        upMsg.textContent = "Your video could not be saved. Please check your internet connection and try again, or click Next to continue anyway.";
        uploaded = true;  // let them continue; video_X_uploaded stays empty in the data
        nextBtn.disabled = false;
      } else {
        upMsg.textContent = "Your video could not be saved. Please check your internet connection and try again.";
      }
    }
  }
  upRetry.addEventListener("click", () => { uploaded = false; uploadThenSubmit(); });
  function interceptSubmit(e) {
    if (!UPLOAD || uploaded) return false;
    if (recorder && recorder.state === "recording") {
      // finish the recording first, then upload and continue
      e.preventDefault();
      e.stopImmediatePropagation();
      submitAfterStop = true;
      recorder.stop();
      return true;
    }
    if (uploading) { e.preventDefault(); e.stopImmediatePropagation(); return true; }
    if (!finalBlob) return false;
    e.preventDefault();
    e.stopImmediatePropagation();
    uploadThenSubmit();
    return true;
  }
  form.addEventListener("submit", interceptSubmit);
  // walk-through mode: skipping is allowed, but a recording that exists is still uploaded
  window.WT_INTERCEPT = interceptSubmit;

  startBtn.addEventListener("click", startWithPrepCountdown);
  stopBtn.addEventListener("click", stopRecording);

  nextBtn.disabled = true;
  updateTakes();
  initCamera();

  window.addEventListener("pagehide", () => {
    try {
      if (recorder && recorder.state === "recording") recorder.stop();
      blurCam.stop();
      if (stream) stream.getTracks().forEach((t) => t.stop());
    } catch (e) {}
  });
})();

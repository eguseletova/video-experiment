// Port of the Qualtrics QID2 camera & microphone check.
// Qualtrics.SurveyEngine.setEmbeddedData("av_test_confirm", v) -> hidden form field.
// Test recordings stay in the browser and are never uploaded.
(function () {
  const previewCanvas = document.getElementById("previewCanvas");
  const blurCam = BlurCamera.create({ canvas: previewCanvas, badge: document.getElementById("blurBadge") });
  const testBtn = document.getElementById("testCameraBtn");
  const recordBtn = document.getElementById("recordTestBtn");
  const status = document.getElementById("statusMessage");
  const audioBar = document.getElementById("audioLevelBar");
  const playbackWrap = document.getElementById("playbackWrap");
  const playbackVideo = document.getElementById("playbackVideo");
  const prepEl = document.getElementById("prepCountdown");
  const timeEl = document.getElementById("timeRemaining");
  const progWrap = document.getElementById("recordProgressWrap");
  const progBar = document.getElementById("recordProgressBar");
  const framingGuide = document.getElementById("framingGuide");
  const confirmWrap = document.getElementById("confirmWrap");
  const confirmYesBtn = document.getElementById("confirmYesBtn");
  const confirmNoBtn = document.getElementById("confirmNoBtn");
  const confirmStatus = document.getElementById("confirmStatus");
  const avConfirmInput = document.getElementById("avConfirmInput");
  const nextBtn = document.getElementById("NextButton");

  let stream = null;
  let audioContext = null, analyser = null, micSource = null, rafId = null;
  let recorder = null, chunks = [], testBlobUrl = null;
  let prepTimerId = null, barRafId = null;

  function hideNextButton() { if (nextBtn) { nextBtn.style.display = "none"; nextBtn.disabled = true; } }
  function showNextButton() { if (nextBtn) { nextBtn.style.display = ""; nextBtn.disabled = false; } }
  function setStatus(msg) { if (status) status.textContent = msg; }

  const baseBtnStyle = {
    padding: "10px 14px", borderRadius: "10px", border: "1px solid #d1d5db",
    background: "#ffffff", color: "#111827", fontWeight: "600", cursor: "pointer",
    fontSize: "18px", fontFamily: "inherit"
  };
  const selectedBtnStyle = { border: "2px solid #2563eb", background: "#eff6ff" };
  function applyStyle(el, s) { if (el) Object.keys(s).forEach(k => { el.style[k] = s[k]; }); }

  function setConfirmSelection(value) {
    if (avConfirmInput) avConfirmInput.value = value;
    applyStyle(confirmYesBtn, baseBtnStyle);
    applyStyle(confirmNoBtn, baseBtnStyle);
    if (value === "yes") applyStyle(confirmYesBtn, selectedBtnStyle);
    if (value === "no") applyStyle(confirmNoBtn, selectedBtnStyle);
    if (confirmStatus) {
      confirmStatus.textContent = value === "yes"
        ? "Saved: confirmed audio/video are working."
        : "Saved: audio/video are not working.";
    }
    showNextButton();
  }

  function resetConfirmUI() {
    if (confirmWrap) confirmWrap.style.display = "none";
    if (confirmStatus) confirmStatus.textContent = "";
    if (avConfirmInput) avConfirmInput.value = "";
    applyStyle(confirmYesBtn, baseBtnStyle);
    applyStyle(confirmNoBtn, baseBtnStyle);
    hideNextButton();
  }

  if (recordBtn) { recordBtn.style.display = "none"; recordBtn.disabled = true; }
  hideNextButton();
  resetConfirmUI();

  function bestMimeType() {
    const c = ["video/webm;codecs=vp9,opus", "video/webm;codecs=vp8,opus", "video/webm", "video/mp4"];
    return c.find(t => window.MediaRecorder && MediaRecorder.isTypeSupported(t)) || "";
  }

  function startAudioMeter() {
    if (!audioContext) audioContext = new (window.AudioContext || window.webkitAudioContext)();
    analyser = audioContext.createAnalyser();
    analyser.fftSize = 256;
    micSource = audioContext.createMediaStreamSource(stream);
    micSource.connect(analyser);
    const data = new Uint8Array(analyser.frequencyBinCount);
    const tick = () => {
      analyser.getByteFrequencyData(data);
      let sum = 0;
      for (let i = 0; i < data.length; i++) sum += data[i];
      const pct = Math.min(100, (sum / data.length) * 2);
      if (audioBar) audioBar.style.width = pct + "%";
      rafId = requestAnimationFrame(tick);
    };
    tick();
  }

  async function testCameraAndMic() {
    try {
      setStatus("Requesting camera and microphone permission...");
      stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
      startAudioMeter();
      setStatus("Loading background blur…");
      await blurCam.start(stream);
      if (recordBtn) { recordBtn.style.display = "inline-block"; recordBtn.disabled = false; }
      setStatus("Camera connected. You can now record a 5-second test.");
    } catch (err) {
      console.error(err);
      setStatus("Could not access camera/microphone. Please allow permissions and try again.");
      if (recordBtn) { recordBtn.disabled = true; recordBtn.style.display = "none"; }
    }
  }

  function resetPrepAndProgressUI() {
    if (prepEl) { prepEl.style.display = "none"; prepEl.textContent = ""; }
    if (timeEl) { timeEl.style.display = "none"; timeEl.textContent = ""; }
    if (progWrap) progWrap.style.display = "none";
    if (progBar) progBar.style.width = "100%";
    if (prepTimerId) { clearInterval(prepTimerId); prepTimerId = null; }
    if (barRafId) { cancelAnimationFrame(barRafId); barRafId = null; }
  }

  function clearTestRecording() {
    chunks = [];
    if (testBlobUrl) { URL.revokeObjectURL(testBlobUrl); testBlobUrl = null; }
    if (playbackVideo) { playbackVideo.removeAttribute("src"); playbackVideo.load(); }
    if (playbackWrap) playbackWrap.style.display = "none";
    resetConfirmUI();
  }

  function startProgressBar(durationMs) {
    progWrap.style.display = "block";
    progBar.style.width = "100%";
    timeEl.style.display = "block";
    const start = Date.now();
    const tick = () => {
      const remainingMs = Math.max(0, durationMs - (Date.now() - start));
      timeEl.textContent = Math.ceil(remainingMs / 1000) + " seconds remaining";
      progBar.style.width = (remainingMs / durationMs) * 100 + "%";
      if (remainingMs > 0 && recorder && recorder.state === "recording") {
        barRafId = requestAnimationFrame(tick);
      } else if (recorder && recorder.state === "recording") {
        recorder.stop();
      }
    };
    barRafId = requestAnimationFrame(tick);
  }

  function startRecordingNow() {
    if (framingGuide) framingGuide.style.display = "none";
    setStatus("Recording…");
    chunks = [];
    const mimeType = bestMimeType();
    const out = new MediaStream([
      ...blurCam.captureStream(30).getVideoTracks(),
      ...stream.getAudioTracks(),
    ]);
    recorder = new MediaRecorder(out, mimeType ? { mimeType } : undefined);
    recorder.ondataavailable = (e) => { if (e.data && e.data.size > 0) chunks.push(e.data); };
    recorder.onstop = () => {
      if (framingGuide) framingGuide.style.display = "block";
      resetPrepAndProgressUI();
      const blob = new Blob(chunks, { type: recorder.mimeType || "video/webm" });
      testBlobUrl = URL.createObjectURL(blob);
      if (playbackVideo) playbackVideo.src = testBlobUrl;
      if (playbackWrap) playbackWrap.style.display = "block";
      if (playbackVideo) playbackVideo.play().catch(() => {});
      if (confirmWrap) confirmWrap.style.display = "block";
      if (confirmStatus) confirmStatus.textContent = "";
      if (avConfirmInput) avConfirmInput.value = "";
      applyStyle(confirmYesBtn, baseBtnStyle);
      applyStyle(confirmNoBtn, baseBtnStyle);
      hideNextButton();
      setStatus("Test recording complete. Replay above if you'd like.");
      if (recordBtn) recordBtn.disabled = false;
      if (testBtn) testBtn.disabled = false;
    };
    recorder.start();
    startProgressBar(5000);
  }

  function recordFiveSecondTest() {
    if (!stream) { setStatus("Please click 'Test Camera & Microphone' first."); return; }
    if (!window.MediaRecorder) {
      setStatus("Your browser does not support in-browser recording (MediaRecorder). Try Chrome or Firefox.");
      return;
    }
    clearTestRecording();
    resetPrepAndProgressUI();
    if (recordBtn) recordBtn.disabled = true;
    if (testBtn) testBtn.disabled = true;
    let prep = 3;
    prepEl.style.display = "block";
    prepEl.textContent = "Recording in " + prep + "...";
    prepTimerId = setInterval(() => {
      prep -= 1;
      if (prep > 0) {
        prepEl.textContent = "Recording in " + prep + "...";
      } else {
        clearInterval(prepTimerId);
        prepTimerId = null;
        prepEl.style.display = "none";
        prepEl.textContent = "";
        startRecordingNow();
      }
    }, 1000);
  }

  if (confirmYesBtn) confirmYesBtn.addEventListener("click", () => setConfirmSelection("yes"));
  if (confirmNoBtn) confirmNoBtn.addEventListener("click", () => setConfirmSelection("no"));
  if (testBtn) testBtn.addEventListener("click", testCameraAndMic);
  if (recordBtn) recordBtn.addEventListener("click", recordFiveSecondTest);

  window.addEventListener("pagehide", function () {
    try {
      resetPrepAndProgressUI();
      if (rafId) cancelAnimationFrame(rafId);
      blurCam.stop();
      if (stream) stream.getTracks().forEach(t => t.stop());
      if (audioContext) audioContext.close().catch(() => {});
    } catch (e) {}
  });
})();

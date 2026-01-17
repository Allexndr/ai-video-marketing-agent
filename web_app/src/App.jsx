import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  Play, Image as ImageIcon, Video, Upload,
  Wand2, Settings, Download, Film, Music, Loader2
} from 'lucide-react';

const API_URL = import.meta.env.PROD ? "" : "http://127.0.0.1:8000";

function App() {
  // State
  const [imagePrompt, setImagePrompt] = useState("Isometric exploded view animation of a white Zeekr car assembling...");
  const [videoPrompt, setVideoPrompt] = useState("Time-lapse of a white Zeekr car being fully assembled. Parts RAPIDLY FLY TOGETHER...");
  const [audioPrompt, setAudioPrompt] = useState("Robotic mechanical assembly sounds...");

  const [generatedImage, setGeneratedImage] = useState(null); // { url, path }
  const [generatedVideo, setGeneratedVideo] = useState(null); // { url, path }
  const [generatedAudio, setGeneratedAudio] = useState(null); // { url, path }

  const [loadingImage, setLoadingImage] = useState(false);
  const [loadingVideo, setLoadingVideo] = useState(false);
  const [loadingAudio, setLoadingAudio] = useState(false);

  const [uploadedImage, setUploadedImage] = useState(null);

  // --- Handlers ---

  const handleGenerateImage = async () => {
    setLoadingImage(true);
    try {
      const res = await axios.post(`${API_URL}/api/generate-image`, { prompt: imagePrompt });
      setGeneratedImage(res.data);
      setUploadedImage(null); // Clear manual upload if we generated one
    } catch (e) {
      alert("Failed to generate image: " + e.message);
    }
    setLoadingImage(false);
  };

  const handleNavigateVideo = async () => {
    // Determine source image
    const imgSource = uploadedImage?.path || generatedImage?.path;
    let imgBase64 = null;

    if (!imgSource) {
      alert("Please generate or upload an image first!");
      return;
    }

    setLoadingVideo(true);
    try {
      // On Vercel (Production), we cannot rely on local file paths persisting between requests.
      // We must send the image data itself (base64).
      // If we have a URL (from generatedImage.url or uploadedImage), fetch it and convert.

      const imgUrl = uploadedImage?.url || generatedImage?.url;
      if (imgUrl) {
        // It's a URL (either /api/files/... or a blob/data URI)
        // Fetch it to get the blob
        const response = await fetch(imgUrl);
        const blob = await response.blob();
        // Convert to base64
        imgBase64 = await new Promise((resolve) => {
          const reader = new FileReader();
          reader.onloadend = () => resolve(reader.result);
          reader.readAsDataURL(blob);
        });
      } else if (imgSource.startsWith('data:')) {
        imgBase64 = imgSource;
      }

      const res = await axios.post(`${API_URL}/api/generate-video`, {
        prompt: videoPrompt,
        image_path: imgSource, // Keep for localhost fallback
        image_base64: imgBase64, // New field for Vercel
        duration: 10
      });
      setGeneratedVideo(res.data);
    } catch (e) {
      alert("Failed to generate video: " + (e.response?.data?.detail || e.message));
    }
    setLoadingVideo(false);
  };

  const handleGenerateAudio = async () => {
    setLoadingAudio(true);
    try {
      const res = await axios.post(`${API_URL}/api/generate-audio`, {
        text: audioPrompt,
        type: "sfx" // or voice
      });
      setGeneratedAudio(res.data);
    } catch (e) {
      alert("Failed Audio: " + e.message);
    }
    setLoadingAudio(false);
  }

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await axios.post(`${API_URL}/api/upload`, formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });
      setUploadedImage(res.data);
      setGeneratedImage(null); // Override generated
    } catch (e) {
      alert("Upload failed");
    }
  };

  // --- UI Components ---

  return (
    <div className="min-h-screen bg-background text-white font-sans selection:bg-primary selection:text-white">
      {/* Header */}
      <header className="border-b border-zinc-800 bg-surface/50 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-gradient-to-tr from-primary to-purple-600 rounded-lg flex items-center justify-center">
              <Film className="w-5 h-5 text-white" />
            </div>
            <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-zinc-400">
              AI Video Studio
            </h1>
          </div>
          <div className="text-xs text-zinc-500 font-mono">v2.0 PRO • API ENABLED</div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto p-6 grid grid-cols-1 lg:grid-cols-3 gap-8">

        {/* Column 1: Prompt Engineering */}
        <section className="space-y-6">
          <div className="flex items-center gap-2 text-primary mb-4">
            <Wand2 className="w-5 h-5" />
            <h2 className="font-semibold uppercase tracking-wider text-sm">1. Prompt Engineering</h2>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-zinc-400 mb-2 uppercase">Image Prompt / Concept</label>
              <textarea
                className="w-full h-32 text-sm bg-zinc-900/50 border-zinc-700 hover:border-zinc-500 focus:border-primary transition-colors resize-none"
                value={imagePrompt}
                onChange={(e) => setImagePrompt(e.target.value)}
                placeholder="Describe the initial visual..."
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-zinc-400 mb-2 uppercase">Video Motion Prompt</label>
              <textarea
                className="w-full h-32 text-sm bg-zinc-900/50 border-zinc-700 hover:border-zinc-500 focus:border-primary transition-colors resize-none"
                value={videoPrompt}
                onChange={(e) => setVideoPrompt(e.target.value)}
                placeholder="Describe the movement and camera action..."
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-zinc-400 mb-2 uppercase">Audio / SFX Prompt</label>
              <input
                type="text"
                className="w-full text-sm bg-zinc-900/50 border-zinc-700"
                value={audioPrompt}
                onChange={(e) => setAudioPrompt(e.target.value)}
              />
              <button
                onClick={handleGenerateAudio}
                disabled={loadingAudio}
                className="mt-2 w-full flex items-center justify-center gap-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 py-2 rounded transition-all text-xs uppercase font-bold tracking-wide"
              >
                {loadingAudio ? <Loader2 className="w-4 h-4 animate-spin" /> : <Music className="w-4 h-4" />}
                Generate Sound
              </button>
              {generatedAudio && (
                <audio controls src={`${API_URL}${generatedAudio.url}`} className="w-full mt-2 h-8" />
              )}
            </div>
          </div>
        </section>

        {/* Column 2: Visual Source */}
        <section className="space-y-6">
          <div className="flex items-center gap-2 text-accent mb-4">
            <ImageIcon className="w-5 h-5" />
            <h2 className="font-semibold uppercase tracking-wider text-sm">2. Source Visual</h2>
          </div>

          <div className="bg-surface border border-zinc-800 rounded-xl overflow-hidden aspect-video flex flex-col relative group">
            {(generatedImage || uploadedImage) ? (
              <img
                src={`${API_URL}${(uploadedImage || generatedImage).url}`}
                alt="Source"
                className="w-full h-full object-cover"
              />
            ) : (
              <div className="flex-1 flex flex-col items-center justify-center text-zinc-500 gap-4">
                <ImageIcon className="w-12 h-12 opacity-20" />
                <p className="text-sm">No image selected</p>
              </div>
            )}

            {loadingImage && (
              <div className="absolute inset-0 bg-black/80 flex items-center justify-center z-10 backdrop-blur-sm">
                <div className="text-center">
                  <Loader2 className="w-10 h-10 animate-spin text-primary mx-auto mb-2" />
                  <p className="text-xs text-primary font-mono animate-pulse">GENERATING PIXELS...</p>
                </div>
              </div>
            )}
          </div>

          <div className="grid grid-cols-2 gap-4">
            <button
              onClick={handleGenerateImage}
              disabled={loadingImage}
              className="bg-primary hover:bg-blue-600 text-white py-3 rounded-lg flex items-center justify-center gap-2 font-bold shadow-lg shadow-blue-900/20 active:scale-95 transition-transform"
            >
              <Wand2 className="w-4 h-4" />
              GENERATE
            </button>
            <label className="bg-zinc-800 hover:bg-zinc-700 cursor-pointer text-white py-3 rounded-lg flex items-center justify-center gap-2 font-bold active:scale-95 transition-transform">
              <Upload className="w-4 h-4" />
              UPLOAD
              <input type="file" className="hidden" onChange={handleFileUpload} accept="image/*" />
            </label>
          </div>
        </section>

        {/* Column 3: Final Output */}
        <section className="space-y-6">
          <div className="flex items-center gap-2 text-green-500 mb-4">
            <Video className="w-5 h-5" />
            <h2 className="font-semibold uppercase tracking-wider text-sm">3. Final Video</h2>
          </div>

          <div className="bg-surface border border-zinc-800 rounded-xl overflow-hidden aspect-[9/16] lg:aspect-video flex flex-col relative shadow-2xl shadow-black">
            {generatedVideo ? (
              <video
                controls
                className="w-full h-full object-contain bg-black"
                src={`${API_URL}${generatedVideo.url}`}
              />
            ) : (
              <div className="flex-1 flex flex-col items-center justify-center text-zinc-500 gap-4 bg-zinc-900/50">
                <Film className="w-12 h-12 opacity-20" />
                <p className="text-sm">Waiting for direction...</p>
              </div>
            )}

            {loadingVideo && (
              <div className="absolute inset-0 bg-black/90 flex items-center justify-center z-20 backdrop-blur-md">
                <div className="text-center p-6 border border-zinc-800 rounded-xl bg-surface/50">
                  <Loader2 className="w-12 h-12 animate-spin text-green-500 mx-auto mb-4" />
                  <h3 className="text-lg font-bold text-white mb-1">PRODUCING VIDEO</h3>
                  <p className="text-xs text-zinc-400 font-mono">
                    Creating motion from stillness...<br />
                    Wait time: ~2-5 mins
                  </p>
                </div>
              </div>
            )}
          </div>

          <button
            onClick={handleNavigateVideo}
            disabled={loadingVideo || (!uploadedImage && !generatedImage)}
            className="w-full bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-500 hover:to-emerald-500 text-white py-4 rounded-xl flex items-center justify-center gap-3 font-bold text-lg shadow-xl shadow-green-900/20 active:scale-95 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loadingVideo ? "PROCESSING..." : (
              <>
                <Play className="w-6 h-6 fill-current" />
                RENDER MOVIE
              </>
            )}
          </button>

          {generatedVideo && (
            <a
              href={`${API_URL}${generatedVideo.url}`}
              download
              className="block text-center text-xs text-zinc-500 hover:text-white transition-colors flex items-center justify-center gap-1"
            >
              <Download className="w-3 h-3" /> Download MP4
            </a>
          )}
        </section>

      </main>
    </div>
  );
}

export default App;

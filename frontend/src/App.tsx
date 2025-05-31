import React, { useState, useEffect } from 'react';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent } from "@/components/ui/card";
import { UploadCloud, Sparkles } from "lucide-react"; // Removed SlidersHorizontal
import { motion } from "framer-motion";

const backendUrl = window.location.hostname === "localhost"
  ? "http://localhost:8000"
  : "https://e24d-97-93-224-68.ngrok-free.app";


const sampleInputs = [
  {
    img: "/armchair2.png",
    prompt: "A photo of an armchair. The armchair is in a minimalist bedroom with blue wall with a mirror, a lamp and a cute puppy.",
  },
  {
    img: "/cat_subject.png",
    prompt: "A photo of a cat. A cat sits on a wooden table in a cozy restaurant, gently eating cat food from a small ceramic plate, surrounded by soft ambient lighting and simple décor.",
  },
  {
    img: "/dresser_subject.png",
    prompt: "A photo of a dresser. A wooden, cane dresser in a minimalist bedroom with soft natural light and things on top of the dresser.",
  },
  {
    img: "/mower_subject.png",
    prompt: "A photo of a lawn mower. A lawn mower is parked on a freshly mowed grassy field in a suburb.",
  },
  // 2nd row
  {
    img: "/alpaca.jpg",
    prompt: "A photo of an alpaca. An alpaca standing on the sidewalk in downtown Manhattan.",
  },
  {
    img: "/tv_stand.png",
    prompt: "A photo of a TV stand. A TV stand in a living room with a tv, some books and decorative items.",
  },
  {
    img: "/adirondack_chair.png",
    prompt: "A photo of a Adirondack chair. A Adirondack chair in the backyard garden.",
  },
  {
    img: "/throw_pillow.png",
    prompt: "A photo of a throw pillow. A textured throw pillow with woven black and white patterns, featuring braided accents and decorative short white tassels on the sides. Displayed against a clean blue background.",
  },
];

export default function GenerativeAILanding() {
  const [image, setImage] = useState<File | null>(null); // Uploaded image state
  const [imagePreview, setImagePreview] = useState<string | null>(null); // Preview for uploaded image
  const [prompt, setPrompt] = useState<string>(""); // Text prompt
  const [generated, setGenerated] = useState<string | null>(null); // Generated image state
  const [isLoading, setIsLoading] = useState<boolean>(false); // Loading state
  const [elapsedTime, setElapsedTime] = useState<number>(0); // Elapsed time for progress bar

  useEffect(() => {
    let timer: NodeJS.Timeout | undefined; // Initialize timer with undefined
    if (isLoading) {
      setElapsedTime(0); // Reset elapsed time
      timer = setInterval(() => {
        setElapsedTime((prev) => prev + 1); // Increment elapsed time every second
      }, 1000);
    } else if (timer) {
      clearInterval(timer); // Clear timer when loading stops
    }
    return () => {
      if (timer) clearInterval(timer); // Cleanup timer on unmount
    };
  }, [isLoading]);

  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (file.size > 5 * 1024 * 1024) { // Check if file size exceeds 5MB
        alert("The uploaded image exceeds the 5MB size limit. Please upload a smaller image.");
        return;
      }
      setImage(file);
      setImagePreview(URL.createObjectURL(file)); // Show uploaded image as preview
    }
  };

  const handleSampleClick = (img: string, text: string) => {
    // Set the sample image and prompt
    setImage(null); // Reset uploaded image
    setImagePreview(img); // Display the sample image in the upload preview
    setPrompt(text);
    setGenerated(null); // Reset the generated image
  };

  const handleGenerate = async () => {
    if (!image && !imagePreview) {
      alert("Please upload an image or select a sample.");
      return;
    }

    if (!prompt) {
      alert("Please enter a prompt.");
      return;
    }

    setIsLoading(true);

    const formData = new FormData();
    if (image) {
      formData.append("product_image", image); // Send the uploaded image
    } else if (imagePreview) {
      // Convert the sample image URL to a Blob and append it as "product_image"
      const response = await fetch(imagePreview);
      const blob = await response.blob();
      formData.append("product_image", blob, "sample_image.png");
    }
    formData.append("prompt", prompt);

    try {
      // const response = await fetch("http://localhost:8000/generate", {
      const response = await fetch(`${backendUrl}/generate`, {

        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error("Failed to generate image");
      }

      const data = await response.json();
      // Use the `url` returned by the backend to display the generated image
      // setGenerated(`http://localhost:8000${data.url}?t=${Date.now()}`);
      console.log("Backend URL:", backendUrl);
      console.log("Full backend response:", data);
      // setGenerated(`${backendUrl}${data.url}?t=${Date.now()}`);
      const fullImageUrl = `${backendUrl}${data.url.startsWith("/") ? data.url : "/" + data.url}?t=${Date.now()}`;
      console.log("Full image URL:", fullImageUrl);
      setGenerated(fullImageUrl);

    } catch (error) {
      console.error("Error generating image:", error);
      alert("An error occurred while generating the image. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#fdfcfb] to-[#e2d1c3] p-6 flex flex-col items-center text-zinc-800">
      <motion.div
        className="text-center max-w-2xl mb-8"
        initial={{ opacity: 0, y: -40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8 }}
      >
        <h1 className="text-5xl font-bold tracking-tight mb-4 text-transparent bg-clip-text bg-gradient-to-r from-orange-600 via-amber-500 to-yellow-400">
          Generative Studio
        </h1>
        <p className="text-lg text-zinc-600">
          Transform your imagination into reality. Upload an image, add a text prompt, and let the AI create professional visuals.
        </p>
      </motion.div>

      <div className="flex w-full max-w-6xl gap-6">
        {/* Left side - Inputs */}
        <Card className="w-[500px] bg-white shadow-2xl rounded-2xl p-6 border border-zinc-200">
          <h2 className="text-lg font-semibold text-zinc-700 mb-4">Input</h2>
          <CardContent className="flex flex-col gap-4">
            <label className="font-medium flex flex-col gap-2">
              <span className="flex items-center gap-2">
                <UploadCloud size={18} /> Upload Image
              </span>
              <div className="relative">
                <Input
                  type="file"
                  accept="image/*"
                  onChange={handleImageUpload}
                  className="absolute inset-0 opacity-0 cursor-pointer"
                />
                <div className="flex items-center justify-center w-full h-12 border border-dashed border-zinc-300 rounded-lg bg-zinc-50 hover:bg-zinc-100 transition-colors cursor-pointer">
                  <p className="text-sm text-zinc-500">Choose a file</p>
                </div>
              </div>
              <p className="text-xs text-zinc-400 mt-1">Please upload an image under 5MB.</p>
            </label>

            {imagePreview && (
              <div className="flex justify-center">
                <img
                  src={imagePreview}
                  alt="Uploaded or Sample preview"
                  className="rounded-xl border object-cover w-32 h-32"
                />
              </div>
            )}

            <label className="font-medium">Text Prompt</label>
            <Textarea
              placeholder="e.g., A photo of a dog. A dog is in a park playing with a ball."
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
            />

            <div className="grid grid-cols-2 gap-4">
              {/* Guidance Bar */}
              {/* <div>
                <label className="font-medium flex items-center gap-2">
                  <SlidersHorizontal size={18} /> Guidance
                </label>
                <input
                  type="range"
                  min={0}
                  max={15}
                  step={0.5}
                  value={guidance}
                  onChange={(e) => setGuidance(Number(e.target.value))}
                  style={{ background: getGuidanceGradient(guidance) }}
                  className="w-full h-2 rounded-lg appearance-none cursor-pointer"
                />
                <p className="text-sm text-zinc-500">{guidance.toFixed(1)}</p>
              </div> */}
            </div>

            <Button
              onClick={handleGenerate}
              className="mt-4 text-lg bg-gradient-to-r from-[#f97316] via-[#fb923c] to-[#f59e0b] hover:opacity-90 text-white"
              disabled={isLoading}
            >
              <Sparkles className="mr-2 h-5 w-5" /> {isLoading ? 'Generating...' : 'Generate'}
            </Button>
          </CardContent>
        </Card>

        {/* Right side - Output */}
        <Card className="w-[650px] bg-white shadow-2xl rounded-2xl p-6 flex items-center justify-center border border-zinc-200 relative">
          <h2 className="absolute top-6 left-6 text-lg font-semibold text-zinc-700">Output</h2>
          <CardContent className="w-full h-full flex flex-col items-center justify-center gap-4 relative overflow-hidden">
            {isLoading ? (
              <div className="flex flex-col items-center gap-4">
                <img 
                  src="/loading.gif" 
                  alt="Loading..." 
                  className="w-32 h-32"
                />
                <p className="text-zinc-500 animate-pulse">Generating your image...</p>
                <p className="text-sm mt-2 text-center bg-gradient-to-r from-orange-500 to-orange-700 text-transparent bg-clip-text">
                  {elapsedTime}s
                </p>
              </div>
            ) : generated ? (
              <div className="relative w-full h-full flex flex-col items-center justify-center gap-4">
                <div className="relative inline-block max-w-full max-h-full">
                  <img
                    src={generated}
                    alt="Generated result"
                    className="rounded-xl border object-contain"
                    style={{
                      maxWidth: "100%",
                      maxHeight: "450px",
                    }}
                  />
                </div>
                <a
                  role="button"
                  title="Download"
                  className="bg-blue-100/70 backdrop-blur-md p-2 rounded-full shadow hover:bg-blue-200/70 transition-colors"
                  onClick={(e) => {
                    e.preventDefault(); // Prevent default behavior of opening the image
                    if (!generated) return;

                    const link = document.createElement("a");
                    link.href = generated; // Use the generated URL
                    link.download = "generated-image.png"; // Set the filename for download
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link); // Clean up the link element
                  }}
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    className="h-5 w-5 text-blue-600"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M4 16v2a2 2 0 002 2h12a2 2 0 002-2v-2m-4-4l-4 4m0 0l-4-4m4 4V4"
                    />
                  </svg>
                </a>
              </div>
            ) : (
              <p className="text-zinc-400">Your generated image will appear here.</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Sample Inputs Card */}
      <Card className="w-full max-w-6xl mt-8 bg-white border border-zinc-100">
        <CardContent className="p-6">
          <p className="font-medium text-zinc-600 mb-4 text-lg">Try a sample:</p>
          <div className="grid grid-cols-4 gap-6"> {/* Adjusted to 4 columns */}
            {sampleInputs.map((sample, idx) => (
              <div
                key={idx}
                className="cursor-pointer flex flex-col items-center p-4 bg-zinc-50 rounded-lg shadow hover:shadow-md transition-shadow"
                onClick={() => handleSampleClick(sample.img, sample.prompt)}
              >
                <img src={sample.img} alt={`Sample ${idx + 1}`} className="rounded-xl border w-32 h-32 object-cover mb-2" />
                <p className="text-sm text-zinc-500 italic text-center">{sample.prompt.slice(0, 60)}...</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Footer Section */}
      <footer className="w-full mt-12 py-4 text-center border-t border-zinc-200 flex justify-between items-center px-6">
        <p className="text-sm text-zinc-600">
          Developed by Jibanul Haque | 2025
        </p>
        <a
          href="https://www.linkedin.com/in/jibanul/"
          target="_blank"
          rel="noopener noreferrer"
          className="text-zinc-500 hover:text-zinc-700 text-sm flex items-center gap-2 transition-colors"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-4 w-4"
            fill="currentColor"
            viewBox="0 0 24 24"
          >
            <path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.761 0 5-2.239 5-5v-14c0-2.761-2.239-5-5-5zm-11 19h-3v-10h3v10zm-1.5-11.268c-.966 0-1.75-.784-1.75-1.75s.784-1.75 1.75-1.75 1.75.784 1.75 1.75-.784 1.75-1.75 1.75zm13.5 11.268h-3v-5.604c0-1.337-.027-3.061-1.865-3.061-1.865 0-2.151 1.455-2.151 2.959v5.706h-3v-10h2.881v1.367h.041c.401-.759 1.381-1.559 2.841-1.559 3.041 0 3.604 2.001 3.604 4.604v5.588z" />
          </svg>
          Contact on LinkedIn
        </a>
      </footer>
    </div>
  );
}
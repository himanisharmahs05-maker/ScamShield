import React, { useState, useRef, useEffect } from "react";
import jsQR from "jsqr";
import {
  QrCode,
  Upload,
  Camera,
  X,
  CheckCircle2,
  AlertCircle,
  ArrowRight,
  Loader2,
  ShieldAlert,
} from "lucide-react";
import "./QuishingScannerModal.css";

export const QuishingScannerModal = ({ isOpen, onClose, onScanUrl }) => {
  const [activeTab, setActiveTab] = useState("upload"); // "upload" | "camera"
  const [decodedData, setDecodedData] = useState(null);
  const [errorMsg, setErrorMsg] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [isDragging, setIsDragging] = useState(false);

  const fileInputRef = useRef(null);
  const videoRef = useRef(null);
  const animationFrameRef = useRef(null);
  const streamRef = useRef(null);

  // Reset state on open/close
  useEffect(() => {
    if (!isOpen) {
      stopCamera();
      setDecodedData(null);
      setErrorMsg("");
      setIsProcessing(false);
    }
  }, [isOpen]);

  // Handle Clipboard Paste (Ctrl + V)
  useEffect(() => {
    if (!isOpen) return;

    const handlePaste = (e) => {
      const items = e.clipboardData?.items;
      if (!items) return;

      for (let i = 0; i < items.length; i++) {
        if (items[i].type.indexOf("image") !== -1) {
          const file = items[i].getAsFile();
          if (file) {
            decodeImageFile(file);
            break;
          }
        }
      }
    };

    window.addEventListener("paste", handlePaste);
    return () => window.removeEventListener("paste", handlePaste);
  }, [isOpen]);

  // Decode Image File with jsQR
  const decodeImageFile = (file) => {
    if (!file) return;
    setIsProcessing(true);
    setErrorMsg("");
    setDecodedData(null);

    const reader = new FileReader();
    reader.onload = (e) => {
      const img = new Image();
      img.onload = () => {
        const canvas = document.createElement("canvas");
        const ctx = canvas.getContext("2d", { willReadFrequently: true });
        canvas.width = img.width;
        canvas.height = img.height;
        ctx.drawImage(img, 0, 0, img.width, img.height);

        const imgData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        const code = jsQR(imgData.data, imgData.width, imgData.height, {
          inversionAttempts: "dontInvert",
        });

        setIsProcessing(false);
        if (code && code.data) {
          setDecodedData(code.data.trim());
        } else {
          setErrorMsg("No QR code detected in this image. Ensure the QR is clear and well-lit.");
        }
      };
      img.onerror = () => {
        setIsProcessing(false);
        setErrorMsg("Failed to process image file.");
      };
      img.src = e.target.result;
    };
    reader.readAsDataURL(file);
  };

  // Camera Management
  const startCamera = async () => {
    try {
      setErrorMsg("");
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "environment" },
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.setAttribute("playsinline", "true");
        await videoRef.current.play();
        requestAnimationFrame(tickCamera);
      }
    } catch (err) {
      console.error(err);
      setErrorMsg("Camera access denied or device has no available camera.");
    }
  };

  const stopCamera = () => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
  };

  const tickCamera = () => {
    if (videoRef.current && videoRef.current.readyState === videoRef.current.HAVE_ENOUGH_DATA) {
      const canvas = document.createElement("canvas");
      canvas.width = videoRef.current.videoWidth;
      canvas.height = videoRef.current.videoHeight;
      const ctx = canvas.getContext("2d", { willReadFrequently: true });
      ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);

      const imgData = ctx.getImageData(0, 0, canvas.width, canvas.height);
      const code = jsQR(imgData.data, imgData.width, imgData.height, {
        inversionAttempts: "dontInvert",
      });

      if (code && code.data) {
        setDecodedData(code.data.trim());
        stopCamera();
        return;
      }
    }
    animationFrameRef.current = requestAnimationFrame(tickCamera);
  };

  // Switch Tabs
  const handleTabChange = (tab) => {
    setActiveTab(tab);
    setErrorMsg("");
    if (tab === "camera") {
      startCamera();
    } else {
      stopCamera();
    }
  };

  // Drag and Drop handlers
  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      decodeImageFile(e.dataTransfer.files[0]);
    }
  };

  // Proceed with scan
  const handleConfirmScan = () => {
    if (!decodedData) return;
    onScanUrl(decodedData);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="quishing-modal-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="quishing-modal-box">
        {/* Header */}
        <div className="quishing-modal-header">
          <div className="quishing-title-wrap">
            <div className="quishing-icon-badge">
              <QrCode size={20} />
            </div>
            <div>
              <h2>Quishing Shield</h2>
              <div className="quishing-subtitle">QR Code & Screenshot Phishing Analyzer</div>
            </div>
          </div>
          <button className="quishing-close-btn" onClick={onClose} aria-label="Close modal">
            <X size={18} />
          </button>
        </div>

        {/* Tab selection */}
        <div className="quishing-tabs">
          <button
            className={`quishing-tab ${activeTab === "upload" ? "active" : ""}`}
            onClick={() => handleTabChange("upload")}
          >
            <Upload size={15} />
            <span>Upload or Paste</span>
          </button>
          <button
            className={`quishing-tab ${activeTab === "camera" ? "active" : ""}`}
            onClick={() => handleTabChange("camera")}
          >
            <Camera size={15} />
            <span>Live Camera</span>
          </button>
        </div>

        {/* Modal Body */}
        <div className="quishing-modal-body">
          {activeTab === "upload" ? (
            <div>
              <div
                className={`quishing-dropzone ${isDragging ? "dragging" : ""}`}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
              >
                <input
                  type="file"
                  ref={fileInputRef}
                  style={{ display: "none" }}
                  accept="image/*"
                  onChange={(e) => e.target.files?.[0] && decodeImageFile(e.target.files[0])}
                />
                <div className="dropzone-inner">
                  <div className="dropzone-icon-circle">
                    {isProcessing ? <Loader2 className="spinner" size={24} /> : <Upload size={24} />}
                  </div>
                  <div className="dropzone-primary-text">
                    {isProcessing ? "Decoding QR Code…" : "Drop QR image here, or click to browse"}
                  </div>
                  <div className="dropzone-sub-text">
                    Tip: You can also press <kbd>Ctrl</kbd> + <kbd>V</kbd> to paste a screenshot!
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="quishing-camera-container">
              <div className="camera-preview-wrapper">
                <video ref={videoRef} className="camera-video" />
                <div className="camera-scan-reticle" />
              </div>
              <div className="dropzone-sub-text">Point camera at QR code to scan automatically</div>
            </div>
          )}

          {/* Error Message */}
          {errorMsg && (
            <div className="quishing-error-message">
              <AlertCircle size={16} />
              <span>{errorMsg}</span>
            </div>
          )}

          {/* Decoded Output */}
          {decodedData && (
            <div className="quishing-result-card">
              <div className="quishing-result-header">
                <CheckCircle2 size={16} />
                <span>QR Code Decoded Successfully</span>
              </div>
              <div className="quishing-decoded-url">{decodedData}</div>
              <button className="quishing-action-btn" onClick={handleConfirmScan}>
                <span>Analyze with ScamShield</span>
                <ArrowRight size={16} />
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

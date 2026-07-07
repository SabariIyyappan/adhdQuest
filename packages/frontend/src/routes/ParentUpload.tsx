import { useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { uploadAssignmentPdf } from "../lib/butterbase";
import { useChildren } from "../hooks/useChildren";
import { useToast } from "../components/ui/ToastProvider";
import { FileUp, Sparkles, BookOpen, AlertCircle, CheckCircle2 } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

export function ParentUpload({ childId: defaultChildId }: { childId: string }) {
  const navigate = useNavigate();
  const { data: children, isLoading: childrenLoading } = useChildren();
  const { success, error } = useToast();
  
  const [selectedChildId, setSelectedChildId] = useState<string>("");
  const [status, setStatus] = useState<"idle" | "uploading" | "simulating_pipeline" | "ready">("idle");
  const [uploadProgress, setUploadProgress] = useState(0);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Initialize selected child
  if (!selectedChildId && children && children.length > 0) {
    setSelectedChildId(children[0].id);
  } else if (!selectedChildId && defaultChildId && defaultChildId !== "TODO-selected-child") {
    setSelectedChildId(defaultChildId);
  }

  async function handleFile(file: File) {
    const activeId = selectedChildId || defaultChildId || "child_demo_1";
    if (file.type !== "application/pdf") {
      error("Only PDF homework sheets are supported!");
      return;
    }

    try {
      setStatus("uploading");
      setUploadProgress(20);
      
      // Upload PDF to Butterbase storage
      await uploadAssignmentPdf(activeId, file);
      
      setUploadProgress(60);
      setStatus("simulating_pipeline");
      
      // Simulate pipeline transition states before routing to game frame
      setTimeout(() => {
        setUploadProgress(90);
        setTimeout(() => {
          setUploadProgress(100);
          setStatus("ready");
          success("Homework uploaded successfully! Connecting to game sandbox...");
          setTimeout(() => {
            navigate(`/play/${activeId}`);
          }, 800);
        }, 1000);
      }, 1000);
      
    } catch (err) {
      console.error(err);
      error("Something went wrong during PDF upload.");
      setStatus("idle");
    }
  }

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const onButtonClick = () => {
    fileInputRef.current?.click();
  };

  const activeChildName = children?.find(c => c.id === selectedChildId)?.name || "Alex";

  return (
    <div style={{ maxWidth: "680px", margin: "2rem auto" }} className="animate-slide-in">
      <div className="card" style={{ padding: "2.5rem" }}>
        
        {/* Title */}
        <div style={{ textAlign: "center", marginBottom: "2rem" }}>
          <div style={{
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
            width: "56px",
            height: "56px",
            borderRadius: "16px",
            backgroundColor: "rgba(108, 92, 231, 0.1)",
            color: "var(--color-primary)",
            marginBottom: "1rem"
          }}>
            <BookOpen size={28} />
          </div>
          <h1 style={{ fontSize: "2rem", fontWeight: "900", marginBottom: "0.5rem" }}>
            Generate a Learning Game
          </h1>
          <p style={{ color: "var(--color-text-secondary)" }}>
            Upload a PDF math homework sheet. The system will create a personalized mini-game.
          </p>
        </div>

        {/* Profile Selector */}
        <div className="form-group" style={{ marginBottom: "2rem" }}>
          <label className="form-label">Select Child Profile</label>
          {childrenLoading ? (
            <div style={{ height: "46px", backgroundColor: "rgba(26,26,46,0.5)", borderRadius: "12px", border: "2px solid var(--color-border)" }} />
          ) : (
            <select
              className="form-select"
              value={selectedChildId}
              onChange={(e) => setSelectedChildId(e.target.value)}
              disabled={status !== "idle"}
            >
              {children?.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name} (Grade {c.grade})
                </option>
              )) || <option value="child_demo_1">Alex (Grade 4)</option>}
            </select>
          )}
        </div>

        {/* Upload Container states */}
        <AnimatePresence mode="wait">
          {status === "idle" ? (
            <motion.div
              key="drag-drop-zone"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              onDragEnter={handleDrag}
              onDragOver={handleDrag}
              onDragLeave={handleDrag}
              onDrop={handleDrop}
              style={{
                border: `3px dashed ${dragActive ? "var(--color-primary)" : "var(--color-border)"}`,
                borderRadius: "20px",
                padding: "3rem 1.5rem",
                textAlign: "center",
                backgroundColor: dragActive ? "rgba(108, 92, 231, 0.05)" : "rgba(26, 26, 46, 0.2)",
                cursor: "pointer",
                transition: "all 0.2s ease-in-out",
                position: "relative"
              }}
              onClick={onButtonClick}
            >
              <input
                ref={fileInputRef}
                type="file"
                className="hidden-file-input"
                style={{ display: "none" }}
                accept="application/pdf"
                onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
              />
              <FileUp
                size={48}
                color={dragActive ? "var(--color-primary)" : "var(--color-text-secondary)"}
                style={{ marginBottom: "1rem" }}
              />
              <h3 style={{ fontSize: "1.25rem", fontWeight: "800", marginBottom: "0.5rem" }}>
                Drag & drop your PDF homework here
              </h3>
              <p style={{ color: "var(--color-text-secondary)", fontSize: "0.9rem", marginBottom: "1.5rem" }}>
                or click to browse files from your computer
              </p>
              
              <div style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "0.5rem",
                fontSize: "0.8rem",
                color: "var(--color-accent)",
                backgroundColor: "rgba(253, 203, 110, 0.1)",
                padding: "0.5rem 1rem",
                borderRadius: "9999px",
                fontWeight: "700"
              }}>
                <Sparkles size={14} />
                Extracts questions & compiles a personalized sandbox game automatically
              </div>
            </motion.div>
          ) : (
            <motion.div
              key="progress-zone"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              style={{
                borderRadius: "20px",
                padding: "3rem 2rem",
                backgroundColor: "rgba(26, 26, 46, 0.5)",
                border: "1px solid var(--color-border)",
                textAlign: "center",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                gap: "1.5rem"
              }}
            >
              <div className="animate-pulse-ring" style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                width: "60px",
                height: "60px",
                borderRadius: "50%",
                backgroundColor: "var(--color-primary)",
                color: "#fff"
              }}>
                {status === "ready" ? <CheckCircle2 size={32} /> : <FileUp className="animate-float" size={30} />}
              </div>

              <div style={{ width: "100%", maxWidth: "400px" }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.5rem", fontSize: "0.85rem", fontWeight: "800" }}>
                  <span style={{ color: "var(--color-text-secondary)" }}>
                    {status === "uploading" && "Uploading homework PDF..."}
                    {status === "simulating_pipeline" && `Analyzing questions for ${activeChildName}...`}
                    {status === "ready" && "Ready to launch!"}
                  </span>
                  <span>{uploadProgress}%</span>
                </div>
                <div style={{ height: "12px", width: "100%", backgroundColor: "var(--color-bg)", borderRadius: "999px", overflow: "hidden", border: "1px solid var(--color-border)" }}>
                  <div style={{ height: "100%", width: `${uploadProgress}%`, backgroundColor: "var(--color-primary)", transition: "width 0.4s ease" }} />
                </div>
              </div>

              {/* Progress Steps List */}
              <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem", textAlign: "left", width: "100%", maxWidth: "340px", margin: "1rem auto 0" }}>
                <StepItem label="Upload PDF sheet to cloud" active={true} completed={status !== "uploading"} />
                <StepItem label="Extract math questions (OCR/NER)" active={status === "simulating_pipeline" || status === "ready"} completed={status === "ready"} />
                <StepItem label="Build personalized Pygame sandbox" active={status === "ready"} completed={status === "ready"} />
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Tip Box */}
        <div style={{
          display: "flex",
          gap: "0.75rem",
          marginTop: "2rem",
          backgroundColor: "rgba(108, 92, 231, 0.05)",
          padding: "1rem",
          borderRadius: "12px",
          border: "1px solid rgba(108, 92, 231, 0.15)"
        }}>
          <AlertCircle size={20} color="var(--color-primary)" style={{ flexShrink: 0 }} />
          <p style={{ fontSize: "0.85rem", color: "var(--color-text-secondary)", lineHeight: 1.4 }}>
            <strong>ADHD-Friendly Note:</strong> Visual game compilation takes around 30 seconds. We automatically adjust game mechanics based on historical concept bottlenecks to keep levels highly engaging.
          </p>
        </div>

      </div>
    </div>
  );
}

function StepItem({ label, active, completed }: { label: string; active: boolean; completed: boolean }) {
  let color = "var(--color-text-muted)";
  if (completed) color = "var(--color-success)";
  else if (active) color = "var(--color-primary)";

  return (
    <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", color, fontWeight: active || completed ? "700" : "500", fontSize: "0.9rem" }}>
      <div style={{
        width: "18px",
        height: "18px",
        borderRadius: "50%",
        border: `2px solid ${color}`,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        fontSize: "0.6rem"
      }}>
        {completed ? "✓" : ""}
      </div>
      <span>{label}</span>
    </div>
  );
}

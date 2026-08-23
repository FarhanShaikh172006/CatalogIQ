"use client";

import { useEffect, useRef, useState } from "react";
import {
  Upload,
  Clipboard,
  FileSpreadsheet,
} from "lucide-react";

type FileUploadProps = {
  onFileSelected: (file: File) => void;
};

export default function FileUpload({
  onFileSelected,
}: FileUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const uploadAreaRef = useRef<HTMLDivElement>(null);

  const [isDragging, setIsDragging] = useState(false);

  useEffect(() => {
    const handlePaste = (event: ClipboardEvent) => {
      const clipboard = event.clipboardData;

      if (!clipboard) return;

      const items = Array.from(clipboard.items);

      const fileItem = items.find(
        (item) => item.kind === "file"
      );

      if (!fileItem) {
        return;
      }

      const file = fileItem.getAsFile();

      if (!file) return;

      const isValidFile =
        /\.(csv|xlsx|xls)$/i.test(file.name);

      if (!isValidFile) {
        event.preventDefault();
        return;
      }

      event.preventDefault();
      event.stopPropagation();

      onFileSelected(file);
    };

    document.addEventListener(
      "paste",
      handlePaste
    );

    return () => {
      document.removeEventListener(
        "paste",
        handlePaste
      );
    };
  }, [onFileSelected]);

  function handleFileChange(
    event: React.ChangeEvent<HTMLInputElement>
  ) {
    const selectedFile =
      event.target.files?.[0];

    if (!selectedFile) return;

    onFileSelected(selectedFile);

    event.target.value = "";
  }

  function handleDragOver(
    event: React.DragEvent<HTMLDivElement>
  ) {
    event.preventDefault();
    event.stopPropagation();

    setIsDragging(true);
  }

  function handleDragLeave(
    event: React.DragEvent<HTMLDivElement>
  ) {
    event.preventDefault();
    event.stopPropagation();

    setIsDragging(false);
  }

  function handleDrop(
    event: React.DragEvent<HTMLDivElement>
  ) {
    event.preventDefault();
    event.stopPropagation();

    setIsDragging(false);

    const droppedFile =
      event.dataTransfer.files?.[0];

    if (!droppedFile) return;

    const isValidFile =
      /\.(csv|xlsx|xls)$/i.test(
        droppedFile.name
      );

    if (!isValidFile) return;

    onFileSelected(droppedFile);
  }

  return (
    <div
      ref={uploadAreaRef}
      tabIndex={0}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={() =>
        inputRef.current?.click()
      }
      className={`
        cursor-pointer
        rounded-xl
        border
        border-dashed
        px-8
        py-16
        text-center
        transition
        outline-none
        ${
          isDragging
            ? "border-zinc-400 bg-zinc-800/70"
            : "border-zinc-700 bg-zinc-900/30 hover:border-zinc-500 hover:bg-zinc-900/60"
        }
      `}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".csv,.xlsx,.xls"
        className="hidden"
        onChange={handleFileChange}
      />

      <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl border border-zinc-800 bg-zinc-900">
        <Upload
          size={21}
          className="text-zinc-400"
        />
      </div>

      <div className="mt-5 text-sm font-medium">
        Upload catalog
      </div>

      <div className="mt-2 text-xs text-zinc-500">
        CSV, XLSX or XLS
      </div>

      <div className="mt-5 flex items-center justify-center gap-2 text-xs text-zinc-600">
        <Clipboard size={14} />

        <span>
          Drag & drop or paste a file
        </span>
      </div>

      {isDragging && (
        <div className="mt-4 text-xs text-zinc-300">
          Drop file to upload
        </div>
      )}
    </div>
  );
}
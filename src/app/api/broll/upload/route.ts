import { NextRequest, NextResponse } from "next/server";
import fs from "fs/promises";
import path from "path";
import { nanoid } from "nanoid";

export const runtime = "nodejs";

const UPLOAD_DIR = path.join(process.cwd(), "storage", "user_uploads");

async function ensureDir() {
  try {
    await fs.mkdir(UPLOAD_DIR, { recursive: true });
  } catch (e) {
    console.error("Failed to create upload directory:", e);
  }
}

export async function POST(req: NextRequest) {
  try {
    await ensureDir();

    const formData = await req.formData();
    const file = formData.get("file") as File;

    if (!file) {
      return NextResponse.json({ success: false, error: "No file provided" }, { status: 400 });
    }

    const extension = path.extname(file.name).toLowerCase();
    const allowedExtensions = [".mp4", ".mov", ".jpg", ".jpeg", ".png"];
    if (!allowedExtensions.includes(extension)) {
      return NextResponse.json({ success: false, error: "Unsupported file type" }, { status: 400 });
    }

    const fileName = `${nanoid()}${extension}`;
    const filePath = path.join(UPLOAD_DIR, fileName);

    const buffer = Buffer.from(await file.arrayBuffer());
    await fs.writeFile(filePath, buffer);

    // Construct a public URL for the file.
    // Note: In a production Next.js app, files in 'storage' aren't automatically public.
    // For this local setup, we'll return the relative path and let the frontend handle it,
    // or assume there's a static server mapping.
    const publicUrl = `/storage/user_uploads/${fileName}`;

    return NextResponse.json({
      success: true,
      clip: {
        id: `user-${nanoid()}`,
        source: "user",
        previewUrl: publicUrl,
        thumbnail: publicUrl, // For images, the file is the thumbnail. For videos, this is a simplification.
        query: file.name,
      },
    });
  } catch (error) {
    console.error("Upload error:", error);
    return NextResponse.json({ success: false, error: "Internal server error" }, { status: 500 });
  }
}

/**
 * Client-side Image Compression Utility.
 *
 * Implements Step 4.3 client requirements:
 * - Compresses images before upload (max dimension <= 1600px, target <= 1 MB)
 * - Strips EXIF metadata during canvas re-drawing
 * - Generates modern WEBP or JPEG blobs to conserve bandwidth and R2 storage
 */

export interface CompressionOptions {
  maxWidthOrHeight?: number;
  maxSizeMB?: number;
  quality?: number;
  outputType?: 'image/webp' | 'image/jpeg';
}

/**
 * Compresses an image file in the browser using HTML5 Canvas.
 *
 * @param file The original image file selected by user
 * @param options Custom compression options (defaults to 1600px, 1MB target, 0.85 quality)
 * @returns A compressed File ready for multipart upload
 */
export async function compressImageForUpload(
  file: File,
  options: CompressionOptions = {}
): Promise<File> {
  const {
    maxWidthOrHeight = 1600,
    maxSizeMB = 1,
    quality = 0.85,
    outputType = 'image/webp',
  } = options;

  // If already small and matches target format, bypass canvas re-encoding
  if (file.size <= maxSizeMB * 1024 * 1024 && (file.type === outputType || file.type === 'image/webp')) {
    return file;
  }

  return new Promise((resolve, reject) => {
    const reader = new FileReader();

    reader.onload = (event) => {
      const img = new Image();
      img.onload = () => {
        let width = img.width;
        let height = img.height;

        // Calculate proportional scale
        if (width > maxWidthOrHeight || height > maxWidthOrHeight) {
          if (width > height) {
            height = Math.round((height * maxWidthOrHeight) / width);
            width = maxWidthOrHeight;
          } else {
            width = Math.round((width * maxWidthOrHeight) / height);
            height = maxWidthOrHeight;
          }
        }

        const canvas = document.createElement('canvas');
        canvas.width = width;
        canvas.height = height;

        const ctx = canvas.getContext('2d');
        if (!ctx) {
          reject(new Error('Không thể khởi tạo Canvas 2D context để xử lý ảnh.'));
          return;
        }

        // Draw image onto canvas (automatically strips EXIF/GPS metadata)
        ctx.drawImage(img, 0, 0, width, height);

        canvas.toBlob(
          (blob) => {
            if (!blob) {
              reject(new Error('Lỗi chuyển đổi Canvas sang định dạng ảnh nhị phân.'));
              return;
            }

            const extension = outputType === 'image/webp' ? '.webp' : '.jpg';
            const baseName = file.name.replace(/\.[^/.]+$/, '');
            const compressedFile = new File([blob], `${baseName}${extension}`, {
              type: outputType,
              lastModified: Date.now(),
            });

            resolve(compressedFile);
          },
          outputType,
          quality
        );
      };

      img.onerror = () => {
        reject(new Error('Tệp hình ảnh không hợp lệ hoặc không thể đọc được.'));
      };

      img.src = event.target?.result as string;
    };

    reader.onerror = () => {
      reject(new Error('Không thể đọc dữ liệu tệp tin.'));
    };

    reader.readAsDataURL(file);
  });
}
